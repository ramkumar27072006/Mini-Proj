# 🧮 Smart Voice Dictionary

## Overview

Smart Voice Dictionary is a Python-based voice assistant that listens to your spoken commands to define English words. It provides:

- **✅ Definitions** (top 2)
- **✅ Synonyms** (up to 5)
- **✅ Antonyms** (up to 5)
- **✅ Example sentence** (1)

It uses speech recognition and text-to-speech to interact naturally.

---

## 📦Features

- Voice commands like:
  - "Define happiness"
  - "What's courage"
  - "Give me the meaning of empathy"
- Speaks back the meaning, synonyms, antonyms, and example sentence.
- Gracefully exits when you say:
  - "Stop", "Thanks", etc.

---

## 🛠️ Technologies Used

- Python 3.x
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) — for speech-to-text
- [pyttsx3](https://pypi.org/project/pyttsx3/) — for text-to-speech
- [NLTK](https://www.nltk.org/) (WordNet corpus) — for word definitions, synonyms, antonyms, examples

---

## 🚀 Installation

1. Clone or download this repository.

2. Install required Python packages:

```bash
pip install nltk pyttsx3 SpeechRecognition pyaudio
