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

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Load DB and Model
engine = AddressVerificationEngine(os.path.join(CURRENT_DIR, "backend", "pincodes_in.db"))
crf_model = joblib.load(os.path.join(CURRENT_DIR, "global_address_resolver_v1.pkl"))

CSV_PATH = os.path.join(CURRENT_DIR, "unstructured_jewellery_addresses_jaipur.csv")
df_raw = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df_raw)} records from {CSV_PATH}")

def extract_ground_truth(original_address):
    """Extract expected PIN, city, state from ground truth across all India."""
    pin_match = re.search(r'\b([1-9]\d{5})\b', original_address)
    expected_pin = pin_match.group(1) if pin_match else ""
    
    orig_lower = original_address.lower()
    expected_state = ""
    for st in ["karnataka", "rajasthan", "maharashtra", "assam", "delhi", "kerala", "telangana", "tamil nadu", "uttar pradesh", "gujarat", "bihar"]:
        if st in orig_lower:
            expected_state = st.title()
            break
            
    expected_city = ""
    for ct in ["bangalore", "bengaluru", "jaipur", "nagpur", "guwahati", "delhi", "new delhi", "thrissur", "mumbai", "hyderabad"]:
        if ct in orig_lower:
            expected_city = ct.title()
            break
            
    return expected_pin, expected_city, expected_state

def run_large_scale_audit():
    print("=" * 85)
    print(f"🚀 STARTING 1,100 REAL-WORLD UNSTRUCTURED ADDRESS AUDIT 🚀")
    print("=" * 85)
    
    results = []
    
    category_stats = {}
    total_processed = 0
    total_strict_pass = 0
    total_pin_match = 0
    total_deliverable = 0
    total_unverified = 0
    total_wrong_misroutes = 0
    
    for idx, row in df_raw.iterrows():
        rid = row.get("Record_ID", idx + 1)
        vtype = str(row.get("Variant_Type", "Unknown")).strip()
        persona = str(row.get("Persona_Style", "")).strip()
        raw_addr = str(row.get("Unstructured_Address", "")).strip()
        orig_addr = str(row.get("Original_Address", "")).strip()
        
        if not raw_addr:
            continue
            
        total_processed += 1
        if vtype not in category_stats:
            category_stats[vtype] = {
                "total": 0, "strict_pass": 0, "pin_match": 0,
                "deliverable": 0, "unverified": 0, "wrong": 0
            }
        category_stats[vtype]["total"] += 1
        
        exp_pin, exp_city, exp_state = extract_ground_truth(orig_addr)
        
        # 1. Preprocess
        proc = preprocess_address(raw_addr)
        chars = list(proc)
        feats = extract_features(chars)
        preds = crf_model.predict_single(feats)
        
        # 2. Resolve
        res, _ = resolve_components(chars, preds)
        res["raw_address"] = raw_addr
        
        # 3. Verify
        verif = engine.verify_address(res)
        resolved = verif["resolved"]
        clean_addr = build_clean_address(resolved)
        status = verif["verification"]["status"]
        method = verif["verification"]["method"]
        
        res_pin = str(resolved.get("postal_code", "")).replace(".0", "").strip()
        res_city = str(resolved.get("city", "")).strip()
        res_state = str(resolved.get("state", resolved.get("state_area", ""))).strip()
        res_dist = str(resolved.get("district", resolved.get("routing_district", ""))).strip()
        
        # Evaluation Logic
        pin_matched = bool(exp_pin and res_pin == exp_pin)
        
        # State/City validation across all India
        state_matched = bool(exp_state.lower() in res_state.lower() or exp_state.lower() in clean_addr.lower() or not exp_state)
        city_matched = bool(exp_city.lower() in res_city.lower() or exp_city.lower() in clean_addr.lower() or exp_city.lower() in res_dist.lower() or not exp_city)
        
        # Strict Pass Criteria:
        # If expected PIN exists: res_pin must match exp_pin.
        if exp_pin:
            strict_pass = (res_pin == exp_pin)
        else:
            strict_pass = (state_matched and city_matched and status in ["verified", "fuzzy_corrected"])
            
        is_deliverable = (status in ["verified", "fuzzy_corrected"] and len(res_pin) == 6)
        is_unverified = (status == "unverified" or not res_pin)
        
        # Wrong / Misroute Criteria:
        # A misroute occurs if the model assigned a PIN belonging to a completely different STATE or distant region
        # while claiming to be "verified".
        is_misroute = False
        if is_deliverable and exp_state:
            if res_state and (exp_state.lower() not in res_state.lower() and res_state.lower() not in exp_state.lower()):
                is_misroute = True
                
        if strict_pass:
            total_strict_pass += 1
            category_stats[vtype]["strict_pass"] += 1
        if pin_matched:
            total_pin_match += 1
            category_stats[vtype]["pin_match"] += 1
        if is_deliverable:
            total_deliverable += 1
            category_stats[vtype]["deliverable"] += 1
        if is_unverified:
            total_unverified += 1
            category_stats[vtype]["unverified"] += 1
        if is_misroute:
            total_wrong_misroutes += 1
            category_stats[vtype]["wrong"] += 1
            
        results.append({
            "Record_ID": rid,
            "Variant_Type": vtype,
            "Raw_Address": raw_addr,
            "Original_Target": orig_addr,
            "Expected_PIN": exp_pin,
            "Resolved_PIN": res_pin,
            "Resolved_City": res_city,
            "Resolved_District": res_dist,
            "Resolved_State": res_state,
            "Clean_Address": clean_addr,
            "Status": status,
            "Method": method,
            "Strict_Pass": strict_pass,
            "PIN_Matched": pin_matched,
            "Is_Deliverable": is_deliverable,
            "Is_Misroute": is_misroute
        })
        
        if total_processed % 100 == 0 or total_processed == len(df_raw):
            print(f"  Processed {total_processed}/{len(df_raw)} addresses | Current Strict Pass: {total_strict_pass}/{total_processed} ({total_strict_pass/total_processed*100:.1f}%) | Deliverable: {total_deliverable}/{total_processed} ({total_deliverable/total_processed*100:.1f}%)")

    df_out = pd.DataFrame(results)
    out_csv = os.path.join(CURRENT_DIR, "audit_1100_unstructured_results.csv")
    df_out.to_csv(out_csv, index=False)
    
    print("\n" + "=" * 85)
    print("📊 1,100 REAL UNSTRUCTURED ADDRESS AUDIT - VARIANT BREAKDOWN 📊")
    print("=" * 85)
    for vt, stats in category_stats.items():
        tot = stats["total"]
        sp = stats["strict_pass"]
        pm = stats["pin_match"]
        deliv = stats["deliverable"]
        unv = stats["unverified"]
        wrg = stats["wrong"]
        print(f"\n📁 [{vt}] (Total: {tot})")
        print(f"   🎯 Strict Pass Accuracy : {sp:4d} / {tot} ({sp/tot*100:.1f}%)")
        print(f"   📮 Exact PIN Match      : {pm:4d} / {tot} ({pm/tot*100:.1f}%)")
        print(f"   🚚 Deliverable Formatted: {deliv:4d} / {tot} ({deliv/tot*100:.1f}%)")
        print(f"   🛡️ Safe Unverified Catch: {unv:4d} / {tot} ({unv/tot*100:.1f}%)")
        print(f"   ❌ Misroute / Out-of-State: {wrg:4d} / {tot} ({wrg/tot*100:.1f}%)")

    print("\n" + "=" * 85)
    print("🏁 OVERALL 1,100 AUDIT METRICS 🏁")
    print("=" * 85)
    print(f"Total Evaluated Addresses : {total_processed}")
    print(f"Strict Overall Accuracy   : {total_strict_pass} / {total_processed} ({total_strict_pass/total_processed*100:.2f}%)")
    print(f"Exact PIN Match Rate      : {total_pin_match} / {total_processed} ({total_pin_match/total_processed*100:.2f}%)")
    print(f"Deliverable Formulated    : {total_deliverable} / {total_processed} ({total_deliverable/total_processed*100:.2f}%)")
    print(f"Safe Unverified Catch     : {total_unverified} / {total_processed} ({total_unverified/total_processed*100:.2f}%)")
    print(f"Dangerous Misroute Rate   : {total_wrong_misroutes} / {total_processed} ({total_wrong_misroutes/total_processed*100:.2f}%)")
    print(f"Detailed CSV Report Saved : {out_csv}")

if __name__ == "__main__":
    run_large_scale_audit()
