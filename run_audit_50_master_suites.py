import os
import sys
import re
import pandas as pd
import joblib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from address_preprocessor import preprocess_address
from features import extract_features
from backend.verification_engine import AddressVerificationEngine
from backend.api_server import resolve_components, build_clean_address

engine = AddressVerificationEngine(os.path.join(CURRENT_DIR, "backend", "pincodes_in.db"))
crf_model = joblib.load(os.path.join(CURRENT_DIR, "global_address_resolver_v1.pkl"))

TEST_CASES_50 = [
    # --- Suite 1: Pincode vs. Locality Mismatches ---
    {"id": 1, "suite": "Pincode vs. Locality Mismatches", "raw": "Flat 402, Tower B, Supertech Capetown, Sector 74, Noida 201301", "target": "201301 is Sector 15; Capetown is actually 201304."},
    {"id": 2, "suite": "Pincode vs. Locality Mismatches", "raw": "Hiranandani Estate, Thane West, Mumbai - 400076", "target": "Thane is a different city (400607); 400076 is Powai."},
    {"id": 3, "suite": "Pincode vs. Locality Mismatches", "raw": "12/A, Salt Lake Sector 5, Kolkata, 700001", "target": "Sec 5 is 700091; 700001 is Dalhousie."},
    {"id": 4, "suite": "Pincode vs. Locality Mismatches", "raw": "Plot No 45, Jubilee Hills, Hyderabad 500081", "target": "Jubilee Hills is 500033; 81 is Madhapur."},
    {"id": 5, "suite": "Pincode vs. Locality Mismatches", "raw": "Block C, Vasant Kunj, New Delhi 110021", "target": "Vasant Kunj is 110070; 21 is Anand Niketan."},
    {"id": 6, "suite": "Pincode vs. Locality Mismatches", "raw": "Shop No 4, Cyber City, Phase 2, Gurgaon, Delhi", "target": "Conflicting states (Haryana vs Delhi); missing pincode entirely."},
    {"id": 7, "suite": "Pincode vs. Locality Mismatches", "raw": "House 32, Anna Nagar, Chennai 600028", "target": "Anna Nagar is 600040; 28 is RA Puram."},
    {"id": 8, "suite": "Pincode vs. Locality Mismatches", "raw": "Andheri East, Near Railway Station, Mumbai 400058", "target": "Andheri East is 400069; 58 is Andheri West."},
    {"id": 9, "suite": "Pincode vs. Locality Mismatches", "raw": "Koregaon Park, Pune, Maharashtra 411014", "target": "Koregaon Park is 411001; 14 is Viman Nagar."},
    {"id": 10, "suite": "Pincode vs. Locality Mismatches", "raw": "Whitefield, Bengaluru, 560001", "target": "Whitefield is 560066; 01 is MG Road."},

    # --- Suite 2: The Landmark Narrative ---
    {"id": 11, "suite": "The Landmark Narrative", "raw": "opp. ganesh temple, 2nd cross, behind old bus stand, hosur road, madivala, b'lore-68", "target": "Purely relational routing using multiple POIs."},
    {"id": 12, "suite": "The Landmark Narrative", "raw": "Sharma Niwas, take left from dairy, near the big banyan tree, civil lines, prayagraj", "target": "Narrative routing with unmapped natural landmarks."},
    {"id": 13, "suite": "The Landmark Narrative", "raw": "Blue gate house, next to the open drain, 3rd street on the right after crossing railway phatak, Ghaziabad", "target": "Visual instructions ('blue gate', 'open drain')."},
    {"id": 14, "suite": "The Landmark Narrative", "raw": "Up the stairs above Agarwal Sweets, corner shop, main bazar, Paharganj, ND", "target": "Vertical routing ('up the stairs')."},
    {"id": 15, "suite": "The Landmark Narrative", "raw": "Gali no 4, teesra makaan left me, peele rang ka gate, near shiv mandir, rohtak", "target": "Code-mixed Hindi routing ('teesra makaan', 'peele rang')."},
    {"id": 16, "suite": "The Landmark Narrative", "raw": "Just behind Apollo hospital, the road going towards the lake, third building, Salt Lake", "target": "Directional vectors rather than exact coordinate points."},
    {"id": 17, "suite": "The Landmark Narrative", "raw": "Near the water tank, opposite to the post office, main road, Kakinada, AP", "target": "Ambiguous POI dependencies (which water tank?)."},
    {"id": 18, "suite": "The Landmark Narrative", "raw": "House with the red balcony, next to Sharmaji ki dukaan, lane beside police station, Jaipur", "target": "Ephemeral landmarks ('Sharmaji ki dukaan')."},
    {"id": 19, "suite": "The Landmark Narrative", "raw": "Ground floor, come inside the alley next to the pharmacy, ring bell twice, Bandra", "target": "Action-based instructions overriding location data."},
    {"id": 20, "suite": "The Landmark Narrative", "raw": "Call me when you reach the petrol pump, I will guide you, house is inside the narrow lane, Kochi", "target": "Complete absence of final destination coordinates."},

    # --- Suite 3: Token Corruption & Slang ---
    {"id": 21, "suite": "Token Corruption & Slang", "raw": "Flt no 2, kormangla 5th blk, bnglr - 560095", "target": "Extreme vowel dropping and abbreviation."},
    {"id": 22, "suite": "Token Corruption & Slang", "raw": "xx Marol Maroshi Rd, Marol, Andheri WAST, Mumbai 400059", "target": "Phonetic typo ('WAST' instead of West)."},
    {"id": 23, "suite": "Token Corruption & Slang", "raw": "Gnd flr, nr chouraha, m.g. rd, pne", "target": "Regional geographic slangs ('chouraha' for crossroads)."},
    {"id": 24, "suite": "Token Corruption & Slang", "raw": "B-23, sct 62, noida, up, ncr", "target": "Excessive use of acronyms."},
    {"id": 25, "suite": "Token Corruption & Slang", "raw": "1st flr, opp sbi bnk, c g rd, ahmd", "target": "Heavy abbreviation of the city token (Ahmedabad)."},
    {"id": 26, "suite": "Token Corruption & Slang", "raw": "H no 12, triplicn, chnnai 5", "target": "Dropped characters and outdated single-digit postal zones."},
    {"id": 27, "suite": "Token Corruption & Slang", "raw": "Qtr no 4, rly colony, ndls", "target": "Sector jargon (NDLS for New Delhi Railway Station)."},
    {"id": 28, "suite": "Token Corruption & Slang", "raw": "Shp 3, opp rly stn, tvm, kerala", "target": "Extreme city abbreviation (Trivandrum -> TVM)."},
    {"id": 29, "suite": "Token Corruption & Slang", "raw": "H no 9, nr r n t med clg, udiapur", "target": "Typo in city ('udiapur') combined with heavy POI acronyms."},
    {"id": 30, "suite": "Token Corruption & Slang", "raw": "F-4, b/h p n b, c p, dli", "target": "Obscure shorthand ('b/h' for behind, CP for Connaught Place)."},

    # --- Suite 4: Noise Injection ---
    {"id": 31, "suite": "Noise Injection", "raw": "Rahul Sharma (S/O Ramesh Sharma), House No 45, Deliver only after 6 PM, Do not call before 5, Sector 12, Dwarka, New Delhi 110075", "target": "PII and temporal delivery instructions mixed with address."},
    {"id": 32, "suite": "Noise Injection", "raw": "Flat 101, Tower 3, Call my wife on 9876543210 if I don't pick up, Prestige Shantiniketan, Whitefield, Bangalore", "target": "Embedded phone numbers confusing numerical extractors."},
    {"id": 33, "suite": "Noise Injection", "raw": "Shop number 5, Give it to the security guard if shop is closed, Main Market, Lajpat Nagar, Delhi 24", "target": "Conditional logic embedded in the string."},
    {"id": 34, "suite": "Noise Injection", "raw": "House 12, Leave package at the door, Beware of dog, Jubilee hills road no 36, Hyderabad", "target": "Extraneous warning text."},
    {"id": 35, "suite": "Noise Injection", "raw": "C/O Mr Gupta, The tall building next to the park, ring the top bell, Vashi Sector 9, Navi Mumbai", "target": "'C/O' prefixes and physical actions."},
    {"id": 36, "suite": "Noise Injection", "raw": "Ramesh Traders, Ask anyone for Ramesh in the market, Wholesale market, Chandni Chowk, Delhi", "target": "Conversational noise."},
    {"id": 37, "suite": "Noise Injection", "raw": "Plot 4, Deliver on Sunday only, Software Park, Hinjewadi phase 1, Pune", "target": "Date and day constraints masking as location data."},
    {"id": 38, "suite": "Noise Injection", "raw": "House 99, If gate is locked throw it over the wall, Anna Nagar East, Chennai", "target": "Extreme physical instructions."},
    {"id": 39, "suite": "Noise Injection", "raw": "Flat 2A, Call me I will come down, Lift is not working, Park Street, Kolkata", "target": "Status updates ('lift not working') acting as noise."},
    {"id": 40, "suite": "Noise Injection", "raw": "Shop 12, Ask for Chotu, He will take the parcel, Main Bazar, Indore", "target": "Secondary human entities."},

    # --- Suite 5: Rural & Administrative Hierarchies ---
    {"id": 41, "suite": "Rural & Administrative Hierarchies", "raw": "Village Rampur, Post Office Shikarpur, Tehsil Bulandshahr, District Bulandshahr, UP 203395", "target": "Standard rural VPO (Village Post Office) hierarchy."},
    {"id": 42, "suite": "Rural & Administrative Hierarchies", "raw": "Ward No 5, Gram Panchayat Kheda, Via Anand, District Kheda, Gujarat", "target": "Use of 'Via' routing points and Panchayat wards."},
    {"id": 43, "suite": "Rural & Administrative Hierarchies", "raw": "House of Sarpanch, Village Kheri, PO Meham, Rohtak, Haryana 124112", "target": "Entity-based rural addressing ('House of Sarpanch')."},
    {"id": 44, "suite": "Rural & Administrative Hierarchies", "raw": "Near Gramin Bank, Village and PO Palampur, Kangra, HP 176061", "target": "Combined Village/PO tokens."},
    {"id": 45, "suite": "Rural & Administrative Hierarchies", "raw": "VPO Dhana, Tehsil Hansi, Dist Hisar, Haryana", "target": "Heavy use of abbreviations (VPO for Village Post Office)."},
    {"id": 46, "suite": "Rural & Administrative Hierarchies", "raw": "Khata no 45, Khasra no 12/3, Village Jonapur, New Delhi 110047", "target": "Land registry numbers (Khata/Khasra) instead of street numbers."},
    {"id": 47, "suite": "Rural & Administrative Hierarchies", "raw": "House 4, Ward 12, Near Panchayat Bhavan, Village Katihar, Bihar", "target": "Local administrative buildings used as anchors."},
    {"id": 48, "suite": "Rural & Administrative Hierarchies", "raw": "C/O Headmaster, Govt Primary School, Village Sombaria, West Sikkim", "target": "Institutional proxy addressing."},
    {"id": 49, "suite": "Rural & Administrative Hierarchies", "raw": "House of Mukhiya, Village Madhopur, PO and PS Hajipur, Vaishali, Bihar", "target": "Police Station (PS) used as a geographic boundary marker."},
    {"id": 50, "suite": "Rural & Administrative Hierarchies", "raw": "Plot 12, Survey No 45, Gram Panchayat limit, Wagholi, Pune 412207", "target": "Survey numbers used in peri-urban or expanding city edges."}
]

def run_suite_audit():
    print("\n" + "=" * 80)
    print("🚀 RUNNING 50-ADDRESS MASTER BENCHMARK AUDIT ACROSS 5 HARD SUITES 🚀")
    print("=" * 80)

    rows = []
    suite_stats = {}

    for item in TEST_CASES_50:
        tid = item["id"]
        suite = item["suite"]
        raw = item["raw"]
        target = item["target"]

        if suite not in suite_stats:
            suite_stats[suite] = {"total": 0, "verified": 0, "fuzzy": 0, "unverified": 0, "ambiguous": 0}
        suite_stats[suite]["total"] += 1

        # 1. Preprocess
        proc = preprocess_address(raw)
        chars = list(proc)
        feats = extract_features(chars)
        preds = crf_model.predict_single(feats)

        # 2. Resolve
        res, _ = resolve_components(chars, preds)
        res["raw_address"] = raw

        # 3. Verify
        verif = engine.verify_address(res)
        resolved = verif["resolved"]
        clean_addr = build_clean_address(resolved)
        status = verif["verification"]["status"]
        method = verif["verification"]["method"]

        if status == "verified":
            suite_stats[suite]["verified"] += 1
        elif status == "fuzzy_corrected":
            suite_stats[suite]["fuzzy"] += 1
        elif status == "unverified":
            suite_stats[suite]["unverified"] += 1
        else:
            suite_stats[suite]["ambiguous"] += 1

        house = resolved.get("house_number", "")
        street = resolved.get("street", resolved.get("street_address", ""))
        city = resolved.get("city", "")
        dist = resolved.get("district", resolved.get("routing_district", ""))
        state = resolved.get("state", resolved.get("state_area", ""))
        pin = resolved.get("postal_code", "")

        rows.append({
            "Test_ID": tid,
            "Suite": suite,
            "Raw_Address": raw,
            "Target_Challenge": target,
            "Resolved_House": house,
            "Resolved_Street": street,
            "Resolved_City": city,
            "Resolved_District": dist,
            "Resolved_State": state,
            "Resolved_PIN": pin,
            "Clean_Address": clean_addr,
            "Status": status,
            "Method": method
        })

        print(f"\n[ID {tid:02d} | {suite}]")
        print(f"  RAW   : {raw}")
        print(f"  CLEAN : {clean_addr}")
        print(f"  STATUS: {status} | PIN: {pin} | DIST: {dist} | STATE: {state}")

    df_out = pd.DataFrame(rows)
    out_csv = os.path.join(CURRENT_DIR, "audit_50_master_suites_results.csv")
    df_out.to_csv(out_csv, index=False)

    print("\n" + "=" * 80)
    print("📊 50-ADDRESS BENCHMARK PERFORMANCE BREAKDOWN BY SUITE 📊")
    print("=" * 80)
    for s_name, stats in suite_stats.items():
        deliverable = stats["verified"] + stats["fuzzy"]
        print(f"\n📁 [{s_name}] (Total: {stats['total']})")
        print(f"   ✅ Verified / Direct   : {stats['verified']} / {stats['total']} ({stats['verified']/stats['total']*100:.1f}%)")
        print(f"   🔄 Fuzzy Corrected     : {stats['fuzzy']} / {stats['total']} ({stats['fuzzy']/stats['total']*100:.1f}%)")
        print(f"   🛡️ Unverified Catch    : {stats['unverified']} / {stats['total']} ({stats['unverified']/stats['total']*100:.1f}%)")
        print(f"   ❓ Ambiguous           : {stats['ambiguous']} / {stats['total']} ({stats['ambiguous']/stats['total']*100:.1f}%)")
        print(f"   🚚 Deliverability Rate : {deliverable} / {stats['total']} ({deliverable/stats['total']*100:.1f}%)")

    total_all = len(TEST_CASES_50)
    total_deliverable = sum(s["verified"] + s["fuzzy"] for s in suite_stats.values())
    total_unverified = sum(s["unverified"] for s in suite_stats.values())
    total_ambiguous = sum(s["ambiguous"] for s in suite_stats.values())

    print("\n" + "=" * 80)
    print("🏁 FINAL SUMMARY (50 MASTER TEST SUITES) 🏁")
    print("=" * 80)
    print(f"Total Test Cases      : {total_all}")
    print(f"Deliverable Formulated: {total_deliverable} / {total_all} ({total_deliverable/total_all*100:.1f}%)")
    print(f"Unverified Safety Catch: {total_unverified} / {total_all} ({total_unverified/total_all*100:.1f}%)")
    print(f"Ambiguous / Review    : {total_ambiguous} / {total_all} ({total_ambiguous/total_all*100:.1f}%)")
    print(f"Detailed Results Saved To: {out_csv}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    run_suite_audit()
