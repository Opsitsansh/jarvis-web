import pyttsx3
import speech_recognition
import pywhatkit
import wikipedia
import webbrowser
from wikipedia.exceptions import DisambiguationError, PageError

# ---------------------------
# 🔊 Text-to-Speech Setup
# ---------------------------
engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)
engine.setProperty("rate", 170)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

# ---------------------------
# 🎤 Voice Command Handler
# ---------------------------
def takeCommand():
    r = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as source:
        print("Listening.....")
        r.pause_threshold = 1
        r.energy_threshold = 300
        audio = r.listen(source, 0, 4)
    try:
        print("Understanding..")
        query = r.recognize_google(audio, language='en-in')
        print(f"You Said: {query}\n")
    except Exception:
        print("Say that again")
        return "None"
    return query

# ---------------------------
# 🔍 Google Search Function
# ---------------------------
def searchGoogle(query):
    if "google" in query:
        query = query.replace("jarvis", "").replace("google search", "").replace("google", "").strip()
        speak(f"Searching Google for {query}")
        pywhatkit.search(query)
        speak("Here are the results.")

# ---------------------------
# ▶️ YouTube Search & Play
# ---------------------------
def searchYoutube(query):
    if "youtube" in query:
        query = query.replace("youtube search", "").replace("youtube", "").replace("jarvis", "").strip()
        speak(f"Searching YouTube for {query}")
        web = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(web)
        pywhatkit.playonyt(query)
        speak("Playing on YouTube, Sir.")

# ---------------------------
# 📚 Wikipedia Summary Lookup
# ---------------------------
def searchWikipedia(query):
    if "wikipedia" in query:
        query = query.lower().replace("wikipedia", "").replace("search wikipedia", "").replace("jarvis", "").strip()

        if query == "":
            speak("What should I search on Wikipedia?")
            return

        # Fix common name spacing errors
        known_fixes = {
            "m s dhoni": "MS Dhoni",
            "a p j abdul kalam": "APJ Abdul Kalam",
            "narendra modi": "Narendra Modi",
            "virat kohli": "Virat Kohli"
        }
        if query in known_fixes:
            query = known_fixes[query]

        speak(f"Searching Wikipedia for {query}...")

        try:
           result = wikipedia.summary(query, sentences=2)
           speak("According to Wikipedia...")
           print(result.encode('utf-8', errors='replace').decode())  # ✅ FIXED LINE
           speak(result)


        except DisambiguationError as e:
            speak(f"{query} is ambiguous. Try being more specific.")
            print("Suggestions:")
            for option in e.options[:5]:
                print(f"- {option}")

        except PageError:
            speak(f"Sorry, I couldn't find a page for {query}. Please try something else.")

        except Exception as e:
            speak("An unexpected error occurred while searching Wikipedia.")
            print("Error:", e)
