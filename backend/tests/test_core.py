import asyncio
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from google.genai import errors, types

from app.core import actions, agent
from app.core.cache import TTLCache
from app.core.catalog import colombo_now, normalize_product
from app.core.critic import unverified_delivery, verify
from app.core.router import detect_language, route
from app.core.state import Session
from app.mcp.client import parse_tool_result
from app.mcp import tools as mcp_tools

SEARCH_ITEM = {
    "id": "FLOWERS00T2075", "name": "6 Red Rose Bouquet", "price": {"amount": 5210, "currency": "LKR"},
    "compare_at_price": None, "in_stock": True, "stock_level": "low",
    "image_url": "https://static2.kapruka.com/product-image/width=330/x.jpg", "url": "https://www.kapruka.com/p",
    "category": {"name": "General"},
}
FULL_PRODUCT = {**SEARCH_ITEM, "images": ["https://www.kapruka.com/shops/a.jpg", "https://www.kapruka.com/shops/b.jpg"],
                "variants": [{"name": "S", "price": {"amount": 5210}}, {"name": "L", "price": {"amount": 7000}}],
                "delivery": {"island_wide": True}}


def run(coro):
    return asyncio.run(coro)


def session_with_product(in_stock=True) -> Session:
    session = Session("test-session")
    session.add_products([{**normalize_product(SEARCH_ITEM), "in_stock": in_stock}])
    return session


class McpParsing(unittest.TestCase):
    def test_json_text_block(self):
        self.assertEqual(parse_tool_result({"content": [{"type": "text", "text": '{"a": 1}'}], "isError": False}), {"a": 1})

    def test_error_text(self):
        result = parse_tool_result({"content": [{"type": "text", "text": "Error (order_not_found): No order"}]})
        self.assertEqual(result, {"error": "order_not_found", "message": "No order"})

    def test_is_error(self):
        result = parse_tool_result({"content": [{"type": "text", "text": "validation failed"}], "isError": True})
        self.assertEqual(result["error"], "invalid_request")

    def test_plain_text(self):
        self.assertEqual(parse_tool_result({"content": [{"type": "text", "text": "No products found"}]}), {"text": "No products found"})


class ProductShape(unittest.TestCase):
    def test_search_result(self):
        item = normalize_product(SEARCH_ITEM)
        for key in ("id", "name", "price", "currency", "in_stock", "stock_level", "image", "url"):
            self.assertIn(key, item)
        self.assertEqual(item["price"], 5210)

    def test_full_product_uses_resized_images_and_variants(self):
        item = normalize_product(FULL_PRODUCT)
        self.assertTrue(item["image"].startswith("https://static2.kapruka.com/product-image/"))
        self.assertEqual(len(item["variants"]), 2)
        self.assertTrue(item["island_wide"])


class CacheBehaviour(unittest.TestCase):
    def test_ttl_expiry(self):
        cache = TTLCache(ttl=60)
        with patch("app.core.cache.time", return_value=1000):
            cache.set("k", 1)
        with patch("app.core.cache.time", return_value=1059):
            self.assertEqual(cache.get("k"), 1)
        with patch("app.core.cache.time", return_value=1061):
            self.assertIsNone(cache.get("k"))

    def test_eviction_bounds_size(self):
        cache = TTLCache(ttl=60, max_entries=3)
        for i in range(10):
            cache.set(str(i), i)
        self.assertLessEqual(len(cache), 3)

    def test_errors_are_not_cached(self):
        fake = AsyncMock(return_value={"error": "unavailable", "message": "down"})
        with patch.object(mcp_tools.mcp_client, "call_tool", fake):
            run(mcp_tools.call_tool("get_product", {"product_id": "abc123"}))
            run(mcp_tools.call_tool("get_product", {"product_id": "abc123"}))
        self.assertEqual(fake.await_count, 2)

    def test_params_request_json(self):
        fake = AsyncMock(return_value={"results": [SEARCH_ITEM]})
        with patch.object(mcp_tools.mcp_client, "call_tool", fake):
            run(mcp_tools.call_tool("search_products", {"q": "unique roses query", "category": None}))
        name, params = fake.await_args.args
        self.assertEqual(name, "kapruka_search_products")
        self.assertEqual(params, {"q": "unique roses query", "response_format": "json"})


class CartRules(unittest.TestCase):
    def test_unknown_product_rejected(self):
        result, _ = run(actions.update_cart(Session("s"), product_id="MADEUP123"))
        self.assertEqual(result["error"], "unknown_product")

    def test_out_of_stock_rejected(self):
        result, _ = run(actions.update_cart(session_with_product(in_stock=False), product_id="FLOWERS00T2075"))
        self.assertEqual(result["error"], "out_of_stock")

    def test_add_and_remove(self):
        session = session_with_product()
        _, events = run(actions.update_cart(session, product_id="flowers00t2075", quantity=2))
        self.assertEqual(events[0]["cart"]["count"], 2)
        run(actions.update_cart(session, product_id="FLOWERS00T2075", quantity=0))
        self.assertEqual(session.cart, [])


def _fake_mcp(name, args=None, use_cache=True):
    if name == "list_delivery_cities":
        return {"cities": [{"name": "Kandy", "aliases": ["galagedara"]}]}
    if name == "get_product":
        return FULL_PRODUCT
    if name == "check_delivery":
        return {"city": "Kandy", "available": True, "rate": 1075, "currency": "LKR", "perishable_warning": None}
    if name == "create_order":
        return {"checkout_url": "https://pay.example/x", "order_ref": "ORD-1", "summary": {"grand_total": 6285, "currency": "LKR"}}
    raise AssertionError(name)


DETAILS = {
    "recipient": {"name": "Amma", "phone": "077 123 4567"},
    "delivery": {"address": "12 Temple Rd", "city": "galagedara", "date": (colombo_now().date() + timedelta(days=1)).isoformat()},
    "sender": {"name": "Nimal"},
    "gift_message": "Happy birthday!",
}


class OrderGate(unittest.TestCase):
    def setUp(self):
        self.mock = AsyncMock(side_effect=_fake_mcp)
        self.patches = [patch("app.core.actions.call_tool", self.mock), patch("app.core.catalog.call_tool", self.mock)]
        for p in self.patches:
            p.start()
        self.session = session_with_product()
        self.session.turn = 1
        run(actions.update_cart(self.session, product_id="FLOWERS00T2075"))

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_place_order_needs_summary(self):
        result, _ = run(actions.place_order(self.session))
        self.assertEqual(result["error"], "no_summary")

    def test_invalid_details_loop_back_to_model(self):
        result, _ = run(actions.prepare_order(self.session, recipient={"name": "A", "phone": "123"}, delivery={}, sender={}))
        self.assertEqual(result["error"], "missing_or_invalid_details")
        self.assertGreaterEqual(len(result["issues"]), 3)

    def test_summary_then_confirm_next_turn(self):
        result, events = run(actions.prepare_order(self.session, **DETAILS))
        self.assertEqual(events[0]["type"], "order_summary")
        summary = events[0]["summary"]
        self.assertEqual(summary["delivery"]["city"], "Kandy")
        self.assertEqual(summary["delivery_fee"], 1075)
        self.assertEqual(summary["recipient"]["phone"], "0771234567")
        self.assertNotIn("1234567", str(result))

        same_turn, _ = run(actions.place_order(self.session))
        self.assertEqual(same_turn["error"], "not_confirmed_yet")

        self.session.turn += 1
        placed, events = run(actions.place_order(self.session))
        self.assertEqual(placed["status"], "payment_link_ready")
        self.assertEqual(events[0]["data"]["checkout_url"], "https://pay.example/x")
        self.assertEqual(self.session.cart, [])
        self.assertIsNone(self.session.pending_order)

    def test_cart_change_invalidates_summary(self):
        run(actions.prepare_order(self.session, **DETAILS))
        run(actions.update_cart(self.session, product_id="FLOWERS00T2075", quantity=3))
        self.session.turn += 1
        result, _ = run(actions.place_order(self.session))
        self.assertEqual(result["error"], "no_summary")


class Routing(unittest.TestCase):
    def test_languages(self):
        self.assertEqual(detect_language("මට කේක් එකක් ඕනේ"), "sinhala")
        self.assertEqual(detect_language("அம்மாவுக்கு பூக்கள்"), "tamil")
        self.assertEqual(detect_language("machan mata rice ekak ona"), "singlish")
        self.assertEqual(detect_language("enakku romba nalla gift venum"), "tanglish")
        self.assertEqual(detect_language("I need a phone under 50k"), "english")

    def test_short_english_keeps_previous_language(self):
        session = Session("s")
        route("machan mata cake ekak ona", session)
        self.assertEqual(route("ok", session)["language"], "singlish")

    def test_intent_and_occasion(self):
        routed = route("I messed up, wife is angry, need flowers", Session("s"))
        self.assertEqual((routed["intent"], routed["occasion"]), ("gift", "apology"))
        self.assertEqual(route("where is my order VIMP34456CB2", Session("s"))["intent"], "track")


class Critic(unittest.TestCase):
    def test_invented_price_flagged(self):
        _, issues = verify("This one is only LKR 3,999!", session_with_product())
        self.assertTrue(issues)

    def test_real_price_passes(self):
        _, issues = verify("Two of these are LKR 10,420 [[product:FLOWERS00T2075]]", session_with_product())
        self.assertEqual(issues, [])

    def test_unknown_marker_removed_and_phone_masked(self):
        clean, _ = verify("Here:\n[[product:FAKE999]]\nCall 0771234567", session_with_product())
        self.assertNotIn("FAKE999", clean)
        self.assertNotIn("0771234567", clean)

    def test_delivery_promise_needs_a_check(self):
        session = session_with_product()
        text = "This one can reach Kandy tomorrow!\n[[product:FLOWERS00T2075]]"
        self.assertTrue(unverified_delivery(text, session))
        session.delivery_checks.append({"product_id": "FLOWERS00T2075", "available": True})
        self.assertFalse(unverified_delivery(text, session))
        self.assertFalse(unverified_delivery("Lovely roses [[product:FLOWERS00T2075]]", Session("s")))
        self.assertFalse(unverified_delivery("[[product:FLOWERS00T2075]]\nWhich city should we deliver to?", Session("s")))

    def test_out_of_stock_must_be_mentioned(self):
        _, issues = verify("[[product:FLOWERS00T2075]] great pick", session_with_product(in_stock=False))
        self.assertTrue(issues)


def _quota_error(seconds):
    return errors.APIError(429, {"error": {"code": 429, "message": f"Quota exceeded. Please retry in {seconds}s."}})


async def _collect(gen):
    return [item async for item in gen]


class ModelFallback(unittest.TestCase):
    def setUp(self):
        agent._cooldown_until.clear()

    def tearDown(self):
        agent._cooldown_until.clear()

    def test_rate_limited_model_falls_back_and_cools_down(self):
        calls = []

        async def fake_stream(model, contents, config):
            calls.append(model)
            if model == agent.MODELS[0]:
                raise _quota_error(12.5)

            async def chunks():
                yield SimpleNamespace(candidates=[SimpleNamespace(content=types.Content(role="model", parts=[types.Part(text="hi")]))])
            return chunks()

        user = [types.Content(role="user", parts=[types.Part(text="hello")])]
        with patch.object(agent.client.aio.models, "generate_content_stream", fake_stream):
            out = run(_collect(agent._stream_step(user, agent._config("sys"))))
            self.assertEqual(out[0], ("delta", "hi"))
            run(_collect(agent._stream_step(user, agent._config("sys"))))
        self.assertEqual(calls, [agent.MODELS[0], agent.MODELS[1], agent.MODELS[1]])

    def test_all_models_busy_reports_retry_time(self):
        async def always_limited(model, contents, config):
            raise _quota_error(20)

        user = [types.Content(role="user", parts=[types.Part(text="hello")])]
        with patch.object(agent.client.aio.models, "generate_content_stream", always_limited):
            with self.assertRaises(agent.ModelsBusy) as caught:
                run(_collect(agent._stream_step(user, agent._config("sys"))))
        self.assertTrue(15 <= caught.exception.retry_after <= 20)

    def test_gemini_3_gets_signature_for_unsigned_tool_calls(self):
        call = types.Part(function_call=types.FunctionCall(name="search_products", args={"q": "roses"}))
        contents = [types.Content(role="model", parts=[call])]
        self.assertIsNone(agent._for_model("models/gemini-2.5-flash", contents)[0].parts[0].thought_signature)
        self.assertEqual(agent._for_model("models/gemini-3.1-flash-lite", contents)[0].parts[0].thought_signature, agent.SKIP_SIGNATURE)


if __name__ == "__main__":
    unittest.main()
