import os
import sys
import sqlite3
import random
import re
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "backend", "pincodes_in.db")

# ---------------------------------------------------------------------------
# 1. Load All-India Postal Database
# ---------------------------------------------------------------------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT place_name, district, state_name, pincode FROM pincodes")
ALL_INDIA_POSTAL_RECORDS = cursor.fetchall()
conn.close()

print(f"Loaded {len(ALL_INDIA_POSTAL_RECORDS):,} official Indian postal records from SQLite DB.")

# ---------------------------------------------------------------------------
# 2. Rich Component Lists (India & Global)
# ---------------------------------------------------------------------------

HOUSE_PREFIXES_IN = [
    "Flat No", "Flat", "Plot No", "Plot", "House No", "H No", "H.No", "H-No", "H/No",
    "Room No", "Room", "Chawl No", "Chawl", "Shop No", "Shop", "Quarter No", "Qtr No",
    "MIG", "HIG", "LIG", "Villa No", "Bungalow No", "Door No", "D.No", "Unit No", "Cabin No",
    "Khasra No", "Khata No", "Survey No", "Holding No", "Premises No"
]

WING_BLOCK_PREFIXES = [
    "Wing A", "Wing B", "Wing C", "Wing D", "A Wing", "B Wing", "C Wing", "D Wing",
    "Block A", "Block B", "Block C", "Block D", "Block 1", "Block 2", "Block 3",
    "Tower 1", "Tower 2", "Tower A", "Tower B", "Floor 1", "Floor 2", "Floor 3", "2nd Floor", "3rd Floor",
    "Pocket A", "Pocket B", "Pocket 1", "Pocket 2", "Phase 1", "Phase 2", "Phase 3"
]

SOCIETIES_IN = [
    "Shanti Niketan", "Ganesh Kunj", "Sai Sadan", "Krishna Heights", "Balaji Residency",
    "Shiv Shakti Apartments", "Saraswati Complex", "Panchavati Enclave", "Geeta Bhavan",
    "Vrindavan Society", "Gokuldham Society", "DLF Phase 2", "Hiranandani Gardens",
    "Prestige Shantiniketan", "Sobha Jasmine", "Tata Sherwood", "Godrej Woods",
    "L&T Emerald Isle", "Orchid Enclave", "Green Meadows", "Radhe Shyam Residency",
    "Sun City", "Royal Palms", "Silver Oak", "Precious Nest", "Grand Towers", "Suraj Nest"
]

STREETS_IN = [
    "MG Road", "Mahatma Gandhi Road", "100 Feet Road", "Double Road", "Link Road",
    "Linking Road", "Mount Road", "Netaji Subhash Marg", "Outer Ring Road", "Service Road",
    "Station Road", "Temple Road", "Court Road", "Market Lane", "Bypass Road",
    "Gali No 1", "Gali No 2", "Gali No 3", "Gali No 4", "Gali No 7", "Gali No 10", "Main Gali",
    "1st Main Road", "2nd Cross Road", "5th Main 7th Cross", "Sector 14 Road", "Civil Lines",
    "Main Market", "Bazar Road", "College Road", "Airport Road", "Factory Lane"
]

LANDMARKS_IN = [
    "Hanuman Mandir", "Shiva Temple", "Ganesh Temple", "Kali Mandir", "Gurudwara",
    "Railway Station", "Metro Station", "Metro Pillar 124", "Metro Pillar 45", "Bus Stand",
    "Civil Hospital", "SBI Bank ATM", "HDFC Bank", "PNB Bank", "Post Office", "Police Station",
    "City Center Mall", "Town Hall", "Government School", "Water Tank", "Clock Tower",
    "Bata Showroom", "Reliance Fresh", "Apollo Pharmacy", "Petrol Pump", "Flyover"
]

PREPOSITIONS_IN = [
    "near", "opp", "opposite", "behind", "bhd", "beside", "next to", "close to", "adjacent to",
    "facing", "in front of", "ke pas", "ke samne", "ke piche", "bagal me", "ki taraf", "ke upar", "ke neeche",
    "nr", "ner", "oppsite", "behnd", "bhind"
]

NAMES_SALUTATIONS = [
    "Mr. Rahul Sharma", "Dr. Ananya Roy", "Smt. Kamala Devi", "Mr. Amit Patel", "Ms. Priya Singh",
    "C/O Rajesh Gupta", "S/O Ramesh Kumar", "Attn: Procurement Team", "Dr. A.K. Verma", "Pooja Verma",
    "To: Anand Mehta", "Shri Suresh Joshi", "Er. Vikas Reddy", "Adv. Pooja Nair"
]

# Global components
GLOBAL_STREETS = [
    "Main St", "Broadway", "Oak Avenue", "Maple Drive", "Park Lane", "Oxford Street",
    "High Street", "King Street", "Queen Street", "Victoria Road", "George St", "Bay Street",
    "Al Wasl Road", "Sheikh Zayed Road", "Orchard Road", "Toa Payoh Lorong 1"
]

GLOBAL_CITIES = [
    {"city": "New York", "state": "NY", "country": "USA", "postcode": "10001"},
    {"city": "Los Angeles", "state": "CA", "country": "USA", "postcode": "90001"},
    {"city": "Chicago", "state": "IL", "country": "USA", "postcode": "60601"},
    {"city": "London", "state": "England", "country": "United Kingdom", "postcode": "SW1A 1AA"},
    {"city": "Manchester", "state": "England", "country": "United Kingdom", "postcode": "M1 1AE"},
    {"city": "Sydney", "state": "NSW", "country": "Australia", "postcode": "2000"},
    {"city": "Melbourne", "state": "VIC", "country": "Australia", "postcode": "3000"},
    {"city": "Toronto", "state": "ON", "country": "Canada", "postcode": "M5V 2T6"},
    {"city": "Vancouver", "state": "BC", "country": "Canada", "postcode": "V6B 1A1"},
    {"city": "Dubai", "state": "Dubai", "country": "UAE", "postcode": "00000"},
    {"city": "Singapore", "state": "Singapore", "country": "Singapore", "postcode": "310123"}
]

# ---------------------------------------------------------------------------
# 3. Address Generators (Tagged Char-by-Char: N=House, S=Street, C=City, A=State, P=PIN)
# ---------------------------------------------------------------------------

def generate_indian_address():
    record = random.choice(ALL_INDIA_POSTAL_RECORDS)
    place_name, district, state_name, pincode = record
    
    components = []
    
    # Optional Recipient Name (Tagged as 'O' or stripped)
    has_name = random.random() < 0.15
    if has_name:
        name_str = random.choice(NAMES_SALUTATIONS) + ", "
        components.append((name_str, 'S')) # labeled S or stripped by preprocessor
        
    # House Number / Building / Wing (Tagged 'N')
    has_house = random.random() < 0.85
    if has_house:
        pref = random.choice(HOUSE_PREFIXES_IN)
        num = random.choice([
            str(random.randint(1, 999)),
            f"{random.randint(1, 100)}/{random.randint(1, 50)}",
            f"{random.randint(1, 50)}-{random.choice(['A', 'B', 'C', 'D'])}",
            f"{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(101, 909)}"
        ])
        house_str = f"{pref} {num}"
        if random.random() < 0.4:
            wing = random.choice(WING_BLOCK_PREFIXES)
            house_str += f" {wing}"
        if random.random() < 0.3:
            soc = random.choice(SOCIETIES_IN)
            house_str += f" {soc}"
        components.append((house_str, 'N'))
        
    # Street & Landmarks (Tagged 'S')
    street_parts = []
    if random.random() < 0.7:
        street_parts.append(random.choice(STREETS_IN))
    if random.random() < 0.6:
        prep = random.choice(PREPOSITIONS_IN)
        landmark = random.choice(LANDMARKS_IN)
        street_parts.append(f"{prep} {landmark}")
    if random.random() < 0.3 and place_name and place_name.lower() != district.lower():
        street_parts.append(place_name)
        
    if not street_parts:
        street_parts.append(random.choice(STREETS_IN))
        
    street_str = ", ".join(street_parts)
    components.append((street_str, 'S'))
    
    # City / District (Tagged 'C')
    components.append((district, 'C'))
    
    # State / Area (Tagged 'A')
    components.append((state_name, 'A'))
    
    # Pincode (Tagged 'P')
    components.append((pincode, 'P'))
    
    return components

def generate_global_address():
    loc = random.choice(GLOBAL_CITIES)
    components = []
    
    # House & Unit (Tagged 'N')
    house_num = random.choice([
        f"{random.randint(1, 9999)}",
        f"Unit {random.randint(1, 50)}, {random.randint(1, 999)}",
        f"Suite {random.randint(100, 900)}, {random.randint(1, 999)}",
        f"Apt {random.randint(1, 20)}{random.choice(['A', 'B', 'C'])}, {random.randint(1, 500)}"
    ])
    components.append((house_num, 'N'))
    
    # Street (Tagged 'S')
    street_name = random.choice(GLOBAL_STREETS)
    components.append((street_name, 'S'))
    
    # City (Tagged 'C')
    components.append((loc["city"], 'C'))
    
    # State / Province (Tagged 'A')
    components.append((f"{loc['state']} {loc['country']}", 'A'))
    
    # Postcode (Tagged 'P')
    components.append((loc["postcode"], 'P'))
    
    return components

def assemble_address_chars(components, noise_level=0.2):
    """
    Assembles components into a sequence of characters and labels.
    Injects realistic OCR noise, spacing corruption, and punctuation variations.
    """
    chars = []
    labels = []
    
    for i, (text, label) in enumerate(components):
        # Add delimiter between components
        if i > 0:
            delimiter = random.choice([", ", " ", " - ", ","])
            for d in delimiter:
                chars.append(d)
                labels.append('O')
                
        for char in text:
            # Noise injection: OCR letter-digit substitutions
            if noise_level > 0 and random.random() < (noise_level * 0.05):
                if char.lower() == 'o':
                    char = '0'
                elif char == '0':
                    char = 'O'
                elif char.lower() == 's':
                    char = '5'
                elif char == '5':
                    char = 'S'
                elif char.lower() == 'i':
                    char = '1'
                elif char == '1':
                    char = 'l'
                    
            chars.append(char)
            labels.append(label)
            
    return chars, labels

# ---------------------------------------------------------------------------
# 4. Generate Master Dataset (50,000 Indian + Global Addresses)
# ---------------------------------------------------------------------------

def generate_master_dataset(num_samples=50000, output_csv="master_address_dataset.csv"):
    print(f"Generating {num_samples:,} Master Training Addresses...")
    rows = []
    
    for i in range(num_samples):
        # 85% Indian (all 35 states), 15% Global
        if random.random() < 0.85:
            comps = generate_indian_address()
        else:
            comps = generate_global_address()
            
        noise = random.choice([0.0, 0.0, 0.1, 0.2, 0.3])
        chars, labels = assemble_address_chars(comps, noise_level=noise)
        
        full_text = "".join(chars)
        label_str = " ".join(labels)
        
        rows.append({
            "address_text": full_text,
            "char_labels": label_str
        })
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1:,} / {num_samples:,} addresses...")
            
    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    print(f"[SUCCESS] Saved Master Dataset with {len(df):,} samples to '{output_csv}' ({os.path.getsize(output_csv) / (1024*1024):.1f} MB)!")
    return df

if __name__ == "__main__":
    generate_master_dataset(num_samples=50000)
