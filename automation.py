from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import webbrowser

# --- 🟢 GLOBAL DRIVER (PREVENTS CRASHES) ---
driver_instance = None

def get_driver():
    global driver_instance
    if driver_instance is not None:
        try:
            driver_instance.title 
            return driver_instance
        except:
            driver_instance = None

    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    
    # 🚀 YOUR PROFILE PATH
    current_user = os.getlogin()
    ai_profile_path = f"C:\\Users\\{current_user}\\Cosmo_Profile"
    options.add_argument(f"user-data-dir={ai_profile_path}")
    options.add_argument("profile-directory=Default")
    
    # 🟢 FIX: Correct syntax to remove the annoying "Automated Test Software" banner
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    try:
        driver_instance = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver_instance
    except Exception as e:
        print(f"❌ Driver Error: {e}")
        return None

# --- 🎥 YOUTUBE ---
def play_video(topic):
    driver = get_driver()
    if not driver: return
    try:
        driver.get(f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}")
        wait = WebDriverWait(driver, 10)
        video = wait.until(EC.element_to_be_clickable((By.ID, "video-title")))
        video.click()
    except: pass

# --- 💚 WHATSAPP (THE NUCLEAR KEYBOARD SHORTCUT HACK) ---
def send_whatsapp(contact_name, message):
    print(f"💚 WhatsApp: Sending to '{contact_name}'...")
    driver = get_driver()
    if not driver: return
    
    # 🟢 HELPER: Removes Emojis to prevent BMP Crash
    def remove_non_bmp(text):
        return ''.join(c for c in text if ord(c) <= 0xFFFF)

    clean_message = remove_non_bmp(message)

    if "whatsapp" not in driver.current_url:
        driver.get("https://web.whatsapp.com")

    try:
        wait = WebDriverWait(driver, 30)
        
        # 1. WAIT FOR CHATS TO LOAD (Look for the main body)
        print("⏳ Waiting for chats to fully load...")
        wait.until(EC.presence_of_element_located((By.ID, "pane-side")))
        time.sleep(1) # Give it a brief moment to settle
        body = driver.find_element(By.TAG_NAME, "body")
        
        # 2. THE NUCLEAR SHORTCUT (Ctrl + Alt + /)
        print("☢️ Deploying Keyboard Shortcut bypass...")
        body.send_keys(Keys.CONTROL, Keys.ALT, "/")
        time.sleep(0.5) # Quick wait for cursor to jump
        
        # 3. GRAB THE ACTIVE BOX AND TYPE
        print("⏳ Typing contact name...")
        active_box = driver.switch_to.active_element
        active_box.send_keys(contact_name)
        time.sleep(1.5) # Wait for the contact to appear in the list
        active_box.send_keys(Keys.ENTER)
        
        # 4. TYPE THE MESSAGE
        print("⏳ Typing message...")
        time.sleep(1.5) # Wait for the chat to open
        
        # Once the chat opens, WhatsApp usually auto-focuses the message box.
        # We just grab whatever the active element is and type!
        chat_box = driver.switch_to.active_element
        chat_box.send_keys(clean_message)
        time.sleep(0.5)
        chat_box.send_keys(Keys.ENTER)
        
        print(f"🚀 Message sent to {contact_name}!")

    except Exception as e:
        print(f"❌ WhatsApp Error: {e}")
        print("💡 TIP: Ensure you are logged in and chats have fully loaded!")
def play_spotify(song_name):
    print(f"🎵 Spotify: Searching for '{song_name}'...")
    driver = get_driver()
    if not driver: return

    # 1. Open Spotify Search directly (🟢 FIX: Corrected Native Spotify URL)
    query = song_name.replace(" ", "%20")
    driver.get(f"https://open.spotify.com/search/{query}")
    
    try:
        # 2. Wait for the big Green Play Button to appear
        wait = WebDriverWait(driver, 15)
        
        # This selector finds the "Play" button for the Top Result
        play_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='play-button']")))
        
        play_btn.click()
        print(f"✅ Clicking Play on {song_name}")
        
    except Exception as e:
        print(f"❌ Spotify Error: {e}")
        print("💡 NOTE: You must be logged into Spotify Web Player for this to work!")

# --- 🌍 UNIVERSAL OPENER (SIMPLE) ---
def open_site(site_name):
    site_name = site_name.lower().replace(" ", "")
    if "." not in site_name: url = f"https://www.{site_name}.com"
    else: url = f"https://{site_name}"
    webbrowser.open(url) # Opens in default browser (Fast)

def google_search(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")