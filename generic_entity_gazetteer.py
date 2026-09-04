"""
generic_entity_gazetteer.py
---------------------------
Authoritative Indian Generic Landmark, Building, Commercial, Locality,
and Civic Entity Gazetteer with comprehensive phonetic and regional transliterations.

Provides:
1. Category classification (BUILDING, COMMERCIAL, LOCALITY, TRANSPORT, etc.)
2. Distinctive Proper Name extraction (isolating 'Drd' from 'Drd Tower', 'Sai' from 'Sai Arcade')
3. Generic inflation protection: prevents matching 'Drd Tower' to 'RK Tower' just because both have 'Tower'
"""

import re
from typing import Tuple, Set

# 1. Building / Property Generic Tokens
BUILDING_TOKENS = {
    "tower", "towers", "towering", "towr", "towrs", "twr", "twrs",
    "building", "bldg", "bld", "buildng", "buildin", "buildingg",
    "block", "blck", "blok", "blk", "blockk",
    "house", "hse", "hous", "home", "homes",
    "residence", "residency", "residance", "residense", "resdt",
    "flat", "flt", "fl", "flats",
    "apartment", "apartments", "apt", "apmt", "aprt", "appartment", "appartments",
    "bhawan", "bhavan", "bhawanam", "bhawan.", "niketan", "niketanam", "niketn",
    "sadan", "sadanam", "sadn",
    "niwas", "nivas", "niwaas", "nivaas", "niwasam", "nivasam",
    "kunj", "kunja", "kutir", "kuteer", "kutira",
    "villa", "villas", "vilaa", "vilas", "bungalow", "bunglow", "kothi", "haveli", "haweli"
}

# 2. Commercial / Shopping Generic Tokens
COMMERCIAL_TOKENS = {
    "plaza", "plazza", "plasa", "plz",
    "complex", "complexx", "comlex", "complx", "cmplx",
    "mall", "maal", "mal", "malls",
    "market", "markit", "markett", "mkt",
    "bazaar", "bazar", "bajar", "bajaar", "bzr",
    "arcade", "arkade", "arcad",
    "emporium", "emporeum",
    "centre", "center", "centr", "cntr", "ctr",
    "mart", "supermart", "super market", "supermarket",
    "retail", "outlet", "showroom", "show room", "show-room",
    "warehouse", "godown", "gdn", "depot", "dep",
    "shop", "shp", "store", "stores", "str", "shopping", "commercial", "residential", "retail", "business", "trade",
    "dukan", "dukaan", "dukkan", "kirana", "mandi", "mundi", "haat", "hat"
}

# 3. Locality / Area / Ward Generic Tokens
LOCALITY_TOKENS = {
    "nagar", "nagara", "nagarh", "ngr",
    "colony", "colny", "coloni", "clny",
    "extension", "ext", "extn", "extention",
    "layout", "lay out", "lay-out", "layot", "lyout",
    "phase", "ph", "phs", "phes",
    "sector", "sec", "sectr",
    "block", "blk", "bl",
    "area", "ariya", "locality", "loc", "localty",
    "town", "towm", "twn",
    "village", "vill", "vlge", "vlg", "gaon",
    "district", "dist", "distrct",
    "suburb", "suburban", "ward", "wrd", "pete", "pet", "basti", "baddi"
}

# 4. Office / Institutional Generic Tokens
INSTITUTIONAL_TOKENS = {
    "office", "off", "ofc", "head office", "regional office", "branch office", "corporate office",
    "institute", "inst", "institution", "academy",
    "school", "sch", "vidyalaya", "vidyalay", "vidhyalaya",
    "college", "coll", "mahavidyalaya",
    "university", "univ", "vishwavidyalaya",
    "campus", "camp", "hostel",
    "kendra", "kendr", "seva kendra", "jan seva kendra", "vikas bhawan",
    "collectorate", "secretariat", "parishad", "nigam"
}

# 5. Medical / Public Health Tokens
MEDICAL_TOKENS = {
    "hospital", "hosp", "hsp", "clinic", "clnc",
    "nursing home", "nursinghome", "health centre", "health center", "medical centre", "medical center",
    "dispensary", "disp", "diagnostic centre", "diagnostic center", "lab", "laboratory", "labs"
}

# 6. Transport Generic Tokens
TRANSPORT_TOKENS = {
    "station", "stn", "sta", "railway station", "rly station", "rly stn", "rail stn",
    "junction", "jn", "jct", "junc", "terminal", "term",
    "bus stand", "busstop", "bus stop", "bus depot", "isbt",
    "metro", "metro station", "metro stn", "metro stop",
    "airport", "air port", "harbour", "harbor", "port", "dock", "docks"
}

# 7. Road / Street Generic Tokens
ROAD_TOKENS = {
    "road", "rd", "rod", "rood", "rode",
    "street", "st", "lane", "ln",
    "gali", "galli", "gal", "marg", "mrg", "path", "paath",
    "highway", "hiway", "hwy", "expressway", "expway",
    "flyover", "overbridge", "bridge", "pul", "setu",
    "cross", "cross road", "crossroad", "main road", "main rd",
    "ring road", "link road", "service road", "service rd", "bypass", "bye pass"
}

# 8. Residential Society / Campus Tokens
RESIDENTIAL_SOCIETY_TOKENS = {
    "society", "soc", "housing society", "housing", "housing complex", "housing colony",
    "enclave", "enclv", "heights", "height", "gardens", "garden",
    "park", "parks", "terrace", "terraces", "villas", "villa", "courts", "court",
    "greens", "green", "meadows", "meadow", "hills", "view", "views"
}

# 9. Religious / Cultural Generic Tokens
RELIGIOUS_TOKENS = {
    "mandir", "mandira", "temple", "devalaya", "devalay", "devsthan", "shrine",
    "masjid", "mosque", "dargah", "mazar", "gurudwara", "gurdwara",
    "derasar", "basadi", "church", "chapel", "cathedral", "ashram", "math", "mutt",
    "vihara", "vihar", "stupa", "samadhi"
}

# 10. Geographic / Physical Landmark Generics
GEOGRAPHIC_TOKENS = {
    "lake", "talab", "talav", "taalaab", "kere", "cheruvu", "pokhar", "pukur", "pond",
    "river", "nadi", "nadhi", "canal", "nahar", "stream", "nullah", "nala",
    "hill", "pahad", "pahar", "tekri", "konda", "mount", "mountain",
    "forest", "van", "jungle", "bagh", "bag", "bagan", "maidan", "ground", "field",
    "chowk", "chauraha", "circle", "square", "junction", "crossing", "more", "mor"
}

# Aggregate master set of all generic tokens
ALL_GENERIC_TOKENS: Set[str] = (
    BUILDING_TOKENS | COMMERCIAL_TOKENS | LOCALITY_TOKENS |
    INSTITUTIONAL_TOKENS | MEDICAL_TOKENS | TRANSPORT_TOKENS |
    ROAD_TOKENS | RESIDENTIAL_SOCIETY_TOKENS | RELIGIOUS_TOKENS |
    GEOGRAPHIC_TOKENS
)

# Compile a fast multi-token regex pattern
_SORTED_GENERIC_PHRASES = sorted([t for t in ALL_GENERIC_TOKENS if " " in t], key=len, reverse=True)
_SINGLE_GENERIC_WORDS = {t for t in ALL_GENERIC_TOKENS if " " not in t}

def is_generic_token(token: str) -> bool:
    """Checks if a single word is a generic entity descriptor."""
    clean = re.sub(r'[^a-zA-Z0-9]', '', token.lower())
    return clean in _SINGLE_GENERIC_WORDS

def extract_distinctive_name(phrase: str) -> str:
    """
    Strips generic entity tokens (Towers, Plaza, Complex, Bhavan, Market, Road, etc.)
    from a landmark or locality phrase to isolate the unique proper noun name.
    
    Examples:
      'Drd Tower'          -> 'Drd'
      'RK Tower'           -> 'RK'
      'GK Tower'           -> 'GK'
      'Shree Ganesh Towers'-> 'Shree Ganesh'
      'Sai Arcade'         -> 'Sai'
      'Chandra Layout'     -> 'Chandra'
      'BEML Layout'        -> 'BEML'
    """
    if not phrase:
        return ""
        
    clean_phrase = phrase.strip()
    
    # Strip multi-word generic phrases first (e.g. 'shopping complex', 'commercial centre')
    p_lower = clean_phrase.lower()
    for gp in _SORTED_GENERIC_PHRASES:
        p_lower = re.sub(rf'\b{re.escape(gp)}\b', '', p_lower)
        
    # Strip single generic words
    words = p_lower.split()
    distinctive_words = [w for w in words if re.sub(r'[^a-zA-Z0-9]', '', w) not in _SINGLE_GENERIC_WORDS]
    
    result = " ".join(distinctive_words).strip()
    return result

def is_purely_generic_entity(phrase: str) -> bool:
    """Returns True if the phrase contains ONLY generic descriptors with no proper noun."""
    dist = extract_distinctive_name(phrase)
    return len(dist.strip()) == 0

def do_distinctive_names_match(name_a: str, name_b: str, min_similarity: float = 0.80) -> bool:
    """
    Verifies that the core proper nouns match, preventing false matches between
    'Drd Tower' and 'RK Tower' simply because both contain 'Tower'.
    """
    dist_a = extract_distinctive_name(name_a).lower().replace(" ", "")
    dist_b = extract_distinctive_name(name_b).lower().replace(" ", "")
    
    # If both phrases are purely generic, we cannot safely match
    if not dist_a or not dist_b:
        return False
        
    # Exact match of proper names
    if dist_a == dist_b:
        return True
        
    # Substring match if long enough (>= 4 chars)
    if len(dist_a) >= 4 and len(dist_b) >= 4:
        if dist_a in dist_b or dist_b in dist_a:
            return True
            
    # Fuzzy match on the proper nouns only!
    import difflib
    ratio = difflib.SequenceMatcher(None, dist_a, dist_b).ratio()
    return ratio >= min_similarity
