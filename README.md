# J.A.R.V.I.S
### Just A Rather Very Intelligent System

> *"Good evening, sir. All systems online."*

A full-featured personal AI assistant for Windows, inspired by Iron Man's JARVIS. Built with Python, Multi-Provider AI (Groq / Gemini / Ollama / Claude), PyQt5 HUD interface, and real-time voice interaction.

---

## Features

| Module | Capabilities |
|--------|-------------|
| 🧠 **Brain** | Multi-provider intelligence: **Groq** (Free Llama 3.3 70B), **Gemini** (Free Gemini 1.5/2.0), **Ollama** (100% offline local), and **Claude** |
| 🎤 **Voice & TTS** | Always-on wake-word listener ("Hey JARVIS" / "Wakeup JARVIS"), Google STT, thread-safe `pyttsx3` / ElevenLabs TTS |
| 🖥️ **PC Control** | Launch apps, file search & opening, screenshot + AI vision (Gemini/Claude), volume & brightness control, keyboard typing |
| 🔍 **Research** | DuckDuckGo web search, webpage summarization, and PDF / text document analysis |
| 💻 **Code Assistant** | Generate, debug, explain, optimize, and test code in any programming language |
| 🧠 **Memory** | Persistent JSON memory store — remembers facts, notes, and conversation history across sessions |
| 🎨 **HUD UI** | Iron Man-inspired PyQt5 dark interface with animated arc reactor waveform and real-time conversation stream |
| 🔔 **System Tray Listener** | Background tray app to launch JARVIS instantly when saying "Wakeup JARVIS" |

---

## Quick Start

### 1. Prerequisites
- Python 3.10+ (Python 3.10, 3.11, 3.12, 3.13, or 3.14 on Windows 10/11)
- Free API Key from [Groq Console](https://console.groq.com/) or [Google AI Studio](https://aistudio.google.com/app/apikey) (or local [Ollama](https://ollama.com/))

### 2. Setup (one-time)
Run the setup script in PowerShell:
```powershell
cd d:\JARVIS
.\setup.ps1
```

### 3. Configure API Key
Edit `.env`:
```env
AI_PROVIDER=groq
GROQ_API_KEY=your_free_groq_api_key_here
```

### 4. Run JARVIS

- **One-Click Batch File:**
  - Double-click `START_JARVIS.bat` to launch the GUI
  - Double-click `START_LISTENER.bat` for background always-on voice wake-word listening
- **Or via Command Line:**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  python main.py           # Full GUI HUD + Voice enabled
  python main.py --cli     # Text-only CLI mode
  python listener.py       # Background system tray listener
  ```

---

## Example Voice & Text Commands

```
"Hey JARVIS, open Chrome"
"Search for latest developments in quantum computing"
"Take a screenshot and describe what's on screen"
"Write me a Python web scraper and save it to scraper.py"
"Volume up" / "Mute" / "Brightness 80"
"Remember that my meeting with Tony is at 3 PM tomorrow"
"What did I tell you about my meeting?"
"Summarize the PDF at C:\docs\report.pdf"
"Debug this code: [paste code]"
```

---

## Project Structure

```
d:/JARVIS/
├── main.py              # Main orchestrator & CLI/GUI entry point
├── brain.py             # Multi-provider AI reasoning (Groq/Gemini/Ollama/Claude)
├── voice.py             # Dedicated TTS worker thread + STT speech recognition
├── listener.py          # Always-on background tray listener (wake up JARVIS)
├── pc_control.py        # Windows system control, app launcher, screenshots & vision
├── research.py          # DuckDuckGo search + URL & PDF reader/summarizer
├── memory.py            # Persistent JSON memory store
├── code_assistant.py    # Code generation, debugging, explanation, & testing
├── ui.py                # Iron Man Arc Reactor PyQt5 HUD interface
├── pyaudio_shim.py      # PyAudioWPatch shim for Python 3.14 Windows compatibility
├── config.py            # Central environment & configuration loader
├── debug_listener.py    # Real-time microphone audio & wake-word diagnostics
├── diagnose_voice.py    # Hardware microphone & STT diagnostic utility
├── requirements.txt     # Complete Python dependencies
├── setup.ps1            # Automated PowerShell setup script
├── START_JARVIS.bat     # One-click JARVIS GUI launcher
├── START_LISTENER.bat   # One-click background voice listener launcher
└── .env.example         # Configuration template
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY / GEMINI_API_KEY missing` | Check your `.env` file and ensure your API key is provided |
| Microphone not detected | Ensure your mic is default in Windows Sound Settings and test with `python diagnose_voice.py` |
| PyAudio errors on Windows | Handled automatically via `PyAudioWPatch` and `pyaudio_shim.py` |
| Background Tray Icon | Run `python listener.py` or double-click `START_LISTENER.bat` |
| CLI / GUI Mode | Use `python main.py --cli` for lightweight terminal interaction |
