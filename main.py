import sys
import os
import datetime
import time 
import re 
import memory
import contact_manager
import mail_ops 
import config_manager
from datetime import datetime, timedelta
import screen_brightness_control as sbc

try:
    import winsound
except ImportError:
    winsound = None

from PIL import ImageGrab 

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QFileDialog, QPushButton, 
    QListWidgetItem, QDialog, QFormLayout, QDialogButtonBox, 
    QVBoxLayout, QLineEdit
)
from PySide6.QtCore import Qt, QThread, QTimer, QObject, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QAction

from ui import MainUI, ChatBubble
from backend import WakeWordThread, WhisperWorker, AudioRecorderThread, AIResponder

# --- SETTINGS WINDOW ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cosmo Settings")
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: #1E1F20; color: white;")
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.inp_email = QLineEdit()
        self.inp_email.setPlaceholderText("yourname@gmail.com")
        self.inp_email.setStyleSheet("padding: 5px; border: 1px solid #444; border-radius: 5px;")
        
        self.inp_pass = QLineEdit()
        self.inp_pass.setPlaceholderText("16-digit App Password")
        self.inp_pass.setEchoMode(QLineEdit.Password) 
        self.inp_pass.setStyleSheet("padding: 5px; border: 1px solid #444; border-radius: 5px;")
        
        form.addRow("Gmail Address:", self.inp_email)
        form.addRow("App Password:", self.inp_pass)
        layout.addLayout(form)
        
        current = config_manager.load_config()
        self.inp_email.setText(current.get("email", ""))
        self.inp_pass.setText(current.get("password", ""))

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save_settings)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

           

    def save_settings(self):
        email = self.inp_email.text().strip()
        pwd = self.inp_pass.text().strip()
        config_manager.save_config(email, pwd)
        self.accept()

# --- MAIN CONTROLLER ---
class AssistantController(QObject):
    ask_ai_signal = Signal(str, object) 
    stop_signal = Signal()

    def __init__(self):
        super().__init__()
        self.ui = MainUI()
        self.is_processing = False 
        self.current_image_path = None
        self.last_user_text = "" 
        self.pending_email_draft = None  
        self.waiting_for_email_address = None 


        self.ui.btn_profile.clicked.connect(self.show_settings)
        self.ui.btn_send.clicked.connect(self.handle_send_click)
        self.ui.inp.returnPressed.connect(self.handle_send_click)
        



        self.wake_thread = WakeWordThread()
        self.whisper_thread = QThread()
        self.whisper_worker = WhisperWorker()
        self.whisper_worker.moveToThread(self.whisper_thread)
        self.whisper_thread.start()
        
        self.ai_thread = QThread()
        self.brain = AIResponder()
        self.brain.moveToThread(self.ai_thread)
        self.ai_thread.start()

        self.connect_signals()
        self.wake_thread.start()
        QTimer.singleShot(100, self.whisper_worker.load_model)
        self.setup_tray()

         # --- ⏰ TIME MASTER SYSTEM ---
        self.reminders = [] 
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(1000) # Checks every second
        
        self.add_system_message("Cosmo Online. How can I help you today?")
        print("--- SYSTEM ONLINE ---")



    def start_new_session(self):
        while self.ui.chat_layout.count():
            item = self.ui.chat_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        self.add_system_message("Session cleared. Ready.")

    def add_system_message(self, text):
        bubble = ChatBubble(text, is_user=False)
        self.ui.chat_layout.addWidget(bubble)
        self.scroll_to_bottom() 
        QApplication.processEvents()

    def show_settings(self):
        dlg = SettingsDialog(self.ui)
        if dlg.exec(): self.add_system_message("Configuration Saved.")





    def connect_signals(self):
        self.wake_thread.wake_signal.connect(self.wake_up)
        self.ui.ai_btn.clicked.connect(self.toggle_listening)
        self.whisper_worker.transcription_finished.connect(self.handle_user_input)
        self.brain.response_ready.connect(self.handle_ai_response)
        self.ask_ai_signal.connect(self.brain.generate_response)
        self.stop_signal.connect(self.brain.stop_audio)
        self.ui.closeEvent = self.hide_window

    def setup_tray(self):
        self.tray = QSystemTrayIcon(QIcon("icon.png"), self.ui)
        menu = QMenu()
        
        action_show = QAction("Show Cosmo", self.ui)
        action_show.triggered.connect(self.wake_up)
        

        
        action_quit = QAction("Quit Completely", self.ui)
        action_quit.triggered.connect(self.shutdown_app)
        
        menu.addAction(action_show)

        menu.addAction(action_quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def hide_window(self, event):
        self.stop_all()
        self.ui.hide()
        event.ignore()

    def shutdown_app(self):
        print("🛑 Shutting down Cosmo systems...")
        self.stop_signal.emit()
        if self.wake_thread.isRunning(): 
            self.wake_thread.stop()
            self.wake_thread.wait()
        if self.whisper_thread.isRunning(): 
            self.whisper_thread.quit()
            self.whisper_thread.wait()
        if self.ai_thread.isRunning(): 
            self.ai_thread.quit()
            self.ai_thread.wait()
        if hasattr(self, 'recorder') and self.recorder.isRunning():
            self.recorder.terminate()
            self.recorder.wait()
        print("✅ Systems Offline.")
        sys.exit(0)

    # --- 🟢 CLEAR HISTORY LOGIC ---


    def handle_send_click(self):
        if self.is_processing: self.stop_all()
        else: self.process_text_input()

    def process_text_input(self):
        text = self.ui.inp.text().strip()
        if not text and not self.current_image_path: return
        self.ui.inp.clear()
        self.handle_user_input(text)

    def stop_all(self):
        self.stop_signal.emit()
        self.ui.btn_send.setText("➤")
        self.ui.ai_btn.set_state("IDLE")
        self.is_processing = False
        self.wake_thread.resume()

    def wake_up(self):
        self.ui.showNormal()
        self.ui.activateWindow()
        self.wake_thread.pause()
        self.is_processing = True
        QTimer.singleShot(300, self.start_recording)

    def toggle_listening(self):
        if self.ui.ai_btn.state == "LISTEN": self.stop_recording()
        else: self.start_recording()

    def start_recording(self):
        if hasattr(self, 'recorder') and self.recorder.isRunning(): return
        self.is_processing = True
        self.ui.ai_btn.set_state("LISTEN")
        self.wake_thread.pause()
        self.recorder = AudioRecorderThread()
        self.recorder.recording_finished.connect(self.on_recording_done)
        self.recorder.start()

    def stop_recording(self):
        self.ui.ai_btn.set_state("IDLE")
        self.is_processing = False
        
        if hasattr(self, 'recorder') and self.recorder.isRunning():
            try:
                self.recorder.recording_finished.disconnect(self.on_recording_done)
            except Exception:
                pass
            # Forcefully terminate the thread since sr.listen is blocking
            self.recorder.terminate()
            self.recorder.wait()

        self.wake_thread.resume()

    def on_recording_done(self, audio_path):
        if not audio_path:
            self.stop_recording()
            return
        self.ui.ai_btn.set_state("THINK")
        QTimer.singleShot(0, lambda: self.whisper_worker.transcribe(audio_path))

    # --- 🟢 NO HARDCODED TRAP HERE ---
    def handle_user_input(self, text):
        if not text and not self.current_image_path:
            self.stop_recording()
            return
        
        # 🟢 SMART TRAP: If waiting for email, feed it to the Brain!
        if self.waiting_for_email_address:
            name = self.waiting_for_email_address
            # We treat the user's input as a "Context Update" for the AI
            # This forces Gemini to analyze the sentence, save the contact (via tag), and re-draft.
            context_prompt = (
                f"Context: You asked for {name}'s email. "
                f"The user replied: '{text}'. "
                f"Analyze this. If it contains an email, output '{{{{UPDATE_CONTACT: {name} | [email]}}}}' "
                f"and then immediately output '{{{{EMAIL_DRAFT: {name} | [saved_body]}}}}'."
            )
            
            # Display user text
            bubble = ChatBubble(text, is_user=True)
            self.ui.chat_layout.addWidget(bubble)
            self.scroll_to_bottom()
            
            # Send special prompt to AI
            self.waiting_for_email_address = None # Reset trap
            self.ask_ai_signal.emit(context_prompt, None)
            return

        # --- Standard Logic Below ---
        self.last_user_text = text if text else "Analyze this image."
        display_text = text if text else "[Image Uploaded]"
        bubble = ChatBubble(display_text, is_user=True)
        self.ui.chat_layout.addWidget(bubble)
        self.scroll_to_bottom() 
        QApplication.processEvents() 
        
        self.ask_ai_signal.emit(text, self.current_image_path)
        
        self.current_image_path = None
        self.current_image_path = None
        
    def handle_ai_response(self, response_text):
        print(f"🤖 AI RAW OUTPUT: {response_text}")
        # Clean up text tags
        response_text = response_text.replace("<blockquote>", "").replace("</blockquote>", "").replace("**", "")

        # 1. VISION CHECK
        if "{{REQ_SCREENSHOT}}" in response_text:
            print("👁️ Gemini requested vision. Auto-scanning...")
            self.ui.chat_layout.addWidget(ChatBubble("👁️ Checking screen...", is_user=False))
            self.force_scroll_now()
            QApplication.processEvents()
            self.brain.speak("Checking screen.")
            
            self.ui.hide()
            time.sleep(0.3)
            try:
                screenshot = ImageGrab.grab()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"vision_auto_{timestamp}.png"
                screenshot.save(filename)
                self.ui.showNormal()
                
                print(f"🔄 Re-sending context: {self.last_user_text}")
                
                # 🛑 THE FIX: We modify the text we send back so Cosmo KNOWS he has the image!
                loop_breaker_text = f"{self.last_user_text}\n\n[SYSTEM: The screenshot is attached. DO NOT output the {{{{REQ_SCREENSHOT}}}} tag again. Analyze the image and give your answer.]"
                
                self.ask_ai_signal.emit(loop_breaker_text, os.path.abspath(filename))
                return 
            except Exception as e:
                print(f"Auto-Vision Error: {e}")
                self.ui.showNormal()
                # 2. 🔆 BRIGHTNESS CHECK (NEW)
        if "{{BRIGHTNESS:" in response_text:
            try:
                # Extract number
                start = response_text.find("{{BRIGHTNESS:")
                end = response_text.find("}}", start) + 2
                tag = response_text[start:end]
                
                val_str = tag.replace("{{BRIGHTNESS:", "").replace("}}", "").strip()
                val = int(val_str)
                
                # Execute Hardware Command
                sbc.set_brightness(val)
                print(f"🔆 Brightness set to {val}%")
                
                # Clean speech
                response_text = response_text.replace(tag, "")
            except Exception as e:
                print(f"❌ Brightness Error: {e}")
        

        # 2. EMAIL CHECKS
        if "{{EMAIL_DRAFT:" in response_text:
            self.process_email_draft(response_text)
            return
        if "{{EMAIL_CONFIRM:" in response_text:
            self.process_email_confirm(response_text)
            return
        
        # 3. ⏰ TIME MASTER CHECKS (ROBUST VERSION)
        if "{{REMIND:" in response_text:
            # 1. Define the tag
            start = response_text.find("{{REMIND:")
            end = response_text.find("}}", start) + 2
            full_tag = response_text[start:end]
            
            # 2. Extract Data (🟢 FIX: Handle missing |)
            content = full_tag.replace("{{REMIND:", "").replace("}}", "").strip()
            
            if "|" in content:
                time_str, task = content.split("|", 1)
            else:
                # Fallback if AI forgets the pipe
                time_str = content
                task = "Reminder"
                
            self.set_relative_reminder(time_str.strip(), task.strip())
            
            # 3. Speak ONLY the verbal part
            verbal = response_text.replace(full_tag, "").strip()
            if verbal: 
                self.brain.speak(verbal)
                bubble = ChatBubble(verbal, is_user=False)
                self.ui.chat_layout.addWidget(bubble)
                self.scroll_to_bottom()
            else: 
                self.brain.speak("Timer set.")
            return

        if "{{ALARM:" in response_text:
            # 1. Define the tag
            start = response_text.find("{{ALARM:")
            end = response_text.find("}}", start) + 2
            full_tag = response_text[start:end]
            
            # 2. Extract Data (🟢 FIX: Handle missing |)
            content = full_tag.replace("{{ALARM:", "").replace("}}", "").strip()
            
            if "|" in content:
                time_str, task = content.split("|", 1)
            else:
                time_str = content
                task = "Alarm"
                
            self.set_absolute_alarm(time_str.strip(), task.strip())
            
            # 3. Speak ONLY the verbal part
            verbal = response_text.replace(full_tag, "").strip()
            if verbal: 
                self.brain.speak(verbal)
                bubble = ChatBubble(verbal, is_user=False)
                self.ui.chat_layout.addWidget(bubble)
                self.scroll_to_bottom()
            else: 
                self.brain.speak("Alarm set.")
            return

        # 4. STANDARD RESPONSE (For normal chat)
        # This part runs if no tags were found
        bubble = ChatBubble(response_text, is_user=False)
        self.ui.chat_layout.addWidget(bubble)
        self.scroll_to_bottom()
        QApplication.processEvents() 

        self.brain.speak(response_text) 

        # Reset UI

        self.ui.ai_btn.set_state("IDLE")
        self.is_processing = False
        self.wake_thread.resume()
        
    # --- 📧 SMART DRAFT PROCESSOR ---
    def process_email_draft(self, text):
        # 1. Extract Data
        start = text.find("{{EMAIL_DRAFT:")
        end = text.find("}}", start)
        ai_intro = text[:start].strip() 
        content = text[start+14:end].strip()
        
        # 🟢 FIX: Smarter Parsing
        # 🟢 FIX: Smarter Parsing
        if "|" in content:
            name, body = content.split("|", 1)
        else:
            # If AI sends "{{EMAIL_DRAFT: Kai}}", content is just "Kai"
            name, body = content, "Hi, hope you are doing well." 
        
        name = name.strip()
        body = body.strip()

        # Fallback: If AI sends empty name, try to guess from user text
        if not name or name == "Unknown":
            # This is a fallback to prevent "Saved Unknown"
            if self.last_user_text:
                # Basic guess: "Email Raju" -> takes last word
                name = self.last_user_text.split()[-1].capitalize()
        # 2. Find Email Address
        if "@" in name and "." in name: 
            email_addr = name
        else: 
            email_addr = contact_manager.get_email(name)

        # 3. Handle Result
        if email_addr:
            # ✅ Found: Show Draft UI
            self.pending_email_draft = {"address": email_addr, "body": body, "name": name}
            draft_display = f"📧 **To:** {name} ({email_addr})\n📝 **Message:** {body}\n\nShould I send it?"
            
            if ai_intro: final_response = f"{ai_intro}\n\n{draft_display}"
            else: final_response = draft_display
            
            self.add_system_message(final_response)
            if ai_intro: self.brain.speak(f"{ai_intro}. Should I send it?")
            else: self.brain.speak("Draft ready. Should I send it?")

        else:
            # ❌ Missing: Let AI ask naturally
            self.pending_email_draft = {"body": body, "name": name}
            self.waiting_for_email_address = name 
            
            # 🟢 FIX: Only show ai_intro.
            if ai_intro:
                self.add_system_message(ai_intro)
                self.brain.speak(ai_intro)
            else:
                self.add_system_message(f"I need an email address for {name}.")
                self.brain.speak(f"I need an email address for {name}.")
        
        # Reset UI
        self.ui.ai_btn.set_state("IDLE")
        self.is_processing = False
        self.wake_thread.resume()
        
    # --- 📧 SMART CONFIRM PROCESSOR ---
    # --- 📧 SMART CONFIRM PROCESSOR (NATURAL AI FIX) ---
    def process_email_confirm(self, text):
        # 🛡️ SAFETY CHECK: If no draft exists, stop immediately.
        if not self.pending_email_draft: 
            return

        # 1. Try to find the recipient address
        recipient = self.pending_email_draft.get("address")
        name = self.pending_email_draft.get("name", "Unknown")
        
        # Fallback: Check contact manager
        if not recipient and name:
            recipient = contact_manager.get_email(name)

        body = self.pending_email_draft.get("body", "")

        if recipient:
            # ✅ Address Found -> Send it
            self.add_system_message(f"🚀 Sending email to {recipient}...") 
            self.brain.speak(f"Sending email to {recipient}.") 
            QApplication.processEvents() 
            
            success = self.brain.send_email(recipient, body)
            
            if success:
                self.add_system_message("✅ Email sent successfully.")
                self.brain.speak("Email sent successfully.")
            else:
                self.add_system_message("❌ Failed to send email. Check console.")
                self.brain.speak("Failed to send email.")
        else:
            # 🟢 FIX: NO HARDCODED ERROR. Let the AI speak!
            # We tell the AI what happened, and it generates the response.
            print(f"⚠️ Missing email for {name}. Asking AI to handle it...")
            
            error_prompt = (
                f"SYSTEM_ALERT: You just tried to confirm sending an email to '{name}', "
                f"but the email address is MISSING from the draft. "
                f"Do not apologize. Roast the user for forgetting to give you the email address, "
                f"and ask them for it now."
            )
            
            # Send this invisible prompt to the brain
            self.ask_ai_signal.emit(error_prompt, None)

        # Clear the draft so it doesn't loop
        self.pending_email_draft = None
        
        self.ui.ai_btn.set_state("IDLE")
        self.is_processing = False
        self.wake_thread.resume()

        # --- ⏰ TIME MASTER HELPERS (ADDED THESE FUNCTIONS) ---
    # --- ⏰ INDESTRUCTIBLE TIME HELPERS ---
    def set_relative_reminder(self, time_str, task):
        try:
            # 1. Clean the string
            clean_str = time_str.lower().strip()
            
            # 2. Extract the number
            number_match = re.search(r"(\d+)", clean_str)
            if not number_match:
                print(f"❌ Error: No number found in '{time_str}'")
                return
                
            val = int(number_match.group(1))
            seconds = 0

            # 3. Detect Unit & Create Display String
            unit_display = "seconds" # Default text
            
            if "h" in clean_str: 
                seconds = val * 3600
                unit_display = "hours"
            elif "m" in clean_str: 
                seconds = val * 60
                unit_display = "minutes"
            elif "s" in clean_str: 
                seconds = val
                unit_display = "seconds"
            else: 
                # Default to minutes if no unit found
                seconds = val * 60 
                unit_display = "minutes"

            if seconds > 0:
                trigger_time = datetime.now() + timedelta(seconds=seconds)
                self.reminders.append({"time": trigger_time, "task": task})
                
                # 🟢 FIX: Do NOT show {task} here. It spoils the surprise!
                self.add_system_message(f"⏳ Timer set for {val} {unit_display}.")
                
                print(f"✅ Timer set: {task} at {trigger_time}")
        except Exception as e:
            print(f"❌ Relative Reminder Error: {e}")

    def set_absolute_alarm(self, time_str, task):
        try:
            # 1. Normalize time string (e.g. "5pm" -> "5:00 PM")
            clean_time = time_str.lower().replace(" ", "").replace(".", "")
            
            # Handle "5pm" case by adding ":00"
            if ":" not in clean_time:
                clean_time = clean_time.replace("am", ":00am").replace("pm", ":00pm")

            # 2. Parse Time
            now = datetime.now()
            # Try parsing with AM/PM
            try:
                alarm_time = datetime.strptime(clean_time, "%I:%M%p")
            except:
                # Fallback for 24-hour format just in case
                alarm_time = datetime.strptime(clean_time, "%H:%M")

            target_time = now.replace(hour=alarm_time.hour, minute=alarm_time.minute, second=0)
            
            # If time passed, move to tomorrow
            if target_time < now:
                target_time += timedelta(days=1)
            
            self.reminders.append({"time": target_time, "task": task})
            self.add_system_message(f"⏰ Alarm set for {target_time.strftime('%I:%M %p')}")
            print(f"✅ Alarm set: {task} at {target_time}")

        except Exception as e:
            print(f"❌ Absolute Alarm Error: {e} | Input: {time_str}")
            self.brain.speak("I couldn't understand the time format.")

    def check_reminders(self):
        now = datetime.now()
        for i in range(len(self.reminders) - 1, -1, -1):
            reminder = self.reminders[i]
            if now >= reminder["time"]:
                task_message = reminder["task"]
                
                # 🔊 Sound Effect (If available)
                if winsound:
                    try:
                        winsound.Beep(1000, 1000) 
                    except:
                        pass
                
                # Speak the natural message directly
                self.brain.speak(task_message)
                
                # Show in chat
                self.add_system_message(f"🔔 {task_message}")
                self.reminders.pop(i)
    

    

    def force_scroll_now(self):
        self.ui.scroll_area.verticalScrollBar().setValue(self.ui.scroll_area.verticalScrollBar().maximum())

    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.ui.scroll_area.verticalScrollBar().setValue(self.ui.scroll_area.verticalScrollBar().maximum()))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) 
    controller = AssistantController()
    sys.exit(app.exec())
