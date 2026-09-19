import asyncio
import logging
import re
from time import monotonic
from collections.abc import AsyncGenerator
from google.genai import Client, errors, types
from app.config import settings
from app.core import actions
from app.core.critic import MARKER, mentioned_products, unverified_delivery, verify
from app.core.router import html_lang, route
from app.core.state import Session, session_store
from app.prompts.system import build_system_prompt

log = logging.getLogger("kapruka.agent")
client = Client(api_key=settings.gemini_api_key)

MODELS = list(dict.fromkeys([settings.gemini_model, *settings.gemini_fallback_models]))
SKIP_SIGNATURE = b"skip_thought_signature_validator"
MAX_COOLDOWN_SECONDS = 3600
_cooldown_until: dict[str, float] = {}
MAX_STEPS = 8
STILL_LOOKING_AFTER = 3
RETRYABLE = {429, 500, 502, 503, 504}
LANGUAGES = {"english", "sinhala", "singlish", "tamil", "tanglish"}
FALLBACK_TEXT = "Sorry, I lost my train of thought there 😅 Could you say that again?"
DELIVERY_NUDGE = (
    "[Internal check - not from the customer] Your reply promises delivery timing for products you haven't checked. "
    "Keep the same product picks and markers. If you know their city, call check_delivery (with product_id and their date) "
    "for the picks now, then reply. If you don't know the city yet, keep the picks but ask for the city instead of promising timing. "
    "Don't mention this check."
)


def _config(system: str, final: bool = False) -> types.GenerateContentConfig:
    kwargs = {
        "system_instruction": system,
        "tools": actions.TOOLS,
        "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
        "tool_config": types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode="NONE" if final else "AUTO")),
    }
    if settings.gemini_thinking_budget is not None:
        kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=settings.gemini_thinking_budget)
    return types.GenerateContentConfig(**kwargs)


def _merge_text(parts: list[types.Part]) -> list[types.Part]:
    """Join streamed text chunks into one part; keep function calls and thought signatures intact."""
    merged: list[types.Part] = []
    for part in parts:
        plain = part.text is not None and not part.function_call and not part.thought_signature and not part.thought
        if plain and merged and merged[-1].text is not None and not merged[-1].function_call and not merged[-1].thought:
            merged[-1] = types.Part(text=merged[-1].text + part.text, thought_signature=merged[-1].thought_signature)
        elif part.function_call or part.thought_signature or part.text:
            merged.append(part)
    return merged


class ModelsBusy(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"all models rate limited, retry in {retry_after}s")


def _available_models() -> list[str]:
    now = monotonic()
    ready = [m for m in MODELS if _cooldown_until.get(m, 0) <= now]
    if not ready:
        raise ModelsBusy(max(1, round(min(_cooldown_until.values()) - now)))
    return ready


def _cool_down(model: str, error: errors.APIError) -> None:
    match = re.search(r"retry in ([\d.]+)s", str(error.message or ""))
    seconds = float(match.group(1)) if match else 30.0
    _cooldown_until[model] = monotonic() + min(seconds, MAX_COOLDOWN_SECONDS)
    log.warning("%s rate limited for %.0fs", model, seconds)


def _for_model(model: str, contents: list[types.Content]) -> list[types.Content]:
    """Gemini 3 models reject tool calls without thought signatures, e.g. ones produced by a 2.5 model."""
    if "gemini-2" in model:
        return contents
    patched = []
    for content in contents:
        if any(p.function_call and not p.thought_signature for p in content.parts or []):
            content = types.Content(role=content.role, parts=[
                p.model_copy(update={"thought_signature": SKIP_SIGNATURE}) if p.function_call and not p.thought_signature else p
                for p in content.parts
            ])
        patched.append(content)
    return patched


async def _stream_step(contents: list[types.Content], config: types.GenerateContentConfig) -> AsyncGenerator[tuple[str, object], None]:
    """Yield ("delta", text) while the model streams, then ("parts", all parts).
    Before any output, falls back to the next model on rate limits and retries once on server errors."""
    for model in _available_models():
        for attempt in range(2):
            parts: list[types.Part] = []
            emitted = False
            try:
                stream = await client.aio.models.generate_content_stream(model=model, contents=_for_model(model, contents), config=config)
                async for chunk in stream:
                    candidate = chunk.candidates[0] if chunk.candidates else None
                    for part in (candidate.content.parts if candidate and candidate.content else None) or []:
                        if part.text and not part.thought:
                            emitted = True
                            yield "delta", part.text
                        parts.append(part)
                yield "parts", parts
                return
            except errors.APIError as e:
                if emitted or e.code not in RETRYABLE:
                    raise
                if e.code == 429:
                    _cool_down(model, e)
                    break
                if attempt:
                    break
                await asyncio.sleep(1.5)
    _available_models()
    raise ModelsBusy(5)


async def _rewrite(session: Session, system: str, issues: list[str]) -> str | None:
    note = types.Content(role="user", parts=[types.Part(text=(
        "[Internal quality check - not from the customer]\nYour last reply has problems:\n- " + "\n- ".join(issues)
        + "\nRewrite that reply fixing them. Use only products, prices and facts from tool results in this chat. "
        "Keep the same language, tone and the valid [[product:ID]] markers. Output only the corrected reply."
    ))])
    try:
        model = _available_models()[0]
        response = await client.aio.models.generate_content(
            model=model, contents=_for_model(model, [*session.contents, note]), config=_config(system, final=True))
        return (response.text or "").strip() or None
    except errors.APIError as e:
        if e.code == 429:
            _cool_down(model, e)
        log.warning("critic rewrite failed: %s", e.code)
        return None
    except ModelsBusy:
        return None


def _seed_profile(session: Session, profile: dict) -> None:
    """Restore long-term memory the browser kept from a previous visit (no personal details)."""
    last = profile.get("last_order")
    if isinstance(last, dict) and isinstance(last.get("items"), list):
        items = []
        for item in last["items"][:30]:
            if isinstance(item, dict) and item.get("product_id"):
                quantity = item.get("quantity")
                items.append({
                    "product_id": str(item["product_id"])[:80],
                    "name": str(item.get("name") or "")[:120],
                    "quantity": quantity if isinstance(quantity, int) and 0 < quantity < 100 else 1,
                })
        if items:
            session.memory["last_order"] = {"items": items, "city": str(last.get("city") or "")[:100]}
    if profile.get("language") in LANGUAGES:
        session.language = profile["language"]


async def _turn(session: Session, message: str, action: dict | None) -> AsyncGenerator[dict, None]:
    session.turn += 1
    routed = route(message, session)
    yield {"type": "meta", "language": routed["language"], "lang": html_lang(routed["language"]), "intent": routed["intent"]}

    if action and action.get("type") == "confirm_order":
        yield {"type": "order_pending"}
    note, events = await actions.apply_ui_action(session, action)
    for event in events:
        yield event

    text = message.strip() + (f"\n\n{note}" if note else "")
    session.add_content(types.Content(role="user", parts=[types.Part(text=text)]))

    turn_products: list[str] = []
    final_parts: list[types.Part] = []
    streamed = retried_empty = nudged = False
    system = ""
    step = 0
    while step < MAX_STEPS:
        last_step = step == MAX_STEPS - 1
        system = build_system_prompt(session, routed)
        parts: list[types.Part] = []
        buffered: list[str] = []
        async for kind, value in _stream_step(session.contents, _config(system, final=last_step)):
            if kind == "parts":
                parts = _merge_text(value)
            elif step == 0:
                yield {"type": "text_delta", "content": value}
            else:
                buffered.append(value)
        calls = [p.function_call for p in parts if p.function_call]
        if calls and step > 0:
            parts = [p for p in parts if p.function_call or p.thought_signature or not p.text]
        step += 1
        if not parts:
            if retried_empty:
                break
            retried_empty = True
            continue
        session.add_content(types.Content(role="model", parts=parts))

        if not calls:
            draft = "".join(p.text or "" for p in parts if not p.thought)
            if not nudged and not last_step and unverified_delivery(draft, session):
                nudged = True
                if step == 1:
                    yield {"type": "retract"}
                session.add_content(types.Content(role="user", parts=[types.Part(text=DELIVERY_NUDGE)]))
                continue
            final_parts, streamed = parts, step == 1
            break

        for call in calls:
            yield {"type": "tool_call", "tool": call.name}
            if call.name == "place_order":
                yield {"type": "order_pending"}
        results = await asyncio.gather(*(actions.run_tool(session, c.name, dict(c.args or {})) for c in calls))
        responses = []
        for call, (result, tool_events) in zip(calls, results):
            if "error" in result:
                log.info("tool %s -> %s", call.name, result.get("error"))
            for event in tool_events:
                if event["type"] == "products":
                    turn_products += [item["id"] for item in event["items"]]
                yield event
            responses.append(types.Part(function_response=types.FunctionResponse(id=call.id, name=call.name, response={"result": result})))
        session.add_content(types.Content(role="user", parts=responses))
        if step == STILL_LOOKING_AFTER:
            yield {"type": "status", "status": "still_looking"}

    draft = "".join(p.text or "" for p in final_parts if not p.thought)
    if not draft.strip():
        yield {"type": "replace", "content": FALLBACK_TEXT}
        session.add_content(types.Content(role="model", parts=[types.Part(text=FALLBACK_TEXT)]))
        return

    clean, issues = verify(draft, session, message)
    if issues:
        log.info("critic flagged: %s", issues)
        rewritten = await _rewrite(session, system, issues)
        if rewritten:
            clean, _ = verify(rewritten, session, message)
    if clean != draft:
        session.contents[-1] = types.Content(role="model", parts=[types.Part(text=clean)])
    if not streamed:
        yield {"type": "text_delta", "content": clean}
    elif clean != draft:
        yield {"type": "replace", "content": clean}
    if not MARKER.search(clean):
        ids = mentioned_products(clean, session, turn_products)
        if ids:
            yield {"type": "attach_products", "ids": ids}


async def chat_stream(session_id: str, message: str, action: dict | None = None, profile: dict | None = None) -> AsyncGenerator[dict, None]:
    session = session_store.get_or_create(session_id)
    if session.lock.locked():
        yield {"type": "error", "code": "busy", "message": "Still working on your last message — one sec!"}
        yield {"type": "done"}
        return

    async with session.lock:
        if profile and not session.contents:
            _seed_profile(session, profile)
        start = len(session.contents)
        completed = False
        try:
            async for event in _turn(session, message, action):
                yield event
            completed = True
        except ModelsBusy as e:
            yield {"type": "error", "code": "model_busy", "retry_after": e.retry_after,
                   "message": "Lots of shoppers right now 😅 Give me a few seconds."}
        except errors.APIError as e:
            log.warning("Gemini error %s: %s", e.code, e.message)
            busy = e.code in RETRYABLE
            yield {"type": "error", "code": "model_busy" if busy else "model_error",
                   "message": "I'm a bit overloaded right now 😅 Give me a moment and try again." if busy
                   else "Something went wrong on my side. Please try again."}
        except Exception:
            log.exception("chat turn failed")
            yield {"type": "error", "code": "internal", "message": "Something went wrong on my side. Please try again."}
        finally:
            if not completed:
                del session.contents[start:]
            session.trim_history()
        yield {"type": "done"}
