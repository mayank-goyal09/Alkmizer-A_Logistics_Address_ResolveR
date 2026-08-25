import re

# Indian address markers (keywords) for substring matching in space-less strings
LANDMARK_TRIGGERS = ["opposite", "opp", "near", "behind", "nextto", "beside", "above", "under", "below", "close", "adjacent", "oppsite", "oppoist", "ner", "nr", "bhnd", "behnd"]
LANDMARK_OBJECTS = ["petrol", "pump", "temple", "church", "mosque", "school", "college", "hospital", "bank", "atm", "station", "stn", "stand", "office", "park", "mall", "market", "nursery", "hotel", "pharmacy", "medical", "clinic", "masjid", "mandir", "pandal", "tank", "pillar", "gate", "stop", "pond", "lake", "factory", "depot", "chowk", "nagar", "garden"]
STREET_TRIGGERS = ["road", "rd", "street", "st", "lane", "ln", "marg", "gali", "path", "way", "highway", "bypass", "cross", "main"]
HOUSE_TRIGGERS = ["flat", "plot", "house", "hno", "room", "shop", "floor", "block", "bldg", "building", "apt", "apartment", "society", "soc", "nivas", "niwas", "villa", "residency", "enclave", "heights", "garden", "park", "plaza", "tower", "arcade", "manor", "chawl", "quarter", "seat", "pocket", "wing", "cabin", "galinumber"]


INDIAN_CITIES = {
    # Primary metros
    "bengaluru", "bangalore", "mumbai", "bombay", "delhi", "newdelhi",
    "hyderabad", "secunderabad", "chennai", "madras",
    "kolkata", "calcutta", "pune", "poona",
    "ahmedabad", "jaipur", "lucknow", "patna", "indore",
    "coimbatore", "surat", "nagpur", "bhopal",
    "visakhapatnam", "vizag", "vadodara", "baroda",
    "kochi", "cochin", "chandigarh",
    # Metro administrative neighbours often written interchangeably
    "howrah", "thane", "navi mumbai", "navimumbai",
    "noida", "gurugram", "gurgaon", "faridabad", "ghaziabad",
    "pimprichinchwad", "pcmc",
    "secunderabad", "ranga reddy", "rangareddy",
    "tambaram", "kancheepuram"
}

INDIAN_LOCALITIES = {
    "koramangala", "indiranagar", "hsrlayout", "whitefield", "marathahalli", "jayanagar",
    "malleshwaram", "electroniccity", "btmlayout", "rajajinagar", "sadashivanagar", "hebbal",
    "yelahanka", "banashankari", "basavanagudi", "ulsoor", "cooketown", "frasertown",
    "richardstown", "borivali", "andheri", "bandra", "dadar", "thane", "kalyan", "goregaon",
    "powai", "chembur", "mulund", "vikhroli", "karolbagh", "connaughtplace", "dwarka", "rohini",
    "vasantkunj", "saket", "lajpatnagar", "rajourigarden", "chandnichowk", "jubileehills",
    "banjarahills", "gachibowli", "madhapur", "kondapur", "secunderabad", "kukatpally",
    "begumpet", "miyapur", "tnagar", "adyar", "velachery", "mylapore", "annanagar",
    "tambaram", "guindy", "nungambakkam", "saltlake", "rajarhat", "howrah", "garia",
    "behala", "newtown", "dumdum", "tollygunge", "hadapsar", "kothrud", "wakad",
    "vimannagar", "hinjenadi", "hinjewadi", "baner", "kalyaninagar", "pimpri",
    "panvel", "vashi", "kharghar", "nerul", "airoli"
}

INDIAN_STATES = {
    "karnataka", "ka", "maharashtra", "mh", "delhi", "dl", "telangana", "ts",
    "tamilnadu", "tn", "westbengal", "wb", "gujarat", "gj", "uttarpradesh", "up",
    "rajasthan", "rj", "bihar", "br", "madhyapradesh", "mp", "kerala", "kl",
    "andhrapradesh", "ap", "punjab", "pb", "haryana", "hr", "odisha", "od",
    "assam", "as"
}

def get_word_at(sent, i):
    """Finds the space-delimited word that the character at sent[i] belongs to."""
    start = i
    while start > 0 and not sent[start-1].isspace():
        start -= 1
    end = i
    while end < len(sent) and not sent[end].isspace():
        end += 1
    return "".join(sent[start:end]).lower().strip(',.')

def check_keyword_at(sent, i, keyword):
    """Checks if the substring of sent starting at i matches keyword (case-insensitive)."""
    k_len = len(keyword)
    if i + k_len <= len(sent):
        val = "".join(sent[i:i+k_len]).lower()
        return val == keyword
    return False

def char2features_optimized(sent, i, precomputed):
    char = sent[i]
    word = get_word_at(sent, i)
    n = len(sent)

    # --- Global position ratio features (prevents C/P labels appearing early) ---
    position_ratio = i / max(n - 1, 1)  # 0.0 = start, 1.0 = end
    # Divide address into 3 zones: early (first 40%), mid (40-70%), late (last 30%)
    in_early_zone = position_ratio < 0.40
    in_mid_zone = 0.40 <= position_ratio < 0.70
    in_late_zone = position_ratio >= 0.70

    # Base features
    features = {
        'bias': 1.0,
        'char': char.lower(),
        'char.isdigit()': char.isdigit(),
        'char.isupper()': char.isupper(),
        'char.ispunct()': not char.isalnum() and not char.isspace(),
        'char.isspace()': char.isspace(),

        # Word-level features (when spaces exist)
        'word_has_digit': any(c.isdigit() for c in word),
        'word_is_short': len(word) <= 2,
        'is_key_suffix': word in ['st', 'rd', 'road', 'ave', 'blvd', 'lane', 'street'],
        'is_indian_trigger': word in ['plot', 'flat', 'nivas', 'opp', 'near', 'floor', 'h', 'no', 'behind', 'beside'],

        # Space-less transitions (digit to letter or letter to digit)
        'digit_transition': i > 0 and sent[i].isdigit() != sent[i-1].isdigit(),
        'punct_transition': i > 0 and (not sent[i].isalnum() and not sent[i].isspace()) != (not sent[i-1].isalnum() and not sent[i-1].isspace()),

        # Global position zone features (strong structural priors)
        'position_early': in_early_zone,    # House numbers live here
        'position_mid': in_mid_zone,        # Street/Locality lives here
        'position_late': in_late_zone,      # City/State/Pincode lives here
        'position_ratio_bin': int(position_ratio * 10),  # 0-9 bin
        'is_known_city_word': word in INDIAN_CITIES,     # Hard city lexicon check
    }
    
    # Substring robust matching for space-less Indian markers (boundaries and spans)
    features['starts_landmark_trigger'] = any(check_keyword_at(sent, i, kw) for kw in LANDMARK_TRIGGERS)
    features['starts_landmark_object'] = any(check_keyword_at(sent, i, kw) for kw in LANDMARK_OBJECTS)
    features['starts_street_trigger'] = any(check_keyword_at(sent, i, kw) for kw in STREET_TRIGGERS)
    features['starts_house_trigger'] = any(check_keyword_at(sent, i, kw) for kw in HOUSE_TRIGGERS)
    
    features['is_landmark_trigger'] = i in precomputed['landmark_trigger']
    features['is_landmark_object'] = i in precomputed['landmark_object']
    features['is_street_trigger'] = i in precomputed['street_trigger']
    features['is_house_trigger'] = i in precomputed['house_trigger']
    
    # Soft dictionary matches
    features['is_indian_city_span'] = i in precomputed['city_span']
    features['is_indian_locality_span'] = i in precomputed['locality_span']
    features['is_indian_state_span'] = i in precomputed['state_span']
    
    # Individual quick checks for highly common keywords (e.g. plot, flat, opp, near, road)
    features['starts_plot'] = check_keyword_at(sent, i, 'plot')
    features['starts_flat'] = check_keyword_at(sent, i, 'flat')
    features['starts_opp'] = check_keyword_at(sent, i, 'opp') or check_keyword_at(sent, i, 'opposite')
    features['starts_near'] = check_keyword_at(sent, i, 'near')
    features['starts_road'] = check_keyword_at(sent, i, 'road') or check_keyword_at(sent, i, 'rd')
    
    features['is_plot'] = i in precomputed['plot']
    features['is_flat'] = i in precomputed['flat']
    features['is_opp'] = i in precomputed['opp']
    features['is_near'] = i in precomputed['near']
    features['is_road'] = i in precomputed['road']
    
    # 🔍 DYNAMIC WINDOW (Look 3 characters back/forward)
    for offset in range(1, 4):
        # Look Back
        if i - offset >= 0:
            features[f'-{offset}:char'] = sent[i-offset].lower()
            features[f'-{offset}:digit'] = sent[i-offset].isdigit()
            features[f'-{offset}:isupper'] = sent[i-offset].isupper()
        # Look Forward
        if i + offset < len(sent):
            features[f'+{offset}:char'] = sent[i+offset].lower()
            features[f'+{offset}:digit'] = sent[i+offset].isdigit()
            features[f'+{offset}:isupper'] = sent[i+offset].isupper()

    if i == 0: features['BOS'] = True
    if i == len(sent)-1: features['EOS'] = True
        
    return features

def extract_features(tokens):
    sent_str = "".join(tokens).lower()
    
    landmark_trigger_set = set()
    for kw in LANDMARK_TRIGGERS:
        for m in re.finditer(re.escape(kw), sent_str):
            landmark_trigger_set.update(range(m.start(), m.end()))
            
    landmark_object_set = set()
    for kw in LANDMARK_OBJECTS:
        for m in re.finditer(re.escape(kw), sent_str):
            landmark_object_set.update(range(m.start(), m.end()))
            
    street_trigger_set = set()
    for kw in STREET_TRIGGERS:
        for m in re.finditer(re.escape(kw), sent_str):
            street_trigger_set.update(range(m.start(), m.end()))
            
    house_trigger_set = set()
    for kw in HOUSE_TRIGGERS:
        for m in re.finditer(re.escape(kw), sent_str):
            house_trigger_set.update(range(m.start(), m.end()))
            
    plot_set = set()
    for m in re.finditer(r'plot', sent_str):
        plot_set.update(range(m.start(), m.end()))
        
    flat_set = set()
    for m in re.finditer(r'flat', sent_str):
        flat_set.update(range(m.start(), m.end()))
        
    opp_set = set()
    for kw in ['opp', 'opposite']:
        for m in re.finditer(re.escape(kw), sent_str):
            opp_set.update(range(m.start(), m.end()))
            
    near_set = set()
    for m in re.finditer(r'near', sent_str):
        near_set.update(range(m.start(), m.end()))
        
    road_set = set()
    for kw in ['road', 'rd']:
        for m in re.finditer(re.escape(kw), sent_str):
            road_set.update(range(m.start(), m.end()))
            
    city_span_set = set()
    for kw in INDIAN_CITIES:
        for m in re.finditer(re.escape(kw), sent_str):
            city_span_set.update(range(m.start(), m.end()))
            
    locality_span_set = set()
    for kw in INDIAN_LOCALITIES:
        for m in re.finditer(re.escape(kw), sent_str):
            locality_span_set.update(range(m.start(), m.end()))
            
    state_span_set = set()
    for kw in INDIAN_STATES:
        for m in re.finditer(re.escape(kw), sent_str):
            state_span_set.update(range(m.start(), m.end()))
            
    precomputed = {
        'landmark_trigger': landmark_trigger_set,
        'landmark_object': landmark_object_set,
        'street_trigger': street_trigger_set,
        'house_trigger': house_trigger_set,
        'plot': plot_set,
        'flat': flat_set,
        'opp': opp_set,
        'near': near_set,
        'road': road_set,
        'city_span': city_span_set,
        'locality_span': locality_span_set,
        'state_span': state_span_set
    }
    
    return [char2features_optimized(tokens, i, precomputed) for i in range(len(tokens))]
