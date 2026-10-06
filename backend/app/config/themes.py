"""Theme taxonomy and signal config. Single source of truth for theme-related tuning."""

THEMES = ["quality", "delivery", "packaging", "size_fit", "value", "usability"]

# Natural-language prototype sentences used for semantic (embedding) similarity.
THEME_PROTOTYPES = {
    "quality": [
        "The product is well made and durable.",
        "This item broke or fell apart quickly.",
        "The build quality feels solid and premium.",
        "The material feels cheap and flimsy.",
        "It works reliably without defects.",
        "The product arrived damaged or defective.",
    ],
    "delivery": [
        "The package arrived on time.",
        "Shipping took much longer than expected.",
        "Delivery was fast and smooth.",
        "The order was delayed for weeks.",
        "The courier handled the shipment well.",
        "Tracking information was inaccurate or missing.",
    ],
    "packaging": [
        "The box arrived in good condition.",
        "The packaging was crushed or torn.",
        "The item was well protected inside the box.",
        "There was not enough padding in the package.",
        "The packaging looked nice and presentable.",
        "The seal was broken when it arrived.",
    ],
    "size_fit": [
        "The size was exactly as described.",
        "It runs too small and doesn't fit.",
        "The fit is comfortable and true to size.",
        "It is too large and loose.",
        "The dimensions matched the listing.",
        "The sizing chart was misleading.",
    ],
    "value": [
        "This is a great price for what you get.",
        "It feels overpriced for the quality.",
        "Good value for the money.",
        "Not worth the price paid.",
        "A fair deal compared to similar products.",
        "I regret spending this much on it.",
    ],
    "usability": [
        "It is easy and intuitive to use.",
        "The instructions were confusing and hard to follow.",
        "Setup was quick and straightforward.",
        "It is complicated to operate.",
        "The interface or controls are user friendly.",
        "I couldn't figure out how to use it.",
    ],
}

# Lexical keyword/phrase dictionary per theme, used for the lexical signal.
THEME_KEYWORDS = {
    "quality": [
        "quality", "durable", "sturdy", "broke", "broken", "defect", "defective",
        "flimsy", "cheaply made", "well made", "solid", "fell apart", "damaged",
        "material", "build quality", "craftsmanship",
    ],
    "delivery": [
        "delivery", "shipping", "shipped", "arrived", "late", "delayed", "on time",
        "tracking", "courier", "carrier", "fast shipping", "slow shipping",
        "took forever", "lost package",
    ],
    "packaging": [
        "packaging", "box", "package", "crushed", "torn", "padding", "wrapped",
        "seal", "bubble wrap", "dented", "presentation", "unboxing",
    ],
    "size_fit": [
        "size", "fit", "fits", "too small", "too big", "too large", "tight",
        "loose", "sizing", "runs small", "runs large", "true to size", "snug",
    ],
    "value": [
        "price", "value", "worth", "overpriced", "expensive", "cheap", "affordable",
        "money", "deal", "cost", "pricey", "budget",
    ],
    "usability": [
        "easy to use", "difficult to use", "intuitive", "instructions", "setup",
        "confusing", "user friendly", "complicated", "manual", "interface",
        "simple to operate",
    ],
}

# Negation cues used by the lexical signal's simple negation check.
NEGATION_CUES = ["not", "n't", "no", "never", "without", "hardly", "barely"]

# Contrast cues used by clause_split to break clauses on top of sentence boundaries.
CONTRAST_CUES = ["but", "although", "however", "though", "while"]
