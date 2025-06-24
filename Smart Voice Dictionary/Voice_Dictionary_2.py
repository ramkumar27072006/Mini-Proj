import speech_recognition as sr
import pyttsx3
from nltk.corpus import wordnet as wn
import nltk

# Download WordNet once if not already downloaded
nltk.download('wordnet')

# Initialize TTS engine
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def get_word_details(word):
    synsets = wn.synsets(word)
    if not synsets:
        return None

    definitions = [s.definition() for s in synsets]
    examples = []
    synonyms = set()
    antonyms = set()

    for syn in synsets:
        for ex in syn.examples():
            if ex:
                examples.append(ex)
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", " "))
            if lemma.antonyms():
                antonyms.add(lemma.antonyms()[0].name().replace("_", " "))

    return {
        "definitions": definitions[:2],
        "synonyms": list(synonyms)[:5],
        "antonyms": list(antonyms)[:5],
        "examples": examples[:1]
    }

def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Speak now (e.g., 'Define love')...")
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio)
        print(f"You said: {command}")
        return command.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return None
    except sr.RequestError:
        speak("Speech service is unavailable.")
        return None

def main():
    speak("Voice dictionary ready. Say 'define' or 'what is' followed by a word. Say 'stop' or 'thank you' to exit.")

    while True:
        query = listen_command()

        if query is None:
            continue

        query = query.strip().lower()  # Normalize text for comparison

        # Check for exit keywords early
        stop_keywords = ["stop", "thank you", "thanks", "thank", "enough"]
        if any(kw in query for kw in stop_keywords):
            speak("Thank you! Exiting voice dictionary.")
            break

        trigger_phrases = ["define", "meaning of", "what is", "what's", "give me the meaning of"]
        matched = False
        word = ""

        for phrase in trigger_phrases:
            if phrase in query:
                word = query.replace(phrase, "").strip()
                matched = True
                break

        if matched and word:
            details = get_word_details(word)

            if not details:
                print(f"\n❌ No definition found for '{word}'.")
                speak(f"Sorry, I couldn't find the word {word}.")
                continue

            print(f"\n📚 Definition of '{word}':")
            speak(f"Definition of {word}")
            for d in details["definitions"]:
                print(f"• {d}")
                speak(d)

            if details["synonyms"]:
                print(f"\n🔁 Synonyms: {', '.join(details['synonyms'])}")
                speak("Synonyms are " + ", ".join(details["synonyms"]))

            if details["antonyms"]:
                print(f"\n↩️ Antonyms: {', '.join(details['antonyms'])}")
                speak("Antonyms are " + ", ".join(details["antonyms"]))

            if details["examples"]:
                print(f"\n📘 Example Sentence:")
                print(f"• {details['examples'][0]}")
                speak("For example,")
                speak(details["examples"][0])
        else:
            speak("Please say 'define' or 'what is' followed by a word.")

if __name__ == "__main__":
    main()
