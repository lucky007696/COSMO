# file_ops.py
import os
import shutil
from send2trash import send2trash

# --- 1. SMART PATH FINDER ---
def get_desktop_path():
    """Finds the Desktop, prioritizing OneDrive to ensure icons appear."""
    user_root = os.path.expanduser("~")
    path_one = os.path.join(user_root, "OneDrive", "Desktop")
    if os.path.exists(path_one): return path_one
    return os.path.join(user_root, "Desktop")

DESKTOP_PATH = get_desktop_path()
print(f"📂 File Operations Active at: {DESKTOP_PATH}")

def get_system_path(folder_name):
    """
    UNIVERSAL FINDER: Treats all folder names equally.
    Scans Home, OneDrive, and Desktop to find the folder you asked for.
    """
    folder_name = folder_name.lower().strip()
    user_root = os.path.expanduser("~")
    
    # 1. Check if the name matches your Home Folder (e.g. 'Users', 'Home')
    if folder_name in ["users", "home", "profile", os.path.basename(user_root).lower()]:
        return user_root

    # 2. Check for the folder in Standard Locations (OneDrive & Home)
    # This works for 'Documents', 'Downloads', 'Raja', 'Game', etc.
    search_roots = [
        os.path.join(user_root, "OneDrive"), # Check Cloud First
        user_root,                           # Check Local
        DESKTOP_PATH                         # Check Desktop
    ]

    for root in search_roots:
        target_path = os.path.join(root, folder_name.capitalize())
        if os.path.exists(target_path):
            return target_path

    # 3. Fallback: If not found anywhere, treat it as a new Desktop folder
    return os.path.join(DESKTOP_PATH, folder_name)

def clean_path(name):
    """Removes 'Desktop/' prefix and cleans slashes."""
    name = name.replace("Desktop/", "").replace("Desktop\\", "")
    return name.lstrip("/").lstrip("\\").strip()

def find_file_smart(filename):
    """
    X-RAY VISION: Finds files anywhere (Desktop, Documents, Downloads, Home).
    Also guesses extensions (e.g., finds 'game.sql' if you just say 'game').
    """
    filename = clean_path(filename)
    
    # Search everywhere: Desktop, Documents, Downloads, Home
    search_paths = [
        DESKTOP_PATH, 
        get_system_path("documents"), 
        get_system_path("downloads"), 
        os.path.expanduser("~")
    ]
    
    extensions = ["", ".py", ".txt", ".java", ".cpp", ".html", ".sql", ".pdf", ".docx"]
    
    for folder in search_paths:
        if not os.path.exists(folder): continue
        for ext in extensions:
            # Try to build the full path
            target = filename if filename.endswith(ext) else filename + ext
            full_path = os.path.join(folder, target)
            if os.path.exists(full_path): return full_path
    
    return None

# --- 2. FILE OPERATIONS ---

def create_file(filename, content=""):
    try:
        filename = clean_path(filename)
        full_path = os.path.join(DESKTOP_PATH, filename)
        
        # STATUS CHECK: Return specific string if exists
        if os.path.exists(full_path):
            print(f"   ⚠️ File already exists: {full_path}")
            return "EXISTS" 
            
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f: f.write(content)
        print(f"   ✅ Created: {full_path}")
        return True
    except Exception as e:
        print(f"   ❌ CREATE ERROR: {e}")
        return False

def rename_file(old_name, new_name):
    try:
        old_path = find_file_smart(old_name)
        if not old_path:
            print(f"   ⚠️ Rename Failed: {old_name} not found.")
            return False
        
        new_name = clean_path(new_name)
        # Keep file in the same folder
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        # Safety: Don't rename if new name already exists
        if os.path.exists(new_path):
            print(f"   ⚠️ Cannot rename: {new_name} already exists.")
            return False

        os.rename(old_path, new_path)
        print(f"   ✏️ Renamed {os.path.basename(old_path)} -> {new_name}")
        return True
    except Exception as e:
        print(f"   ❌ RENAME ERROR: {e}")
        return False

def move_file(filename, destination_name):
    try:
        source_path = find_file_smart(filename)
        dest_folder = get_system_path(destination_name)
        
        if not source_path:
            print(f"   ⚠️ Move Failed: Source {filename} not found.")
            return False
        
        if not os.path.exists(dest_folder): os.makedirs(dest_folder)
            
        shutil.move(source_path, dest_folder)
        print(f"   📦 Moved {os.path.basename(source_path)} to {dest_folder}")
        return True
    except Exception as e:
        print(f"   ❌ MOVE ERROR: {e}")
        return False

def delete_file(filename):
    try:
        full_path = find_file_smart(filename)
        if full_path:
            send2trash(full_path)
            print(f"   🗑️ Deleted: {full_path}")
            return True
        print(f"   ⚠️ Delete Failed: {filename} not found.")
        return False
    except: return False


def create_folder(foldername):
    try:
        foldername = clean_path(foldername)
        full_path = os.path.join(DESKTOP_PATH, foldername)
        
        # STATUS CHECK: Return specific string if exists
        if os.path.exists(full_path):
            print(f"   ⚠️ Folder already exists: {full_path}")
            return "EXISTS"
            
        os.makedirs(full_path, exist_ok=True)
        print(f"   📂 Created Folder: {full_path}")
        return True
    except: return False