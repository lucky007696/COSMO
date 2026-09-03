# memory.py
import json
import os
from datetime import datetime

MEMORY_FILE = "chat_history.json"

def load_history():
    """Loads past conversations from the file."""
    if not os.path.exists(MEMORY_FILE):
        return [] # Return empty list if no file exists
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_interaction(user_text, ai_text):
    """Saves a single Q&A exchange to the history."""
    history = load_history()
    
    # Create the new entry
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_text,
        "ai": ai_text
    }
    
    # Add to list and save
    history.append(new_entry)
    
    # Keep it manageable (keep last 50 messages only)
    if len(history) > 50:
        history = history[-50:]
        
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
    
    print("   💾 Memory Updated.")

def get_recent_context():
    """Returns the last 5 exchanges as a string for Gemini context."""
    history = load_history()
    if not history: return ""
    
    # Get last 5
    recent = history[-5:]
    context_str = "\n--- PREVIOUS CONVERSATION ---\n"
    for item in recent:
        context_str += f"User: {item['user']}\nAI: {item['ai']}\n"
    context_str += "--- END CONTEXT ---\n"
    return context_str