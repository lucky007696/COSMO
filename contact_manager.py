import json
import os
import threading

# 1. Setup paths and locks
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTACTS_FILE = os.path.join(BASE_DIR, "contacts.json")
file_lock = threading.Lock() # 🔒 This prevents the "Race Condition"

def load_contacts():
    """Loads contacts safely."""
    with file_lock: # Wait your turn!
        if not os.path.exists(CONTACTS_FILE):
            return {}
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except Exception as e:
            print(f"⚠️ Read Error: {e}")
            return {}

def save_contact(name, email):
    """Saves contact safely with locking."""
    with file_lock: # 🔒 Lock the file so no one else can touch it
        print(f"💾 Saving: {name} -> {email}")
        
        # 1. Read existing data
        contacts = {}
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content: contacts = json.loads(content)
            except: contacts = {}

        # 2. Update data
        name_key = name.strip().lower()
        contacts[name_key] = {
            "name": name.strip(),
            "email": email.strip()
        }
        
        # 3. Write back to disk
        try:
            with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
                json.dump(contacts, f, indent=4)
                f.flush()
                os.fsync(f.fileno()) # Force Windows to save NOW
            print(f"✅ Saved to {CONTACTS_FILE}")
            return True
        except Exception as e:
            print(f"❌ Save Failed: {e}")
            return False

def get_email(name):
    """Finds an email safely."""
    with file_lock:
        if not os.path.exists(CONTACTS_FILE): return None
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                contacts = json.load(f)
                
            name_key = name.strip().lower()
            if name_key in contacts:
                return contacts[name_key]["email"]
            
            # Fuzzy search
            for key, info in contacts.items():
                if name_key in key: return info["email"]
        except: return None
    return None