
import speech_recognition as sr
import pyttsx3
import os
import subprocess
import shutil
import datetime
import requests
import time
import webbrowser
from urllib.parse import quote_plus

engine = pyttsx3.init('sapi5')
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

def speak(text):
    print("Assistant:", text)

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("Speech Error:", e)

    time.sleep(0.3)


def listen():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("\nListening...")

            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=7
            )

            command = recognizer.recognize_google(audio)

            print("You said:", command)
            return command.lower()

    except sr.WaitTimeoutError:
        print("No voice detected.")

    except sr.UnknownValueError:
        print("Sorry, I could not understand.")

    except sr.RequestError:
        speak("Speech recognition service is unavailable.")

    except OSError as e:
        print("Microphone Error:", e)

    return None


def tell_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    print(f"The current time is {current_time}")


def tell_weather():
    city = input("Enter your city: ")

    try:
        url = f"https://wttr.in/{city}?format=3"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        print(response.text)

    except requests.RequestException:
        print("Unable to get weather information.")


def open_chrome():
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    if os.path.exists(chrome):
        subprocess.Popen([chrome])
        print("Opening Google Chrome.")
    else:
        speak("Chrome is not installed.")


def open_notepad():
    subprocess.Popen(["notepad.exe"])
    print("Opening Notepad.")


def open_app(app_name):
    """Launch an installed app by executable name or Start Menu shortcut."""
    app_name = app_name.strip().strip('"')
    if not app_name:
        speak("Please say the name of the app to open.")
        return

    executable = shutil.which(app_name)
    if executable:
        subprocess.Popen([executable])
        speak(f"Opening {app_name}.")
        return

    # Find shortcuts in the standard Windows Start Menu locations.
    start_menu_dirs = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
    ]
    target = app_name.casefold()
    for folder in start_menu_dirs:
        if not os.path.isdir(folder):
            continue
        for root, _, files in os.walk(folder):
            for filename in files:
                if filename.casefold() in (target, target + ".lnk"):
                    os.startfile(os.path.join(root, filename))
                    speak(f"Opening {app_name}.")
                    return

    speak(f"I couldn't find an app named {app_name}.")


def shutdown():
    print("Do you really want to shut down your computer? Say yes or no.")

    answer = listen()

    if answer and answer.strip() in ["yes", "yes please"]:
        print("Shutting down the computer.")
        subprocess.run(["shutdown", "/s", "/t", "10"], check=False)

    else:
        print("Shutdown cancelled.")


conversation = []


def ask_ai(question):
    """Answer general questions using the OpenAI API when configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        speak("I can do my built-in tasks, but general questions need an OPENAI_API_KEY.")
        return

    conversation.append({"role": "user", "content": question})
    messages = [
        {"role": "system", "content": (
            "You are a concise, helpful voice assistant. Answer clearly. "
            "Do not claim to have performed actions on the user's computer."
        )}
    ] + conversation[-12:]

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": messages},
            timeout=30,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"].strip()
        conversation.append({"role": "assistant", "content": answer})
        speak(answer)
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        speak("I couldn't get an answer right now. Please try again.")


def show_help():
    speak("You can ask for the time or weather, open Chrome or Notepad, search the web, or shut down. I can also answer general questions when an API key is configured.")


print("Hello! I am your voice assistant. How can I help you today?")
while True:
    command = listen()

    if command:
        if any(word in command for word in ("help", "what can you do", "your tasks")):
            show_help()

        elif any(word in command for word in ("time", "clock")):
            tell_time()

        elif "weather" in command:
            tell_weather()

        elif "open chrome" in command or "launch chrome" in command:
            open_chrome()

        elif "open notepad" in command or "launch notepad" in command:
            open_notepad()

        elif command.startswith("open ") or command.startswith("launch "):
            app_name = command.removeprefix("open ").removeprefix("launch ").strip()
            open_app(app_name)

        elif command.startswith("search for ") or command.startswith("google "):
            query = command.removeprefix("search for ").removeprefix("google ").strip()
            if query:
                webbrowser.open("https://www.google.com/search?q=" + quote_plus(query))
                speak("Here are the search results.")
            else:
                speak("What would you like me to search for?")

        elif "shutdown" in command:
            shutdown()

        elif "exit" in command or "quit" in command:
            print("Goodbye!")
            break

        else:
            ask_ai(command)