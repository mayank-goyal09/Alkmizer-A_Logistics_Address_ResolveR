"""
urban_sublocalities_matcher.py
------------------------------
High-Performance Fuzzy, Spaceless, and Phonetic Urban Sub-Locality Matcher.

Connects colloquial residential layouts, shopping alleys, and local quarters
(e.g. 'Beml Layout', 'Chandra Layout', 'Ashoka Pillar Jayanagar', 'Raja Market')
directly to their verified India Post Delivery Post Office and PIN codes.

Handles:
1. Spaceless concatenations: 'bemllayout' -> 'BEML Layout' (560098)
2. Phonetic spelling errors: 'chandra leyout' -> 'Chandra Layout' (560040)
3. Minimal / Zero-City inputs: 'near ashoka pillar jayanagar' -> '560011' (Bengaluru)
"""

import os
import json
import re
import difflib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GAZETTEER_PATH = os.path.join(CURRENT_DIR, "urban_sublocalities.json")

# Load compiled gazetteer once
_SUBLOCALITIES = {}
if os.path.exists(GAZETTEER_PATH):
    with open(GAZETTEER_PATH, "r", encoding="utf-8") as f:
        _SUBLOCALITIES = json.load(f)

# Common layout suffixes to strip/standardize for fuzzy comparison
_LAYOUT_STOPWORDS = {"layout", "leyout", "layot", "nagar", "nagarr", "colony", "colny", "bazaar", "bazar", "bzr", "market", "mrkt", "block", "blk", "road", "rod", "rood"}

def _get_sound_key(s: str) -> str:
    """Consonant phonetic sound key for Indian words."""
    if not s:
        return ""
    clean = re.sub(r'[^a-zA-Z]', '', s.lower())
    if not clean:
        return ""
    # Standardize consonants
    clean = clean.replace('ph', 'f').replace('gh', 'g').replace('kh', 'k').replace('th', 't').replace('dh', 'd').replace('sh', 's').replace('ee', 'i').replace('oo', 'u')
    first = clean[0]
    rem = "".join([c for c in clean[1:] if c not in "aeiou"])
    # Dedup
    dedup = ""
    last = ""
    for c in (first + rem):
        if c != last:
            dedup += c
            last = c
    return dedup

def match_urban_sublocality(text: str, context_city: str = None) -> dict:
    """
    Finds the best matching urban sub-locality from text.
    Handles:
    - Direct substring matches
    - Spaceless matches
    - Phonetic typo matches
    
    Returns dict with {canonical_name, city, district, state, pincode, match_type} or None.
    """
    if not text:
        return None

    t_clean = text.lower().replace(".", " ").replace(",", " ")
    t_words = t_clean.split()
    t_unspaced = t_clean.replace(" ", "")

    # Detect city in text if not explicitly provided in context_city
    if not context_city:
        for c in ["bengaluru", "bangalore", "jaipur", "nagpur", "guwahati", "delhi", "new delhi", "thrissur", "mumbai", "hyderabad"]:
            if re.search(rf'\b{c}\b', t_clean):
                context_city = c
                break

    # Filter keys to ensure consistency with city if city is known
    filtered_keys = []
    sorted_keys = sorted(_SUBLOCALITIES.keys(), key=len, reverse=True)
    for k in sorted_keys:
        # Skip keys that start with numbers or are too short
        if re.match(r'^\d', k) or len(k) < 5:
            continue
        cand_city = _SUBLOCALITIES[k].get("city", "").lower()
        if context_city and cand_city:
            if context_city not in cand_city and cand_city not in context_city:
                continue
        filtered_keys.append(k)

    # 1. Fast Path: Direct key or substring matching
    for key in filtered_keys:
        # Check whole word or phrase in text
        if len(key) >= 5:
            pattern = rf'\b{re.escape(key)}\b'
            if re.search(pattern, t_clean):
                match_data = dict(_SUBLOCALITIES[key])
                match_data["match_type"] = "exact_phrase"
                return match_data
                
            # Check spaceless
            key_unspaced = key.replace(" ", "")
            if len(key_unspaced) >= 7 and key_unspaced in t_unspaced:
                match_data = dict(_SUBLOCALITIES[key])
                match_data["match_type"] = "spaceless"
                return match_data

    # 2. Phonetic & Fuzzy Path: For spelling errors like 'chandra leyout', 'beml layot', 'ashoka pilar'
    # Check 2-word and 3-word n-grams from the query
    ngrams = []
    for n in [2, 3, 4]:
        for i in range(len(t_words) - n + 1):
            ngrams.append(" ".join(t_words[i:i+n]))

    best_cand = None
    best_score = 0.0

    for ng in ngrams:
        if len(ng) < 6:
            continue
        ng_sound = _get_sound_key(ng)
        for key in filtered_keys:
            # Check length similarity first
            if abs(len(ng) - len(key)) > 4:
                continue
                
            # SequenceMatcher ratio
            ratio = difflib.SequenceMatcher(None, ng, key).ratio()
            
            # Sound key match gives huge boost to Indian typos
            key_sound = _get_sound_key(key)
            sound_ratio = difflib.SequenceMatcher(None, ng_sound, key_sound).ratio()
            
            combined_score = max(ratio, sound_ratio * 0.95)
            
            if combined_score > best_score and combined_score >= 0.82:
                # 1. Distinctive Name Guard: Prevent 'Drd Tower' matching 'RK Tower'
                from generic_entity_gazetteer import do_distinctive_names_match
                if not do_distinctive_names_match(ng, key):
                    continue
                    
                # 2. Geographic Coherence Guard: Check for state/city contradiction
                cand_state = _SUBLOCALITIES[key].get("state", "").lower()
                state_conflict = False
                if cand_state and cand_state not in t_clean:
                    for s in ["kerala", "assam", "telangana", "maharashtra", "rajasthan", "karnataka", "delhi", "uttar pradesh", "west bengal", "tamil nadu", "gujarat", "haryana", "bihar"]:
                        if re.search(rf'\b{s}\b', t_clean) and s != cand_state:
                            state_conflict = True
                            break
                if state_conflict:
                    continue
                            
                best_score = combined_score
                best_cand = dict(_SUBLOCALITIES[key])
                best_cand["matched_ngram"] = ng
                best_cand["confidence"] = combined_score
                best_cand["match_type"] = "fuzzy_phonetic"

    if best_cand and best_score >= 0.82:
        return best_cand

    return None
