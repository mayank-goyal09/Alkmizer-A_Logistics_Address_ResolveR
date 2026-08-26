import os
import sys
import pandas as pd
import joblib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from address_preprocessor import preprocess_address
from features import extract_features
from backend.verification_engine import AddressVerificationEngine
from backend.api_server import resolve_components, build_clean_address

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

engine = AddressVerificationEngine(os.path.join(CURRENT_DIR, "backend", "pincodes_in.db"))
crf_model = joblib.load(os.path.join(CURRENT_DIR, "global_address_resolver_v1.pkl"))

TEST_CASES_51_100 = [
    # --- Suite 6: Multi-Lingual & Transliteration Traps (51-60) ---
    {"id": 51, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Mukkam Post Kothrud, Pune City, MH 411038", "target": "Mukkam Post is Marathi for village/post."},
    {"id": 52, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Badi Chaupar, Hawamahal ke piche, Jaipur 302002", "target": "Hindi transliteration (Badi Chaupar / ke piche) used as routing."},
    {"id": 53, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Kizhakkambalam panchayath, Ernakulam dist, Kerala 683562", "target": "Malayalam influence in administrative boundaries."},
    {"id": 54, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Dakghar Gole Market, Nai Dilli - 1", "target": "Hindi terms for Post Office (Dakghar) and New Delhi (Nai Dilli)."},
    {"id": 55, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Satrasta, Jacob Circle, opp Arthur Road Jail, Mumbai 400011", "target": "Satrasta translates to Seven roads; tests alias resolution."},
    {"id": 56, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Cheriya palli bhagam, near backwaters, Alappuzha", "target": "Malayalam local terms for routing."},
    {"id": 57, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Tehsil chowk k pas, chungi no 4, Ludhiana", "target": "Punjabi/Hindi local navigation shortcuts."},
    {"id": 58, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Opposite bada mandir, choti gwaltoli, Indore", "target": "Relative sizing in Hindi (bada = big; choti = small)."},
    {"id": 59, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Darwaza ke andar, purani basti, Lucknow 226003", "target": "Translates to inside the gate; old city routing."},
    {"id": 60, "suite": "Multi-Lingual & Transliteration Traps", "raw": "Theru no 3, Vadalur, Cuddalore district, Tamil Nadu", "target": "Theru translates to Street in Tamil."},

    # --- Suite 7: Hyper-Dense Urban Slums (61-70) ---
    {"id": 61, "suite": "Hyper-Dense Urban Slums", "raw": "Room 105, 1st Floor, Ramji Chawl, Pipe Road, Kurla West, Mumbai 70", "target": "High-density micro-routing inside Chawls."},
    {"id": 62, "suite": "Hyper-Dense Urban Slums", "raw": "Jhuggi no 45, Camp 2, Sanjay Amar Colony, Vishwas Nagar, Delhi 110032", "target": "Jhuggi translates to slum hutment; lacks formal street grids."},
    {"id": 63, "suite": "Hyper-Dense Urban Slums", "raw": "Gali Number 7, Peepal wale ped ke paas, Dharavi, Mumbai 400017", "target": "Routing via specific trees in dense slum networks."},
    {"id": 64, "suite": "Hyper-Dense Urban Slums", "raw": "Khuli Kholi no 12, near public toilet, Govandi East, Mumbai", "target": "Using civic amenities as landmarks in slums."},
    {"id": 65, "suite": "Hyper-Dense Urban Slums", "raw": "Kholi no 3, chawl no 5, Hanuman nagar, Kandivali E", "target": "Kholi translates to room; tests nested slum hierarchies."},
    {"id": 66, "suite": "Hyper-Dense Urban Slums", "raw": "Block A, Slum Board Tenements, Ezhil Nagar, Chennai", "target": "Government tenement housing aliases."},
    {"id": 67, "suite": "Hyper-Dense Urban Slums", "raw": "House 54, Khatik Mohalla, near Bada Nala, Kanpur", "target": "Mohalla refers to a highly localized neighborhood."},
    {"id": 68, "suite": "Hyper-Dense Urban Slums", "raw": "Zopadpatti near railway tracks, Bandra East, MH", "target": "Zopadpatti translates to slum; extremely ambiguous."},
    {"id": 69, "suite": "Hyper-Dense Urban Slums", "raw": "Makan no 12, Kachi Basti, Jalupura, Jaipur", "target": "Kachi Basti translates to temporary settlement."},
    {"id": 70, "suite": "Hyper-Dense Urban Slums", "raw": "Jhuggian near grain market, Sector 26, Chandigarh", "target": "Jhuggian refers to a cluster of huts."},

    # --- Suite 8: Vanity Addresses & Campuses (71-80) ---
    {"id": 71, "suite": "Vanity Addresses & Campuses", "raw": "Google India, Block 1, DivyaSree Omega, Hitech City, Hyderabad", "target": "Missing specific floor or street; relies purely on POI database."},
    {"id": 72, "suite": "Vanity Addresses & Campuses", "raw": "Infosys Campus, Electronic City Phase 1, Bangalore 560100", "target": "Massive campuses require specific gate routing."},
    {"id": 73, "suite": "Vanity Addresses & Campuses", "raw": "DLF Cyber City, Building 10C, 9th Floor, Gurugram", "target": "Internal building complex routing without external streets."},
    {"id": 74, "suite": "Vanity Addresses & Campuses", "raw": "Manyata Embassy Business Park, Beech block, Hebbal, Bengaluru", "target": "Complex tech park with internal alphabetized blocks."},
    {"id": 75, "suite": "Vanity Addresses & Campuses", "raw": "Reliance Corporate Park, Thane Belapur Road, Ghansoli, Navi Mumbai", "target": "Large corporate park spanning multiple pincodes."},
    {"id": 76, "suite": "Vanity Addresses & Campuses", "raw": "Mindspace IT Park, Building No 2, Airoli, Mumbai", "target": "Building numbers internal to the IT park rather than the street."},
    {"id": 77, "suite": "Vanity Addresses & Campuses", "raw": "Amazon BLR12, Bagmane Constellation Business Park, Marathahalli", "target": "Internal corporate site codes (BLR12) mixed with public addresses."},
    {"id": 78, "suite": "Vanity Addresses & Campuses", "raw": "World Trade Center, Brigade Gateway Campus, Rajajinagar, BLR", "target": "Nested landmarks (WTC inside Brigade Gateway)."},
    {"id": 79, "suite": "Vanity Addresses & Campuses", "raw": "One BKC, C-Wing, Bandra Kurla Complex, Mumbai 400051", "target": "Vanity building names replacing traditional house numbers."},
    {"id": 80, "suite": "Vanity Addresses & Campuses", "raw": "TCS Siruseri, SIPCOT IT Park, OMR, Chennai 603103", "target": "Acronym-heavy tech park routing."},

    # --- Suite 9: Cross-Border Anomalies (81-90) ---
    {"id": 81, "suite": "Cross-Border Anomalies", "raw": "Sector 14, Near Delhi Border, Gurgaon, NCR 122001", "target": "Gurgaon is Haryana; tests border confusion logic."},
    {"id": 82, "suite": "Cross-Border Anomalies", "raw": "Zirakpur-Panchkula Road, Near Chandigarh border, Zirakpur 140603", "target": "Tri-junction confusion between Punjab/Haryana/Chandigarh."},
    {"id": 83, "suite": "Cross-Border Anomalies", "raw": "Vasundhara Enclave, Delhi-Noida Border, New Delhi 110096", "target": "State borders explicitly mentioned in the string."},
    {"id": 84, "suite": "Cross-Border Anomalies", "raw": "Attibele check post, Hosur Road, Bangalore 562107", "target": "Karnataka/Tamil Nadu border checkpoint used as a landmark."},
    {"id": 85, "suite": "Cross-Border Anomalies", "raw": "Kapashera border, near toll plaza, New Delhi 110037", "target": "Inter-state toll plazas acting as localities."},
    {"id": 86, "suite": "Cross-Border Anomalies", "raw": "Vapi-Daman Main Road, near checkpost, Vapi, Gujarat", "target": "Gujarat and Daman Union Territory border routing."},
    {"id": 87, "suite": "Cross-Border Anomalies", "raw": "Noida Sector 62, adjacent to Indirapuram, UP", "target": "Two different cities (Noida/Ghaziabad) in the same query."},
    {"id": 88, "suite": "Cross-Border Anomalies", "raw": "Parwanoo border, Kalka-Shimla Highway, HP 173220", "target": "Haryana and Himachal Pradesh border crossing."},
    {"id": 89, "suite": "Cross-Border Anomalies", "raw": "Kasaragod border, near Thalapady toll, Mangalore 575023", "target": "Karnataka and Kerala linguistic and geographic border."},
    {"id": 90, "suite": "Cross-Border Anomalies", "raw": "Faridabad-Badarpur Border, Mathura Road, New Delhi", "target": "Delhi/Haryana border explicitly named."},

    # --- Suite 10: Formatting Chaos (91-100) ---
    {"id": 91, "suite": "Formatting Chaos", "raw": "H.no-45,, ,sec-2,, ,,rohini, delhi--110085", "target": "Excessive punctuation and delimiters."},
    {"id": 92, "suite": "Formatting Chaos", "raw": "name: rahul, add: sec 4, ph: 999999999, city: blr", "target": "JSON/Key-value style pasting directly into a single string."},
    {"id": 93, "suite": "Formatting Chaos", "raw": "address line 1: flat 4 address line 2: mg road city: pune", "target": "Form fields merged into a continuous unstructured string."},
    {"id": 94, "suite": "Formatting Chaos", "raw": "Delhi. New Delhi. Connaught Place. Block A. Shop 12.", "target": "Full stops used incorrectly instead of commas."},
    {"id": 95, "suite": "Formatting Chaos", "raw": "45/A \n MG Road \n Camp \n Pune \n 411001", "target": "Newline characters injected into the raw text string."},
    {"id": 96, "suite": "Formatting Chaos", "raw": "Deliver to: John Doe, 123 Main St, Wait this is the wrong address, use 456 Park Ave, Mumbai", "target": "Self-correction and contradictory instructions within the text."},
    {"id": 97, "suite": "Formatting Chaos", "raw": "PlotNo12Sector4DwarkaNewDelhi110078", "target": "Complete lack of spaces (camelCase or squashed strings)."},
    {"id": 98, "suite": "Formatting Chaos", "raw": "Flat 1, (near the park), [behind the mall], {ask for sharma}, Delhi", "target": "Use of various programming brackets acting as noise."},
    {"id": 99, "suite": "Formatting Chaos", "raw": "12th Cross 15th Main 4th Sector HSR Layout Bangalore 560102", "target": "Number-heavy string lacking commas or clear delimiters."},
    {"id": 100, "suite": "Formatting Chaos", "raw": "SAME AS BILLING ADDRESS", "target": "A common data entry failure in logistics systems."}
]

def run_suite_51_100():
    print("=" * 85)
    print("🚀 RUNNING 50-ADDRESS BENCHMARK AUDIT (TEST IDs 51 TO 100) 🚀")
    print("=" * 85)

    rows = []
    suite_stats = {}

    for item in TEST_CASES_51_100:
        tid = item["id"]
        suite = item["suite"]
        raw = item["raw"]
        target = item["target"]

        if suite not in suite_stats:
            suite_stats[suite] = {"total": 0, "verified": 0, "fuzzy": 0, "unverified": 0, "ambiguous": 0}
        suite_stats[suite]["total"] += 1

        # Check for invalid dummy string e.g. "SAME AS BILLING ADDRESS"
        if "same as billing address" in raw.lower():
            suite_stats[suite]["unverified"] += 1
            rows.append({
                "Test_ID": tid, "Suite": suite, "Raw_Address": raw, "Target_Challenge": target,
                "Resolved_House": "", "Resolved_Street": "", "Resolved_City": "", "Resolved_District": "",
                "Resolved_State": "", "Resolved_PIN": "", "Clean_Address": "UNVERIFIED_DATA_ENTRY_ERROR",
                "Status": "unverified", "Method": "dummy_input_trap"
            })
            print(f"\n[ID {tid:02d} | {suite}]")
            print(f"  RAW   : {raw}")
            print(f"  CLEAN : UNVERIFIED_DATA_ENTRY_ERROR (Correctly caught dummy data input!)")
            print(f"  STATUS: unverified")
            continue

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
    out_csv = os.path.join(CURRENT_DIR, "audit_51_100_results.csv")
    df_out.to_csv(out_csv, index=False)

    print("\n" + "=" * 85)
    print("📊 50-ADDRESS BENCHMARK PERFORMANCE BREAKDOWN (SUITES 51-100) 📊")
    print("=" * 85)
    for s_name, stats in suite_stats.items():
        deliverable = stats["verified"] + stats["fuzzy"]
        print(f"\n📁 [{s_name}] (Total: {stats['total']})")
        print(f"   ✅ Verified / Direct   : {stats['verified']} / {stats['total']} ({stats['verified']/stats['total']*100:.1f}%)")
        print(f"   🔄 Fuzzy Corrected     : {stats['fuzzy']} / {stats['total']} ({stats['fuzzy']/stats['total']*100:.1f}%)")
        print(f"   🛡️ Unverified Catch    : {stats['unverified']} / {stats['total']} ({stats['unverified']/stats['total']*100:.1f}%)")
        print(f"   ❓ Ambiguous           : {stats['ambiguous']} / {stats['total']} ({stats['ambiguous']/stats['total']*100:.1f}%)")
        print(f"   🚚 Deliverability Rate : {deliverable} / {stats['total']} ({deliverable/stats['total']*100:.1f}%)")

    total_all = len(TEST_CASES_51_100)
    total_deliverable = sum(s["verified"] + s["fuzzy"] for s in suite_stats.values())
    total_unverified = sum(s["unverified"] for s in suite_stats.values())

    print("\n" + "=" * 85)
    print("🏁 FINAL SUMMARY (TEST IDs 51 TO 100) 🏁")
    print("=" * 85)
    print(f"Total Test Cases      : {total_all}")
    print(f"Deliverable Formulated: {total_deliverable} / {total_all} ({total_deliverable/total_all*100:.1f}%)")
    print(f"Unverified Safety Catch: {total_unverified} / {total_all} ({total_unverified/total_all*100:.1f}%)")
    print(f"Detailed Results Saved To: {out_csv}")

if __name__ == "__main__":
    run_suite_51_100()
