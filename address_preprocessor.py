"""
address_preprocessor.py
-----------------------
Shared preprocessing module used by all audit scripts and the API server.
Fixes are systematic — each function targets an entire CLASS of problems,
not individual addresses.

Classes fixed:
  1. OCR corruption      : F1at n0 3O2 → Flat no 302
  2. Digit/letter fusion : room18chawlno3 → room 18 chawlno 3
  3. City name fusion    : ballygungecalcutta → ballygunge calcutta
  4. Common misspellings : Blok→Block, pilar→pillar, nr→near, opp→opposite
  5. City equivalences   : gurugram↔gurgaon, kolkata↔calcutta, bengaluru↔bangalore
"""

import re

# ---------------------------------------------------------------------------
# 1. City equivalence table
#    Used in clean_string_compare to accept equivalent city names as matches.
#    Both directions are listed so either side can be GT or resolved.
# ---------------------------------------------------------------------------
CITY_EQUIVALENCES = {
    "gurugram": "gurgaon",
    "gurgaon": "gurugram",
    "bengaluru": "bangalore",
    "bangalore": "bengaluru",
    "kolkata": "calcutta",
    "calcutta": "kolkata",
    "mumbai": "bombay",
    "bombay": "mumbai",
    "chennai": "madras",
    "madras": "chennai",
    "delhi": "newdelhi",
    "newdelhi": "delhi",
    "pune": "poona",
    "poona": "pune",
    "kochi": "cochin",
    "cochin": "kochi",
    "noida": "gautambudhnagar",
    "gautambudhnagar": "noida",
    "visakhapatnam": "vizag",
    "vizag": "visakhapatnam",
    "vadodara": "baroda",
    "baroda": "vadodara",
    "thiruvananthapuram": "trivandrum",
    "trivandrum": "thiruvananthapuram",
    "amritsar": "amritsar",
    # Phonetic equivalents
    "chandigad": "chandigarh",
    "amdavad": "ahmedabad",
    "banglor": "bengaluru",
    "mumbay": "mumbai",
    "dilli": "delhi",
    "gajiyabad": "ghaziabad",
    "hiderabad": "hyderabad",
    "calcuta": "kolkata",
    "chennay": "chennai",
    "nasik": "nashik",
    "maduray": "madurai",
    "simla": "shimla",
}

# ---------------------------------------------------------------------------
# 2. OCR character corrections (context-aware)
#    These are the most common OCR scanner mistakes in Indian addresses.
#    Applied per "word" (token), not globally, to avoid over-correction.
# ---------------------------------------------------------------------------

# Words that are commonly OCR-corrupted → their clean form
OCR_WORD_CORRECTIONS = {
    # flat / floor
    "f1at": "flat", "f1ot": "flat", "fiat": "flat",
    # no / number
    "n0": "no", "n0.": "no",
    # block
    "blok": "block", "bl0k": "block", "bl0ck": "block",
    # pillar
    "pilar": "pillar", "pillar": "pillar",
    # opposite
    "oppsite": "opposite", "opsite": "opposite",
    # near
    "neer": "near", "nea r": "near",
    # sector
    "sect0r": "sector",
    # road
    "ro ad": "road",
    # wing
    "w1ng": "wing",
    # plot
    "pl0t": "plot",
    # room
    "ro0m": "room", "r00m": "room",
    # shop
    "sh0p": "shop",
    # house
    "hous3": "house",
}

# In a run of digit characters, these substitutions are valid:
#   O → 0, o → 0, l → 1, I → 1, S → 5, Z → 2, B → 8
# In a run of letter characters, these substitutions are valid:
#   0 → O, 1 → l/i (context-dependent, skip for now)
DIGIT_LIKE_CHARS = {'O': '0', 'o': '0', 'l': '1', 'I': '1', 'S': '5', 'Z': '2'}

def _fix_ocr_in_token(token: str) -> str:
    """Fix OCR corruption within a single whitespace-delimited token."""
    # 1. Check direct word correction table first (fastest path)
    lower = token.lower().rstrip('.,;:')
    if lower in OCR_WORD_CORRECTIONS:
        return OCR_WORD_CORRECTIONS[lower]

    # 2. ONLY fix pincode-like sequences — all caps/digits, 5-7 chars
    #    e.g. '56O066' → '560066', '4OO069' → '400069'
    #    Must be mostly digits with some letter substitutes to qualify.
    if re.match(r'^[0-9A-Z]{5,7}$', token):
        digit_count = sum(1 for c in token if c.isdigit())
        if digit_count >= 3:  # at least 3 real digits → likely a pincode
            fixed = ""
            for ch in token:
                fixed += DIGIT_LIKE_CHARS.get(ch, ch)
            return fixed

    # 3. Short known-bad OCR words (≤5 chars) with a digit-like char:
    #    e.g. 'F1at', 'N0.', 'n0', 'Bl0k'
    #    Only attempt if token has ≤5 chars AND contains a digit-like char
    if len(token) <= 5 and re.search(r'[0OolIlS]', token):
        candidate = token
        for bad, good in [('0', 'O'), ('1', 'l'), ('I', 'l')]:
            candidate = candidate.replace(bad, good)
        lower_cand = candidate.lower()
        if lower_cand in OCR_WORD_CORRECTIONS:
            return OCR_WORD_CORRECTIONS[lower_cand]

    return token


def _fix_ocr(text: str) -> str:
    """Apply OCR corrections token-by-token across the full address string."""
    tokens = text.split()
    return " ".join(_fix_ocr_in_token(t) for t in tokens)


# ---------------------------------------------------------------------------
# 3. City/locality name de-fusion
#    Handles cases like 'ballygungecalcutta' where a city name is embedded
#    in a longer spaceless string. We split known city/locality names out.
# ---------------------------------------------------------------------------

# Ordered by length desc so longer names are matched before subsets
_CITIES_FOR_SPLIT = sorted([
    "thiruvananthapuram", "tiruchirappalli", "secunderabad", "visakhapatnam",
    "bhubaneswar", "gachibowli", "gachiboli", "secundrabad", "jamshedpur", 
    "jamshedpr", "muzaffarnagar", "muzafarnagar", "chittinagar", "subashpally",
    "ahmedabad", "bengaluru", "bangalore", "hyderabad", "iderabad", "hiderabad",
    "chandigarh", "chandigad", "darjiling", "coimbatore", "aurangabad",
    "faridabad", "ghaziabad", "navimumbai", "vijayawada", "puducherry",
    "pondicherry", "ponducherry", "koducherry", "moradabad", "moradbd", 
    "firozabad", "firozbad", "jabalpur", "jabalpr", "bhilwara", "bhilawada", 
    "udaipur", "udaypur", "jalandhar", "jalandr", "amritsar", "calcutta", 
    "kolkata", "chennai", "madras", "mumbai", "bombay", "mumbay", "nagpur", 
    "indore", "bhopal", "patna", "kochi", "cochin", "vizag", "vadodara", 
    "baroda", "surat", "jaipur", "lucknow", "pune", "poona", "noida", 
    "gurugram", "gurgaon", "thane", "howrah", "pimpri", "rajkot", "meerut", 
    "nashik", "nasik", "hubli", "dharwad", "mysuru", "mysore", "mangaluru", 
    "mangalore", "jodhpur", "agra", "kanpur", "varanasi", "allahabad", 
    "prayagraj", "ranchi", "raipur", "guwahati", "trivandrum", "madurai", 
    "tirupur", "salem", "erode", "vellore", "guntur", "nellore", "warangal", 
    "karimnagar", "belgaum", "bellary", "bidar", "gulbarga", "shimla", 
    "simla", "dehradun", "haridwar", "roorkee", "jalandhar", "patiala", 
    "ambala", "panaji", "panjim", "ratlam", "ratlamm", "ujjain", "ujain", 
    "kota", "kotaj", "alwar", "bikaner", "jaisalmer", "ajmer", "korba", 
    "bhilai", "bhilay", "dhanbad", "dhanbd", "bokaro", "mathura", "unnao", "unao"
], key=len, reverse=True)

def _split_embedded_cities(text: str) -> str:
    """
    Insert spaces around city/locality names that are fused into longer words.
    e.g. 'flt101blockagoldenpalmsnearcybercitygachiboliiderabad'
         → 'flt101 block a golden palms near cyber city gachibowli hyderabad'
    """
    known_cities = set(_CITIES_FOR_SPLIT)
    words = text.split()
    
    for city in _CITIES_FOR_SPLIT:
        new_words = []
        for w in words:
            if w.lower() in known_cities:
                new_words.append(w)
            elif city in w.lower():
                pattern_pre = r'(?<=[a-zA-Z0-9])(' + re.escape(city) + r')'
                split_w = re.sub(pattern_pre, r' \1', w, flags=re.IGNORECASE)
                pattern_post = r'(' + re.escape(city) + r')(?=[a-zA-Z0-9])'
                split_w = re.sub(pattern_post, r'\1 ', split_w, flags=re.IGNORECASE)
                new_words.extend(split_w.split())
            else:
                new_words.append(w)
        words = new_words
        
    return " ".join(words)




# ---------------------------------------------------------------------------
# 4. Personal Name & Recipient Extraction Helper
# ---------------------------------------------------------------------------

# Comprehensive Salutation / Title / Recipient Regex
NAME_SALUTATIONS = r'(?:mr|mrs|ms|miss|dr|prof|shri|smt|late|master|er|adv|m/s)'
CARE_OF_PREFIXES = r'(?:c/o|s/o|d/o|w/o|care\s+of|son\s+of|daughter\s+of|wife\s+of)'
ATTN_PREFIXES = r'(?:attn|attention|kind\s+attn|to|name|recipient|customer|contact\s+person)'

ADDRESS_START_KEYWORDS = {
    "flat", "plot", "room", "house", "shop", "quarter", "chawl", "makan", "villa", 
    "bungalow", "cottage", "apartment", "apartments", "office", "building", "hno", 
    "door", "unit", "block", "wing", "tower", "sector", "phase", "road", "street", 
    "lane", "nagar", "gali", "colony", "society", "near", "opp", "opposite", "behind", 
    "beside", "floor", "pocket", "khasra", "survey", "khata", "holding", "premise", 
    "premises", "bldg", "complex", "enclave", "heights", "residency", "court", "view"
}

def extract_and_strip_name(raw_text: str):
    """
    Detects and strips personal names, salutations, titles, and recipient identifiers 
    from the beginning of the address string.
    Returns: (clean_address, recipient_name)
    """
    if not raw_text:
        return raw_text, ""
    
    text = raw_text.strip()
    recipient_name = ""

    # Pattern 1: Explicit Salutation (e.g. "Mr. Rahul Sharma,", "Dr. Ananya Roy -")
    salutation_pattern = rf'^\s*({NAME_SALUTATIONS}\.?\s+[A-Za-z\.\'\s]+?)(?:,\s*|\s*[-–:]\s*|\s+(?=(?:h\.?no|flat|plot|room|house|shop|block|bldg|building|door|unit|qtr|quarter|near|opp|behind|beside|\d+|#|sector|phase|gali|road|street)\b))'
    m1 = re.match(salutation_pattern, text, re.IGNORECASE)
    if m1:
        recipient_name = m1.group(1).strip(" ,-–:")
        text = text[m1.end():].strip(" ,-–:")
        return text, recipient_name

    # Pattern 2: Care of / Son of / Wife of (e.g. "C/O Rajesh Gupta,", "S/O Ramesh Kumar,")
    care_of_pattern = rf'^\s*({CARE_OF_PREFIXES}[\s\:\.\-]+[A-Za-z\.\'\s]+?)(?:,\s*|\s*[-–:]\s*|\s+(?=(?:h\.?no|flat|plot|room|house|shop|block|bldg|building|door|unit|qtr|quarter|near|opp|behind|beside|\d+|#|sector|phase|gali|road|street)\b))'
    m2 = re.match(care_of_pattern, text, re.IGNORECASE)
    if m2:
        recipient_name = m2.group(1).strip(" ,-–:")
        text = text[m2.end():].strip(" ,-–:")
        return text, recipient_name

    # Pattern 3: Attention / To / Recipient Header (e.g. "Attn: Procurement Team,", "To: Rahul Sharma,")
    attn_pattern = rf'^\s*({ATTN_PREFIXES}[\s\:\.\-]+[A-Za-z0-9\.\'\s]+?)(?:,\s*|\s*[-–:]\s*|\s+(?=(?:h\.?no|flat|plot|room|house|shop|block|bldg|building|door|unit|qtr|quarter|near|opp|behind|beside|\d+|#|sector|phase|gali|road|street)\b))'
    m3 = re.match(attn_pattern, text, re.IGNORECASE)
    if m3:
        recipient_name = m3.group(1).strip(" ,-–:")
        text = text[m3.end():].strip(" ,-–:")
        return text, recipient_name

    # Pattern 4: Standalone name before comma + address keyword
    # e.g. "Rahul Sharma, H.No 18/4..." or "Pooja Verma, Flat 302..."
    parts = text.split(',', 1)
    if len(parts) == 2:
        first_clause = parts[0].strip()
        words = first_clause.split()
        if 1 <= len(words) <= 3 and all(re.match(r'^[A-Za-z\.]+$', w) for w in words):
            first_clause_lower = set(w.lower().strip('.') for w in words)
            if not first_clause_lower.intersection(ADDRESS_START_KEYWORDS):
                second_clause = parts[1].strip()
                second_clause_first_word = second_clause.split()[0].lower().strip(".,-;#") if second_clause.split() else ""
                if second_clause_first_word in ADDRESS_START_KEYWORDS or (second_clause and second_clause[0].isdigit()) or second_clause_first_word.startswith("h.") or second_clause_first_word.startswith("hno"):
                    recipient_name = first_clause
                    text = second_clause
                    return text, recipient_name

    return text, recipient_name

def preprocess_address(raw: str) -> str:
    """
    Unified normalizer applied prior to character-level feature extraction.
    Steps:
      0) Detect and strip personal names/salutations/care-of recipient headers
      a) Strip non-printable / trailing chars
      b) Fix OCR noise (0->o in words, 5->s in words)
      c) Split fused phone number + pincode combinations
      d) Split wing/block prefix fusions (bshanti -> b shanti)
      e) Keyword de-fusion (e.g. flat302 -> flat 302, blockb -> block b)
      f) Phonetic translations (phlat -> flat, kotej -> cottage) & Preposition Normalization (ke pas -> near)
      g) Split digit/letter fusion boundaries (room18 -> room 18)
      h) Split embedded city names from fused strings (ballygungecalcutta -> ballygunge calcutta)
      i) Final whitespace collapse
    """
    if not raw:
        return raw

    s = raw.strip()

    # (0) Strip personal names / salutations / care of headers
    s, _ = extract_and_strip_name(s)

    # (b) OCR fix
    s = _fix_ocr(s)

    # (c) Split fused phone number + pincode combinations
    s = re.sub(r'\b(\d{10})(\d{6})\b', r'\1 \2', s)

    # Split phonetic digit fusions (e.g., 'tchar' → 't char', 'bdo' → 'b do')
    s = re.sub(r'\b([a-zA-Z])(do|teen|char)\b', r'\1 \2', s, flags=re.IGNORECASE)

    # (d) Split single-letter wing/block prefixes (a-g followed by known building/society tokens)
    s = re.sub(r'\b([a-gA-G])(shanti|mangal|precious|preciyus|suraj|regency|nest|kunj|dham|vihar|palace|society|tower|wing|block)\b', r'\1 \2', s, flags=re.IGNORECASE)

    # (d1) Fix glued dots between words without spaces (e.g. galee.Patanagere -> galee, Patanagere)
    s = re.sub(r'([a-zA-Z0-9])\.([a-zA-Z])', r'\1, \2', s)

    # (d2) Regional Administrative & Locality keyword de-fusion (e.g. KengerihobliPatanagere -> Kengeri hobli Patanagere)
    # 1. CamelCase splitting (e.g. KengerihobliPatanagere -> Kengerihobli Patanagere)
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    # 2. Administrative keyword de-fusion
    ADMIN_DEFUSION_PATTERN = r'\b([a-zA-Z]{3,})(hobli|hoblii|hobly|hoblee|hobali|hoballi|taluka|taluk|taluq|tlk|tluka|tehsil|tahsil|tehesil|tahseel|tehseel|thsil|teshil|mandal|mandla|mandel|mandhal|mndl|mandalam|mandala)\b'
    s = re.sub(ADMIN_DEFUSION_PATTERN, r'\1 \2', s, flags=re.IGNORECASE)
    # 3. Land / plot identifier number de-fusion (e.g. khasra123 -> khasra 123, chak5 -> chak 5)
    s = re.sub(r'\b(khasra|khata|khatauni|chak|survey|plot|gali|lane|chawl|room|flat|hno)(\d+)\b', r'\1 \2', s, flags=re.IGNORECASE)

    # (d3) Pan-Indian Transliteration Normalization (Equivalence Families)
    TRANSLITERATION_MAP = {
        r'\b(galli|gali|galley|gal|gally|gallii|galee|galii|glli|gaali|galiyaa)\b': 'gali',
        r'\b(hobli|hoblii|hobly|hoblee|hobali|hoballi|hobliya)\b': 'hobli',
        r'\b(halli|hallii|hali|haali|hally|halle)\b': 'halli',
        r'\b(kere|keri|keere|kerey|kerre|kerr|keree|keray|kereya)\b': 'kere',
        r'\b(palya|palia|palliya|pallya|paly|palyae|palyaa|paalya)\b': 'palya',
        r'\b(pete|pette|peete|peteh|petay|peth|peta|petae)\b': 'pete',
        r'\b(nagara|nagarh|naagar|nager)\b': 'nagar',
        r'\b(wadi|waadi|wadee|wadiy|wady|vaadi|vadi|vadiy|wadiya)\b': 'wadi',
        r'\b(pada|paada|padaa|waada)\b': 'pada',
        r'\b(taluka|taluk|taluq|talook|talukaa|tlk|tluka)\b': 'taluk',
        r'\b(tehsil|tahsil|tehesil|tehsill|tahseel|tehseel|tehsheel|thsil|teshil)\b': 'tehsil',
        r'\b(mandal|mandla|mandel|mandhal|mandalh|mdl|mndl|mandalam|mandala)\b': 'mandal',
        r'\b(palli|pally|pali|palle|pallii|pallie|paali|paalli|palley)\b': 'palli',
        r'\b(thanda|tanda|thaanda|thandaa|taanda)\b': 'thanda',
        r'\b(colny|collony|coloney|coloni|colonie|clny)\b': 'colony',
        r'\b(khasra|khasraa|khashra|khasara|khasraah)\b': 'khasra',
        r'\b(khata|khatha|khaata|khataa|khatauni)\b': 'khata',
        r'\b(basti|bastii|bastee|basty)\b': 'basti',
        r'\b(chak|chaak|chaq|chakk)\b': 'chak',
        r'\b(chawl|chawll|chaul|chawle|chaawl)\b': 'chawl',
        r'\b(gaon|gao|gan|gaaon|gaawn|gaw|gav|gaav|gaava|gaam|gam)\b': 'gaon'
    }
    for pat, repl in TRANSLITERATION_MAP.items():
        s = re.sub(pat, repl, s, flags=re.IGNORECASE)

    # (e) Expanded Block/wing/phonetic keyword de-fusion
    # Includes standard and common phonetic variations of house, street, landmark, and number words
    KEYWORD_DEFUSION_PATTERN = r'(block|blak|wing|tower|flat|phlat|room|rum|house|hawus|haus|plot|pilet|pelot|shop|sop|hno|cottage|kotej|chawl|cawl|number|nuber|sector|secter|road|rod|colony|colny|society|sosaiti|sosayti|station|stasan|school|scul|building|bilding|near|ner|nner|behind|bhind|opposite|samne|apartment|apartments|apts|apt)'
    s = re.sub(KEYWORD_DEFUSION_PATTERN + r'(?=[a-zA-Z0-9])', r'\1 ', s, flags=re.IGNORECASE)
    s = re.sub(r'(?<=[a-zA-Z0-9])' + KEYWORD_DEFUSION_PATTERN, r' \1', s, flags=re.IGNORECASE)

    # Pre-clean Opp. and variations to remove trailing periods
    s = re.sub(r'\bopp\.\b|\bopp\b', 'opposite', s, flags=re.IGNORECASE)

    # (f) Phonetic / illiterate spelling translations & Preposition Normalization
    # Multi-word Hinglish & English phrases are matched first before single words
    phonetic_mappings = {
        # --- 1. FACING & OPPOSITE (English & Hinglish) ---
        r'\b(opp\.?\s*ke\s*s[aa]*mn[ey]\s*wal[aa]|ke\s*s[aa]*mn[ey]\s*wal[aa]|s[aa]*mn[ey]\s*wal[aa])\b': 'opposite',
        r'\b(ke\s*s[aa]*mn[ey]|k\s*s[aa]*mn[ey]|s[aa]*mn[ey]\s*me[in]*|opposite\s*to)\b': 'opposite',
        r'\b(oposite|oppsite|opposit|oppostie|oppossit|oppossite|oppisite|oppozite|opossite|opposte|oppoosite|opppossite|oppposit|oppossitte|oppost|s[aa]*mn[ey]|facinng|faceing|fascing|fasing|facng|facin|facig|faising|facingg|fcing)\b': 'opposite',

        # --- 2. BEHIND & BACKSIDE (English & Hinglish) ---
        r'\b(ke\s*p[eei]*chh?[eeya]*|k\s*p[eei]*chh?[eeya]*|p[eei]*chh?[eeya]*\s*ki\s*taraf|p[eei]*chh?[eeya]*\s*wal[aa]|back\s*side\s*me[in]*|back\s*me[in]*|p[eei]*chh?[eeya]*\s*me[in]*)\b': 'behind',
        r'\b(backside|back\s*side|back-side|backsde|backsid|backsied|backsides|backof|back\s*of|at\s*the\s*back|rear\s*side|rearside)\b': 'behind',
        r'\b(p[eei]*chh?[eeya]*|behined|behnd|beind|behindd|behiind|behhind|behnid|behid|behidn|beehind|bihind|bihend|behend|behin|behinde|behimd|behinnd|b-hind|kepeche|peche)\b': 'behind',

        # --- 3. IN FRONT OF & FRONT (English & Hinglish) ---
        r'\b(in\s*front\s*of|infront\s*of|infrontof|in\s*frontof|front\s*of|frontof|front\s*side|frontside|front-side|at\s*front|at\s*the\s*front|aage\s*ki\s*taraf|aagey\s*ki\s*taraf|aage\s*me[in]*|front\s*side\s*me[in]*|front\s*me[in]*)\b': 'in front of',
        r'\b(infront|infrnt|infornt|infron|froont|frontt|fronnt|aagey|aage)\b': 'in front of',

        # --- 4. BESIDE & ADJACENT & NEXT TO (English & Hinglish) ---
        r'\b(ke\s*bagal\s*me[in]*|k\s*bagal\s*me[in]*|ke\s*side\s*me[in]*|k\s*side\s*me[in]*|bagal\s*me[in]*|bagal\s*wal[aa]|side\s*me[in]*|by\s*side|byside)\b': 'beside',
        r'\b(adjacent\s*to|adjacentto|adjecent\s*to|adjecentto|adjacant\s*to|adjacnt\s*to|adjcent\s*to|adjent\s*to|adjacantto|adjto|adj\s*to)\b': 'beside',
        r'\b(adjecent|adjacant|adjacently|adjascent|adjasent|adjuscent|adjusent|adjacnt|adj)\b': 'beside',
        r'\b(next\s*to|nextto|next\s*too|nexttoo|nex\s*to|nexxt\s*to|neext\s*to|nextt\s*o|nxt\s*to|nxtto|next-to|nexttwo|next\s*2|next2|nex\s*2|nxt\s*2|nexxtto)\b': 'beside',
        r'\b(besid|besied|besdie|besside|besidee|besiide|besidde|besde|besiid|be-side|bsde|bagal)\b': 'beside',

        # --- 5. NEAR & CLOSE TO (English & Hinglish) ---
        r'\b(ke\s*p[aa]*ss?|k\s*p[aa]*ss?|p[aa]*ss?\s*me[in]*|p[aa]*ss?\s*mai|p[aa]*ss?\s*hi|p[aa]*ss?\s*hee|p[aa]*ss?\s*wal[aa]|kareeb\s*me[in]*|karib\s*me[in]*|nazdeek\s*me[in]*|najdik\s*me[in]*|bilkul\s*paas|bahut\s*paas)\b': 'near',
        r'\b(close\s*to|closeto|clsoe\s*to|closs\s*to|cloose\s*to|closee\s*to|clos\s*to|cloze\s*to|close\s*2|close2|close\s*by|closeby|near\s*by|near\s*to|nearto|near\s*too|neer\s*to|ner\s*to|nir\s*to)\b': 'near',
        r'\b(p[aa]*ss?|kareeb|karib|qareeb|nazdeek|najdik|najdeek|nazdik|neer|neaar|neir|nir|ner|neare|neear|nearr|neeer|nera|nre|nr|nehr|naer|n-ear)\b': 'near',

        # --- 6. TOWARDS & DIRECTIONAL (English & Hinglish) ---
        r'\b(ki\s*taraf|ke\s*taraf|k\s*taraf|taraf\s*se|ki\s*side|ke\s*side|k\s*side|side\s*me[in]*|us\s*taraf|iss\s*taraf|is\s*taraf|uss\s*taraf|direction\s*me[in]*)\b': 'towards',
        r'\b(taraf|taraph|trf|toward|twords|twrds|towads|towrds|towars|towrd|towarrds|towards|toword|towrad|towadrs|twowards|twds|towrdss|towardss|towarsd|twards)\b': 'towards',

        # --- 7. ABOVE & TOP (English & Hinglish) ---
        r'\b(ke\s*u[op]*ar|k\s*u[op]*ar|u[op]*ar\s*me[in]*|u[op]*ar\s*ki\s*taraf|u[op]*ar\s*wal[aa]|u[op]*ar\s*side|top\s*par|top\s*pe|top\s*me[in]*|on\s*top|onthetop|upper\s*side)\b': 'above',
        r'\b(u[op]+ar|u[op]+err?|uppar|uparr|opaar|abov|abve|aboe|abovve|abovee|aboove|abv|over|ovr|top|upper|upstairs|upp|uppper)\b': 'above',

        # --- 8. BELOW & UNDER (English & Hinglish) ---
        r'\b(ke\s*n[eei]*ch[eeya]*|k\s*n[eei]*ch[eeya]*|n[eei]*ch[eeya]*\s*ke|n[eei]*ch[eeya]*\s*me[in]*|n[eei]*ch[eeya]*\s*ki\s*taraf|n[eei]*ch[eeya]*\s*wal[aa]|n[eei]*ch[eeya]*\s*side|bottom\s*me[in]*|bottom\s*side|lower\s*side|bottom\s*of|below\s*the)\b': 'below',
        r'\b(n[eei]*ch[eeya]*|belo|belw|belew|bellow|beloww|belowe|belwo|belov|blw|under|underneath|underneeth|beneath|beneth|benath|bottom|lower|down|dwn|undr|uder|unnder|undder|undeer)\b': 'below',

        # Other standard phonetic translations
        r'\bphlat\b': 'flat',
        r'\bpilet\b': 'plot',
        r'\bpelot\b': 'plot',
        r'\bhawus\b': 'house',
        r'\bhaus\b': 'house',
        r'\bkotej\b': 'cottage',
        r'\bcawl\b': 'chawl',
        r'\brum\b': 'room',
        r'\bnuber\b': 'number',
        r'\bsop\b': 'shop',
        r'\bblak\b': 'block',
        r'\bsecter\b': 'sector',
        r'\brod\b': 'road',
        r'\bcolny\b': 'colony',
        r'\bsosaiti\b': 'society',
        r'\bsosayti\b': 'society',
        r'\bmetrostasan\b': 'metro station',
        r'\brailwaystasan\b': 'railway station',
        r'\bstasan\b': 'station',
        r'\bscul\b': 'school',
        r'\bbilding\b': 'building',
        r'\bner\b': 'near',
        r'\bnner\b': 'near',
        r'\bbhind\b': 'behind',
        r'\bamdavad\b': 'ahmedabad',
        r'\bbanglor\b': 'bangalore',
        r'\bmumbay\b': 'mumbai',
        r'\bdilli\b': 'delhi',
        r'\bgajiyabad\b': 'ghaziabad',
        r'\bhiderabad\b': 'hyderabad',
        r'\bcalcuta\b': 'calcutta',
        r'\bchennay\b': 'chennai',
        r'\bchandigad\b': 'chandigarh',
        r'\bnasik\b': 'nashik',
        r'\bmaduray\b': 'madurai',
        r'\bdo\b': '2',
        r'\bteen\b': '3',
        r'\bchar\b': '4',
    }
    for pattern, repl in phonetic_mappings.items():
        s = re.sub(pattern, repl, s, flags=re.IGNORECASE)

    # (g) Digit/letter boundary splitting
    s = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', s)

    # (h) City name de-fusion
    s = _split_embedded_cities(s)

    # Clean phonetic city mappings again after city splitting (e.g. "chandigad" split from longer word)
    for pattern, repl in phonetic_mappings.items():
        s = re.sub(pattern, repl, s, flags=re.IGNORECASE)

    # (i) Collapse whitespace
    s = " ".join(s.split())

    return s





# ---------------------------------------------------------------------------
# 5. City comparison helper — uses equivalences for fair evaluation
# ---------------------------------------------------------------------------

def _normalize_city(c: str) -> str:
    """Normalize a city string for comparison — removes punctuation and applies equivalences."""
    if not c:
        return ""
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(c)).lower()
    return CITY_EQUIVALENCES.get(clean, clean)


def city_matches(resolved_city: str, gt_city: str) -> bool:
    """
    Returns True if resolved_city and gt_city are equivalent,
    accounting for aliases (gurugram=gurgaon, kolkata=calcutta, etc.).
    """
    if not resolved_city or not gt_city:
        return resolved_city == gt_city
    return _normalize_city(resolved_city) == _normalize_city(gt_city)


# ---------------------------------------------------------------------------
# 6. Preposition Trimming Helper — Strips dangling prepositions from text
# ---------------------------------------------------------------------------
DANGLING_PREPOSITIONS = {
    "near", "opposite", "opp", "behind", "beside", "towards", "facing", 
    "adjacent to", "adjacent", "close to", "close", "next to", "next", 
    "above", "below", "under"
}

def trim_dangling_prepositions(text: str) -> str:
    """
    Strips trailing prepositions at the end of a street/landmark string if no landmark follows it.
    e.g., 'Flat 404 Block 3 Greenwood Residency near' -> 'Flat 404 Block 3 Greenwood Residency'
    """
    if not text:
        return text
    # Clean trailing dot after opposite
    text = re.sub(r'\bopposite\.\s*', 'opposite ', text, flags=re.IGNORECASE)
    words = text.strip().split()
    while words and words[-1].lower().strip(".,-;") in DANGLING_PREPOSITIONS:
        words.pop()
    return " ".join(words)

