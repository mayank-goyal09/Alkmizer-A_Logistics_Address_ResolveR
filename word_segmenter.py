import os
import re

class WordSegmenter:
    def __init__(self, vocab_path=None):
        if vocab_path is None:
            vocab_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "address_vocabulary.txt")
            
        self.words = set()
        if os.path.exists(vocab_path):
            with open(vocab_path, "r", encoding="utf-8") as f:
                for line in f:
                    self.words.add(line.strip().lower())
                    
        # Programmatically inject common address & regional administrative terms to ensure correct segmentation
        common_address_terms = {
            "flat", "plot", "room", "house", "shop", "quarter", "chawl", "makan", "bungalow", "villa", "apartment", 
            "apartments", "society", "colony", "towers", "tower", "residency", "enclave", "block", "wing", "floor", 
            "gate", "station", "market", "plaza", "building", "palace", "road", "street", "lane", "cross", "main", 
            "bypass", "highway", "path", "near", "opposite", "behind", "opp", "bhd", "beside", "nr", "next", "facing", 
            "sector", "phase", "zone", "area", "layout", "nagari", "nagar", "vihar", "penta", "puram", "gali", 
            "delhi", "newdelhi", "mumbai", "bombay", "kolkata", "calcutta", "chennai", "madras", "bengaluru", 
            "bangalore", "hyderabad", "secunderabad", "pune", "poona", "noida", "gurugram", "gurgaon", "ghaziabad", 
            "faridabad", "lucknow", "patna", "jaipur", "ahmedabad", "surat", "nagpur", "indore", "bhopal", 
            "chandigarh", "kochi", "cochin", "visakhapatnam", "vizag", "vadodara", "baroda", "coimbatore", "amritsar", 
            "ludhiana", "agra", "varanasi", "rajkot", "jodhpur", "raipur", "ranchi", "guwahati", "bhubaneswar", 
            "madurai", "dehradun", "shimla", "mysuru", "mysore", "nashik", "north", "south", "east", "west", 
            "central", "extension", "no", "number", "block", "sector", "gali", "landmark", "complex", "ward", 
            "district", "state", "pincode", "hno", "door", "floor", "avenue", "park", "gardens", "garden", "plaza",
            "view", "heights", "square", "circle", "junction", "terminal", "airport", "railway", "office", "postoffice",
            # Regional Administrative Terms (Karnataka, Maharashtra, Telangana/AP, North India)
            "hobli", "hoblii", "hobly", "hoblee", "hobali", "hoballi", "taluk", "taluka", "taluq", "tehsil", "tahsil", 
            "mandal", "mandalam", "mandala", "circle", "division", "prant", "halli", "palli", "palle", "pally", 
            "palya", "pete", "peth", "peta", "kere", "wadi", "vadi", "pada", "wada", "gaon", "gaam", "gam", "gav", 
            "gaav", "thanda", "tanda", "basti", "khasra", "khata", "khatauni", "chak", "patanagere", "pattanagere", 
            "kengeri", "rajarajeshwari", "begur", "varthur", "whitefield", "electroniccity", "electronic", "city"
        }
        self.words.update(common_address_terms)
        
        # Max word length to bound search
        self.max_len = 20
        
    def get_word_cost(self, word):
        if not word:
            return 0
        if word.isdigit():
            return 1.0
        if word in self.words:
            return 1.0
        if len(word) == 1:
            if word in 'ai':
                return 2.0
            return 10.0
        if len(word) == 2 and word not in {"no", "rd", "st", "dr", "w/", "c/", "h/", "fl"}:
            return 8.0  # Heavy penalty for arbitrary 2-letter chops like 're', 'in', 'at'
        # Unknown word cost: scales linearly to keep words unified
        return 1.5 * len(word)
        
    def segment(self, text):
        if not text:
            return ""
            
        # Segment contiguous alphanumeric chunks to preserve existing whitespace and punctuation
        tokens = re.split(r'(\s+|[^\w\s])', text)
        segmented_tokens = []
        for token in tokens:
            if not token:
                continue
            if token.isalnum():
                segmented_tokens.append(self._segment_alnum(token))
            else:
                segmented_tokens.append(token)
                
        result = "".join(segmented_tokens)
        return " ".join(result.split())

    def _segment_alnum(self, s):
        s_lower = s.lower()
        L = len(s_lower)
        if L == 0:
            return ""
            
        dp = [float('inf')] * (L + 1)
        parent = [0] * (L + 1)
        
        dp[0] = 0.0
        split_penalty = 5.0
        
        for i in range(1, L + 1):
            for j in range(max(0, i - self.max_len), i):
                word = s_lower[j:i]
                cost = self.get_word_cost(word) + split_penalty
                if dp[j] + cost < dp[i]:
                    dp[i] = dp[j] + cost
                    parent[i] = j
                    
        words = []
        curr = L
        while curr > 0:
            p = parent[curr]
            words.append(s[p:curr])
            curr = p
            
        words.reverse()
        return " ".join(words)
