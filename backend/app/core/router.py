import re
from app.core.state import Session

SINHALA_SCRIPT = re.compile(r"[඀-෿]")
TAMIL_SCRIPT = re.compile(r"[஀-௿]")
WORD = re.compile(r"[a-z']+")

SINGLISH_STRONG = {
    "machan", "machang", "ona", "oney", "onee", "kiyala", "ekak", "denna", "dennako", "puluwan", "puluwanda",
    "karanna", "ganna", "gannada", "thiyenawa", "tiyenawa", "thiyanawa", "kohomada", "monawada", "mokakda",
    "lassana", "patta", "supiri", "elakiri", "gedara", "heta", "anidda", "ganan", "keeyada", "kiyada",
    "wenuwen", "yawanna", "yawanawa", "hoyanna", "hoyala", "nathnam", "mokak", "kawda", "oyata", "mata",
}
SINGLISH_WEAK = {
    "aiyo", "ane", "hari", "ow", "nane", "nehe", "neda", "wage", "eka", "malli", "nangi", "akka", "aiya",
    "ayya", "thaththa", "honda", "hondai", "bn", "ban", "oya", "oyage", "mage", "dan", "ada", "epa", "godak",
    "tikak", "poddak", "ekka", "ekata", "kenek", "kenekta", "balanna", "enna", "yanna", "salli", "amma",
}
TANGLISH_STRONG = {
    "vanakkam", "venum", "vendum", "irukku", "irukka", "romba", "sollunga", "pannunga", "eppadi", "enakku",
    "unakku", "evvalavu", "ethanai", "kudunga", "vaanga", "neenga", "illai", "paarunga", "vaangi", "sapadu",
}
TANGLISH_WEAK = {"enna", "nalla", "sollu", "podu", "anna", "thambi", "appa", "paati", "thatha", "naan", "nee", "sari", "seri", "machi", "illa"}

INTENTS = [
    ("track", re.compile(r"\btrack|where('?s| is) my (order|parcel|package)|order status|\b[A-Z]{3,5}\d{3,}[A-Z0-9]*\b|කොහෙද.*ඇණවුම|order eka koheda", re.I)),
    ("reorder", re.compile(r"same as last|last time|re-?order|order again|previous order|kalin wage|ayeth|ආයෙත්|කලින් වගේ", re.I)),
    ("checkout", re.compile(r"check ?out|place (the |my )?order|\bpay\b|payment|continue to delivery|my address|deliver it to|yes,? place", re.I)),
    ("delivery", re.compile(r"deliver|delivery|arrive|when can|by tomorrow|by today|\bheta\b|\bada\b|courier|යවන්න|ගෙනැල්ලා|டெலிவரி", re.I)),
    ("gift", re.compile(r"gift|present|surprise|for my (wife|husband|mom|mum|mother|dad|father|sister|brother|friend|girlfriend|boyfriend|boss|teacher)|thaagi|thagi|තෑග්ග|තෑගි|பரிசு", re.I)),
]

OCCASIONS = [
    ("apology", re.compile(r"messed up|mess(ed)? it up|angry|sorry|apolog|fight|argument|broke ?up|break ?up|forgive|upset|tharaha|කේන්ති|සමාව|தப்பு", re.I)),
    ("sympathy", re.compile(r"funeral|condolence|passed away|\bdied\b|sympathy|mala gedara|මළ ගෙදර|අවමංගල|இரங்கல்", re.I)),
    ("birthday", re.compile(r"birthday|b'?day|upandina|upan dina|උපන්දින|பிறந்த", re.I)),
    ("anniversary", re.compile(r"anniversary|valentine|romantic|propos(e|al)|date night", re.I)),
    ("avurudu", re.compile(r"avurudu|new year|අවුරුදු|புத்தாண்டு|kavili|කැවිලි", re.I)),
    ("wedding", re.compile(r"wedding|marriage|engagement|homecoming|magul|මගුල|திருமண", re.I)),
    ("get_well", re.compile(r"hospital|get well|\bsick\b|surgery|recover|ලෙඩ", re.I)),
    ("newborn", re.compile(r"\bbaby\b|newborn|new born|baby shower|babata|බබා", re.I)),
    ("corporate", re.compile(r"corporate|office|client|staff|colleague|employees|hamper|bulk", re.I)),
    ("festive", re.compile(r"christmas|xmas|vesak|poson|deepavali|diwali|ramadan|ramazan|\beid\b|pongal|mother'?s day|father'?s day|teacher'?s day", re.I)),
    ("achievement", re.compile(r"graduat|exam|results|promotion|new job|congrat", re.I)),
    ("everyday", re.compile(r"grocer|\brice\b|dhal|sugar|milk powder|onion|potato|vegetable|cooking oil|detergent|soap|nappies|diaper|essentials|weekly|monthly|phone|laptop|\btv\b|fridge|earbuds|headphone|shoes|for myself|for me\b", re.I)),
]


def detect_language(text: str) -> str:
    if SINHALA_SCRIPT.search(text):
        return "sinhala"
    if TAMIL_SCRIPT.search(text):
        return "tamil"
    words = set(WORD.findall(text.lower()))
    si_strong, si_weak = len(words & SINGLISH_STRONG), len(words & SINGLISH_WEAK)
    ta_strong, ta_weak = len(words & TANGLISH_STRONG), len(words & TANGLISH_WEAK)
    if ta_strong and ta_strong + ta_weak > si_strong + si_weak:
        return "tanglish"
    if si_strong or si_weak >= 2:
        return "singlish"
    if ta_weak >= 2:
        return "tanglish"
    return "english"


def route(text: str, session: Session) -> dict:
    """Pick language, intent (which specialist leads) and occasion playbook for this turn."""
    language = detect_language(text)
    if language == "english" and session.language != "english" and len(text.split()) < 4:
        language = session.language
    session.language = language

    intent = next((name for name, pattern in INTENTS if pattern.search(text)), None)
    occasion = next((name for name, pattern in OCCASIONS if pattern.search(text)), None)
    if occasion and occasion != "everyday":
        session.remember(occasion=occasion)
    if intent is None:
        if session.pending_order:
            intent = "checkout"
        elif occasion and occasion != "everyday":
            intent = "gift"
        else:
            intent = "shop"
    return {"language": language, "intent": intent, "occasion": occasion or session.memory.get("occasion")}


def html_lang(language: str) -> str:
    return {"sinhala": "si", "tamil": "ta"}.get(language, "en")
