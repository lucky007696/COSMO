# Cosmo AI Assistant

Cosmo is a Windows desktop AI assistant that provides AI responses, speech recognition, text-to-speech, application launching, file management, email automation, and system controls.

## Features

- Gemini AI responses
- Offline speech recognition with Faster-Whisper
- Wake-word detection
- Text-to-speech using Piper and Windows voices
- Windows application launching
- File creation, deletion, moving, and renaming
- Email automation
- WhatsApp automation
- YouTube and Spotify controls
- Battery and system information
- PySide6 graphical interface

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or 3.11
- Git
- Working microphone
- Internet connection
- Gemini API key
- Gmail App Password for email features
- Optional NVIDIA GPU for faster speech recognition

## Installation

Open PowerShell in the project directory:

```powershell
cd "C:\Users\naray\assisstent new"
```

Create a virtual environment:

```powershell
py -3.11 -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install the required libraries:

```powershell
pip install PySide6 google-generativeai faster-whisper piper-tts PyAudio requests pygame pyttsx3 Pillow python-dotenv SpeechRecognition numpy pywin32
```

For NVIDIA GPU support, optionally install:

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-runtime-cu12
```

If PyAudio installation fails:

```powershell
pip install pipwin
pipwin install pyaudio
```

## API Configuration

Create a file named `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Get a Gemini API key from:

https://aistudio.google.com/app/apikey

Never share or commit this key.

## Gmail Configuration

To use email features:

1. Enable two-factor authentication on your Gmail account.
2. Create a Gmail App Password.
3. Open the application settings.
4. Save your Gmail address and App Password.

Do not use your normal Gmail password.

## Project Structure

```text
assisstent new/
├── backend.py
├── main.py
├── automation.py
├── contact_manager.py
├── config_manager.py
├── file_ops.py
├── memory.py
├── system_tools.py
├── contacts.json
├── .env
├── .gitignore
└── README.md
```

The local Python modules required by `backend.py` include:

- `automation.py`
- `contact_manager.py`
- `config_manager.py`
- `file_ops.py`
- `memory.py`
- `system_tools.py`

## Running the Application

Activate the virtual environment:

```powershell
cd "C:\Users\naray\assisstent new"
.\.venv\Scripts\Activate.ps1
```

Start the application:

```powershell
python main.py
```

## Testing the Installation

Test the installed libraries:

```powershell
python -c "import PySide6, faster_whisper, piper, pyaudio, pygame, pyttsx3, PIL, speech_recognition, numpy; print('Dependencies installed successfully')"
```

Check the Gemini API key:

```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API key configured:', bool(os.getenv('GEMINI_API_KEY')))"
```

## Troubleshooting

### Microphone problems

- Check Windows microphone permissions.
- Confirm that a microphone is connected.
- Reinstall PyAudio.
- Close other applications using the microphone.

### Gemini connection problems

- Confirm that the `.env` file exists.
- Check that `GEMINI_API_KEY` is valid.
- Check your internet connection.
- Check your Gemini API quota.

### CUDA or GPU problems

The application can use CPU mode if CUDA is unavailable. CPU mode may be slower.

Check the NVIDIA packages:

```powershell
pip show nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-runtime-cu12
```

### Missing local modules

Ensure all project Python files are located in the same directory as `backend.py`.

### Text-to-speech problems

- Confirm that a Windows speech voice is installed.
- Check your computer's audio output.
- Restart the application after installing voice packages.

## Security Notes

Never publish:

- `.env`
- Gemini API keys
- Gmail App Passwords
- Personal contact information
- `contacts.json`

Review file deletion and application launching commands carefully.

## License

Add the project license information here.