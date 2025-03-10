import random

words = [
    "aback", "abase", "abate", "abbey", "abbot", "abhor", "abide", "abled", "abode", "abort", "about", "above", "abuse",
    "abyss",
    "acorn", "acrid", "actor", "acute", "adage", "adapt", "adept", "admin", "admit", "adopt", "adore", "adorn", "adult",
    "affix",
    "after", "again", "agent", "agile", "aging", "aglow", "agony", "agree", "ahead", "aisle", "alarm", "album", "alert",
    "algae",
    "alias", "alibi", "alien", "align", "alike", "alive", "allow", "alloy", "alone", "along", "aloof", "aloud", "alpha",
    "altar",
    "alter", "amber", "amble", "amend", "amiss", "among", "ample", "amuse", "angel", "anger", "angle", "angry", "angst",
    "anise",
    "ankle", "annex", "annoy", "anvil", "apart", "apple", "apply", "apron", "arise", "armor", "aroma", "arose", "arrow",
    "aside",
    "asset", "atoll", "attic", "audio", "audit", "augur", "aural", "avail", "avoid", "awake", "award", "aware", "awful",
    "azure",
    "bacon", "badge", "badly", "bagel", "baggy", "baker", "ballet", "balmy", "banjo", "barge", "barren", "basal",
    "basic", "basil",
    "basin", "basis", "baste", "batch", "bathe", "baton", "battle", "baulk", "beach", "beads", "beast", "beech",
    "beefy", "befit",
    "began", "begun", "beige", "being", "belie", "belly", "below", "bench", "berry", "berth", "bevel", "bezel", "bible",
    "bicep",
    "biddy", "bigot", "bilge", "billy", "binge", "biome", "bison", "black", "blade", "blame", "bland", "blank", "blast",
    "blaze",
    "bleak", "blend", "bless", "blimp", "blind", "blink", "bliss", "bloat", "block", "blond", "blood", "bloom", "blown",
    "bluff",
    "blunt", "blurt", "blush", "board", "boast", "bobby", "boney", "bonus", "booth", "booty", "booze", "bosom", "botch",
    "bough",
    "bowel", "boxer", "brace", "braid", "brain", "brake", "brand", "brash", "brave", "bravo", "brawn", "bread", "break",
    "breed",
    "breeze", "brick", "bride", "brief", "brine", "bring", "brink", "brisk", "broad", "broil", "broke", "brook",
    "broom", "broth",
    "brown", "brush", "brute", "buddy", "budge", "buggy", "build", "built", "bully", "bunch", "bunny", "burly", "burns",
    "burst",
    "bushy", "busty", "buyer", "cabin", "cable", "cacti", "cadet", "cagey", "cairn", "camel", "cameo", "canal", "candy",
    "canoe",
    "canon", "caper", "carat", "cargo", "carol", "carry", "carve", "caste", "catch", "cater", "cause", "cedar", "chain",
    "chair",
    "chant", "chaos", "charm", "chart", "chase", "cheap", "check", "cheer", "chest", "chief", "child", "chili", "chime",
    "china",
    "chirp", "chock", "choir", "choke", "chord", "chore", "chuck", "cider", "cinch", "civic", "civil", "claim", "clamp",
    "clang",
    "clash", "clasp", "class", "clerk", "cling", "clink", "cloak", "clock", "clone", "close", "cloth", "cloud", "clown",
    "cluck",
    "clued", "clump", "clung", "coach", "coast", "cobra", "cocoa", "colon", "color", "comet", "comic", "comma", "comet",
    "comfy",
    "coral", "cordy", "corky", "costs", "couch", "crack", "crane", "crave", "crawl", "crazy", "creak", "crept", "cress",
    "crest",
    "crime", "crook", "cross", "crown", "crust", "crypt", "cubic", "cumin", "curly", "curve", "curvy", "cycle", "daily",
    "dairy",
    "daisy", "dance", "dated", "daunt", "dealt", "death", "decal", "decor", "decoy", "defer", "delta", "dense", "depth",
    "derby",
    "detox", "devil", "diary", "digit", "dingy", "dirty", "dizzy", "dodge", "doing", "doubt", "dowdy", "dozen", "draft",
    "drama",
    "drawn", "dread", "dream", "dress", "dried", "drill", "drink", "drive", "drown", "druid", "dumpy", "dusty", "early",
    "earth",
    "ebony", "edged", "eject", "elder", "elect", "elite", "email", "empty", "enjoy", "epoch", "equal", "equip", "erase",
    "error",
    "ethos", "evade", "event", "exact", "exile", "exist", "extra", "facet", "faith", "false", "fancy", "fatal", "feast",
    "fetch",
    "fetal", "fever", "fifth", "fight", "flame", "flare", "flash", "float", "flock", "flora", "flour", "fluff", "fluid",
    "flung",
    "flute", "focal", "focus", "force", "forge", "forth", "found", "frame", "fraud", "fresh", "froth", "fruit", "frost",
    "funky",
    "funny", "fuzzy", "gamma", "giant", "giver", "glare", "glass", "glide", "gloom", "glory", "glove", "glued", "gnash",
    "gnome",
    "goose", "grace", "grain", "grand", "grant", "grasp", "grass", "grave", "great", "grief", "grill", "gross", "grove",
    "guard",
    "guess", "guest", "guide", "guild", "guilt", "guise", "gully", "gumbo", "gusty", "habit", "hairy", "halft", "happy",
    "harsh",
    "hasty", "haunt", "havoc", "heady", "heart", "heavy", "hedge", "hello", "henry", "heron", "hilly", "hitch", "hoist",
    "honey",
    "honor", "horde", "horny", "horse", "hotel", "hound", "hover", "human", "humid", "humor", "humph", "hurry", "ideal",
    "image",
    "impel", "inert", "infer", "infix", "inner", "input", "irony", "issue", "ivory", "jaunt", "jewel", "joint", "jolly",
    "joust",
    "jumbo", "jumpy", "junior", "kneel", "knife", "known", "kudos", "label", "latch", "later", "layer", "leaky",
    "legal", "lobby",
    "local", "logic", "lodge", "lofty", "loner", "loose", "lover", "lower", "lucid", "lucky", "lunar", "lunch", "lunge",
    "lyric",
    "macho", "maker", "match", "moist", "motto", "music", "muted", "mylar", "nadir", "nasal", "nasty", "needy", "nerve",
    "never",
    "newly", "night", "noble", "noisy", "north", "novel", "nymph", "ocean", "offer", "olive", "optic", "orbit", "other",
    "outer",
    "ovary", "oxide", "ozone", "paddy", "paint", "panic", "paper", "party", "peace", "penny", "peril", "petal", "pivot",
    "place",
    "plane", "plant", "plate", "plaza", "plead", "plump", "point", "polar", "poppy", "porch", "pouch", "pound", "pride",
    "prize",
    "probe", "proxy", "pulse", "pupil", "quail", "quilt", "query", "quick", "quiet", "quilt", "quote", "racer", "radio",
    "rainy",
    "ranch", "rapid", "rebel", "relic", "renew", "revel", "ridge", "rifle", "river", "robot", "rodeo", "roomy", "rosin",
    "round",
    "royal", "rugby", "rusty", "salty", "savvy", "scarf", "scary", "scone", "score", "scorn", "scrap", "sheep", "shine",
    "shiny",
    "shoes", "shout", "shrew", "silly", "skate", "sleep", "small", "smile", "smoke", "snake", "solar", "toxic", "track",
    "talky", "throw", "trick", "total", "under", "unity",
    "upset", "usual", "vocal", "vowel", "video", "viper", "vivid", "vocal", "voyce", "youth"
]


# Function to randomly select a word
def choose_random_word():
    return random.choice(words)


if __name__ == "__main__":
    random_word = choose_random_word()
    print(f"Random Wordle word: {random_word}")
