# backend.py
import os
import sys

# --- 🔧 NVIDIA GPU LINK ---
venv_path = sys.prefix
# ... (Keep your existing NVIDIA path code here) ...

import automation
# --- 🔧 NVIDIA GPU LINK (MUST BE AT THE VERY TOP) ---
venv_path = sys.prefix
nvidia_base = os.path.join(venv_path, "Lib", "site-packages", "nvidia")
if os.path.exists(nvidia_base):
    paths_to_add = []
    for root, dirs, files in os.walk(nvidia_base):
        if any(f.endswith(".dll") for f in files):
            paths_to_add.append(root)
    os.environ["PATH"] = ";".join(paths_to_add) + ";" + os.environ.get("PATH", "")
import sys
import warnings

import requests
warnings.simplefilter(action='ignore', category=FutureWarning)

from faster_whisper import WhisperModel
import warnings
# Import the Piper library
from piper.voice import PiperVoice

import os

# backend.py imports section
import contact_manager 
import config_manager  
import json
import shutil  
import re
import memory 
import speech_recognition as sr
import os
import time
import datetime
import random
import pygame
import pyttsx3
import PIL.Image
import webbrowser 
import subprocess 
import threading 
import pythoncom 
import contact_manager 
import numpy as np 
# 👇 IMPORT YOUR TOOLS 👇
import system_tools 
import file_ops 

from PySide6.QtCore import QThread, Signal, QObject, QCoreApplication
import google.generativeai as genai

microphone_lock = threading.Lock()

# --- CONFIG ---

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

class TextToSpeech(QThread):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            pythoncom.CoInitialize() 
            engine = pyttsx3.init()
            
            # --- 🟢 FIX: SELECT ZIRA VOICE INSIDE THE THREAD ---
            voices = engine.getProperty('voices')
            for v in voices:
                if "zira" in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break
            
            engine.setProperty('rate', 175) # Speed adjustment
            engine.say(self.text)
            engine.runAndWait()
        except:
            pass
        finally:
            pythoncom.CoUninitialize()

class AIResponder(QObject):
    response_ready = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.is_cancelled = False
        self.chat = None
        self.offline_mode = False 
        self.speech_lock = threading.Lock() 
        self.wake_thread = None 

        # --- 🛡️ CRASH FIX: Keep track of active voice threads ---
        self.tts_queue = [] 
        
        app = QCoreApplication.instance()
        if app: app.aboutToQuit.connect(self.cleanup)
        
        try: pygame.mixer.init(frequency=24000, buffer=1024)
        except: pass

        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.connect_to_model()
        except Exception as e:
            print(f"Backend Init Error: {e}")
            self.offline_mode = True

    # --- 🟢 CHANGE 1: UPDATED CLEANUP (Fixes Red Error) ---
    def cleanup(self):
        print("🛑 System: Cleaning up threads...")
        self.is_cancelled = True
        self.stop_audio()
        
        # --- 🛡️ FIX: Wait for speech to finish (Prevents Red Error) ---
        for t in self.tts_queue:
            if t.isRunning(): t.wait(500)

        if self.wake_thread and self.wake_thread.isRunning():
            self.wake_thread.stop()
            self.wake_thread.wait(1000)
            if self.wake_thread.isRunning(): self.wake_thread.terminate()

    def connect_to_model(self):
        try:
            self.model = genai.GenerativeModel("models/gemini-3.5-flash-lite")
            self.chat = self.model.start_chat(history=[])
            print(f"✅ SUCCESS: Connected to Gemini")
            self.offline_mode = False
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            self.offline_mode = True
            # ...existing code...
    # ==========================================
    # 🟢 LAYER 1: DIRECT RUN COMMANDS (Type 3)
    # ==========================================
    def try_direct_run(self, app_name):
        # Tries to run simple commands like "notepad", "calc", "explorer"
        try:
            # specifically handle common abbreviations
            aliases = {
                "calculator": "calc",
                "file explorer": "explorer",
                "cmd": "cmd",
                "terminal": "wt",
                "powershell": "powershell",
                "paint": "mspaint",
                "notepad": "notepad",
                "task manager": "taskmgr",
                "nvidia control panel": "nvcplui",
            }
            cmd = aliases.get(app_name, app_name)

            # Check if it's runnable
            if shutil.which(cmd):
                os.system(f"start {cmd}")
                print(f"   ✅ Layer 1 Success: Direct Run '{cmd}'")
                return True
        except: pass
        return False

    # ==========================================
    # 🟢 LAYER 2: START MENU SHORTCUTS (Type 2)
    # ==========================================
    def try_start_menu_scan(self, app_name):
        # Scans user and system Start Menu for .lnk files
        # Matches: "VS Code", "Revo Uninstaller", "XAMPP", "Chrome"

        # 1. Define Paths to Scan
        search_paths = [
            os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ["USERPROFILE"], "Desktop"),
            # Added this back because VS Code often lives here:
            os.path.join(os.environ["LOCALAPPDATA"], "Programs")
        ]

        print("   📂 Layer 2: Scanning Start Menu...")
        best_match = None
        highest_score = 0
        search_terms = app_name.split()

        # 🛑 JUNK FILTER: Ignore these words to prevent opening uninstallers
        ignore_list = ["uninstall", "remove", "help", "manual", "website", "readme", "license", "setup", "update", "config"]

        for path in search_paths:
            if not os.path.exists(path): continue
            for root, dirs, files in os.walk(path):
                # Optimization: Don't scan too deep (max 2 folders down)
                if root.count(os.sep) - path.count(os.sep) > 2: continue

                for file in files:
                    if not file.lower().endswith(".lnk"): continue

                    fname = file.lower().replace(".lnk", "")

                    # 🛡️ Safety Check: Skip uninstallers/help files
                    if any(bad in fname for bad in ignore_list): continue

                    score = 0

                    # 1. Exact Match (e.g. "Calc" == "Calc")
                    if app_name == fname: score += 100

                    # 2. Starts With (e.g. "Revo" -> "Revo Uninstaller")
                    elif fname.startswith(app_name): score += 90

                    # 3. Word Match (e.g. "Code" -> "Visual Studio Code")
                    elif all(term in fname for term in search_terms): score += 70

                    # 4. Partial Match (e.g. "XAMPP" -> "XAMPP Control Panel")
                    elif app_name in fname: score += 50

                    if score > highest_score:
                        highest_score = score
                        best_match = os.path.join(root, file)
                        # print(f"      Candidate: {fname} | Score: {score}")

        # Threshold 50 means we found at least a decent partial match
        if best_match and highest_score >= 50:
            print(f"   ✅ Layer 2 Success: Found Shortcut '{best_match}'")
            os.startfile(best_match)
            return True
        return False

    # ==========================================
    # 🟢 LAYER 3: POWERSHELL STORE APPS (Type 1)
    # ==========================================
    def try_store_apps(self, app_name):
        # Uses PowerShell to find AppIDs for Camera, WhatsApp, Settings, etc.
        print("   ⚡ Layer 3: Querying Windows Store Apps...")
        try:
            # This command lists ALL apps installed on Windows
            cmd = "Get-StartApps | ConvertTo-Json"
            # Use creationflags to hide the PowerShell popup window
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode != 0: return False

            apps_list = json.loads(result.stdout)

            # We filter the list in Python because it's smarter than PowerShell
            for app in apps_list:
                name = app.get("Name", "").lower()
                app_id = app.get("AppID", "")

                # Check for match
                # Fixes "Camera" matching "Camera", "Whats" matching "WhatsApp"
                if app_name in name or name in app_name:
                    # Strict check: Don't let "Note" match "OneNote" if user wanted "Notepad"
                    # But allow "Camera" to match "Windows Camera"
                    print(f"   ✅ Layer 3 Success: Found AppID '{name}' -> {app_id}")

                    # This special command launches the Store App
                    os.system(f'explorer shell:appsFolder\\{app_id}')
                    return True
        except Exception as e:
            print(f"Layer 3 Error: {e}")
        return False

    # ==========================================
    # 🟢 MASTER CONTROLLER (SMART HYBRID)
    # ==========================================
    def find_and_open_app(self, app_name):
        app_name = app_name.lower().strip()
        print(f"🔎 Master Search: '{app_name}'")

        # 1. Try Direct Command (Fastest - e.g. Notepad, Calc)
        if self.try_direct_run(app_name): return True

        # 2. Try Start Menu Shortcuts (Most installed apps)
        if self.try_start_menu_scan(app_name): return True

        # 3. Try Windows Store Apps (Camera, WhatsApp)
        if self.try_store_apps(app_name): return True

        # 4. 🟢 FINAL FALLBACK: OPEN AS WEBSITE (The Fix)
        # instead of searching Google, we open the site directly.
        print(f"🌐 App not found. Opening as Website: {app_name}")
        
        # Clean the name (e.g. "Epic Games" -> "epicgames")
        site_name = app_name.replace(" ", "")
        
        # Open standard .com URL
        webbrowser.open(f"https://www.{site_name}.com")
        return True
  

    # --- HELPER: LOAD DATABASE ---
    def load_contacts(self):
        try:
            with open("contacts.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {} 

    # --- HELPER: SAVE DATABASE ---
    def save_contact(self, name, email):
        contacts = self.load_contacts() 
        contacts[name] = email          
        with open("contacts.json", "w") as f:
            json.dump(contacts, f, indent=4)
        print(f"   💾 Saved {name} to Database.")

    # --- MAIN FUNCTION: AUTO-SEND EMAIL (SMTP) ---
    def send_email(self, contact_name, body=""):
        import smtplib
        import ssl
        from email.message import EmailMessage
        
        # 1. LOAD CREDENTIALS FROM USER SETTINGS
        config = config_manager.load_config()
        SENDER_EMAIL = config.get("email")
        APP_PASSWORD = config.get("password")

        # 2. CHECK IF THEY EXIST
        if not SENDER_EMAIL or not APP_PASSWORD:
            print("❌ Error: Credentials missing. Please click the Profile icon and save your details.")
            return False

        print(f"   📧 Sending email to: '{contact_name}' from {SENDER_EMAIL}...")

        try:
            # Create the email structure
            msg = EmailMessage()
            msg.set_content(body)
            msg["Subject"] = "Message from Cosmo AI"
            msg["From"] = SENDER_EMAIL
            msg["To"] = contact_name 

            # Connect to Gmail Server
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(SENDER_EMAIL, APP_PASSWORD)
                server.send_message(msg)
            
            print(f"   ✅ EMAIL SENT SUCCESSFULLY!")
            return True

        except Exception as e:
            print(f"   ❌ Failed to send email: {e}")
            return False
        
    def get_live_context(self):
        # 1. TIME & DATE
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")
        
        # 2. BATTERY
        batt = system_tools.get_battery()
        
        # ⚡ REMOVED the broken weather website completely!
        # Now this function takes 0.001 seconds instead of 5.0 seconds.

        return f"[System Context: Today is {date_str} | Time: {time_str} | Battery: {batt}]"
    
    def generate_response(self, user_text, image_path=None):
        self.is_cancelled = False
        if not user_text and not image_path: return

        if self.offline_mode:
            self.response_ready.emit("I'm offline.")
            # self.speak_text("I'm offline.") # Removed to avoid double speak
            return

        try:
            print(f"Backend: Sending to Gemini -> '{user_text}'...")
            
            # --- 1. THE INSTRUCTIONS (YOUR ORIGINAL INSTRUCTIONS) ---
            system_instruction = (
                "You are Cosmo, an elite AI Operating System. "
                "You are intelligent, witty, efficient, and the user's sarcastic best friend. "
                
               "--- 🎭 MODULE 1: THE 'SHARP BEST FRIEND' PERSONA ---"
                "1. THE 'SHORT & PUNCHY' RULE:"
                "   - Be fun, but be FAST. You have 1-3 sentences MAX per turn."
                "   - Deliver the roast/joke and the answer immediately. Move on."
                "   - DO NOT end with questions like 'Need anything else?'. It's annoying."
                
                "2. VIBE: INTELLIGENT & SARCASTIC:"
                "   - Tease the user lightly if they are being lazy."
                "   - Celebrate if they are being productive."
                "   - Example: 'I'm bored' -> 'Only boring people get bored. Go code something. 💻'"
                "   - Example: 'Open YouTube' -> 'Distraction time again? Fine. 📺 {{OPEN: youtube.com}}'"

                "3. VISUAL STYLE:"
                "   - Use Emojis (🚀, 💀, ✨) naturally to add flavor."
                "   - Use **Bold** for key words to make it look sharp on screen."

                "--- 🚀 MODULE 2: SYSTEM CONTROL (UNIVERSAL LOGIC) ---"
                "1. APP OPENING PRINCIPLE (THE 'SPECIFICITY' LAW):"
                "   - GOAL: Clean the request, but NEVER lose the specific identity of the app."
                
                "   - RULE A (REMOVE FLUFF): Remove words that describe the *file type* or *interface*."
                "     * TRASH WORDS: 'App', 'Application', 'Launcher', 'Executable', 'Tool', 'The', 'Client'."
                "     * Example: 'Open Epic Games Launcher' -> '{{OPEN: epic games}}' (Launcher is fluff)."

                "   - RULE B (PRESERVE MODIFIERS): If a word describes the *Brand*, *Edition*, or *Type*, KEEP IT."
                "     * CRITICAL: Do not shorten 'Nvidia Control Panel' to 'Control Panel' (That opens Windows Settings!)."
                "     * CRITICAL: Do not shorten 'Visual Studio Code' to 'Code' (That might open a random file)."
                "     * LOGIC: If removing the word changes *which* app opens, it is NOT fluff."
                "     * Right: 'Open Nvidia Control Panel' -> '{{OPEN: nvidia control panel}}'."

                "3. TRANSLATION PROTOCOL (UNIVERSAL NICKNAME RESOLVER):"
                "   - RULE: Users use slang/abbreviations. You MUST expand them to the Official Software Name."
                "   - LOGIC: If user says 'VS Code', you know the app is named 'Visual Studio Code'. Output the FULL name."
                "   - LOGIC: If user says 'Geforce', the app is 'Geforce Experience'."
                "   - LOGIC: If user says 'Word', the app is 'Microsoft Word'."
                "   - ALWAYS output the most likely official name found in a Windows Start Menu."
                "   - SYNTAX: '{{OPEN: [Official Name]}}'."

                "4. AMBIGUITY CHECK (THE SMART GUARD):"
                "   - CASE A (VAGUE REQUEST): If user says a brand name with multiple apps (e.g., 'Open Nvidia', 'Open Adobe'), DO NOT GUESS."
                "     * Action: Ask 'Which one? [Option A] or [Option B]?'"
                "     * CRITICAL: DO NOT output the {{OPEN}} tag while asking."
                "   - CASE B (SPECIFIC REQUEST): If user says a specific name (e.g., 'Open Nvidia App', 'Open Photoshop'), TRUST THEM."
                "     * Action: Execute immediately. Do not ask."
                "     * Output: '{{OPEN: [Cleaned Name]}}'."
                

                "--- ⚡ MODULE 3: SYSTEM GOD MODE (UPGRADE 1) ---"
                "1. AUDIO KINETICS:"
                "   - User: 'Set volume to 50%' -> You: '{{VOLUME: 50}} Audio adjusted to 50%.'"
                "   - User: 'Mute this' -> You: '{{VOLUME: 0}} Silence is golden. Muted.'"
                "2. POWER DIAGNOSTICS:"
                "   - User: 'Check battery' -> You: '{{BATTERY}} Scanning power cells...'"

                "--- 📂 MODULE 4: FILE OPERATIONS (UNIVERSAL) ---"
                "1. CREATE: 'Create [Filename]' -> '{{CREATE: [Filename]}}' (ALWAYS add extension if user forgets)."
                "   - 'Make a folder [Name]' -> '{{MKDIR: [Name]}}' (Treats all folders equally)."
                "2. DELETE: 'Delete [Name]' -> '{{DELETE: [Name]}}' (Will search Desktop/Docs/Downloads automatically)."
                "3. MOVE: 'Move [Name] to [Folder]' -> '{{MOVE: [Name] TO [Folder]}}'."
                "   - Note: Works for ANY folder (Documents, Desktop, Downloads, or custom folders)."
                "4. RENAME: 'Rename [Old] to [New]' -> '{{RENAME: [Old] TO [New]}}'."

                "--- ⏰ MODULE 5: CHRONOS (NEW) ---"
                "1. TIME/DATE: You have access to the system clock in the context."
                "   - 'What time is it?' -> 'It is [Time]. Time to code.'"
                "   - 'What day is it?' -> 'It's [Date].'"

                "--- ⚖️ MODULE 6: DECISION MATRIX ---"
                "1. SAFETY RULE (ONE COMMAND ONLY): You can ONLY execute ONE command tag per turn."
                "   - If user asks: 'Create folder X and move file Y', ONLY do the CREATE first."
                "   - Then ask: 'Folder created. Want me to move the file now?'"

                "2. SHOPPING/BUYING PROTOCOL (NEW):"
                "   - If user says 'I want to buy [Item]' (e.g., watch, phone, laptop), DO NOT SEARCH IMMEDIATELY."
                "   - ASK clarifying questions first: 'What budget?', 'Which brand?', 'What type?'"
                "   - ONLY use {{SEARCH: ...}} when the user gives specific details (e.g., 'Buy Rolex under $5000')."

                
              "--- 📧 MODULE 7: INTELLIGENT EMAIL (OPTIMIZED) ---"
            "1. DATABASE FIRST PROTOCOL:"
            "   - ALWAYS output '{{EMAIL_DRAFT: [Name] | [Body]}}' immediately when asked to email someone."
            "   - DO NOT ASK for an email address yet. The System will check the database for you."
            "   - IF the System returns 'Contact Not Found', ONLY THEN ask the user: 'I don't have an email for [Name]. What is it?'"

            "2. NEW CONTACT FLOW (The Response):"
            "   - WHEN the user provides an email (e.g., 'It's jack@gmail.com'), you MUST output TWO tags:"
            "     a. '{{UPDATE_CONTACT: [Name] | [Email]}}' (To save it)"
            "     b. '{{EMAIL_DRAFT: [Name] | [Body]}}' (To re-trigger the draft)"
            "   - Example: 'Thanks, saving that. {{UPDATE_CONTACT: Jack | jack@gmail.com}} {{EMAIL_DRAFT: Jack | Hi Jack...}}'"

            "3. THE GHOSTWRITER PROTOCOL (ADVANCED BODY GENERATION):"
            "   - RULE A: THE 'ANTI-ROBOT' FILTER:"
            "     * NEVER start with 'I hope this email finds you well' or 'I am writing to...'."
            "     * Start DIRECTLY with the topic. (e.g., instead of 'I am writing to ask about the file', say 'Do you have the file?')."
            
            "   - RULE B: DYNAMIC TONE MATCHING:"
            "     * IF intent is 'Urgent/Angry' -> Short sentences. No fluff. Direct. (e.g., 'We need to talk.')"
            "     * IF intent is 'Request' -> Polite but concise. Use 'Could you...' or 'Please...'."
            "     * IF intent is 'Casual/Friend' -> Use contractions ('can't', 'won't'). Warm sign-off."
            
            "   - RULE C: THE 'CONTEXT EXPANDER':"
            "     * If user gives vague input like 'meeting tuesday', expand it intelligently: 'Are we still on for the meeting this Tuesday?'"
            "     * If user gives NO context, use the 'Soft Ping': 'Hey, just checking in. How are things?'"

            "4. UNIVERSAL TRANSLATION (THE 'DIRECT' RULE):"
            "   - CRITICAL: Users often speak indirectly. You must translate to DIRECT address."
            "   - IF user says: 'Tell [Name] that [X]'"
            "   - YOU WRITE: '[X]' (converted to Second Person 'You')."
            "     * User: 'Tell Boss I quit' -> Body: 'I quit.'"
            "     * User: 'Tell John his file is wrong' -> Body: 'Your file is wrong.'"
            "     * User: 'Ask mom if she is coming' -> Body: 'Are you coming?'"

            "5. COMMANDS:"
            "   - User says 'Send it'/'Yes' -> Output '{{EMAIL_CONFIRM: YES}}'."
            "   - User says 'Change email to [X]' -> Output '{{UPDATE_CONTACT: [Name] | [X]}}'."

             "--- 🚥 MODULE 8: COMMUNICATION TRAFFIC CONTROL (THE ROUTER) ---"
                "1. THE 'STRICT KEYWORD' HIERARCHY:"
                "   - You must detect the 'Carrier Word' to decide between Email and WhatsApp."
                
                "2. TEAM EMAIL (TRIGGERS MODULE 8):"
                "   - Keywords: 'Email', 'Mail', 'Gmail', 'Letter'."
                "   - Rule: If ANY of these words exist, you MUST use {{EMAIL_DRAFT...}}."
                "   - Example: 'Send a mail to Boss' -> {{EMAIL_DRAFT: Boss...}}"
                "   - Example: 'Email Mom' -> {{EMAIL_DRAFT: Mom...}}"

                "3. TEAM WHATSAPP (TRIGGERS MODULE 12):"
                "   - Keywords: 'WhatsApp', 'Text', 'Ping', 'Message', 'Tell', 'Ask'."
                "   - Rule: These words are FAST communication. Use {{WHATSAPP...}}."
                "   - CRITICAL: 'Tell' and 'Message' default to WhatsApp, NOT Email."
                "   - Example: 'Message Mom hi' -> {{WHATSAPP: Mom | hi}}"
                "   - Example: 'Tell Dad I am home' -> {{WHATSAPP: Dad | I am home}}"

                "4. CONFLICT RESOLUTION (THE 'EMAIL OVERRIDE'):"
                "   - If a user mixes words (e.g., 'Message mail'), EMAIL WINS."
                "   - Logic: 'Mail' is a specific object. 'Message' is a general action."
                "   - User: 'Send a message to John' -> WhatsApp (Ambiguous = Fast)."
                "   - User: 'Send an email message to John' -> Email (Specific)."

                "--- 👁️ MODULE 9: VISION PROTOCOL (SMART EYES) ---"
                "1. AUTHORITY: You have the ability to see the user's screen."
                "   - If the user says 'Look at this', 'Read this', or 'Scan screen', an image is likely attached."
                "2. VISUAL NECESSITY CHECK (CRITICAL):"
                "   - BEFORE requesting a screenshot, ask yourself: 'Can I answer this with text only?'"
                "   - User: 'I am totally lost in science' -> DO NOT SCREENSHOT. Just explain science."
                "   - User: 'I am totally lost, what button do I click?' -> {{REQ_SCREENSHOT}}."
                "   - User: 'What is this?' -> {{REQ_SCREENSHOT}}."
                "3. TRIGGER RULE:"
                "   - If the user's query implies looking at the active display (errors, UI elements, specific text on screen) AND no image is provided:"
                "   - OUTPUT: '{{REQ_SCREENSHOT}}'."
                "4. TASKS:"
                "   - 'What is this error?' -> Explain the error code and offer a fix."
                "   - 'Read this' -> Summarize the text on the screen."
                "   - 'Rate my setup' -> Be sarcastic or impressed based on what you see."
                "5. CONTEXT: The provided image IS the user's current screen. Treat it as reality."

                "--- ⏳ MODULE 10: TEMPORAL MANAGEMENT (TIME TRAVEL PROTOCOL) ---"
                "1. THE 'TWO-STAGE' REACTION:"
                "   - You exist in two times: NOW (Setting the timer) and LATER (When it rings)."
                
                "2. STEP 1 - IMMEDIATE RESPONSE (VERBAL):"
                "   - React to the user's request *right now*."
                "   - Example logic: If they ask for a nap, judge them for being lazy *now*."

                "3. STEP 2 - FUTURE MESSAGE (INSIDE TAG):"
                "   - You must write the script for your 'Future Self' to speak when the alarm rings."
                "   - The text inside the tag MUST be a full, personality-driven sentence."
                "   - Do NOT write the task name (e.g., 'Bath'). Write the command (e.g., 'Go take a bath, you smell!')."

                "4. UNIVERSAL SYNTAX (STRICT):"
                "   - RELATIVE: '{{REMIND: [Duration] | [Full Future Spoken Sentence]}}'"
                "   - ABSOLUTE: '{{ALARM: [Time] | [Full Future Spoken Sentence]}}'"
                "   - CRITICAL: The text after the '|' is exactly what you will say when the time comes. Make it count."

                "--- 🔆 MODULE 11: HARDWARE CONTROL ---"
                "1. BRIGHTNESS:"
                "   - If user says 'dim screen', 'max brightness', or 'set brightness to 50%':"
                "   - Output: '{{BRIGHTNESS: [0-100]}}'."
                "   - Example: 'Set brightness to 10%' -> 'Going dark mode. 🌑 {{BRIGHTNESS: 10}}'"

                "--- 🤖 MODULE 12: UNIVERSAL AUTOMATION (ROBOT HANDS) ---"
                "1. THE 'MESSAGE' TRAFFIC COP (CRITICAL RULE):"
                "   - You must decide between EMAIL (Module 8) and WHATSAPP (Module 12)."
                "   - RULE A: If user says 'Email', 'Mail', or 'Letter' -> USE MODULE 8 tags."
                "   - RULE B: If user says 'Message', 'Text', 'Tell', 'Ask', or 'WhatsApp' -> USE {{WHATSAPP...}} tag."
                "   - AMBIGUITY CHECK: 'Send a message to mom' -> WhatsApp (It is faster/default)."
                "   - CONTRADICTION CHECK: 'Message mail to Boss' -> Email (The word 'mail' overrides 'message')."

                "2. YOUTUBE DJ (WEB):"
                "   - Trigger: 'Play [Song/Video]' or 'Watch [Video]'."
                "   - Action: Output '{{PLAY: [Search Query]}}'."
                "   - Example: 'Play Believer' -> 'Turning it up. 🎧 {{PLAY: Believer}}'"
                "   - Example: 'Watch tech news' -> 'Opening feed. {{PLAY: tech news}}'"

                "3. WHATSAPP (WEB):"
                "   - Trigger: 'Message [Name] [Body]' or 'Tell [Name] [Body]'."
                "   - Action: Output '{{WHATSAPP: [Name] | [Body]}}'."
                "   - Example: 'Tell Dad I'm coming' -> 'Sending now. {{WHATSAPP: Dad | I'm coming}}'"
                "   - Example: 'Message Mom hello' -> 'Done. {{WHATSAPP: Mom | hello}}'"

                 "   - CRITICAL (THE 'DIRECT' RULE): Users often speak indirectly. You MUST translate the message to a DIRECT, first-person text as if the user typed it themselves."
                "   - IF user says: 'Tell [Name] that [X]', YOU SEND: '[X]' (converted to Second Person 'You')."
                "   - Example: 'Tell John his code is broken' -> '{{WHATSAPP: John | Your code is broken}}'"
                "   - Example: 'Ask Mom if she wants food' -> '{{WHATSAPP: Mom | Do you want food?}}'"
                "   - Example: 'Tell Sarah I will be late' -> '{{WHATSAPP: Sarah | I will be late}}'"
                 
                 "   - GROUP CHAT PROTOCOL: If the user mentions sending a message to a 'group', adjust your ghostwriting for MULTIPLE people."
                "   - Use plural pronouns like 'you guys', 'everyone', or 'we' instead of just 'you'."
                "   - CRITICAL (THE EXACT MATCH RULE): DO NOT remove the word 'group' from the target name. Output the EXACT name the user gives you."
                "   - Example: 'Tell the project group I am coming' -> '{{WHATSAPP: project group | I am coming, everyone.}}'"
                "   - Example: 'Ask the gaming boys if they are playing' -> '{{WHATSAPP: gaming boys | Are you guys playing?}}'"
                
                "4. SPOTIFY (WEB PLAYER):"
                "   - Trigger: 'Spotify play [Song]'."
                "   - Action: Output '{{SPOTIFY: [Song Name]}}'."
                "   - Example: 'Spotify play Drake' -> 'Vibes incoming. {{SPOTIFY: Drake}}'"

                 "5. RESEARCH (GOOGLE SEARCH):"
                "   - Trigger: 'Search for [Query]' OR questions about current events/news."
                "   - Rule A: IF you know the answer (e.g. 'Who is Einstein?', 'Capital of France'), ANSWER DIRECTLY. Do not search."
                "   - Rule B: IF the user asks for real-time info (News, Stocks, Weather) or you don't know, THEN output '{{SEARCH: [Query]}}'."
                "   - Example: 'Who won the game last night?' -> '{{SEARCH: Who won the game last night}}' (You don't know)."
                "   - Example: 'What is gravity?' -> 'Gravity is...' (Internal knowledge, NO search)."


            )
            
            # --- 2. GET CONTEXT AND MEMORY ---
            history_context = memory.get_recent_context()
            live_context = self.get_live_context()
            
            # Combine everything
            full_prompt = f"{system_instruction}\n{history_context}\n{live_context}\nUser: {user_text}"
            
            if image_path:
                img = PIL.Image.open(image_path)
                response = self.model.generate_content([full_prompt, img])
            else:
                if not self.chat: self.connect_to_model()
                response = self.model.generate_content(full_prompt)

            ai_text = response.text.replace("*", "").strip()
            
             # 1. YOUTUBE DJ
            if "{{PLAY:" in ai_text:
                try:
                    start = ai_text.find("{{PLAY:")
                    end = ai_text.find("}}", start) + 2
                    song = ai_text[start+7:end-2].strip()
                    automation.play_video(song)
                    ai_text = ai_text[:start] + ai_text[end:] # ✂️ Silence tag
                except: pass

            # 2. WHATSAPP
            if "{{WHATSAPP:" in ai_text:
                try:
                    start = ai_text.find("{{WHATSAPP:")
                    end = ai_text.find("}}", start) + 2
                    content = ai_text[start+11:end-2].strip()
                    if "|" in content:
                        name, msg = content.split("|", 1)
                        automation.send_whatsapp(name.strip(), msg.strip())
                    ai_text = ai_text[:start] + ai_text[end:] # ✂️ Silence tag
                except: pass

            # 3. SPOTIFY
            if "{{SPOTIFY:" in ai_text:
                try:
                    start = ai_text.find("{{SPOTIFY:")
                    end = ai_text.find("}}", start) + 2
                    song = ai_text[start+10:end-2].strip()
                    automation.play_spotify(song) 
                    ai_text = ai_text[:start] + ai_text[end:] # ✂️ Silence tag
                except: pass

            # 4. UNIVERSAL OPENER (SMART HYBRID)
            if "{{OPEN:" in ai_text:
                try:
                    start = ai_text.find("{{OPEN:")
                    end = ai_text.find("}}", start) + 2
                    app_name = ai_text[start+7:end-2].strip()
                    
                    # 🟢 CRITICAL FIX: Use 'self.find_and_open_app' NOT 'automation.open_site'
                    # This checks your PC first (Calculator, Notepad). 
                    # If it doesn't find it, THEN it goes to Google.
                    self.find_and_open_app(app_name)
                    
                    ai_text = ai_text[:start] + ai_text[end:] # ✂️ Silence tag
                except: pass

            # 5. GOOGLE SEARCH
            if "{{SEARCH:" in ai_text:
                try:
                    start = ai_text.find("{{SEARCH:")
                    end = ai_text.find("}}", start) + 2
                    query = ai_text[start+9:end-2].strip()
                    automation.google_search(query)
                    ai_text = ai_text[:start] + ai_text[end:] # ✂️ Silence tag
                except: pass
            

            if "{{CREATE:" in ai_text:
                try:
                    start = ai_text.find("{{CREATE:")
                    end = ai_text.find("}}", start) + 2
                    fname = ai_text[start+9:end-2].strip()
                    result = file_ops.create_file(fname)
                    if result is True:
                        ai_text = ai_text[:start] + ai_text[end:]
                    elif result == "EXISTS":
                        ai_text = f"I didn't create '{fname}' because it already exists."
                    elif result == "UNSAFE":
                        ai_text = f"I cannot create '{fname}' in that system folder."
                    else: 
                        ai_text = f"I failed to create {fname}."
                except: pass

            if "{{MKDIR:" in ai_text:
                try:
                    start = ai_text.find("{{MKDIR:")
                    end = ai_text.find("}}", start) + 2
                    folder = ai_text[start+8:end-2].strip()
                    result = file_ops.create_folder(folder)
                    if result is True:
                        ai_text = ai_text[:start] + ai_text[end:]
                    elif result == "EXISTS":
                        ai_text = f"The folder '{folder}' is already there."
                    elif result == "UNSAFE":
                        ai_text = f"I cannot create folder '{folder}' there."
                    else: 
                        ai_text = f"I couldn't create folder {folder}."
                except: pass

            if "{{DELETE:" in ai_text:
                try:
                    start = ai_text.find("{{DELETE:")
                    end = ai_text.find("}}", start) + 2
                    fname = ai_text[start+9:end-2].strip()
                    result = file_ops.delete_file(fname)
                    if result is True: 
                        ai_text = ai_text[:start] + ai_text[end:]
                    elif result == "UNSAFE":
                        ai_text = f"I cannot delete '{fname}'. That is a protected system file."
                    else: 
                        ai_text = f"I couldn't find {fname} to delete."
                except: pass

            if "{{RENAME:" in ai_text:
                try:
                    start = ai_text.find("{{RENAME:")
                    end = ai_text.find("}}", start) + 2
                    params = ai_text[start+9:end-2].strip().split(" TO ")
                    if len(params) == 2:
                        if file_ops.rename_file(params[0], params[1]):
                            ai_text = ai_text[:start] + ai_text[end:]
                        else: ai_text = f"I couldn't rename {params[0]}."
                except: pass

            if "{{MOVE:" in ai_text:
                try:
                    start = ai_text.find("{{MOVE:")
                    end = ai_text.find("}}", start) + 2
                    params = ai_text[start+7:end-2].strip().split(" TO ")
                    if len(params) == 2:
                        if file_ops.move_file(params[0], params[1]):
                            ai_text = ai_text[:start] + ai_text[end:]
                        else: ai_text = f"I couldn't move {params[0]}."
                except: pass

            if "{{VOLUME:" in ai_text:
                try:
                    start = ai_text.find("{{VOLUME:")
                    end = ai_text.find("}}", start) + 2
                    vol_level = ai_text[start+9:end-2].strip()
                    system_tools.set_volume(int(vol_level))
                    ai_text = ai_text[:start] + ai_text[end:]
                except: pass

            if "{{BATTERY}}" in ai_text:
                ai_text = ai_text.replace("{{BATTERY}}", "").strip()

            if "{{OPEN:" in ai_text:
                try:
                    start = ai_text.find("{{OPEN:")
                    end = ai_text.find("}}", start) + 2
                    app_to_open = ai_text[start+7:end-2].strip().lower()
                    print(f"🧠 JARVIS COMMAND: '{app_to_open}'")
                    # --- CALL THE UPDATED HYBRID OPENER ---
                    success = self.find_and_open_app(app_to_open)
                    ai_text = ai_text[:start] + ai_text[end:] 
                    if not success: ai_text = f"I tried to launch {app_to_open}, but it's missing."
                except: pass

            # --- ⏰ REMINDER LOGIC ---
            if "{{REMIND:" in ai_text:
                try:
                    start = ai_text.find("{{REMIND:")
                    end = ai_text.find("}}", start) + 2
                    content = ai_text[start+9:end-2].strip()
                    seconds_str, message = content.split("|", 1)
                    seconds = int(seconds_str.strip())
                    message = message.strip()
                    ai_text = ai_text[:start] + ai_text[end:]
                    def reminder_job():
                        time.sleep(seconds)
                        self.response_ready.emit(f"⏰ REMINDER: {message}")
                        self.speak_text(f"Excuse me. Reminder: {message}")
                    threading.Thread(target=reminder_job, daemon=True).start()
                except Exception as e: print(f"Reminder Error: {e}")

            # --- 📝 SILENT & SMART CONTACT SAVE (The "Free Talking" Fix) ---
            # --- 📝 SILENT & SMART CONTACT SAVE ---
            if "{{UPDATE_CONTACT:" in ai_text:
                try:
                    start = ai_text.find("{{UPDATE_CONTACT:")
                    end = ai_text.find("}}", start) + 2
                    content = ai_text[start+17:end-2].strip()
                    
                    if "|" in content:
                        name, messy_text = content.split("|", 1)
                        name = name.strip()
                        # REGEX FILTER
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', messy_text)
                        if email_match:
                            clean_email = email_match.group(0)
                            contact_manager.save_contact(name, clean_email)
                            print(f"   ✅ Backend Silent Save: {name} -> {clean_email}")

                    # REMOVE TAG so the user only sees the natural text
                    ai_text = ai_text[:start] + ai_text[end:]
                    
                except Exception as e: 
                    print(f"Contact Save Error: {e}")

            # --- 4. SAVE TO MEMORY ---
            memory.save_interaction(user_text, ai_text)

            # --- 🟢 CHANGE 3: SILENCE BACKEND (Fixes Double Speaking) ---
            self.response_ready.emit(ai_text)

            # --- 🟢 CHANGE: Handle the Email Draft Tag ---
           
            # ✅ KEEP THIS BLOCK ONLY
            # --- 🟢 SILENT TAG CLEANER (Keep this only) ---
            if "{{EMAIL_DRAFT:" in ai_text:
                try:
                    start = ai_text.find("{{EMAIL_DRAFT:")
                    end = ai_text.find("}}", start) + 2
                    # This removes the tag so it doesn't print technical brackets,
                    # but it leaves the rest of the AI's natural sentence alone.
                    ai_text = ai_text[:start] + ai_text[end:] 
                except:
                    pass
            
        except Exception as e:
            if "429" in str(e):
                self.response_ready.emit("I'm exhausted. Google's rate limit hit.")
            else:
                print(f"Gemini Error: {e}")
                self.response_ready.emit("Connection trouble.")
            
    # --- 🔵 HELPER TO FIX MAIN.PY ERROR 🔵 ---
    def speak(self, text):
        """Allows main.py to call self.brain.speak()"""
        # 🟢 FIX: Remove emojis/special chars just for the voice
        # This keeps the text safe for the TTS engine
        clean_text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        # Send the clean text to the voice engine
        self.speak_text(clean_text)

    # --- 🛡️ CRASH-PROOF SPEECH SYSTEM (THE FIX) ---
    def speak_text(self, text):
        if not text or self.is_cancelled: return
        self.speech_lock.acquire(blocking=True) 
        try:
            # 1. Create the thread
            new_thread = TextToSpeech(text)
            
            # 2. Add to SAFE list so Python doesn't delete it
            self.tts_queue.append(new_thread)
            
            # 3. Connect cleanup so it removes itself when done
            new_thread.finished.connect(lambda: self.cleanup_tts(new_thread))
            
            # 4. Start talking
            new_thread.start()
        except Exception as e: print(f"TTS Start Error: {e}")
        finally: 
            self.speech_lock.release()

    def cleanup_tts(self, thread):
        """Removes the thread from the safe list once it's done talking."""
        if thread in self.tts_queue:
            self.tts_queue.remove(thread)
        thread.deleteLater() # Safe Qt deletion

    def stop_audio(self):
        self.is_cancelled = True
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop(); pygame.mixer.music.unload()
        except: pass

class WhisperWorker(QObject):
    transcription_finished = Signal(str)
    model_loaded = Signal() 
    
    def __init__(self): 
        super().__init__()
        self.model = None
        
    def load_model(self): 
        try:
            print("🧠 Loading Offline AI Ears into RTX 2050...")
            # Using 'base.en' for speed. 'float16' uses your GPU's Tensor cores.
            self.model = WhisperModel("base.en", device="cuda", compute_type="float16")
            print("✅ Offline Ears Ready! (Zero Ping)")
            self.model_loaded.emit()
        except Exception as e:
            print(f"❌ GPU Loading Failed, falling back to CPU: {e}")
            self.model = WhisperModel("base.en", device="cpu", compute_type="int8")
            self.model_loaded.emit() 
            
    def transcribe(self, audio_path):
        if not self.model:
            self.transcription_finished.emit("")
            return
            
        try:
            # beam_size=1 is the "Speed Mode" for instant results
            segments, info = self.model.transcribe(audio_path, beam_size=1)
            text = "".join([segment.text for segment in segments]).strip()
            print(f"👂 Heard (GPU): '{text}'")
            self.transcription_finished.emit(text)
        except Exception as e:
            print(f"Transcription Error: {e}")
            self.transcription_finished.emit("")
        finally:
            try: os.remove(audio_path)
            except: pass

class AudioRecorderThread(QThread):
    recording_finished = Signal(str)

    def __init__(self): 
        super().__init__()
        self.daemon = True 

    def run(self):
        r = sr.Recognizer()
        
        # 🟢 THE HANG FIX: Let it adapt to your room noise
        r.dynamic_energy_threshold = True
        r.energy_threshold = 400
        
        # 1️⃣ THE "THINKING" TIMER: Changed from 0.8 to 1.5
        r.pause_threshold = 1.5
        r.non_speaking_duration = 0.5

        try:
            with sr.Microphone() as s:
                r.adjust_for_ambient_noise(s, duration=0.2) 
                print("🎤 Listening... (Speak now)")
                
                # 2️⃣ & 3️⃣ THE "WAITING" & "MAXIMUM" TIMERS: Changed to 8 and 30
                audio = r.listen(s, timeout=8, phrase_time_limit=30)
                
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio.get_wav_data())
                    temp_path = f.name
                
                self.recording_finished.emit(temp_path)

        except sr.WaitTimeoutError:
            print("❌ Timeout: You didn't speak.")
            self.recording_finished.emit("")
        except Exception as e:
            print(f"❌ Mic Error: {e}")
            self.recording_finished.emit("")


class WakeWordThread(QThread):
    wake_signal = Signal()
    def __init__(self): 
        super().__init__()
        self.is_listening = True
        self.is_running = True
        self.daemon = True 
    
    def stop(self): 
        self.is_running = False
        self.is_listening = False
        self.requestInterruption()
        self.quit()

    def pause(self): self.is_listening = False
    def resume(self): self.is_listening = True
    
    def run(self):
        r = sr.Recognizer()
        r.energy_threshold = 400
        r.dynamic_energy_threshold = False  
        r.pause_threshold = 0.5 
        r.non_speaking_duration = 0.4
        
        while self.is_running:
            if self.isInterruptionRequested(): break
            if not self.is_listening: 
                time.sleep(0.1) 
                continue
            
            wake_triggered = False
            try:
                with sr.Microphone() as s:
                    r.adjust_for_ambient_noise(s, duration=0.2)
                    print("Backend: Listening for Wake Word 'Cosmo'...")
                    
                    while self.is_listening and self.is_running:
                        try:
                            audio = r.listen(s, timeout=1.0, phrase_time_limit=1.5)
                            text = r.recognize_google(audio).lower()
                            print(f"   --> Heard: '{text}'") 
                            
                            if "cosmo" in text: 
                                print("⚡ Cosmo awake! Releasing hardware to main AI...")
                                self.is_listening = False 
                                wake_triggered = True
                                break # 🛑 EXITS THE 'WITH' BLOCK FIRST
                                
                        except sr.WaitTimeoutError:
                            continue 
                        except Exception: 
                            continue
            except Exception:
                time.sleep(0.5)
                
            # 🛑 EMITS THE SIGNAL AFTER THE MICROPHONE IS COMPLETELY CLOSED
            if wake_triggered:
                self.wake_signal.emit()
