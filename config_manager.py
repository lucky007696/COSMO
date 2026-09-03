import json
import os

# The name of the file where we save your login details
CONFIG_FILE = "config.json"

def load_config():
    """
    Reads the 'config.json' file to get your saved email and password.
    Returns an empty dictionary {} if the file doesn't exist yet.
    """
    if not os.path.exists(CONFIG_FILE):
        return {} # No config saved yet
    
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(email, password):
    """
    Saves your email and app password to 'config.json'.
    This is called when you click 'Save' in the Settings window.
    """
    data = {
        "email": email.strip(),
        "password": password.strip()
    }
    
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
        print("✅ Configuration saved successfully.")
        return True
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False