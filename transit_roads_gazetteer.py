"""
transit_roads_gazetteer.py
--------------------------
Authoritative Inter-City Arterial Road & Destination-Named Highway Gazetteer.

Maps famous Indian roads, highways, and expressways that are named after destination cities
to their TRUE physical geographical locations (City, District, State, Postal Hub).

Prevents greedy alias inversions (e.g. 'Old Madras Road' being misrouted to Chennai instead of Bangalore).
Data structured in accordance with OpenStreetMap (OSM) administrative boundary tags and NHAI route data.
"""

import re

# Common Indian phonetic regex variations for Road and Highway
_ROAD_PAT = r'(?:r(?:oa|oo|o)?d|rode)'
_HWY_PAT = r'(?:highway|hi\s*way|hiway|hwy|higway|expressway|expresway|expway|express|exp)'

# Destination-Named Arterial Roads & Inter-City Highways
TRANSIT_ROADS_DATA = [
    # --- 1. BENGALURU / KARNATAKA ---
    {
        "canonical_name": "Old Madras Road",
        "pattern": rf'\b(old\s*madras\s*{_ROAD_PAT}|madras\s*{_ROAD_PAT})\b',
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "pincode": "560036",
        "route_ref": "NH 75 (Old NH 4)",
        "prominent_localities": ["Krishnarajapuram", "KR Puram", "Indiranagar", "Ulsoor", "Dooravaninagar", "Binnamangala"]
    },
    {
        "canonical_name": "Bangalore-Mysore Expressway",
        "pattern": rf'\b(bangalore[\s\-]*mysore\s*({_HWY_PAT}|{_ROAD_PAT})|mysore\s*{_ROAD_PAT})\b',
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "pincode": "560026",
        "route_ref": "NH 275",
        "prominent_localities": ["Kengeri", "Rajarajeshwari Nagar", "Nayandahalli", "Bidadi"]
    },
    {
        "canonical_name": "Hosur Road",
        "pattern": rf'\b(hosur\s*{_ROAD_PAT})\b',
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "pincode": "560068",
        "route_ref": "NH 44",
        "prominent_localities": ["Bommanahalli", "Electronic City", "Attibele", "Madiwala"]
    },
    {
        "canonical_name": "Bellary Road",
        "pattern": rf'\b(bellary\s*{_ROAD_PAT})\b',
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "pincode": "560024",
        "route_ref": "NH 44",
        "prominent_localities": ["Hebbal", "Yelahanka", "Ganganagar", "Sadashivanagar"]
    },
    {
        "canonical_name": "Poona-Bangalore Road",
        "pattern": rf'\b(poona[\s\-]*bangalore\s*{_ROAD_PAT}|pune[\s\-]*bangalore\s*{_HWY_PAT})\b',
        "city": "Kolhapur",
        "district": "Kolhapur",
        "state": "Maharashtra",
        "pincode": "416122",
        "route_ref": "NH 48",
        "prominent_localities": ["Shiroli", "Uchgaon", "Gokul Shirgaon"]
    },

    # --- 2. DELHI-NCR & HARYANA ---
    {
        "canonical_name": "Old Delhi Road",
        "pattern": rf'\b(old\s*delhi\s*{_ROAD_PAT}|delhi\s*{_ROAD_PAT})\b',
        "city": "Gurgaon",
        "district": "Gurgaon",
        "state": "Haryana",
        "pincode": "122001",
        "route_ref": "MDR 136",
        "prominent_localities": ["Sector 14", "Sector 17", "Sector 21", "Dundahera", "Palam Vihar"]
    },
    {
        "canonical_name": "Delhi-Jaipur Highway",
        "pattern": rf'\b(delhi[\s\-]*jaipur\s*({_HWY_PAT}|{_ROAD_PAT})|jaipur\s*{_HWY_PAT})\b',
        "city": "Gurgaon",
        "district": "Gurgaon",
        "state": "Haryana",
        "pincode": "122001",
        "route_ref": "NH 48",
        "prominent_localities": ["Manesar", "Bilaspur", "Bawal", "Dharuhera"]
    },
    {
        "canonical_name": "Mathura Road",
        "pattern": rf'\b(mathura\s*{_ROAD_PAT})\b',
        "city": "New Delhi",
        "district": "South Delhi",
        "state": "Delhi",
        "pincode": "110044",
        "route_ref": "Old NH 2",
        "prominent_localities": ["Badarpur", "Okhla", "Sarita Vihar", "Ashram"]
    },
    {
        "canonical_name": "Rohtak Road",
        "pattern": rf'\b(rohtak\s*{_ROAD_PAT})\b',
        "city": "New Delhi",
        "district": "West Delhi",
        "state": "Delhi",
        "pincode": "110041",
        "route_ref": "NH 10",
        "prominent_localities": ["Nangloi", "Punjabi Bagh", "Peera Garhi", "Tikri"]
    },

    # --- 3. MUMBAI & PUNE / MAHARASHTRA ---
    {
        "canonical_name": "Bombay-Pune Highway",
        "pattern": rf'\b(bombay[\s\-]*pune\s*({_HWY_PAT}|{_ROAD_PAT})|mumbai[\s\-]*pune\s*({_HWY_PAT}|{_ROAD_PAT}))\b',
        "city": "Pune",
        "district": "Pune",
        "state": "Maharashtra",
        "pincode": "411044",
        "route_ref": "NH 48",
        "prominent_localities": ["Pimpri", "Chinchwad", "Dehu Road", "Nigdi", "Wakad"]
    },
    {
        "canonical_name": "Agra Road",
        "pattern": rf'\b(agra\s*{_ROAD_PAT}|bombay[\s\-]*agra\s*{_ROAD_PAT})\b',
        "city": "Thane",
        "district": "Thane",
        "state": "Maharashtra",
        "pincode": "400601",
        "route_ref": "NH 3",
        "prominent_localities": ["Kalyan", "Bhiwandi", "Shahapur", "Kasara"]
    },
    {
        "canonical_name": "Nagpur Road",
        "pattern": rf'\b(nagpur\s*{_ROAD_PAT})\b',
        "city": "Jabalpur",
        "district": "Jabalpur",
        "state": "Madhya Pradesh",
        "pincode": "482001",
        "route_ref": "NH 34",
        "prominent_localities": ["Madan Mahal", "Garha"]
    },

    # --- 4. RAJASTHAN & JAIPUR ---
    {
        "canonical_name": "Agra Road (Jaipur)",
        "pattern": rf'\b(agra\s*{_ROAD_PAT}|jaipur[\s\-]*agra\s*{_ROAD_PAT})\b',
        "city": "Jaipur",
        "district": "Jaipur",
        "state": "Rajasthan",
        "pincode": "302003",
        "route_ref": "NH 21",
        "prominent_localities": ["Ghat Gate", "Sisodia Rani Garden", "Transport Nagar", "Kanota"]
    },
    {
        "canonical_name": "Ajmer Road",
        "pattern": rf'\b(ajmer\s*{_ROAD_PAT}|jaipur[\s\-]*ajmer\s*({_HWY_PAT}|{_ROAD_PAT}))\b',
        "city": "Jaipur",
        "district": "Jaipur",
        "state": "Rajasthan",
        "pincode": "302006",
        "route_ref": "NH 48",
        "prominent_localities": ["Civil Lines", "Sodala", "Purani Chungi", "Heerapura", "Bhankrota"]
    },
    {
        "canonical_name": "Tonk Road",
        "pattern": rf'\b(tonk\s*{_ROAD_PAT})\b',
        "city": "Jaipur",
        "district": "Jaipur",
        "state": "Rajasthan",
        "pincode": "302015",
        "route_ref": "NH 52",
        "prominent_localities": ["Narayan Singh Circle", "Gopalpura", "Durgapura", "Sanganer"]
    },
    {
        "canonical_name": "Delhi Road (Jaipur)",
        "pattern": rf'\b(delhi\s*{_ROAD_PAT}|jaipur[\s\-]*delhi\s*{_ROAD_PAT})\b',
        "city": "Jaipur",
        "district": "Jaipur",
        "state": "Rajasthan",
        "pincode": "302028",
        "route_ref": "NH 48",
        "prominent_localities": ["Amer", "Kukas", "Achrol"]
    },

    # --- 5. TAMIL NADU & CHENNAI ---
    {
        "canonical_name": "Madras Bank Road",
        "pattern": rf'\b(madras\s*bank\s*{_ROAD_PAT})\b',
        "city": "Ooty",
        "district": "Nilgiris",
        "state": "Tamil Nadu",
        "pincode": "643001",
        "route_ref": "Municipal Road",
        "prominent_localities": ["Upper Bazaar", "Charing Cross", "Ooty Town"]
    },
    {
        "canonical_name": "Bangalore Highway (Chennai)",
        "pattern": rf'\b(bangalore\s*({_HWY_PAT}|{_ROAD_PAT})|chennai[\s\-]*bangalore\s*{_HWY_PAT})\b',
        "city": "Chennai",
        "district": "Kanchipuram",
        "state": "Tamil Nadu",
        "pincode": "600123",
        "route_ref": "NH 48",
        "prominent_localities": ["Sriperumbudur", "Poonamallee", "Maduravoyal"]
    },
    {
        "canonical_name": "Calcutta Road / G.T. Road (East)",
        "pattern": rf'\b(calcutta\s*{_ROAD_PAT}|calcutta\s*trunk\s*{_ROAD_PAT})\b',
        "city": "Asansol",
        "district": "Paschim Bardhaman",
        "state": "West Bengal",
        "pincode": "713301",
        "route_ref": "Grand Trunk Road",
        "prominent_localities": ["Burnpur", "Barakar", "Raniganj"]
    }
]

# Compile regex patterns once for sub-millisecond lookup
for entry in TRANSIT_ROADS_DATA:
    entry["compiled_regex"] = re.compile(entry["pattern"], re.IGNORECASE)


def match_transit_road(text: str) -> dict:
    """
    Checks if the address text contains a known destination-named arterial road or highway.
    Returns: dict with {canonical_name, city, district, state, pincode} or None.
    """
    if not text:
        return None
        
    t_clean = text.lower()
    first_match = None
    for entry in TRANSIT_ROADS_DATA:
        if entry["compiled_regex"].search(t_clean):
            # Check if any prominent locality of this specific corridor matches
            locs = entry.get("prominent_localities", [])
            if any(loc.lower() in t_clean for loc in locs):
                return {
                    "canonical_name": entry["canonical_name"],
                    "city": entry["city"],
                    "district": entry["district"],
                    "state": entry["state"],
                    "pincode": entry["pincode"],
                    "route_ref": entry["route_ref"]
                }
            if first_match is None:
                first_match = entry

    if first_match:
        return {
            "canonical_name": first_match["canonical_name"],
            "city": first_match["city"],
            "district": first_match["district"],
            "state": first_match["state"],
            "pincode": first_match["pincode"],
            "route_ref": first_match["route_ref"]
        }
    return None


# Set of road/highway indicator words that prevent a city name from being interpreted as a destination city
ROAD_INDICATOR_SUFFIXES = {
    "road", "rd", "rood", "rode", "rod", "marg", "highway", "hiway", "hwy", 
    "higway", "expressway", "expresway", "expway", "salai", "path", 
    "bypass", "circle", "lane", "gali", "chowk", "square", "cross", "market", 
    "bazaar", "bazar", "gate", "bridge", "flyover", "overbridge"
}

ROAD_INDICATOR_PREFIXES = {
    "old", "new", "grand", "upper", "lower", "inner", "outer", "great", "bypass"
}


def is_city_word_in_road_context(text: str, city_word: str) -> bool:
    """
    Returns True if city_word (e.g. 'madras', 'delhi', 'bombay') appears as part of a road compound
    (e.g. 'Old Madras Road', 'Delhi Highway', 'Bombay Bazar') rather than a standalone destination city.
    """
    if not text or not city_word:
        return False
        
    pattern = rf'\b(?:({"|".join(ROAD_INDICATOR_PREFIXES)})\s+)?{re.escape(city_word)}(?:[\s\-]+({"|".join(ROAD_INDICATOR_SUFFIXES)}))\b'
    return bool(re.search(pattern, text, re.IGNORECASE))
