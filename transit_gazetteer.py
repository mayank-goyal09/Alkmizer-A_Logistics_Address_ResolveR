"""
transit_gazetteer.py
--------------------
Authoritative multi-layer transit, railway, airport, and city shorthand gazetteer.
Preserves entity types and context-aware expansions.

Four distinct layers:
1. Railway Station Codes (CRIS / Indian Railways official codes e.g. NDLS, CSMT, SBC, MAS, TVC)
2. City Shorthand & Historical Aliases (e.g. BLR, BOM, TVM, GGN, GZB, ALD)
3. Airport / IATA Transport Codes (e.g. DEL, BOM, BLR, HYD, MAA, CCU, COK)
4. Local Transit & Infrastructure Shorthand (e.g. rly stn, jn, cantt, term, isbt, dmrc, bmrcl)
"""

import re

# ---------------------------------------------------------------------------
# Layer 1: Major Indian Railway Station Codes (CRIS / IR Standard)
# ---------------------------------------------------------------------------
RAILWAY_STATION_CODES = {
    # Delhi / NCR
    "ndls": {"canonical": "New Delhi", "entity": "railway_station", "station_name": "New Delhi Railway Station", "city": "New Delhi", "district": "Central Delhi", "state": "Delhi", "pincode": "110002"},
    "dli":  {"canonical": "Old Delhi", "entity": "railway_station", "station_name": "Delhi Junction Railway Station", "city": "Delhi", "district": "Central Delhi", "state": "Delhi", "pincode": "110006"},
    "nzm":  {"canonical": "Hazrat Nizamuddin", "entity": "railway_station", "station_name": "Hazrat Nizamuddin Railway Station", "city": "New Delhi", "district": "South Delhi", "state": "Delhi", "pincode": "110013"},
    "anvt": {"canonical": "Anand Vihar Terminal", "entity": "railway_station", "station_name": "Anand Vihar Railway Terminal", "city": "Delhi", "district": "East Delhi", "state": "Delhi", "pincode": "110092"},
    "dec":  {"canonical": "Delhi Cantt", "entity": "railway_station", "station_name": "Delhi Cantonment Railway Station", "city": "New Delhi", "district": "South West Delhi", "state": "Delhi", "pincode": "110010"},
    "dee":  {"canonical": "Delhi Sarai Rohilla", "entity": "railway_station", "station_name": "Sarai Rohilla Railway Station", "city": "Delhi", "district": "North Delhi", "state": "Delhi", "pincode": "110035"},
    "dsa":  {"canonical": "Shahdara", "entity": "railway_station", "station_name": "Delhi Shahdara Junction", "city": "Delhi", "district": "East Delhi", "state": "Delhi", "pincode": "110032"},
    "gzb":  {"canonical": "Ghaziabad", "entity": "railway_station", "station_name": "Ghaziabad Junction", "city": "Ghaziabad", "district": "Ghaziabad", "state": "Uttar Pradesh", "pincode": "201001"},
    "ggn":  {"canonical": "Gurgaon", "entity": "railway_station", "station_name": "Gurgaon Railway Station", "city": "Gurgaon", "district": "Gurgaon", "state": "Haryana", "pincode": "122001"},
    "fdb":  {"canonical": "Faridabad", "entity": "railway_station", "station_name": "Faridabad Railway Station", "city": "Faridabad", "district": "Faridabad", "state": "Haryana", "pincode": "121002"},

    # Mumbai / Maharashtra
    "csmt": {"canonical": "Mumbai CSMT", "entity": "railway_station", "station_name": "Chhatrapati Shivaji Maharaj Terminus", "city": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "pincode": "400001"},
    "bct":  {"canonical": "Mumbai Central", "entity": "railway_station", "station_name": "Mumbai Central Railway Station", "city": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "pincode": "400008"},
    "mmct": {"canonical": "Mumbai Central", "entity": "railway_station", "station_name": "Mumbai Central Railway Station", "city": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "pincode": "400008"},
    "ltt":  {"canonical": "Lokmanya Tilak Terminus", "entity": "railway_station", "station_name": "Lokmanya Tilak Terminus Kurla", "city": "Mumbai", "district": "Mumbai Suburban", "state": "Maharashtra", "pincode": "400089"},
    "bdts": {"canonical": "Bandra Terminus", "entity": "railway_station", "station_name": "Bandra Terminus Railway Station", "city": "Mumbai", "district": "Mumbai Suburban", "state": "Maharashtra", "pincode": "400051"},
    "bvi":  {"canonical": "Borivali", "entity": "railway_station", "station_name": "Borivali Railway Station", "city": "Mumbai", "district": "Mumbai Suburban", "state": "Maharashtra", "pincode": "400066"},
    "tna":  {"canonical": "Thane", "entity": "railway_station", "station_name": "Thane Railway Station", "city": "Thane", "district": "Thane", "state": "Maharashtra", "pincode": "400601"},
    "kyn":  {"canonical": "Kalyan", "entity": "railway_station", "station_name": "Kalyan Junction", "city": "Thane", "district": "Thane", "state": "Maharashtra", "pincode": "421301"},
    "pnvl": {"canonical": "Panvel", "entity": "railway_station", "station_name": "Panvel Junction", "city": "Navi Mumbai", "district": "Raigad", "state": "Maharashtra", "pincode": "410206"},
    "pune": {"canonical": "Pune", "entity": "railway_station", "station_name": "Pune Junction", "city": "Pune", "district": "Pune", "state": "Maharashtra", "pincode": "411001"},
    "svjr": {"canonical": "Shivajinagar", "entity": "railway_station", "station_name": "Shivajinagar Railway Station", "city": "Pune", "district": "Pune", "state": "Maharashtra", "pincode": "411005"},
    "ngp":  {"canonical": "Nagpur", "entity": "railway_station", "station_name": "Nagpur Junction", "city": "Nagpur", "district": "Nagpur", "state": "Maharashtra", "pincode": "440001"},

    # Karnataka
    "sbc":  {"canonical": "Bengaluru City", "entity": "railway_station", "station_name": "KSR Bengaluru City Railway Station", "city": "Bengaluru", "district": "Bengaluru", "state": "Karnataka", "pincode": "560023"},
    "ypr":  {"canonical": "Yesvantpur", "entity": "railway_station", "station_name": "Yesvantpur Junction", "city": "Bengaluru", "district": "Bengaluru", "state": "Karnataka", "pincode": "560022"},
    "kjm":  {"canonical": "Krishnarajapuram", "entity": "railway_station", "station_name": "Krishnarajapuram Railway Station", "city": "Bengaluru", "district": "Bengaluru", "state": "Karnataka", "pincode": "560036"},
    "bnc":  {"canonical": "Bengaluru Cantt", "entity": "railway_station", "station_name": "Bengaluru Cantonment Railway Station", "city": "Bengaluru", "district": "Bengaluru", "state": "Karnataka", "pincode": "560046"},
    "ubl":  {"canonical": "Hubballi", "entity": "railway_station", "station_name": "SSS Hubballi Junction", "city": "Hubballi", "district": "Dharwad", "state": "Karnataka", "pincode": "580020"},
    "mys":  {"canonical": "Mysuru", "entity": "railway_station", "station_name": "Mysuru Junction", "city": "Mysuru", "district": "Mysore", "state": "Karnataka", "pincode": "570001"},
    "majn": {"canonical": "Mangaluru Junction", "entity": "railway_station", "station_name": "Mangaluru Junction", "city": "Mangaluru", "district": "Dakshina Kannada", "state": "Karnataka", "pincode": "575007"},
    "maq":  {"canonical": "Mangaluru Central", "entity": "railway_station", "station_name": "Mangaluru Central", "city": "Mangaluru", "district": "Dakshina Kannada", "state": "Karnataka", "pincode": "575001"},

    # Tamil Nadu
    "mas":  {"canonical": "Chennai Central", "entity": "railway_station", "station_name": "Puratchi Thalaivar Dr. M.G. Ramachandran Central", "city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "pincode": "600003"},
    "ms":   {"canonical": "Chennai Egmore", "entity": "railway_station", "station_name": "Chennai Egmore Railway Station", "city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "pincode": "600008"},
    "tbm":  {"canonical": "Tambaram", "entity": "railway_station", "station_name": "Tambaram Railway Station", "city": "Chennai", "district": "Chengalpattu", "state": "Tamil Nadu", "pincode": "600045"},
    "msb":  {"canonical": "Chennai Beach", "entity": "railway_station", "station_name": "Chennai Beach Railway Station", "city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "pincode": "600001"},
    "tpj":  {"canonical": "Tiruchirappalli", "entity": "railway_station", "station_name": "Tiruchirappalli Junction", "city": "Tiruchirappalli", "district": "Tiruchirappalli", "state": "Tamil Nadu", "pincode": "620001"},
    "mdu":  {"canonical": "Madurai", "entity": "railway_station", "station_name": "Madurai Junction", "city": "Madurai", "district": "Madurai", "state": "Tamil Nadu", "pincode": "625001"},
    "cbe":  {"canonical": "Coimbatore", "entity": "railway_station", "station_name": "Coimbatore Main Junction", "city": "Coimbatore", "district": "Coimbatore", "state": "Tamil Nadu", "pincode": "641018"},

    # Kerala
    "tvc":  {"canonical": "Thiruvananthapuram Central", "entity": "railway_station", "station_name": "Thiruvananthapuram Central", "city": "Thiruvananthapuram", "district": "Thiruvananthapuram", "state": "Kerala", "pincode": "695014"},
    "ers":  {"canonical": "Ernakulam Junction", "entity": "railway_station", "station_name": "Ernakulam South Junction", "city": "Kochi", "district": "Ernakulam", "state": "Kerala", "pincode": "682016"},
    "ern":  {"canonical": "Ernakulam Town", "entity": "railway_station", "station_name": "Ernakulam Town North", "city": "Kochi", "district": "Ernakulam", "state": "Kerala", "pincode": "682018"},
    "qln":  {"canonical": "Kollam", "entity": "railway_station", "station_name": "Kollam Junction", "city": "Kollam", "district": "Kollam", "state": "Kerala", "pincode": "691001"},
    "tcr":  {"canonical": "Thrissur", "entity": "railway_station", "station_name": "Thrissur Railway Station", "city": "Thrissur", "district": "Thrissur", "state": "Kerala", "pincode": "680001"},

    # AP / Telangana
    "hyb":  {"canonical": "Hyderabad Deccan", "entity": "railway_station", "station_name": "Hyderabad Nampally Station", "city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "pincode": "500001"},
    "sc":   {"canonical": "Secunderabad", "entity": "railway_station", "station_name": "Secunderabad Junction", "city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "pincode": "500003"},
    "kcg":  {"canonical": "Kacheguda", "entity": "railway_station", "station_name": "Kacheguda Railway Station", "city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "pincode": "500027"},
    "bza":  {"canonical": "Vijayawada", "entity": "railway_station", "station_name": "Vijayawada Junction", "city": "Vijayawada", "district": "Krishna", "state": "Andhra Pradesh", "pincode": "520001"},
    "vskp": {"canonical": "Visakhapatnam", "entity": "railway_station", "station_name": "Visakhapatnam Junction", "city": "Visakhapatnam", "district": "Visakhapatnam", "state": "Andhra Pradesh", "pincode": "530004"},

    # West Bengal / East / Northeast
    "hwh":  {"canonical": "Howrah", "entity": "railway_station", "station_name": "Howrah Railway Station", "city": "Howrah", "district": "Howrah", "state": "West Bengal", "pincode": "711101"},
    "sdah": {"canonical": "Sealdah", "entity": "railway_station", "station_name": "Sealdah Railway Station", "city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "pincode": "700014"},
    "koaa": {"canonical": "Kolkata", "entity": "railway_station", "station_name": "Kolkata Railway Station", "city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "pincode": "700037"},
    "kgp":  {"canonical": "Kharagpur", "entity": "railway_station", "station_name": "Kharagpur Junction", "city": "Kharagpur", "district": "Paschim Medinipur", "state": "West Bengal", "pincode": "721301"},
    "njp":  {"canonical": "New Jalpaiguri", "entity": "railway_station", "station_name": "New Jalpaiguri Junction", "city": "Siliguri", "district": "Jalpaiguri", "state": "West Bengal", "pincode": "734007"},
    "ghy":  {"canonical": "Guwahati", "entity": "railway_station", "station_name": "Guwahati Railway Station", "city": "Guwahati", "district": "Kamrup", "state": "Assam", "pincode": "781001"},
    "bbs":  {"canonical": "Bhubaneswar", "entity": "railway_station", "station_name": "Bhubaneswar Railway Station", "city": "Bhubaneswar", "district": "Khordha", "state": "Odisha", "pincode": "751001"},
    "pnbe": {"canonical": "Patna", "entity": "railway_station", "station_name": "Patna Junction", "city": "Patna", "district": "Patna", "state": "Bihar", "pincode": "800001"},
    "rnc":  {"canonical": "Ranchi", "entity": "railway_station", "station_name": "Ranchi Junction", "city": "Ranchi", "district": "Ranchi", "state": "Jharkhand", "pincode": "834001"},
    "tata": {"canonical": "Jamshedpur Tatanagar", "entity": "railway_station", "station_name": "Tatanagar Junction", "city": "Jamshedpur", "district": "East Singhbhum", "state": "Jharkhand", "pincode": "831002"},

    # UP / MP / Rajasthan / Gujarat
    "lko":  {"canonical": "Lucknow", "entity": "railway_station", "station_name": "Lucknow Charbagh", "city": "Lucknow", "district": "Lucknow", "state": "Uttar Pradesh", "pincode": "226004"},
    "cnb":  {"canonical": "Kanpur Central", "entity": "railway_station", "station_name": "Kanpur Central", "city": "Kanpur Nagar", "district": "Kanpur Nagar", "state": "Uttar Pradesh", "pincode": "208004"},
    "pryj": {"canonical": "Prayagraj", "entity": "railway_station", "station_name": "Prayagraj Junction", "city": "Prayagraj", "district": "Allahabad", "state": "Uttar Pradesh", "pincode": "211001"},
    "bsb":  {"canonical": "Varanasi", "entity": "railway_station", "station_name": "Varanasi Junction", "city": "Varanasi", "district": "Varanasi", "state": "Uttar Pradesh", "pincode": "221002"},
    "gkp":  {"canonical": "Gorakhpur", "entity": "railway_station", "station_name": "Gorakhpur Junction", "city": "Gorakhpur", "district": "Gorakhpur", "state": "Uttar Pradesh", "pincode": "273001"},
    "bpl":  {"canonical": "Bhopal", "entity": "railway_station", "station_name": "Bhopal Junction", "city": "Bhopal", "district": "Bhopal", "state": "Madhya Pradesh", "pincode": "462001"},
    "indb": {"canonical": "Indore", "entity": "railway_station", "station_name": "Indore Junction", "city": "Indore", "district": "Indore", "state": "Madhya Pradesh", "pincode": "452001"},
    "gwl":  {"canonical": "Gwalior", "entity": "railway_station", "station_name": "Gwalior Junction", "city": "Gwalior", "district": "Gwalior", "state": "Madhya Pradesh", "pincode": "474002"},
    "jp":   {"canonical": "Jaipur", "entity": "railway_station", "station_name": "Jaipur Junction", "city": "Jaipur", "district": "Jaipur", "state": "Rajasthan", "pincode": "302006"},
    "ju":   {"canonical": "Jodhpur", "entity": "railway_station", "station_name": "Jodhpur Junction", "city": "Jodhpur", "district": "Jodhpur", "state": "Rajasthan", "pincode": "342001"},
    "bkn":  {"canonical": "Bikaner", "entity": "railway_station", "station_name": "Bikaner Junction", "city": "Bikaner", "district": "Bikaner", "state": "Rajasthan", "pincode": "334001"},
    "adi":  {"canonical": "Ahmedabad", "entity": "railway_station", "station_name": "Ahmedabad Junction Kalupur", "city": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "pincode": "380002"},
    "brc":  {"canonical": "Vadodara", "entity": "railway_station", "station_name": "Vadodara Junction", "city": "Vadodara", "district": "Vadodara", "state": "Gujarat", "pincode": "390002"}
}

# ---------------------------------------------------------------------------
# Layer 2: Common City Shorthand & Historical Aliases
# ---------------------------------------------------------------------------
CITY_SHORTHAND_GAZETTEER = {
    # City Shorthand
    "dl": "Delhi", "del": "Delhi", "ncr": "National Capital Region", "nd": "New Delhi",
    "bom": "Mumbai", "mum": "Mumbai", "blr": "Bengaluru", "bglr": "Bengaluru", "bang": "Bangalore",
    "hyd": "Hyderabad", "che": "Chennai", "maa": "Chennai", "ccu": "Kolkata", "cal": "Kolkata",
    "pun": "Pune", "pne": "Pune", "amd": "Ahmedabad", "ahmd": "Ahmedabad", "ahd": "Ahmedabad",
    "jpr": "Jaipur", "lko": "Lucknow", "agr": "Agra", "vns": "Varanasi", "ald": "Prayagraj",
    "pry": "Prayagraj", "bpl": "Bhopal", "idr": "Indore", "jbp": "Jabalpur", "gwl": "Gwalior",
    "ngp": "Nagpur", "sur": "Surat", "vad": "Vadodara", "rjt": "Rajkot", "ldh": "Ludhiana",
    "asr": "Amritsar", "pat": "Patna", "rnc": "Ranchi", "bbs": "Bhubaneswar", "guw": "Guwahati",
    "cok": "Kochi", "trv": "Thiruvananthapuram", "tvm": "Thiruvananthapuram", "mys": "Mysuru",
    "cbe": "Coimbatore", "mdu": "Madurai", "udiapur": "Udaipur", "chnnai": "Chennai",

    # Historical Names (Preserved as Aliases)
    "bombay": "Mumbai", "bangalore": "Bengaluru", "madras": "Chennai", "calcutta": "Kolkata",
    "poona": "Pune", "allahabad": "Prayagraj", "baroda": "Vadodara", "trivandrum": "Thiruvananthapuram",
    "cochin": "Kochi", "mangalore": "Mangaluru", "mysore": "Mysuru", "belgaum": "Belagavi",
    "gurgaon": "Gurugram"
}

# ---------------------------------------------------------------------------
# Layer 3: IATA Airport Codes
# ---------------------------------------------------------------------------
AIRPORT_IATA_GAZETTEER = {
    "del": {"name": "Indira Gandhi International Airport", "city": "New Delhi", "pincode": "110037"},
    "bom": {"name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai", "pincode": "400099"},
    "blr": {"name": "Kempegowda International Airport", "city": "Bengaluru", "pincode": "560300"},
    "hyd": {"name": "Rajiv Gandhi International Airport", "city": "Hyderabad", "pincode": "500409"},
    "maa": {"name": "Chennai International Airport", "city": "Chennai", "pincode": "600027"},
    "ccu": {"name": "Netaji Subhash Chandra Bose Airport", "city": "Kolkata", "pincode": "700052"},
    "pnq": {"name": "Pune International Airport", "city": "Pune", "pincode": "411032"},
    "amd": {"name": "Sardar Vallabhbhai Patel Airport", "city": "Ahmedabad", "pincode": "380003"},
    "cok": {"name": "Cochin International Airport", "city": "Kochi", "pincode": "683111"},
    "goi": {"name": "Dabolim Airport", "city": "Goa", "pincode": "403801"},
    "trv": {"name": "Trivandrum International Airport", "city": "Thiruvananthapuram", "pincode": "695008"},
    "jai": {"name": "Jaipur International Airport", "city": "Jaipur", "pincode": "302029"},
    "ixc": {"name": "Shaheed Bhagat Singh Airport", "city": "Chandigarh", "pincode": "160004"},
    "gau": {"name": "Lokpriya Gopinath Bordoloi Airport", "city": "Guwahati", "pincode": "781015"},
    "bbi": {"name": "Biju Patnaik Airport", "city": "Bhubaneswar", "pincode": "751020"}
}

# ---------------------------------------------------------------------------
# Layer 4: Local Metro & Railway-Specific Shorthand
# ---------------------------------------------------------------------------
TRANSIT_INFRASTRUCTURE_EXPANSIONS = {
    r'\brly\s*stn\b|\brail\s*stn\b|\brailway\s*stn\b|\brly\s*station\b': 'Railway Station',
    r'\brly\s*colony\b': 'Railway Colony',
    r'\bjn\b|\bjct\b|\bjunc\b': 'Junction',
    r'\bcnt\b|\bcant\b|\bcantt\b|\bct\b': 'Cantonment',
    r'\bterm\b|\bterminal\b': 'Terminal',
    r'\bstn\b|\bsta\b': 'Station',
    r'\bisbt\b': 'ISBT Bus Terminal',
    r'\bdmrc\b|\bdmetro\b': 'Delhi Metro',
    r'\bbmrcl\b': 'Bengaluru Metro',
    r'\bkmrl\b': 'Kochi Metro',
    r'\bmmrda\b|\bmmts\b': 'MMTS Transit',
    r'\bmtr\s*stn\b|\bmetro\s*stn\b': 'Metro Station'
}

def resolve_transit_tokens(text: str) -> str:
    """
    Expands transit abbreviations, railway codes, city shorthand, and airport tokens.
    """
    s = text

    # 1. Expand Railway infrastructure terms (e.g. "rly stn", "cantt", "jn")
    for pat, repl in TRANSIT_INFRASTRUCTURE_EXPANSIONS.items():
        s = re.sub(pat, repl, s, flags=re.IGNORECASE)

    # 2. Check for explicit railway station codes (e.g. "NDLS", "CSMT", "SBC", "MAS", "TVC")
    # Matches words with length 3-4 standing alone or next to station/rly/stop
    tokens = s.split()
    expanded_tokens = []
    for t in tokens:
        clean_t = t.lower().strip(".,-;#")
        if clean_t in RAILWAY_STATION_CODES:
            # Expand to canonical station / city
            info = RAILWAY_STATION_CODES[clean_t]
            expanded_tokens.append(info["canonical"])
        elif clean_t in CITY_SHORTHAND_GAZETTEER:
            from transit_roads_gazetteer import is_city_word_in_road_context
            if is_city_word_in_road_context(s, clean_t):
                expanded_tokens.append(t)
            else:
                expanded_tokens.append(CITY_SHORTHAND_GAZETTEER[clean_t])
        else:
            expanded_tokens.append(t)

    s = " ".join(expanded_tokens)
    return s
