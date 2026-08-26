"""
regional_vocabulary.py
----------------------
Probabilistic, context-aware Pan-Indian Regional Locality & Directional Gazetteer.
Covers 11 major linguistic and administrative zones:
1. Bengali / West Bengal
2. Tamil Nadu
3. Telugu / AP & Telangana
4. Kannada / Karnataka
5. Marathi / Maharashtra
6. Hindi / North India
7. Gujarati
8. Malayalam / Kerala
9. Odia / Odisha
10. Punjabi
11. Assamese

Stores metadata: surface form, canonical standard, language, regions, category, confidence.
"""

import re

# ---------------------------------------------------------------------------
# Master Regional Schema Dictionary
# ---------------------------------------------------------------------------
REGIONAL_GAZETTEER = [
    # =========================================================================
    # 1. BENGALI / WEST BENGAL
    # =========================================================================
    # Locality markers
    {"surface": "para", "canonical": "para", "language": "bengali", "regions": ["west_bengal", "tripura", "assam"], "category": "locality_marker", "confidence": 0.95},
    {"surface": "paraa", "canonical": "para", "language": "bengali", "regions": ["west_bengal"], "category": "locality_marker", "confidence": 0.95},
    {"surface": "polli", "canonical": "palli", "language": "bengali", "regions": ["west_bengal"], "category": "locality_marker", "confidence": 0.95},
    {"surface": "sarani", "canonical": "sarani", "language": "bengali", "regions": ["west_bengal"], "category": "road_type", "confidence": 0.98},
    {"surface": "sharani", "canonical": "sarani", "language": "bengali", "regions": ["west_bengal"], "category": "road_type", "confidence": 0.98},
    {"surface": "shoroni", "canonical": "sarani", "language": "bengali", "regions": ["west_bengal"], "category": "road_type", "confidence": 0.98},
    {"surface": "pukur", "canonical": "pukur", "language": "bengali", "regions": ["west_bengal"], "category": "water_body", "confidence": 0.95},
    {"surface": "more", "canonical": "more", "language": "bengali", "regions": ["west_bengal"], "category": "junction", "confidence": 0.95},
    {"surface": "mor", "canonical": "more", "language": "bengali", "regions": ["west_bengal"], "category": "junction", "confidence": 0.95},
    {"surface": "bagan", "canonical": "bagan", "language": "bengali", "regions": ["west_bengal"], "category": "locality_marker", "confidence": 0.95},
    {"surface": "danga", "canonical": "danga", "language": "bengali", "regions": ["west_bengal"], "category": "locality_marker", "confidence": 0.95},
    {"surface": "tala", "canonical": "tala", "language": "bengali", "regions": ["west_bengal"], "category": "locality_marker", "confidence": 0.95},
    # Directional
    {"surface": "baam dike", "canonical": "on the left", "language": "bengali", "regions": ["west_bengal"], "category": "directional", "confidence": 0.98},
    {"surface": "bam dike", "canonical": "on the left", "language": "bengali", "regions": ["west_bengal"], "category": "directional", "confidence": 0.98},
    {"surface": "daan dike", "canonical": "on the right", "language": "bengali", "regions": ["west_bengal"], "category": "directional", "confidence": 0.98},
    {"surface": "dan dike", "canonical": "on the right", "language": "bengali", "regions": ["west_bengal"], "category": "directional", "confidence": 0.98},
    {"surface": "pechhone", "canonical": "behind", "language": "bengali", "regions": ["west_bengal"], "category": "relationship", "confidence": 0.98},
    {"surface": "pichhone", "canonical": "behind", "language": "bengali", "regions": ["west_bengal"], "category": "relationship", "confidence": 0.98},
    {"surface": "upore", "canonical": "above", "language": "bengali", "regions": ["west_bengal"], "category": "relationship", "confidence": 0.98},
    {"surface": "pashe", "canonical": "beside", "language": "bengali", "regions": ["west_bengal"], "category": "relationship", "confidence": 0.98},
    {"surface": "paashe", "canonical": "beside", "language": "bengali", "regions": ["west_bengal"], "category": "relationship", "confidence": 0.98},
    {"surface": "kache", "canonical": "near", "language": "bengali", "regions": ["west_bengal"], "category": "relationship", "confidence": 0.98},
    {"surface": "kachhe", "canonical": "near", "language": "bengali", "regions": ["west_bengal"], "category": "relationship", "confidence": 0.98},

    # =========================================================================
    # 2. TAMIL NADU
    # =========================================================================
    # Locality markers
    {"surface": "theru", "canonical": "theru", "language": "tamil", "regions": ["tamil_nadu", "puducherry"], "category": "street_type", "confidence": 0.98},
    {"surface": "salai", "canonical": "salai", "language": "tamil", "regions": ["tamil_nadu"], "category": "road_type", "confidence": 0.98},
    {"surface": "saalai", "canonical": "salai", "language": "tamil", "regions": ["tamil_nadu"], "category": "road_type", "confidence": 0.98},
    {"surface": "pettai", "canonical": "pettai", "language": "tamil", "regions": ["tamil_nadu"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "kuppam", "canonical": "kuppam", "language": "tamil", "regions": ["tamil_nadu", "andhra_pradesh"], "category": "settlement", "confidence": 0.95},
    {"surface": "palayam", "canonical": "palayam", "language": "tamil", "regions": ["tamil_nadu"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "ooru", "canonical": "oor", "language": "tamil", "regions": ["tamil_nadu"], "category": "settlement", "confidence": 0.95},
    {"surface": "kovil", "canonical": "kovil", "language": "tamil", "regions": ["tamil_nadu"], "category": "landmark", "confidence": 0.98},
    {"surface": "koil", "canonical": "kovil", "language": "tamil", "regions": ["tamil_nadu"], "category": "landmark", "confidence": 0.98},
    {"surface": "kulam", "canonical": "kulam", "language": "tamil", "regions": ["tamil_nadu"], "category": "water_body", "confidence": 0.95},
    {"surface": "medu", "canonical": "medu", "language": "tamil", "regions": ["tamil_nadu"], "category": "locality_marker", "confidence": 0.95},
    # Directional
    {"surface": "munnaadi", "canonical": "in front of", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "munadi", "canonical": "in front of", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "pinnadi", "canonical": "behind", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "pinnaadi", "canonical": "behind", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "keezhe", "canonical": "below", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "keela", "canonical": "below", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "pakkam", "canonical": "side", "language": "tamil", "regions": ["tamil_nadu"], "category": "directional", "confidence": 0.98},
    {"surface": "kitta", "canonical": "near", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "kittae", "canonical": "near", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "arugil", "canonical": "near", "language": "tamil", "regions": ["tamil_nadu"], "category": "relationship", "confidence": 0.98},
    {"surface": "valathu", "canonical": "on the right", "language": "tamil", "regions": ["tamil_nadu"], "category": "directional", "confidence": 0.98},
    {"surface": "valadhu", "canonical": "on the right", "language": "tamil", "regions": ["tamil_nadu"], "category": "directional", "confidence": 0.98},
    {"surface": "idathu", "canonical": "on the left", "language": "tamil", "regions": ["tamil_nadu"], "category": "directional", "confidence": 0.98},
    {"surface": "idadhu", "canonical": "on the left", "language": "tamil", "regions": ["tamil_nadu"], "category": "directional", "confidence": 0.98},

    # =========================================================================
    # 3. TELUGU / TELANGANA & ANDHRA PRADESH
    # =========================================================================
    # Locality markers
    {"surface": "veedhi", "canonical": "veedhi", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "street_type", "confidence": 0.98},
    {"surface": "vidhi", "canonical": "veedhi", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "street_type", "confidence": 0.98},
    {"surface": "thanda", "canonical": "thanda", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "settlement", "confidence": 0.98},
    {"surface": "tanda", "canonical": "thanda", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "settlement", "confidence": 0.98},
    {"surface": "gudem", "canonical": "gudem", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "settlement", "confidence": 0.98},
    {"surface": "cheruvu", "canonical": "cheruvu", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "water_body", "confidence": 0.98},
    {"surface": "kunta", "canonical": "kunta", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "water_body", "confidence": 0.98},
    {"surface": "konda", "canonical": "konda", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "hill", "confidence": 0.95},
    # Directional
    {"surface": "mundhu", "canonical": "in front of", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "mundu", "canonical": "in front of", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "venaka", "canonical": "behind", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "paina", "canonical": "above", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "kindha", "canonical": "below", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "kinda", "canonical": "below", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "pakkana", "canonical": "beside", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "daggara", "canonical": "near", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "daggira", "canonical": "near", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "relationship", "confidence": 0.98},
    {"surface": "edama", "canonical": "on the left", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "directional", "confidence": 0.98},
    {"surface": "kudi", "canonical": "on the right", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "directional", "confidence": 0.98},
    {"surface": "vaipu", "canonical": "towards", "language": "telugu", "regions": ["telangana", "andhra_pradesh"], "category": "directional", "confidence": 0.98},

    # =========================================================================
    # 4. KANNADA / KARNATAKA
    # =========================================================================
    # Locality markers
    {"surface": "halli", "canonical": "halli", "language": "kannada", "regions": ["karnataka"], "category": "village_suffix", "confidence": 0.98},
    {"surface": "palya", "canonical": "palya", "language": "kannada", "regions": ["karnataka"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "paalya", "canonical": "palya", "language": "kannada", "regions": ["karnataka"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "pete", "canonical": "pete", "language": "kannada", "regions": ["karnataka"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "kere", "canonical": "kere", "language": "kannada", "regions": ["karnataka"], "category": "water_body", "confidence": 0.98},
    {"surface": "katte", "canonical": "katte", "language": "kannada", "regions": ["karnataka"], "category": "platform", "confidence": 0.95},
    {"surface": "beedi", "canonical": "beedi", "language": "kannada", "regions": ["karnataka"], "category": "street_type", "confidence": 0.98},
    {"surface": "agrahara", "canonical": "agrahara", "language": "kannada", "regions": ["karnataka"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "thota", "canonical": "thota", "language": "kannada", "regions": ["karnataka"], "category": "estate", "confidence": 0.95},
    {"surface": "gudi", "canonical": "gudi", "language": "kannada", "regions": ["karnataka"], "category": "temple", "confidence": 0.98},
    # Directional
    {"surface": "munde", "canonical": "in front of", "language": "kannada", "regions": ["karnataka"], "category": "relationship", "confidence": 0.98},
    {"surface": "mundhe", "canonical": "in front of", "language": "kannada", "regions": ["karnataka"], "category": "relationship", "confidence": 0.98},
    {"surface": "hinde", "canonical": "behind", "language": "kannada", "regions": ["karnataka"], "category": "relationship", "confidence": 0.98},
    {"surface": "hindhe", "canonical": "behind", "language": "kannada", "regions": ["karnataka"], "category": "relationship", "confidence": 0.98},
    {"surface": "kelage", "canonical": "below", "language": "kannada", "regions": ["karnataka"], "category": "relationship", "confidence": 0.98},
    {"surface": "pakkadalli", "canonical": "beside", "language": "kannada", "regions": ["karnataka"], "category": "relationship", "confidence": 0.98},
    {"surface": "hattira", "canonical": "near", "language": "kannada", "regions": ["karnataka"], "category": "relationship", "confidence": 0.98},
    {"surface": "hatra", "canonical": "near", "language": "kannada", "regions": ["karnataka"], "category": "relationship", "confidence": 0.98},
    {"surface": "edagade", "canonical": "on the left", "language": "kannada", "regions": ["karnataka"], "category": "directional", "confidence": 0.98},
    {"surface": "balagade", "canonical": "on the right", "language": "kannada", "regions": ["karnataka"], "category": "directional", "confidence": 0.98},
    {"surface": "kadege", "canonical": "towards", "language": "kannada", "regions": ["karnataka"], "category": "directional", "confidence": 0.98},

    # =========================================================================
    # 5. MARATHI / MAHARASHTRA
    # =========================================================================
    # Locality markers
    {"surface": "ali", "canonical": "ali", "language": "marathi", "regions": ["maharashtra"], "category": "lane", "confidence": 0.95},
    {"surface": "aali", "canonical": "ali", "language": "marathi", "regions": ["maharashtra"], "category": "lane", "confidence": 0.95},
    {"surface": "wadi", "canonical": "wadi", "language": "marathi", "regions": ["maharashtra", "gujarat"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "vaadi", "canonical": "wadi", "language": "marathi", "regions": ["maharashtra", "gujarat"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "pada", "canonical": "pada", "language": "marathi", "regions": ["maharashtra"], "category": "settlement", "confidence": 0.98},
    {"surface": "paada", "canonical": "pada", "language": "marathi", "regions": ["maharashtra"], "category": "settlement", "confidence": 0.98},
    {"surface": "wada", "canonical": "wada", "language": "marathi", "regions": ["maharashtra"], "category": "mansion_settlement", "confidence": 0.98},
    {"surface": "peth", "canonical": "peth", "language": "marathi", "regions": ["maharashtra"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "chawl", "canonical": "chawl", "language": "marathi", "regions": ["maharashtra"], "category": "tenement", "confidence": 0.98},
    {"surface": "vasti", "canonical": "vasti", "language": "marathi", "regions": ["maharashtra"], "category": "settlement", "confidence": 0.95},
    # Directional
    {"surface": "samor", "canonical": "opposite", "language": "marathi", "regions": ["maharashtra"], "category": "relationship", "confidence": 0.98},
    {"surface": "mage", "canonical": "behind", "language": "marathi", "regions": ["maharashtra"], "category": "relationship", "confidence": 0.98},
    {"surface": "pudhe", "canonical": "ahead", "language": "marathi", "regions": ["maharashtra"], "category": "relationship", "confidence": 0.98},
    {"surface": "varti", "canonical": "above", "language": "marathi", "regions": ["maharashtra"], "category": "relationship", "confidence": 0.98},
    {"surface": "khali", "canonical": "below", "language": "marathi", "regions": ["maharashtra"], "category": "relationship", "confidence": 0.98},
    {"surface": "javal", "canonical": "near", "language": "marathi", "regions": ["maharashtra"], "category": "relationship", "confidence": 0.98},
    {"surface": "bajula", "canonical": "beside", "language": "marathi", "regions": ["maharashtra"], "category": "relationship", "confidence": 0.98},
    {"surface": "shejari", "canonical": "next to", "language": "marathi", "regions": ["maharashtra"], "category": "relationship", "confidence": 0.98},
    {"surface": "davikade", "canonical": "on the left", "language": "marathi", "regions": ["maharashtra"], "category": "directional", "confidence": 0.98},
    {"surface": "ujvikade", "canonical": "on the right", "language": "marathi", "regions": ["maharashtra"], "category": "directional", "confidence": 0.98},

    # =========================================================================
    # 6. HINDI / NORTH INDIA
    # =========================================================================
    # Locality markers
    {"surface": "mohalla", "canonical": "mohalla", "language": "hindi", "regions": ["delhi", "up", "bihar", "rajasthan", "mp", "haryana"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "basti", "canonical": "basti", "language": "hindi", "regions": ["delhi", "up", "bihar", "rajasthan", "mp", "haryana"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "gaon", "canonical": "gaon", "language": "hindi", "regions": ["north_india"], "category": "village", "confidence": 0.98},
    {"surface": "tola", "canonical": "tola", "language": "hindi", "regions": ["bihar", "jharkhand", "up"], "category": "settlement", "confidence": 0.98},
    {"surface": "dera", "canonical": "dera", "language": "hindi", "regions": ["punjab", "haryana", "rajasthan"], "category": "settlement", "confidence": 0.95},
    {"surface": "dhani", "canonical": "dhani", "language": "hindi", "regions": ["rajasthan", "haryana"], "category": "hamlet", "confidence": 0.98},
    {"surface": "khera", "canonical": "khera", "language": "hindi", "regions": ["up", "haryana"], "category": "village", "confidence": 0.98},
    {"surface": "sarai", "canonical": "sarai", "language": "hindi", "regions": ["delhi", "up", "bihar"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "chauraha", "canonical": "chauraha", "language": "hindi", "regions": ["north_india"], "category": "crossroads", "confidence": 0.98},
    {"surface": "phatak", "canonical": "phatak", "language": "hindi", "regions": ["north_india"], "category": "railway_crossing", "confidence": 0.98},
    # Directional
    {"surface": "baayein", "canonical": "on the left", "language": "hindi", "regions": ["north_india"], "category": "directional", "confidence": 0.98},
    {"surface": "baaye", "canonical": "on the left", "language": "hindi", "regions": ["north_india"], "category": "directional", "confidence": 0.98},
    {"surface": "daayein", "canonical": "on the right", "language": "hindi", "regions": ["north_india"], "category": "directional", "confidence": 0.98},
    {"surface": "daaye", "canonical": "on the right", "language": "hindi", "regions": ["north_india"], "category": "directional", "confidence": 0.98},
    {"surface": "saamne", "canonical": "opposite", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "samne", "canonical": "opposite", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "aage", "canonical": "ahead", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "peeche", "canonical": "behind", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "piche", "canonical": "behind", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "upar", "canonical": "above", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "neeche", "canonical": "below", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "bagal mein", "canonical": "beside", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "bagal me", "canonical": "beside", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "paas", "canonical": "near", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "nazdeek", "canonical": "near", "language": "hindi", "regions": ["north_india"], "category": "relationship", "confidence": 0.98},
    {"surface": "ki taraf", "canonical": "towards", "language": "hindi", "regions": ["north_india"], "category": "directional", "confidence": 0.98},

    # =========================================================================
    # 7. GUJARATI
    # =========================================================================
    {"surface": "pol", "canonical": "pol", "language": "gujarati", "regions": ["gujarat"], "category": "housing_cluster", "confidence": 0.98},
    {"surface": "faliya", "canonical": "faliya", "language": "gujarati", "regions": ["gujarat"], "category": "locality_marker", "confidence": 0.98},
    {"surface": "gam", "canonical": "gaon", "language": "gujarati", "regions": ["gujarat"], "category": "village", "confidence": 0.98},
    {"surface": "chali", "canonical": "chali", "language": "gujarati", "regions": ["gujarat"], "category": "tenement", "confidence": 0.98},
    {"surface": "vasahat", "canonical": "vasahat", "language": "gujarati", "regions": ["gujarat"], "category": "settlement", "confidence": 0.98},
    {"surface": "chokdi", "canonical": "crossroads", "language": "gujarati", "regions": ["gujarat"], "category": "crossroads", "confidence": 0.98},
    {"surface": "aagal", "canonical": "ahead", "language": "gujarati", "regions": ["gujarat"], "category": "relationship", "confidence": 0.98},
    {"surface": "paachhal", "canonical": "behind", "language": "gujarati", "regions": ["gujarat"], "category": "relationship", "confidence": 0.98},
    {"surface": "bajuma", "canonical": "beside", "language": "gujarati", "regions": ["gujarat"], "category": "relationship", "confidence": 0.98},
    {"surface": "paase", "canonical": "near", "language": "gujarati", "regions": ["gujarat"], "category": "relationship", "confidence": 0.98},
    {"surface": "najik", "canonical": "near", "language": "gujarati", "regions": ["gujarat"], "category": "relationship", "confidence": 0.98},
    {"surface": "jamni", "canonical": "on the right", "language": "gujarati", "regions": ["gujarat"], "category": "directional", "confidence": 0.98},
    {"surface": "dabhi", "canonical": "on the left", "language": "gujarati", "regions": ["gujarat"], "category": "directional", "confidence": 0.98},

    # =========================================================================
    # 8. MALAYALAM / KERALA
    # =========================================================================
    {"surface": "theruvu", "canonical": "theru", "language": "malayalam", "regions": ["kerala"], "category": "street_type", "confidence": 0.98},
    {"surface": "kara", "canonical": "kara", "language": "malayalam", "regions": ["kerala"], "category": "locality_marker", "confidence": 0.95},
    {"surface": "kavala", "canonical": "kavala", "language": "malayalam", "regions": ["kerala"], "category": "junction", "confidence": 0.98},
    {"surface": "angadi", "canonical": "angadi", "language": "malayalam", "regions": ["kerala"], "category": "market", "confidence": 0.98},
    {"surface": "kaavu", "canonical": "kavu", "language": "malayalam", "regions": ["kerala"], "category": "sacred_grove", "confidence": 0.95},
    {"surface": "kadavu", "canonical": "kadavu", "language": "malayalam", "regions": ["kerala"], "category": "riverbank_landing", "confidence": 0.95},
    {"surface": "mukku", "canonical": "mukku", "language": "malayalam", "regions": ["kerala"], "category": "junction_corner", "confidence": 0.98},
    {"surface": "munpil", "canonical": "in front of", "language": "malayalam", "regions": ["kerala"], "category": "relationship", "confidence": 0.98},
    {"surface": "purakil", "canonical": "behind", "language": "malayalam", "regions": ["kerala"], "category": "relationship", "confidence": 0.98},
    {"surface": "thazhe", "canonical": "below", "language": "malayalam", "regions": ["kerala"], "category": "relationship", "confidence": 0.98},
    {"surface": "aduthu", "canonical": "near", "language": "malayalam", "regions": ["kerala"], "category": "relationship", "confidence": 0.98},
    {"surface": "arike", "canonical": "near", "language": "malayalam", "regions": ["kerala"], "category": "relationship", "confidence": 0.98},
    {"surface": "vazhi", "canonical": "via", "language": "malayalam", "regions": ["kerala"], "category": "transit_path", "confidence": 0.98},

    # =========================================================================
    # 9. ODIA / ODISHA
    # =========================================================================
    {"surface": "sahi", "canonical": "sahi", "language": "odia", "regions": ["odisha"], "category": "lane_locality", "confidence": 0.98},
    {"surface": "chhak", "canonical": "chhak", "language": "odia", "regions": ["odisha"], "category": "crossroads", "confidence": 0.98},
    {"surface": "pokhari", "canonical": "pokhari", "language": "odia", "regions": ["odisha"], "category": "water_body", "confidence": 0.95},
    {"surface": "agare", "canonical": "in front of", "language": "odia", "regions": ["odisha"], "category": "relationship", "confidence": 0.98},
    {"surface": "pachhare", "canonical": "behind", "language": "odia", "regions": ["odisha"], "category": "relationship", "confidence": 0.98},
    {"surface": "pakhare", "canonical": "beside", "language": "odia", "regions": ["odisha"], "category": "relationship", "confidence": 0.98},
    {"surface": "bama", "canonical": "on the left", "language": "odia", "regions": ["odisha"], "category": "directional", "confidence": 0.98},
    {"surface": "dahana", "canonical": "on the right", "language": "odia", "regions": ["odisha"], "category": "directional", "confidence": 0.98},

    # =========================================================================
    # 10. PUNJABI
    # =========================================================================
    {"surface": "pind", "canonical": "pind", "language": "punjabi", "regions": ["punjab", "haryana"], "category": "village", "confidence": 0.98},
    {"surface": "chonk", "canonical": "chowk", "language": "punjabi", "regions": ["punjab"], "category": "crossroads", "confidence": 0.98},
    {"surface": "adda", "canonical": "adda", "language": "punjabi", "regions": ["punjab"], "category": "bus_stand_junction", "confidence": 0.98},
    {"surface": "agge", "canonical": "ahead", "language": "punjabi", "regions": ["punjab"], "category": "relationship", "confidence": 0.98},
    {"surface": "pichhe", "canonical": "behind", "language": "punjabi", "regions": ["punjab"], "category": "relationship", "confidence": 0.98},
    {"surface": "uppar", "canonical": "above", "language": "punjabi", "regions": ["punjab"], "category": "relationship", "confidence": 0.98},
    {"surface": "thalle", "canonical": "below", "language": "punjabi", "regions": ["punjab"], "category": "relationship", "confidence": 0.98},
    {"surface": "nere", "canonical": "near", "language": "punjabi", "regions": ["punjab"], "category": "relationship", "confidence": 0.98},
    {"surface": "naal", "canonical": "beside", "language": "punjabi", "regions": ["punjab"], "category": "relationship", "confidence": 0.98},
    {"surface": "sajje", "canonical": "on the right", "language": "punjabi", "regions": ["punjab"], "category": "directional", "confidence": 0.98},
    {"surface": "khabbe", "canonical": "on the left", "language": "punjabi", "regions": ["punjab"], "category": "directional", "confidence": 0.98},
    {"surface": "wal", "canonical": "towards", "language": "punjabi", "regions": ["punjab"], "category": "directional", "confidence": 0.98},

    # =========================================================================
    # 11. ASSAMESE
    # =========================================================================
    {"surface": "path", "canonical": "path", "language": "assamese", "regions": ["assam"], "category": "road_type", "confidence": 0.95},
    {"surface": "pukhuri", "canonical": "pukhuri", "language": "assamese", "regions": ["assam"], "category": "water_body", "confidence": 0.95},
    {"surface": "agfal", "canonical": "in front of", "language": "assamese", "regions": ["assam"], "category": "relationship", "confidence": 0.98},
    {"surface": "pisfal", "canonical": "behind", "language": "assamese", "regions": ["assam"], "category": "relationship", "confidence": 0.98},
    {"surface": "usor", "canonical": "near", "language": "assamese", "regions": ["assam"], "category": "relationship", "confidence": 0.98}
]

# Fast lookup hash map by surface token
SURFACE_TO_ENTRY = {e["surface"].lower(): e for e in REGIONAL_GAZETTEER}

def normalize_regional_terms(text: str) -> str:
    """
    Scans the address string for multi-word and single-word regional directional 
    and relational markers and normalizes them cleanly into standard English/Hinglish delivery tags.
    """
    s = text

    # Sort by surface phrase length descending (match multi-word phrases first e.g. "baam dike" before "dike")
    sorted_entries = sorted(REGIONAL_GAZETTEER, key=lambda x: len(x["surface"]), reverse=True)
    
    for entry in sorted_entries:
        cat = entry["category"]
        surf = entry["surface"]
        canon = entry["canonical"]
        
        # Only rewrite directional and relationship terms (e.g. "daggara" -> "near", "baam dike" -> "on the left")
        # Preserve locality markers (e.g. "para", "halli", "theru", "veedhi", "peth", "mohalla") as proper geographic nouns!
        if cat in ["directional", "relationship"]:
            pattern = rf'\b{re.escape(surf)}\b'
            s = re.sub(pattern, canon, s, flags=re.IGNORECASE)

    # Clean redundant multi-spaces
    s = " ".join(s.split())
    return s
