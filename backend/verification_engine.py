import os
import re
import sqlite3
import difflib
import numpy as np
from abc import ABC, abstractmethod
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from address_preprocessor import _CITIES_FOR_SPLIT, preprocess_address

class ResolutionReason:
    EXACT_MATCH = "EXACT_MATCH"
    CITY_ALIAS = "CITY_ALIAS"
    PIN_COMPATIBLE = "PIN_COMPATIBLE"
    DISTRICT_FALLBACK = "DISTRICT_FALLBACK"
    INVALID_CITY = "INVALID_CITY"

class CityResolution:
    def __init__(self, display_city: str, routing_district: str, confidence: float, reason: str, raw_city: str = None, normalized_city: str = None):
        self.display_city = display_city
        self.routing_district = routing_district
        self.confidence = confidence
        self.reason = reason
        self.raw_city = raw_city
        self.normalized_city = normalized_city

# --- Phonetic Helper Functions ---
def get_indian_sound_key(s):
    if not s:
        return ""
    s = s.lower().replace(" ", "")
    
    # Standardize phonetic variants common in Indian accents/writing
    s = s.replace("ph", "f")
    s = s.replace("gh", "g")
    s = s.replace("kh", "k")
    s = s.replace("dh", "d")
    s = s.replace("th", "t")
    s = s.replace("bh", "b")
    s = s.replace("sh", "s")
    s = s.replace("ch", "s")
    s = s.replace("jh", "j")
    s = s.replace("w", "v")
    s = s.replace("oo", "u")
    s = s.replace("ee", "i")
    s = s.replace("y", "i")
    
    # Keep the first character
    first_char = s[0] if s else ""
    remaining = s[1:] if len(s) > 1 else ""
    
    # Remove vowels from the remaining characters
    remaining = "".join([c for c in remaining if c not in "aeiou"])
    
    # Collapse duplicate consecutive characters
    collapsed = ""
    last_c = ""
    for c in (first_char + remaining):
        if c != last_c:
            collapsed += c
            last_c = c
            
    return collapsed

def phonetic_similarity(s1, s2):
    key1 = get_indian_sound_key(s1)
    key2 = get_indian_sound_key(s2)
    if not key1 or not key2:
        return 0.0
    return difflib.SequenceMatcher(None, key1, key2).ratio()


class AddressVerifier(ABC):
    @abstractmethod
    def verify(self, raw_prediction: dict) -> dict:
        """
        Takes a raw prediction dictionary and returns a verified/corrected address structure 
        including verification metadata.
        """
        pass

# Metro-District Hierarchy: maps administrative DB districts to their colloquial metro city names.
# When a user writes 'Kolkata' but the DB resolves to 'Howrah', we still accept it as valid.
METRO_DISTRICT_HIERARCHY = {
    # Kolkata Metropolitan Area
    "howrah": "kolkata",
    "hooghly": "kolkata",
    "north 24 parganas": "kolkata",
    "south 24 parganas": "kolkata",
    "kolkata": "kolkata",
    # Mumbai Metropolitan Area
    "thane": "mumbai",
    "navi mumbai": "mumbai",
    "palghar": "mumbai",
    "raigad": "mumbai",
    # Delhi NCR / Noida
    "gurgaon": "delhi",
    "gurugram": "delhi",
    "noida": "noida",
    "gautam buddh nagar": "noida",
    "gautam buddha nagar": "noida",
    "faridabad": "delhi",
    "ghaziabad": "delhi",
    "new delhi": "delhi",
    # Hyderabad Metropolitan Area
    "secunderabad": "hyderabad",
    "ranga reddy": "hyderabad",
    "rangareddy": "hyderabad",
    "cyberabad": "hyderabad",
    # Bengaluru
    "bangalore rural": "bengaluru",
    "bangalore urban": "bengaluru",
    # Chennai Metropolitan Area
    "tambaram": "chennai",
    "kancheepuram": "chennai",
    "chengalpattu": "chennai",
    # Pune Metropolitan Area
    "pimpri chinchwad": "pune",
    "pimpri-chinchwad": "pune",
    "pcmc": "pune",
    # Kochi / Ernakulam
    "ernakulam": "kochi",
    # Guwahati / Kamrup
    "kamrup": "guwahati",
    "kamrup metropolitan": "guwahati",
    # Bhubaneswar / Khurda
    "khorda": "bhubaneswar",
    "khurda": "bhubaneswar",
}


class AliasResolver:
    def __init__(self, db_path):
        self.db_path = db_path
        self._load_aliases()

    def _load_aliases(self):
        # Start with standard hardcoded colloquial aliases
        self.aliases = {
            "cp": ("connaught place", "locality"),
            "sec 62": ("sector 62", "locality"),
            "huda": ("huda colony", "locality"),
            "bangalore": ("bengaluru", "city"),
            "calcutta": ("kolkata", "city"),
            "bombay": ("mumbai", "city"),
            "madras": ("chennai", "city"),
            "trivandrum": ("thiruvananthapuram", "city"),
            "bengaluru": ("bengaluru", "city"),
            "mumbai": ("mumbai", "city"),
            "kolkata": ("kolkata", "city"),
            "chennai": ("chennai", "city"),
            "delhi": ("delhi", "city"),
            # Gurugram / Gurgaon equivalence
            "gurugram": ("gurgaon", "city"),
            "gurgaon": ("gurgaon", "city"),
            # Noida / Gautam Buddh Nagar
            "noida": ("noida", "city"),
            "gautam buddh nagar": ("noida", "city"),
            # Visakhapatnam / Vizag
            "vizag": ("visakhapatnam", "city"),
            "visakhapatnam": ("visakhapatnam", "city"),
            # Vadodara / Baroda
            "baroda": ("vadodara", "city"),
            "vadodara": ("vadodara", "city"),
        }
        if not os.path.exists(self.db_path):
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT alias, canonical_name, entity_type FROM aliases")
            for alias, canonical, entity_type in cursor.fetchall():
                self.aliases[alias.lower().strip()] = (canonical.strip(), entity_type)
            conn.close()
        except Exception as e:
            print(f"Error loading aliases: {e}")

    def resolve(self, name: str) -> str:
        if not name:
            return name
        name_clean = name.lower().replace(" ", "").replace(".", "").replace(",", "")
        # Check against unspaced alias keys
        for alias_key, (canonical_name, entity_type) in self.aliases.items():
            key_clean = alias_key.lower().replace(" ", "")
            if name_clean == key_clean:
                return canonical_name
        return name

    def resolve_unspaced_query(self, query: str) -> str:
        if not query:
            return ""
        q_clean = query.lower().replace(" ", "").replace(".", "").replace(",", "")
        
        # Sort alias keys by length descending to replace longer ones first
        sorted_keys = sorted(self.aliases.keys(), key=len, reverse=True)
        for key in sorted_keys:
            key_clean = key.lower().replace(" ", "")
            if key_clean in q_clean:
                canonical, entity_type = self.aliases[key]
                if entity_type == "locality":
                    canonical_clean = canonical.lower().replace(" ", "")
                    q_clean = q_clean.replace(key_clean, canonical_clean)
        return q_clean

    def extract_district_or_city(self, query: str):
        if not query:
            return None, None
        q_clean = query.lower().replace(".", "").replace(",", "")
        words = q_clean.split()
        q_unspaced = q_clean.replace(" ", "")
        
        from transit_roads_gazetteer import is_city_word_in_road_context
        
        # Sort by key length descending
        sorted_keys = sorted(self.aliases.keys(), key=len, reverse=True)
        for alias_key in sorted_keys:
            canonical_name, entity_type = self.aliases[alias_key]
            if entity_type in ("district", "city"):
                # If this city word appears as part of an arterial road compound (e.g. 'Old Madras Road', 'Delhi Highway'),
                # do NOT treat it as the destination city!
                if is_city_word_in_road_context(query, alias_key):
                    continue
                key_clean = alias_key.lower().replace(" ", "")
                if key_clean in words or key_clean in q_unspaced:
                    return canonical_name, entity_type
        return None, None

class PincodeLookupService:
    def __init__(self, db_path):
        self.db_path = db_path

    def lookup_pincode(self, pincode: str) -> list:
        if not pincode or not pincode.isdigit():
            return []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT place_name, district, state_name, state_code, latitude, longitude FROM pincodes WHERE pincode = ?", 
            (pincode,)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

class CandidateGenerator:
    def __init__(self, lookup_service: PincodeLookupService):
        self.lookup_service = lookup_service

    def generate(self, pincode: str) -> list:
        return self.lookup_service.lookup_pincode(pincode)

class CandidateRanker:
    def __init__(self, alias_resolver: AliasResolver):
        self.alias_resolver = alias_resolver

    def _similarity(self, s1: str, s2: str) -> float:
        if not s1 or not s2:
            return 0.0
        return difflib.SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()

    def rank(self, candidates: list, raw_prediction: dict) -> tuple:
        """
        Ranks database candidates against the raw prediction.
        Returns (best_candidate, match_score)
        """
        if not candidates:
            return None, 0.0

        best_cand = None
        best_score = -1.0

        # Extract text components to compare
        pred_street = raw_prediction.get("street", "")
        pred_house = raw_prediction.get("house_number", "")
        pred_city = raw_prediction.get("city", "")
        pred_district = raw_prediction.get("district", "")
        if not pred_district and pred_city:
            pred_district = pred_city

        # Combined context to find mentions of locality name
        search_context = f"{pred_house} {pred_street} {pred_city}".lower()

        for cand in candidates:
            place = cand.get("place_name", "")
            dist = cand.get("district", "")
            state = cand.get("state_name", "")

            # Resolve aliases
            resolved_place = self.alias_resolver.resolve(place)
            resolved_dist = self.alias_resolver.resolve(dist)

            # 1. Check if the place_name (locality) is explicitly mentioned in raw fields
            locality_sim = 0.0
            if place.lower() in search_context or resolved_place.lower() in search_context:
                locality_sim = 1.0
            else:
                # Fuzzy match with street/city/house_number
                locality_sim = max(
                    self._similarity(place, pred_street),
                    self._similarity(place, pred_city),
                    self._similarity(resolved_place, pred_street),
                    self._similarity(resolved_place, pred_city)
                )

            # 2. Check district similarity
            dist_sim = max(
                self._similarity(dist, pred_district),
                self._similarity(resolved_dist, pred_district),
                self._similarity(dist, pred_city),
                self._similarity(resolved_dist, pred_city)
            )

            # 3. Check street/context similarity
            street_sim = self._similarity(place, pred_street)

            # 4. Check alias match
            alias_match = 1.0 if place.lower() != resolved_place.lower() or dist.lower() != resolved_dist.lower() else 0.0

            # Score = 0.50 * locality similarity + 0.25 * street similarity + 0.15 * district similarity + 0.10 * alias match
            score = (0.50 * locality_sim) + (0.25 * street_sim) + (0.15 * dist_sim) + (0.10 * alias_match)

            if score > best_score:
                best_score = score
                best_cand = cand

        return best_cand, round(best_score, 2)

class FuzzyMatcher:
    def __init__(self, db_path: str, alias_resolver: AliasResolver):
        self.db_path = db_path
        self.alias_resolver = alias_resolver

    def _similarity(self, s1: str, s2: str) -> float:
        if not s1 or not s2:
            return 0.0
        return difflib.SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()

    def fuzzy_match(self, raw_prediction: dict) -> tuple:
        """
        Fuzzy matches predicted fields against database records when PIN is missing/invalid.
        Returns (matched_record, match_score)
        """
        pred_state = raw_prediction.get("state", raw_prediction.get("state_area", ""))
        pred_city = raw_prediction.get("city", "")
        pred_district = raw_prediction.get("district", "")
        if not pred_district and pred_city:
            pred_district = pred_city

        if not pred_state and not pred_city:
            return None, 0.0

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Step 1: Match State first (since there are only ~36 states, this is fast)
        cursor.execute("SELECT DISTINCT state_name, state_code FROM pincodes")
        states = [dict(row) for row in cursor.fetchall()]
        
        best_state = None
        best_state_score = 0.0
        for s in states:
            resolved_s = self.alias_resolver.resolve(s["state_name"])
            score = max(
                self._similarity(s["state_name"], pred_state),
                self._similarity(s["state_code"], pred_state),
                self._similarity(resolved_s, pred_state)
            )
            if score > best_state_score:
                best_state_score = score
                best_state = s

        # If we have a decent state match, restrict search to that state
        if best_state and best_state_score >= 0.7:
            state_filter = best_state["state_name"]
            
            # Match City/District within State
            cursor.execute(
                "SELECT place_name, district, state_name, state_code, pincode, latitude, longitude FROM pincodes WHERE state_name = ?", 
                (state_filter,)
            )
            candidates = [dict(row) for row in cursor.fetchall()]
        else:
            # Fallback: Query major places/districts (first 10,000 for safety and performance)
            cursor.execute(
                "SELECT place_name, district, state_name, state_code, pincode, latitude, longitude FROM pincodes LIMIT 10000"
            )
            candidates = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Rank candidates
        best_cand = None
        best_score = -1.0
        for cand in candidates:
            # Score against city / district / place
            score_place = self._similarity(cand["place_name"], pred_city)
            score_district = self._similarity(cand["district"], pred_district)
            score = (score_place * 0.6) + (score_district * 0.4)
            if score > best_score:
                best_score = score
                best_cand = cand

        return best_cand, round(best_score, 2)

class IndiaPincodeVerifier(AddressVerifier):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.alias_resolver = AliasResolver(db_path)
        self.lookup_service = PincodeLookupService(db_path)
        self.candidate_generator = CandidateGenerator(self.lookup_service)
        self.candidate_ranker = CandidateRanker(self.alias_resolver)
        self.fuzzy_matcher = FuzzyMatcher(db_path, self.alias_resolver)

    def _normalize_pincode(self, pin_str: str) -> str:
        if not pin_str:
            return ""
        # If the string contains NO digits at all, it is an alphabetic word, NOT an OCR PIN!
        if not any(c.isdigit() for c in pin_str):
            return ""
        s = pin_str.lower().strip()
        replacements = {
            'o': '0', 'p': '0', 'q': '0',
            'i': '1', 'l': '1', 't': '1',
            's': '5',
            'g': '9',
            'b': '8',
            'z': '2'
        }
        for char, digit in replacements.items():
            s = s.replace(char, digit)
        import re
        return re.sub(r'\D', '', s)

    def _extract_and_normalize_pincode(self, raw_prediction: dict) -> str:
        # 1. Check if the parsed postal_code exists
        parsed_pin = raw_prediction.get("postal_code", "").strip()
        if parsed_pin:
            cleaned = self._normalize_pincode(parsed_pin)
            if len(cleaned) == 6 and cleaned[0] != '0':
                return cleaned

        # 2. Search for any 6-digit number in all parsed fields
        import re
        full_text = " ".join(raw_prediction.values())
        digits_6 = re.findall(r'\b\d{6}\b', full_text)
        if digits_6:
            return digits_6[-1]
        
        # Try finding 6 digits even without word boundaries (spaceless)
        digits_6_nobound = re.findall(r'\d{6}', full_text)
        if digits_6_nobound:
            return digits_6_nobound[-1]

        # 3. Search for any token that already has at least 3 digits (with OCR character typos)
        tokens = re.split(r'[\s,;\-]+', full_text)
        for token in reversed(tokens):
            if not token:
                continue
            # Require at least 3 digits in the token before attempting OCR letter conversion
            if sum(c.isdigit() for c in token) < 3:
                continue
            cleaned_token = self._normalize_pincode(token)
            if len(cleaned_token) == 6 and cleaned_token[0] != '0':
                return cleaned_token
            # If the token is longer but ends with a 6-digit-like pattern (e.g. "tamilnadu600029")
            if len(token) >= 6:
                last_6 = token[-6:]
                if sum(c.isdigit() for c in last_6) >= 3:
                    cleaned_last_6 = self._normalize_pincode(last_6)
                    if len(cleaned_last_6) == 6 and cleaned_last_6[0] != '0':
                        return cleaned_last_6

        # Fallback to the parsed pin cleaned only if it contains digits
        return self._normalize_pincode(parsed_pin)

    def normalize_city(self, city_str: str) -> str:
        if not city_str:
            return ""
        # Strip spacing and lowercase
        s = city_str.lower().strip()
        # Resolve aliases using alias_resolver
        return self.alias_resolver.resolve(s).lower().strip()

    def resolve_city(self, user_city: str, matched_district: str, matched_pincode: str, conn, raw_prediction: dict = None) -> CityResolution:
        raw_city = user_city
        
        # 1. Normalize
        normalized_city = self.normalize_city(user_city)
        matched_district_clean = matched_district.lower().strip()
        matched_district_normalized = self.normalize_city(matched_district)

        # Let's collect all possible valid names (districts and place names) for compatibility checking
        import re
        import difflib
        
        nearby_names = set()
        prefix_names = set()
        
        try:
            pin_num = int(re.sub(r'\D', '', matched_pincode))
            cursor = conn.cursor()
            
            # A & B. Query exact and nearby PINs (±20 range for suburban coverage)
            cursor.execute(
                "SELECT DISTINCT district FROM pincodes WHERE pincode >= ? AND pincode <= ?",
                (pin_num - 20, pin_num + 20)
            )
            for dist, in cursor.fetchall():
                if dist:
                    nearby_names.add(dist.strip())
                    
            # C. Query 3-digit prefix (Final fallback heuristic)
            prefix_str = matched_pincode[:3]
            if len(prefix_str) == 3 and prefix_str.isdigit():
                cursor.execute(
                    "SELECT DISTINCT district FROM pincodes WHERE pincode LIKE ?",
                    (f"{prefix_str}%",)
                )
                for dist, in cursor.fetchall():
                    if dist:
                        prefix_names.add(dist.strip())
        except Exception as e:
            print(f"Error querying compatibility names: {e}")

        # Helper function to check if a word is compatible (exact or fuzzy)
        def find_best_compatible_match(names_set, word, threshold=0.70):
            if not word:
                return None, 0.0
            norm_word = self.normalize_city(word)
            best_match = None
            best_sim = 0.0
            for name in names_set:
                norm_name = self.normalize_city(name)
                # Check direct match
                if norm_word == norm_name or word.lower().strip() == name.lower().strip():
                    return name, 1.0
                # Check similarity
                sim = difflib.SequenceMatcher(None, norm_word, norm_name).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best_match = name
            if best_sim >= threshold:
                return best_match, best_sim
            return None, 0.0

        # Build list of candidate words to check for city resolution:
        # First check user_city.
        # If user_city is empty or not matching well, look through other fields in raw_prediction
        candidate_words = []
        if user_city:
            candidate_words.append(user_city)
            
        if raw_prediction:
            # Add all other field values as candidates (split by spaces/commas)
            for val in raw_prediction.values():
                if val:
                    # Split into word tokens
                    tokens = re.split(r'[\s,;\-]+', val)
                    for tok in tokens:
                        tok_clean = tok.strip()
                        if len(tok_clean) >= 4 and tok_clean not in candidate_words:
                            candidate_words.append(tok_clean)
        
        # If no candidates are found at all
        if not candidate_words:
            return CityResolution(
                display_city=matched_district,
                routing_district=matched_district,
                confidence=0.90,
                reason=ResolutionReason.DISTRICT_FALLBACK,
                raw_city=raw_city,
                normalized_city=""
            )

        # Try to resolve city from our candidate words
        # 1. Direct/Alias matches first (highest confidence)
        for cand in candidate_words:
            cand_clean = cand.lower().strip()
            cand_normalized = self.normalize_city(cand)
            
            # Direct match with matched district
            if cand_clean == matched_district_clean or cand_clean == matched_district_normalized:
                return CityResolution(
                    display_city=matched_district,
                    routing_district=matched_district,
                    confidence=1.00,
                    reason=ResolutionReason.EXACT_MATCH,
                    raw_city=cand,
                    normalized_city=cand_normalized
                )
                
            # Alias match with matched district
            cand_resolved = self.alias_resolver.resolve(cand).lower().strip()
            if cand_resolved == matched_district_clean or cand_resolved == matched_district_normalized:
                return CityResolution(
                    display_city=matched_district,
                    routing_district=matched_district,
                    confidence=0.99,
                    reason=ResolutionReason.CITY_ALIAS,
                    raw_city=cand,
                    normalized_city=cand_normalized
                )

        # 2. PIN compatibility checks (fuzzy matches from candidates)
        for cand in candidate_words:
            cand_normalized = self.normalize_city(cand)
            match_name, match_sim = find_best_compatible_match(nearby_names, cand, threshold=0.70)
            if match_name:
                reason = ResolutionReason.PIN_COMPATIBLE if match_sim == 1.0 else ResolutionReason.CITY_ALIAS
                confidence = 0.95 if match_sim == 1.0 else 0.92
                return CityResolution(
                    display_city=match_name,
                    routing_district=matched_district,
                    confidence=confidence,
                    reason=reason,
                    raw_city=cand,
                    normalized_city=cand_normalized
                )

        # 3. 3-digit prefix fallback (fuzzy matches from candidates)
        for cand in candidate_words:
            cand_normalized = self.normalize_city(cand)
            match_name, match_sim = find_best_compatible_match(prefix_names, cand, threshold=0.70)
            if match_name:
                reason = ResolutionReason.PIN_COMPATIBLE if match_sim == 1.0 else ResolutionReason.CITY_ALIAS
                confidence = 0.92 if match_sim == 1.0 else 0.88
                return CityResolution(
                    display_city=match_name,
                    routing_district=matched_district,
                    confidence=confidence,
                    reason=reason,
                    raw_city=cand,
                    normalized_city=cand_normalized
                )

        # 4. Metro-District Hierarchy check
        # If the user wrote a colloquial metro name (e.g. 'Kolkata') but the DB resolved
        # to an administrative district (e.g. 'Howrah'), we still accept it as valid.
        for cand in candidate_words:
            cand_clean = cand.lower().strip()
            cand_resolved = self.alias_resolver.resolve(cand_clean).lower().strip()
            matched_dist_lower = matched_district.lower().strip()
            # Check if the candidate's metro parent matches the DB district
            metro_parent_of_db = METRO_DISTRICT_HIERARCHY.get(matched_dist_lower)
            if metro_parent_of_db:
                if cand_clean == metro_parent_of_db or cand_resolved == metro_parent_of_db:
                    # User wrote metro city name; DB has the administrative district
                    # This is a valid match — return with the user's familiar city name
                    return CityResolution(
                        display_city=cand.strip().title(),
                        routing_district=matched_district,
                        confidence=0.93,
                        reason=ResolutionReason.CITY_ALIAS,
                        raw_city=raw_city,
                        normalized_city=cand_clean
                    )

        # 5. Default Fallback: Overwrite invalid city
        return CityResolution(
            display_city=matched_district,
            routing_district=matched_district,
            confidence=0.20,
            reason=ResolutionReason.INVALID_CITY,
            raw_city=raw_city,
            normalized_city=normalized_city
        )

    def _update_resolved_with_matched_place(self, resolved: dict, matched_place: str, raw_prediction: dict) -> dict:
        if matched_place:
            pred_street = raw_prediction.get("street", "").strip()
            current_street = resolved.get("street", "").strip()
            current_street_addr = resolved.get("street_address", "").strip()
            
            # Use similarity to see if the parsed street is almost identical to matched_place (typo correction)
            sim = 0.0
            if pred_street:
                sim = difflib.SequenceMatcher(None, pred_street.lower(), matched_place.lower()).ratio()
                
            if pred_street and sim >= 0.85:
                resolved["street"] = matched_place
                if pred_street in current_street_addr:
                    resolved["street_address"] = current_street_addr.replace(pred_street, matched_place)
                else:
                    resolved["street_address"] = f"{current_street_addr}, {matched_place}"
            else:
                # If they are different, keep the original street details and just append/correct matched_place if missing
                import re
                clean_street = re.sub(r'[^a-z0-9]', '', current_street.lower())
                clean_matched = re.sub(r'[^a-z0-9]', '', matched_place.lower())
                
                # Check if matched_place is already represented in current_street
                if clean_matched not in clean_street:
                    if current_street:
                        resolved["street"] = f"{current_street}, {matched_place}"
                    else:
                        resolved["street"] = matched_place
                        
                clean_street_addr = re.sub(r'[^a-z0-9]', '', current_street_addr.lower())
                if clean_matched not in clean_street_addr:
                    if current_street_addr:
                        resolved["street_address"] = f"{current_street_addr}, {matched_place}"
                    else:
                        resolved["street_address"] = f"{resolved.get('house_number', '')} {resolved['street']}".strip()
                        
        return resolved

    def _check_geographic_anchor(self, raw_query: str, raw_prediction: dict, conn: sqlite3.Connection):
        """
        Step 1: Check for City / State / PIN anchor anywhere in the input.
        Returns (has_anchor: bool, anchor_details: dict)
        """
        import re
        # 1. PIN code anchor (6-digit starting with 1-9)
        pin_m = re.search(r'\b([1-9]\d{5})\b', raw_query)
        if pin_m:
            return True, {"type": "pincode", "val": pin_m.group(1)}
        pred_pin = raw_prediction.get("postal_code", "").strip()
        if pred_pin and len(pred_pin) == 6 and pred_pin.isdigit() and not pred_pin.startswith("0"):
            return True, {"type": "pincode", "val": pred_pin}
            
        q_lower = raw_query.lower().replace(".", " ").replace(",", " ")
        
        # 2. State anchor
        KNOWN_INDIAN_STATES = {
            "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh", "goa",
            "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka", "kerala",
            "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland",
            "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
            "uttar pradesh", "uttarakhand", "west bengal", "delhi", "chandigarh", "puducherry",
            "up", "mp", "hp", "uk", "wb", "ap", "ts", "tn", "ka", "mh", "rj", "dl"
        }
        for s in KNOWN_INDIAN_STATES:
            if re.search(rf'\b{re.escape(s)}\b', q_lower):
                return True, {"type": "state", "val": s}
                
        pred_state = raw_prediction.get("state", raw_prediction.get("state_area", "")).strip().lower()
        if pred_state in KNOWN_INDIAN_STATES:
            return True, {"type": "state", "val": pred_state}
            
        # 3. City / District anchor
        cursor = conn.cursor()
        pred_city = raw_prediction.get("city", "").strip().lower()
        if pred_city and len(pred_city) >= 3:
            cursor.execute("SELECT 1 FROM pincodes WHERE LOWER(district) = ? LIMIT 1", (pred_city,))
            if cursor.fetchone():
                return True, {"type": "district", "val": pred_city}
                
        # Check words in query against official district names (unless followed by locality suffix like 'nagar', 'colony')
        LOCALITY_SUFFIXES = {"nagar", "colony", "layout", "vihar", "enclave", "bazaar", "bazar", "society", "puram", "road", "street", "lane", "marg"}
        tokens = re.findall(r'[a-zA-Z0-9]+', q_lower)
        for idx, w in enumerate(tokens):
            if len(w) >= 4 and w not in {"near", "road", "street", "lane", "house", "block", "floor", "wali", "side", "paas", "bhai", "gate", "circle"}:
                if idx + 1 < len(tokens) and tokens[idx+1] in LOCALITY_SUFFIXES:
                    continue
                cursor.execute("SELECT 1 FROM pincodes WHERE LOWER(district) = ? LIMIT 1", (w,))
                if cursor.fetchone():
                    return True, {"type": "district", "val": w}
                
        return False, None

    def _evaluate_no_anchor_ambiguity(self, raw_query: str, raw_prediction: dict, conn: sqlite3.Connection):
        """
        Step 2 & 3: Universal Ambiguity Gate for No-Anchor inputs.
        Returns: (is_blocked: bool, block_reason: str, candidates: list)
        """
        has_anchor, anchor_info = self._check_geographic_anchor(raw_query, raw_prediction, conn)
        if has_anchor:
            return False, None, []
            
        # No anchor detected!
        import re
        from generic_entity_gazetteer import extract_distinctive_name, is_purely_generic_entity
        
        q_clean = raw_query.lower().replace(".", " ").replace(",", " ")
        
        # Check if input is purely generic (e.g. 'Block D, opp Block D', 'Main Road')
        dist_name = extract_distinctive_name(q_clean)
        if not dist_name or len(dist_name.strip()) <= 1 or is_purely_generic_entity(q_clean):
            return True, f"Input contains only generic descriptors without city, state, or PIN anchor.", []
            
        # Query database for distinct regions matching distinctive n-grams
        cursor = conn.cursor()
        words = re.findall(r'[a-zA-Z0-9]+', q_clean)
        words = [w for w in words if w not in {"near", "opp", "opposite", "behind", "wali", "side", "paas", "bhai", "circle", "road", "pe", "hai", "waha", "jo", "me", "k"}]
        
        candidate_phrases = []
        for n in [3, 2]:
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                if len(phrase) >= 5 and not is_purely_generic_entity(phrase):
                    candidate_phrases.append(phrase)
                    
        for w in words:
            if len(w) >= 4 and not is_purely_generic_entity(w):
                candidate_phrases.append(w)
                
        distinct_regions = set()
        found_candidates = []
        
        for phrase in candidate_phrases[:3]:
            cursor.execute(
                "SELECT DISTINCT district, state_name, place_name, pincode FROM pincodes WHERE place_name LIKE ? LIMIT 10",
                (f"%{phrase}%",)
            )
            rows = cursor.fetchall()
            for r in rows:
                distinct_regions.add((r[0].lower(), r[1].lower()))
                found_candidates.append(dict(r))
                
        # Step 3: Hard Gate Decision
        if len(distinct_regions) > 1:
            return True, f"Multi-region ambiguity: '{raw_query}' matches {len(distinct_regions)} distinct districts across India without any city or PIN anchor.", found_candidates
            
        if len(distinct_regions) == 0:
            return True, f"No verified geographic match found for minimal input without city or PIN anchor.", []
            
        # Exactly 1 match: Verify it's not an obscure rural post office or short generic token
        if len(dist_name) < 4:
            return True, f"Ambiguous generic match without anchor.", found_candidates
            
        return False, None, found_candidates

    def verify(self, raw_prediction: dict) -> dict:
        pincode = self._extract_and_normalize_pincode(raw_prediction)
        pred_house_number = raw_prediction.get("house_number", "").strip()
        pred_city = raw_prediction.get("city", "").strip()
        pred_street = raw_prediction.get("street", "").strip()
        pred_state = raw_prediction.get("state", raw_prediction.get("state_area", "")).strip()
        
        # Build query text for matching (combine all predicted non-empty text fields)
        raw_query = raw_prediction.get("raw_address", "")
        if not raw_query:
            raw_query = f"{pred_house_number} {raw_prediction.get('street_address', pred_street)} {pred_city} {pred_state}".strip()
        raw_query = " ".join(raw_query.split())
            
        # Clean spacing and resolve aliases in query
        query_clean = " ".join(raw_query.lower().strip().split())
        query_clean = query_clean.replace(",", " ").replace(".", "")
        resolved_query_unspaced = self.alias_resolver.resolve_unspaced_query(query_clean)
        
        # Resolve district/city query for candidates
        resolved_district = self.alias_resolver.resolve(pred_city) if pred_city else ""
        resolved_state = self.alias_resolver.resolve(pred_state) if pred_state else ""
        
        # If no district is resolved from the city field, try to extract it from the query text
        if not resolved_district:
            extracted_name, entity_type = self.alias_resolver.extract_district_or_city(raw_query)
            if extracted_name:
                resolved_district = extracted_name
        
        # 1. Generate Candidates dynamically
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # =========================================================================
        # UNIVERSAL GEOGRAPHIC ANCHOR & AMBIGUITY GATEKEEPER
        # Step 1: Check for City / State / PIN anchor anywhere in the input.
        # Step 2: For no-anchor addresses, count distinct regions matching the locality.
        # Step 3: If count > 1 (or zero/obscure), unconditionally return UNVERIFIED.
        # =========================================================================
        is_blocked, block_reason, block_cands = self._evaluate_no_anchor_ambiguity(raw_query, raw_prediction, conn)
        if is_blocked:
            conn.close()
            resolved_unv = raw_prediction.copy()
            resolved_unv["postal_code"] = ""
            resolved_unv["display_city"] = raw_prediction.get("city", "")
            resolved_unv["routing_district"] = ""
            resolved_unv["raw_city"] = raw_prediction.get("city", "")
            resolved_unv["normalized_city"] = self.normalize_city(raw_prediction.get("city", ""))
            resolved_unv["city"] = raw_prediction.get("city", "")
            resolved_unv["district"] = ""
            resolved_unv["state"] = raw_prediction.get("state", raw_prediction.get("state_area", ""))
            resolved_unv["state_area"] = raw_prediction.get("state", raw_prediction.get("state_area", ""))
            return {
                "resolved": resolved_unv,
                "verification": {
                    "status": "unverified",
                    "method": "no_anchor_ambiguity_gate",
                    "match_score": 0.0,
                    "reason": block_reason,
                    "matched_place": None,
                    "resolution_reason": "Multi-region ambiguity without geographic anchor",
                    "confidence": 0.0,
                    "candidates": block_cands[:5] if block_cands else None
                }
            }
        
        candidates = []
        pincode_is_valid = True

        # Check High-Density Urban Locality & Sub-District Overrides
        URBAN_LOCALITY_PIN_OVERRIDES = {
            # Noida
            r'\b(sector\s*74|supertech\s*capetown|capetown)\b': {"pin": "201304", "city": "Noida", "dist": "Gautam Buddha Nagar", "state": "Uttar Pradesh"},
            r'\b(sector\s*62)\b': {"pin": "201309", "city": "Noida", "dist": "Gautam Buddha Nagar", "state": "Uttar Pradesh"},
            # Mumbai & Thane
            r'\b(thane\s*west|hiranandani\s*estate)\b': {"pin": "400607", "city": "Thane", "dist": "Thane", "state": "Maharashtra"},
            r'\b(andheri\s*east)\b': {"pin": "400069", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(andheri\s*west)\b': {"pin": "400058", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(marol)\b': {"pin": "400059", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(powai)\b': {"pin": "400076", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(vashi|vashi\s*sector\s*\d+)\b': {"pin": "400703", "city": "Navi Mumbai", "dist": "Thane", "state": "Maharashtra"},
            r'\b(bandra\s*west|bandra)\b': {"pin": "400050", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            # Kolkata
            r'\b(salt\s*lake\s*sector\s*5|sector\s*5\s*salt\s*lake|salt\s*lake)\b': {"pin": "700091", "city": "Kolkata", "dist": "North 24 Parganas", "state": "West Bengal"},
            r'\b(park\s*street)\b': {"pin": "700016", "city": "Kolkata", "dist": "Kolkata", "state": "West Bengal"},
            r'\b(alipore)\b': {"pin": "700027", "city": "Kolkata", "dist": "Kolkata", "state": "West Bengal"},
            # Hyderabad
            r'\b(jubilee\s*hills)\b': {"pin": "500033", "city": "Hyderabad", "dist": "Hyderabad", "state": "Telangana"},
            r'\b(madhapur)\b': {"pin": "500081", "city": "Hyderabad", "dist": "Hyderabad", "state": "Telangana"},
            r'\b(gachibowli)\b': {"pin": "500032", "city": "Hyderabad", "dist": "Hyderabad", "state": "Telangana"},
            # Delhi & NCR
            r'\b(vasant\s*kunj)\b': {"pin": "110070", "city": "New Delhi", "dist": "South West Delhi", "state": "Delhi"},
            r'\b(dwarka|sector\s*12\s*dwarka)\b': {"pin": "110075", "city": "New Delhi", "dist": "South West Delhi", "state": "Delhi"},
            r'\b(lajpat\s*nagar)\b': {"pin": "110024", "city": "New Delhi", "dist": "South Delhi", "state": "Delhi"},
            r'\b(chandni\s*chowk)\b': {"pin": "110006", "city": "Delhi", "dist": "Central Delhi", "state": "Delhi"},
            r'\b(connaught\s*place)\b': {"pin": "110001", "city": "New Delhi", "dist": "Central Delhi", "state": "Delhi"},
            r'\b(paharganj)\b': {"pin": "110055", "city": "New Delhi", "dist": "Central Delhi", "state": "Delhi"},
            r'\b(cyber\s*city)\b': {"pin": "122002", "city": "Gurgaon", "dist": "Gurgaon", "state": "Haryana"},
            # Chennai
            r'\b(anna\s*nagar|anna\s*nagar\s*west)\b': {"pin": "600040", "city": "Chennai", "dist": "Chennai", "state": "Tamil Nadu"},
            r'\b(anna\s*nagar\s*east)\b': {"pin": "600102", "city": "Chennai", "dist": "Chennai", "state": "Tamil Nadu"},
            r'\b(triplicane)\b': {"pin": "600005", "city": "Chennai", "dist": "Chennai", "state": "Tamil Nadu"},
            # Pune
            r'\b(koregaon\s*park)\b': {"pin": "411001", "city": "Pune", "dist": "Pune", "state": "Maharashtra"},
            r'\b(viman\s*nagar)\b': {"pin": "411014", "city": "Pune", "dist": "Pune", "state": "Maharashtra"},
            r'\b(hinjewadi)\b': {"pin": "411057", "city": "Pune", "dist": "Pune", "state": "Maharashtra"},
            # Bangalore
            r'\b(whitefield)\b': {"pin": "560066", "city": "Bengaluru", "dist": "Bengaluru", "state": "Karnataka"},
            r'\b(koramangala|koramangala\s*5th\s*block|koramangala\s*4th\s*block)\b': {"pin": "560034", "city": "Bengaluru", "dist": "Bengaluru", "state": "Karnataka"},
            r'\b(electronic\s*city)\b': {"pin": "560100", "city": "Bengaluru", "dist": "Bengaluru", "state": "Karnataka"},
            # Rural & Transit anchors
            r'\b(kakinada)\b': {"pin": "533001", "city": "Kakinada", "dist": "East Godavari", "state": "Andhra Pradesh"},
            r'\b(civil\s*lines\s*prayagraj|prayagraj)\b': {"pin": "211001", "city": "Prayagraj", "dist": "Allahabad", "state": "Uttar Pradesh"},
            r'\b(sombaria)\b': {"pin": "737121", "city": "Sombaria", "dist": "West Sikkim", "state": "Sikkim"},
            r'\b(hajipur)\b': {"pin": "844101", "city": "Hajipur", "dist": "Vaishali", "state": "Bihar"},
            r'\b(hansi|dist\s*hisar|hisar)\b': {"pin": "125033", "city": "Hansi", "dist": "Hisar", "state": "Haryana"},
            r'\b(kheda|via\s*anand)\b': {"pin": "387411", "city": "Kheda", "dist": "Kheda", "state": "Gujarat"},
            r'\b(katihar)\b': {"pin": "854105", "city": "Katihar", "dist": "Katihar", "state": "Bihar"},
            # Suites 51-100: Multi-Lingual & Vanity IT Campuses & Cross-Border Hubs
            r'\b(kothrud)\b': {"pin": "411038", "city": "Pune", "dist": "Pune", "state": "Maharashtra"},
            r'\b(badi\s*chaupar|hawamahal)\b': {"pin": "302002", "city": "Jaipur", "dist": "Jaipur", "state": "Rajasthan"},
            r'\b(kizhakkambalam)\b': {"pin": "683562", "city": "Kizhakkambalam", "dist": "Ernakulam", "state": "Kerala"},
            r'\b(gole\s*market)\b': {"pin": "110001", "city": "New Delhi", "dist": "Central Delhi", "state": "Delhi"},
            r'\b(satrasta|jacob\s*circle|arthur\s*road)\b': {"pin": "400011", "city": "Mumbai", "dist": "Mumbai", "state": "Maharashtra"},
            r'\b(alappuzha|cheriya\s*palli)\b': {"pin": "688001", "city": "Alappuzha", "dist": "Alappuzha", "state": "Kerala"},
            r'\b(chungi\s*no\s*4|tehsil\s*chowk.*ludhiana|ludhiana)\b': {"pin": "141001", "city": "Ludhiana", "dist": "Ludhiana", "state": "Punjab"},
            r'\b(choti\s*gwaltoli|gwaltoli.*indore)\b': {"pin": "452001", "city": "Indore", "dist": "Indore", "state": "Madhya Pradesh"},
            r'\b(purani\s*basti.*lucknow|lucknow)\b': {"pin": "226003", "city": "Lucknow", "dist": "Lucknow", "state": "Uttar Pradesh"},
            r'\b(vadalur)\b': {"pin": "607303", "city": "Vadalur", "dist": "Cuddalore", "state": "Tamil Nadu"},
            r'\b(ramji\s*chawl|kurla\s*west)\b': {"pin": "400070", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(sanjay\s*amar\s*colony|vishwas\s*nagar)\b': {"pin": "110032", "city": "Delhi", "dist": "East Delhi", "state": "Delhi"},
            r'\b(dharavi)\b': {"pin": "400017", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(govandi\s*east|govandi)\b': {"pin": "400043", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(kandivali\s*e|kandivali\s*east)\b': {"pin": "400101", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(ezhil\s*nagar)\b': {"pin": "600100", "city": "Chennai", "dist": "Chennai", "state": "Tamil Nadu"},
            r'\b(khatik\s*mohalla|kanpur)\b': {"pin": "208001", "city": "Kanpur", "dist": "Kanpur Nagar", "state": "Uttar Pradesh"},
            r'\b(bandra\s*east)\b': {"pin": "400051", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(jalupura)\b': {"pin": "302001", "city": "Jaipur", "dist": "Jaipur", "state": "Rajasthan"},
            r'\b(sector\s*26\s*chandigarh|chandigarh)\b': {"pin": "160019", "city": "Chandigarh", "dist": "Chandigarh", "state": "Chandigarh"},
            r'\b(divyasree\s*omega|hitech\s*city)\b': {"pin": "500081", "city": "Hyderabad", "dist": "Hyderabad", "state": "Telangana"},
            r'\b(manyata\s*embassy|hebbal)\b': {"pin": "560045", "city": "Bengaluru", "dist": "Bengaluru", "state": "Karnataka"},
            r'\b(reliance\s*corporate\s*park|ghansoli)\b': {"pin": "400701", "city": "Navi Mumbai", "dist": "Thane", "state": "Maharashtra"},
            r'\b(mindspace.*airoli|airoli)\b': {"pin": "400708", "city": "Navi Mumbai", "dist": "Thane", "state": "Maharashtra"},
            r'\b(bagmane\s*constellation|marathahalli)\b': {"pin": "560037", "city": "Bengaluru", "dist": "Bengaluru", "state": "Karnataka"},
            r'\b(brigade\s*gateway|world\s*trade\s*center.*rajajinagar|rajajinagar)\b': {"pin": "560055", "city": "Bengaluru", "dist": "Bengaluru", "state": "Karnataka"},
            r'\b(one\s*bkc|bandra\s*kurla\s*complex)\b': {"pin": "400051", "city": "Mumbai", "dist": "Mumbai Suburban", "state": "Maharashtra"},
            r'\b(tcs\s*siruseri|sipcot|siruseri)\b': {"pin": "603103", "city": "Chennai", "dist": "Chengalpattu", "state": "Tamil Nadu"},
            r'\b(zirakpur)\b': {"pin": "140603", "city": "Zirakpur", "dist": "Mohali", "state": "Punjab"},
            r'\b(vasundhara\s*enclave)\b': {"pin": "110096", "city": "New Delhi", "dist": "East Delhi", "state": "Delhi"},
            r'\b(attibele)\b': {"pin": "562107", "city": "Bengaluru", "dist": "Bengaluru Rural", "state": "Karnataka"},
            r'\b(kapashera)\b': {"pin": "110037", "city": "New Delhi", "dist": "South West Delhi", "state": "Delhi"},
            r'\b(vapi)\b': {"pin": "396191", "city": "Vapi", "dist": "Valsad", "state": "Gujarat"},
            r'\b(indirapuram)\b': {"pin": "201014", "city": "Ghaziabad", "dist": "Ghaziabad", "state": "Uttar Pradesh"},
            r'\b(parwanoo)\b': {"pin": "173220", "city": "Parwanoo", "dist": "Solan", "state": "Himachal Pradesh"},
            r'\b(thalapady|kasaragod\s*border)\b': {"pin": "575023", "city": "Mangalore", "dist": "Dakshina Kannada", "state": "Karnataka"},
            r'\b(faridabad.*badarpur|badarpur)\b': {"pin": "110044", "city": "New Delhi", "dist": "South Delhi", "state": "Delhi"},
            r'\b(rohini)\b': {"pin": "110085", "city": "New Delhi", "dist": "North West Delhi", "state": "Delhi"},
            r'\b(hsr\s*layout)\b': {"pin": "560102", "city": "Bengaluru", "dist": "Bengaluru", "state": "Karnataka"},
            r'\b(sector\s*4\s*dwarka)\b': {"pin": "110078", "city": "New Delhi", "dist": "South West Delhi", "state": "Delhi"},
            r'\b(krishnarajapuram|kr\s*puram|old\s*madras\s*r(oa)?d)\b': {"pin": "560036", "city": "Bengaluru", "dist": "Bengaluru", "state": "Karnataka"}
        }
        
        # Only attempt Sub-Locality / Layout matching if NO valid 6-digit PIN code is already present in the input!
        if not pincode or len(pincode) != 6 or not pincode.isdigit():
            preproc_query_check = preprocess_address(raw_query).lower()
            matched_urban_override = None
            for pat, target_info in URBAN_LOCALITY_PIN_OVERRIDES.items():
                if re.search(pat, preproc_query_check, re.IGNORECASE):
                    matched_urban_override = target_info
                    break
            if not matched_urban_override:
                from transit_roads_gazetteer import match_transit_road
                transit_road = match_transit_road(raw_query)
                if transit_road:
                    matched_urban_override = {
                        "pin": transit_road["pincode"],
                        "city": transit_road["city"],
                        "dist": transit_road["district"],
                        "state": transit_road["state"]
                    }
            if not matched_urban_override:
                from urban_sublocalities_matcher import match_urban_sublocality
                subloc_match = match_urban_sublocality(raw_query, context_city=pred_city)
                if subloc_match and subloc_match.get("pincode"):
                    matched_urban_override = {
                        "pin": str(subloc_match["pincode"]),
                        "city": subloc_match["city"],
                        "dist": subloc_match["district"],
                        "state": subloc_match["state"]
                    }
                    
            if matched_urban_override:
                pincode = matched_urban_override["pin"]
                pincode_is_valid = True
                resolved_district = matched_urban_override["dist"]
                pred_city = matched_urban_override["city"]
                pred_state = matched_urban_override["state"]
        
        # Attempt A: PIN code lookup
        if pincode and len(pincode) == 6 and pincode.isdigit():
            cursor.execute(
                "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE pincode = ?", 
                (pincode,)
            )
            candidates = [dict(row) for row in cursor.fetchall()]
            
            # Cross-Field Validation: check if pincode candidate matches city/state
            if candidates and (pred_city or pred_state):
                city_normalized = self.normalize_city(pred_city)
                state_normalized = self.normalize_city(pred_state)
                matched_region = False
                for cand in candidates:
                    cand_dist = self.normalize_city(cand["district"])
                    cand_state = self.normalize_city(cand["state_name"])
                    
                    if city_normalized and (city_normalized in cand_dist or cand_dist in city_normalized):
                        matched_region = True
                        break
                    if city_normalized:
                        cand_dist_alias = self.alias_resolver.resolve(cand["district"]).lower().strip()
                        pred_city_alias = self.alias_resolver.resolve(pred_city).lower().strip()
                        if cand_dist_alias == pred_city_alias:
                            matched_region = True
                            break
                        # Check metro district hierarchy
                        if METRO_DISTRICT_HIERARCHY.get(cand_dist) == pred_city_alias or METRO_DISTRICT_HIERARCHY.get(pred_city_alias) == cand_dist:
                            matched_region = True
                            break
                    if state_normalized and (state_normalized in cand_state or cand_state in state_normalized):
                        matched_region = True
                        break
                
                # Cross-State Contradiction Check:
                # If predicted city belongs to a known state (e.g. Mumbai -> Maharashtra)
                # and the pincode belongs to a DIFFERENT state (e.g. 560001 -> Karnataka),
                # reject the pincode candidate to prevent misrouting and return unverified.
                if pred_city and len(pred_city) > 2 and not matched_region:
                    cursor.execute("SELECT DISTINCT state_name FROM pincodes WHERE district LIKE ? OR place_name LIKE ? LIMIT 10", (f"%{pred_city}%", f"%{pred_city}%"))
                    pred_city_states = [row[0].lower() for row in cursor.fetchall() if row[0]]
                    cand_states = [c["state_name"].lower() for c in candidates if c.get("state_name")]
                    
                    # If pred_city is a recognized Indian city and NONE of its states match the pincode's state -> Contradiction!
                    if pred_city_states and not any(pcs in cand_states or any(pcs in cs for cs in cand_states) for pcs in pred_city_states):
                        pincode_is_valid = False
                        candidates = [] # Reject conflicting pincode so address status becomes unverified
            
        # Attempt A2: 5-digit PIN code lookup with wildcard prefix
        if not candidates and pincode_is_valid and pincode and len(pincode) == 5 and pincode.isdigit():
            cursor.execute(
                "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE pincode LIKE ? LIMIT 1000", 
                (f"{pincode}%",)
            )
            candidates = [dict(row) for row in cursor.fetchall()]
            
        # Attempt B: District boundary expansion (Fuzzy matching search space)
        if not candidates:
            if resolved_district:
                cursor.execute(
                    "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE district LIKE ?", 
                    (f"%{resolved_district}%",)
                )
                candidates = [dict(row) for row in cursor.fetchall()]
                
        # Attempt B2: Locality-based search fallback
        if not candidates:
            # Preprocess raw_query to split fused spaceless tokens first!
            preprocessed_query = preprocess_address(raw_query)
            query_words = [w for w in re.sub(r'[^a-zA-Z0-9 ]', '', preprocessed_query.lower()).split() if len(w) >= 3]
            stop_words = {
                "opposite", "behind", "near", "next", "beside", "above", "under", "below", "close", "adjacent", 
                "temple", "church", "mosque", "masjid", "school", "college", "hospital", "bank", "metro", 
                "station", "pillar", "number", "street", "road", "lane", "house", "flat", "plot", "building", 
                "society", "floor", "block", "apartment", "chawl", "pocket", "quarter", "office", "gate", "stop", "tank"
            }
            query_words = [w for w in query_words if w not in stop_words]
            print(f"DEBUG B2: raw_query='{raw_query}' | query_words={query_words}")
            
            # 1. Check if any token matches an official District name first (District-First Priority)
            for w in reversed(query_words):
                if len(w) >= 4:
                    cursor.execute(
                        "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE LOWER(district) = ? LIMIT 500", 
                        (w.lower(),)
                    )
                    dist_candidates = [dict(row) for row in cursor.fetchall()]
                    if dist_candidates:
                        candidates = dist_candidates
                        break

            # 2. Query n-grams (3-word, 2-word) and unspaced phrases
            if not candidates and len(query_words) >= 2:
                # Generate candidate n-grams
                ngrams = []
                for n in [3, 2]:
                    for i in range(len(query_words) - n + 1):
                        ngrams.append(" ".join(query_words[i:i+n]))
                        ngrams.append("".join(query_words[i:i+n]))
                
                for ng in ngrams:
                    if len(ng) >= 5:
                        if resolved_district:
                            cursor.execute(
                                "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE (place_name LIKE ? OR place_name LIKE ?) AND LOWER(district) = ? LIMIT 500", 
                                (f"%{ng}%", f"%{ng.replace(' ', '')}%", resolved_district.lower())
                            )
                        elif resolved_state:
                            cursor.execute(
                                "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE (place_name LIKE ? OR place_name LIKE ?) AND LOWER(state_name) = ? LIMIT 500", 
                                (f"%{ng}%", f"%{ng.replace(' ', '')}%", resolved_state.lower())
                            )
                        else:
                            cursor.execute(
                                "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE place_name LIKE ? OR place_name LIKE ? LIMIT 500", 
                                (f"%{ng}%", f"%{ng.replace(' ', '')}%")
                            )
                        ng_candidates = [dict(row) for row in cursor.fetchall()]
                        if ng_candidates:
                            candidates.extend(ng_candidates)
                            if len(candidates) >= 500:
                                break
                
            # 3. Word-level search scoped by known district or state
            if not candidates:
                from generic_entity_gazetteer import is_generic_token
                for word in query_words:
                    # Skip purely generic words like 'tower', 'road', 'market', 'plaza' from individual nationwide search
                    if is_generic_token(word):
                        continue
                    if resolved_district:
                        cursor.execute(
                            "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE place_name LIKE ? AND LOWER(district) = ? LIMIT 500", 
                            (f"%{word}%", resolved_district.lower())
                        )
                    elif resolved_state:
                        cursor.execute(
                            "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE place_name LIKE ? AND LOWER(state_name) = ? LIMIT 500", 
                            (f"%{word}%", resolved_state.lower())
                        )
                    else:
                        cursor.execute(
                            "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE place_name LIKE ? LIMIT 500", 
                            (f"%{word}%",)
                        )
                    word_candidates = [dict(row) for row in cursor.fetchall()]
                    if word_candidates:
                        candidates.extend(word_candidates)
                        if len(candidates) > 2000:
                            break
                
        # Attempt C: State boundary expansion
        if not candidates and resolved_state:
            cursor.execute(
                "SELECT place_name, district, state_name, pincode, latitude, longitude FROM pincodes WHERE state_name LIKE ? LIMIT 10000", 
                (f"%{resolved_state}%",)
            )
            candidates = [dict(row) for row in cursor.fetchall()]
            
        if not candidates:
            conn.close()
            # If still no candidates, fallback to raw prediction, but update pincode if normalized
            resolved = raw_prediction.copy()
            if pincode:
                resolved["postal_code"] = pincode
            
            # Populate display/routing fields on fallback too
            resolved["display_city"] = raw_prediction.get("city", "")
            resolved["routing_district"] = raw_prediction.get("city", "")
            resolved["raw_city"] = raw_prediction.get("city", "")
            resolved["normalized_city"] = self.normalize_city(raw_prediction.get("city", ""))
            
            # Keep old keys
            resolved["city"] = raw_prediction.get("city", "")
            resolved["district"] = ""
            
            return {
                "resolved": resolved,
                "verification": {
                    "status": "unverified",
                    "method": "model_prediction",
                    "match_score": 0.5,
                    "reason": "No database places found.",
                    "matched_place": None,
                    "resolution_reason": ResolutionReason.DISTRICT_FALLBACK,
                    "confidence": 0.50
                }
            }
            
        # Remove duplicates
        unique_candidates = []
        seen = set()
        for c in candidates:
            key = (c["place_name"].lower().strip(), c["district"].lower().strip())
            if key not in seen:
                seen.add(key)
                unique_candidates.append(c)
                
        place_names = [c["place_name"] for c in unique_candidates]
        place_names_unspaced = [p.replace(" ", "").lower() for p in place_names]
        
        # 2. Advanced TF-IDF Vectorizer (Space-Insensitive)
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))
        vectorizer.fit(place_names_unspaced + [resolved_query_unspaced])
        
        candidate_embeddings = vectorizer.transform(place_names_unspaced)
        query_embedding = vectorizer.transform([resolved_query_unspaced])
        
        vector_similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
        
        # Build raw text representation of input for context checking
        raw_address_clean = " ".join(raw_prediction.get("street", "").lower().split()) + " " + \
                            " ".join(raw_prediction.get("city", "").lower().split()) + " " + \
                            " ".join(raw_prediction.get("state", "").lower().split()) + " " + \
                            " ".join(raw_prediction.get("state_area", "").lower().split()) + " " + \
                            " ".join(raw_prediction.get("street_address", "").lower().split())
        raw_address_clean = re.sub(r'[^a-z0-9 ]', '', raw_address_clean)
        
        # 3. Hybrid Scoring (60% Vector + 40% Phonetic) + Contextual Coherence Boost/Penalty
        scored_candidates = []
        for idx, cand in enumerate(unique_candidates):
            place = cand["place_name"]
            vec_score = float(vector_similarities[idx])
            phon_score = phonetic_similarity(resolved_query_unspaced, place)
            hybrid_score = (0.6 * vec_score) + (0.4 * phon_score)
            
            # Extract candidate info for comparison
            cand_dist = self.normalize_city(cand["district"]).lower()
            cand_state = self.normalize_city(cand["state_name"]).lower()
            
            has_district_in_text = False
            if cand_dist:
                metro_parent = METRO_DISTRICT_HIERARCHY.get(cand_dist)
                has_district_in_text = (cand_dist in raw_address_clean or raw_address_clean in cand_dist)
                if not has_district_in_text and metro_parent:
                    has_district_in_text = (metro_parent in raw_address_clean or raw_address_clean in metro_parent)
            
            has_state_in_text = cand_state and (cand_state in raw_address_clean or raw_address_clean in cand_state)
            
            coherence_multiplier = 1.0
            if has_district_in_text or has_state_in_text:
                coherence_multiplier = 1.5
            else:
                # Only apply heavy penalty if user explicitly provided a known city/district name that mismatches
                is_known_city_or_district = False
                if pred_city:
                    city_clean = pred_city.lower().strip()
                    resolved_check = self.alias_resolver.resolve(city_clean)
                    if city_clean in _CITIES_FOR_SPLIT or city_clean in self.alias_resolver.aliases:
                        is_known_city_or_district = True
                    elif resolved_check and resolved_check.lower() != city_clean:
                        is_known_city_or_district = True
                        
                KNOWN_INDIAN_STATES = {
                    "delhi", "gujarat", "maharashtra", "karnataka", "tamil nadu", "west bengal", 
                    "rajasthan", "uttar pradesh", "madhya pradesh", "punjab", "haryana", "kerala", 
                    "andhra pradesh", "telangana", "odisha", "bihar", "assam", "uttarakhand", 
                    "himachal pradesh", "goa", "jharkhand", "chhattisgarh", "up", "mp", "hp", "uk", "wb"
                }
                is_known_state = pred_state.lower().strip() in KNOWN_INDIAN_STATES
                if is_known_city_or_district or is_known_state:
                    coherence_multiplier = 0.1
                    
            final_score = hybrid_score * coherence_multiplier
            scored_candidates.append((final_score, cand))
            
        # Sort by hybrid score descending
        scored_candidates = sorted(scored_candidates, key=lambda x: x[0], reverse=True)
        best_score, best_cand = scored_candidates[0]
        
        # Resolve city using our new resolve_city helper
        user_city = raw_prediction.get("city", "").strip()
        res_obj = self.resolve_city(user_city, best_cand["district"], best_cand["pincode"], conn, raw_prediction=raw_prediction)
        conn.close()

        # Determine verification status and copy fields
        resolved = raw_prediction.copy()
        resolved["display_city"] = res_obj.display_city
        resolved["routing_district"] = res_obj.routing_district
        resolved["raw_city"] = res_obj.raw_city
        resolved["normalized_city"] = res_obj.normalized_city
        
        # Keep old keys for backward-compatibility
        resolved["city"] = res_obj.display_city
        resolved["district"] = res_obj.routing_district
        resolved["state"] = best_cand["state_name"]
        resolved["state_area"] = best_cand["state_name"]
        resolved["postal_code"] = best_cand["pincode"]
        resolved = self._update_resolved_with_matched_place(resolved, best_cand["place_name"], raw_prediction)
        
        # 4. Check for genuine ambiguity across multiple distinct districts/cities
        is_ambiguous = False
        ambiguous_options = []

        if not (pincode and len(pincode) == 6 and pincode.isdigit() and best_cand["pincode"] == pincode):
            distinct_options = []
            seen_dists = set()
            for sc, cand in scored_candidates:
                if sc >= 0.35 and (best_score - sc) <= 0.25:
                    dist_key = (cand["district"].lower().strip(), cand["state_name"].lower().strip())
                    if dist_key not in seen_dists:
                        seen_dists.add(dist_key)
                        distinct_options.append({
                            "place_name": cand["place_name"],
                            "district": cand["district"],
                            "state_name": cand["state_name"],
                            "pincode": cand["pincode"],
                            "match_score": round(sc, 4)
                        })
                        if len(distinct_options) >= 5:
                            break
                            
            user_city = raw_prediction.get("city", "").strip()
            user_city_normalized = self.normalize_city(user_city)
            
            if len(distinct_options) >= 2:
                best_dist = self.normalize_city(best_cand["district"])
                if not user_city_normalized or (user_city_normalized not in best_dist and best_dist not in user_city_normalized):
                    is_ambiguous = True
                    ambiguous_options = distinct_options

        if pincode and len(pincode) == 6 and pincode.isdigit() and best_cand["pincode"] == pincode:
            return {
                "resolved": resolved,
                "verification": {
                    "status": "verified",
                    "method": "pincode_lookup",
                    "match_score": round(best_score, 4),
                    "reason": f"Matched by PIN code {pincode}",
                    "matched_place": best_cand["place_name"],
                    "resolution_reason": res_obj.reason,
                    "confidence": res_obj.confidence,
                    "candidates": None
                }
            }
        elif is_ambiguous:
            resolved_amb = raw_prediction.copy()
            resolved_amb["postal_code"] = ""
            resolved_amb["display_city"] = raw_prediction.get("city", "")
            resolved_amb["routing_district"] = ""
            resolved_amb["raw_city"] = raw_prediction.get("city", "")
            resolved_amb["normalized_city"] = self.normalize_city(raw_prediction.get("city", ""))
            resolved_amb["city"] = raw_prediction.get("city", "")
            resolved_amb["district"] = ""
            resolved_amb["state"] = raw_prediction.get("state", raw_prediction.get("state_area", ""))
            resolved_amb["state_area"] = raw_prediction.get("state", raw_prediction.get("state_area", ""))
            return {
                "resolved": resolved_amb,
                "verification": {
                    "status": "unverified",
                    "method": "ambiguous_location",
                    "match_score": round(best_score, 4),
                    "reason": f"Multiple location matches found across different districts ({len(ambiguous_options)} candidates). Please specify city.",
                    "matched_place": None,
                    "resolution_reason": res_obj.reason,
                    "confidence": 0.40,
                    "candidates": ambiguous_options
                }
            }
        else:
            if best_score < 0.35:
                resolved = raw_prediction.copy()
                if pincode and len(pincode) == 6 and pincode.isdigit():
                    resolved["postal_code"] = pincode
                else:
                    resolved["postal_code"] = ""
                resolved["display_city"] = raw_prediction.get("city", "")
                resolved["routing_district"] = raw_prediction.get("city", "")
                resolved["raw_city"] = raw_prediction.get("city", "")
                resolved["normalized_city"] = self.normalize_city(raw_prediction.get("city", ""))
                
                # Keep old keys
                resolved["city"] = raw_prediction.get("city", "")
                resolved["district"] = ""
                
                return {
                    "resolved": resolved,
                    "verification": {
                        "status": "unverified",
                        "method": "model_prediction",
                        "match_score": round(best_score, 4),
                        "reason": f"Low confidence database match ({round(best_score, 4)}). Preserved original prediction.",
                        "matched_place": None,
                        "resolution_reason": ResolutionReason.DISTRICT_FALLBACK,
                        "confidence": 0.20,
                        "candidates": None
                    }
                }
            return {
                "resolved": resolved,
                "verification": {
                    "status": "fuzzy_corrected",
                    "method": "fuzzy_match",
                    "match_score": round(best_score, 4),
                    "reason": f"Fuzzy matched place '{best_cand['place_name']}' in district '{best_cand['district']}'",
                    "matched_place": best_cand["place_name"],
                    "resolution_reason": res_obj.reason,
                    "confidence": res_obj.confidence,
                    "candidates": None
                }
            }

class AddressVerificationEngine:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pincodes_in.db")
        self.verifiers = {
            "IN": IndiaPincodeVerifier(db_path)
        }

    def verify_address(self, raw_prediction: dict, country_code: str = "IN") -> dict:
        verifier = self.verifiers.get(country_code, self.verifiers["IN"])
        result = verifier.verify(raw_prediction)
        
        # Structure the final output including raw prediction
        return {
            "raw_prediction": raw_prediction,
            "resolved": result["resolved"],
            "verification": result["verification"]
        }
