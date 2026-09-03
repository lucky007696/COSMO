# system_tools.py
import psutil
import time
from ctypes import windll
import subprocess

# --- 🛠️ VIRTUAL KEYBOARD CONTROLLER (Bypasses Broken Drivers) ---
def press_key(vk_code):
    """Simulates a key press using Windows Core API"""
    windll.user32.keybd_event(vk_code, 0, 0, 0) # Press
    windll.user32.keybd_event(vk_code, 0, 2, 0) # Release

def set_volume(level):
    """Sets volume by simulating key presses. Reliable fallback."""
    try:
        level = max(0, min(100, int(level)))
        
        # 1. Reset Volume to 0 (Press VolDown 50 times fast)
        # Windows usually changes volume by 2% per key press.
        # So 50 presses guarantees we hit 0 from anywhere.
        for _ in range(50):
            press_key(0xAE) # VK_VOLUME_DOWN
            
        # 2. Raise to Target (Press VolUp X/2 times)
        # Example: To get 50%, we need 25 presses (25 * 2% = 50%)
        presses_needed = int(level / 2)
        
        for _ in range(presses_needed):
            press_key(0xAF) # VK_VOLUME_UP
            
        print(f"   🔊 SUCCESS: Volume set to {level}% (Virtual)")
        return True

    except Exception as e:
        print(f"   ⚠️ VOLUME ERROR: {e}")
        return False
    

# --- 🔆 BRIGHTNESS CONTROL (FAST BACKGROUND VERSION) ---
def set_brightness(level):
    """Sets screen brightness natively using Windows PowerShell in the background."""
    try:
        level = max(0, min(100, int(level)))
        
        cmd = f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})'
        
        # ⚡ SPEED FIX: We use Popen instead of run. 
        # Popen fires the command in the background and INSTANTLY moves to the next line.
        # This prevents Cosmo from freezing while Windows changes the screen.
        subprocess.Popen(
            ["powershell", "-Command", cmd], 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        print(f"   🔆 SUCCESS: Brightness command sent: {level}%")
        return True
        
    except Exception as e:
        print(f"   ⚠️ BRIGHTNESS ERROR: {e}")
        return False

# --- 🔋 BATTERY STATUS ---
def get_battery():
    try:
        battery = psutil.sensors_battery()
        if battery:
            plugged = "Charging" if battery.power_plugged else "Discharging"
            return f"{battery.percent}% ({plugged})"
        return "Unknown"
    except: return "Unavailable"