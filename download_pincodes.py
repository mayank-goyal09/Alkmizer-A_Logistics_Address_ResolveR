import os
import zipfile
import urllib.request
import sqlite3

DATABASE_PATH = os.path.join("backend", "pincodes_in.db")
ZIP_URL = "http://download.geonames.org/export/zip/IN.zip"
ZIP_FILE = "IN.zip"
TXT_FILE = "IN.txt"

def main():
    print("Creating backend directory if it doesn't exist...")
    os.makedirs("backend", exist_ok=True)

    print(f"Downloading {ZIP_URL}...")
    try:
        urllib.request.urlretrieve(ZIP_URL, ZIP_FILE)
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download zip file: {e}")
        return

    print(f"Extracting {TXT_FILE} from {ZIP_FILE}...")
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extract(TXT_FILE)
        print("Extraction complete.")
    except Exception as e:
        print(f"Failed to extract zip file: {e}")
        # Clean up zip
        if os.path.exists(ZIP_FILE):
            os.remove(ZIP_FILE)
        return

    print(f"Connecting to SQLite database at {DATABASE_PATH}...")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Drop existing tables to ensure clean setup
    cursor.execute("DROP TABLE IF EXISTS pincodes")
    cursor.execute("DROP TABLE IF EXISTS aliases")

    # Create pincodes table
    cursor.execute("""
        CREATE TABLE pincodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pincode TEXT,
            place_name TEXT,
            district TEXT,
            state_name TEXT,
            state_code TEXT,
            latitude REAL,
            longitude REAL
        )
    """)

    # Create aliases table
    cursor.execute("""
        CREATE TABLE aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alias TEXT UNIQUE,
            canonical_name TEXT,
            entity_type TEXT
        )
    """)

    print("Seeding aliases...")
    aliases_data = [
        ("bombay", "mumbai", "city"),
        ("bangalore", "bengaluru", "city"),
        ("calcutta", "kolkata", "city"),
        ("madras", "chennai", "city"),
        ("trivandrum", "thiruvananthapuram", "city"),
        ("cochin", "kochi", "city"),
        ("pondicherry", "puducherry", "city"),
        ("benares", "varanasi", "city"),
        ("baroda", "vadodara", "city"),
        ("poona", "pune", "city"),
        ("orissa", "odisha", "state"),
        ("banglore", "bengaluru", "city"),
        ("delhhi", "delhi", "city"),
        ("delh", "delhi", "city"),
        ("seelampr", "seelampur", "locality")
    ]
    cursor.executemany("INSERT INTO aliases (alias, canonical_name, entity_type) VALUES (?, ?, ?)", aliases_data)

    print("Parsing IN.txt and inserting records...")
    insert_query = """
        INSERT INTO pincodes (pincode, place_name, district, state_name, state_code, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    records = []
    count = 0
    with open(TXT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 11:
                pincode = parts[1].strip()
                place_name = parts[2].strip()
                state_name = parts[3].strip()
                state_code = parts[4].strip()
                district = parts[5].strip()
                try:
                    lat = float(parts[9])
                    lng = float(parts[10])
                except ValueError:
                    lat = None
                    lng = None

                records.append((pincode, place_name, district, state_name, state_code, lat, lng))
                count += 1

                if len(records) >= 1000:
                    cursor.executemany(insert_query, records)
                    records = []
        
        if records:
            cursor.executemany(insert_query, records)

    print(f"Successfully loaded {count} pincode records.")

    print("Creating database indexes...")
    cursor.execute("CREATE INDEX idx_pincode ON pincodes(pincode)")
    cursor.execute("CREATE INDEX idx_place_name ON pincodes(place_name)")
    cursor.execute("CREATE INDEX idx_district ON pincodes(district)")
    cursor.execute("CREATE INDEX idx_state_name ON pincodes(state_name)")
    
    conn.commit()
    conn.close()
    print("Database indexing complete.")

    print("Cleaning up temporary files...")
    if os.path.exists(ZIP_FILE):
        os.remove(ZIP_FILE)
    if os.path.exists(TXT_FILE):
        os.remove(TXT_FILE)
    print("Cleanup complete. Setup finished successfully.")

if __name__ == "__main__":
    main()
