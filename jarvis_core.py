import ast
import datetime as dt
import os
import platform
import random
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

import requests

try:
    import pyttsx3
except ImportError:  # pragma: no cover - optional dependency
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - optional dependency
    sr = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None


WEB_APPS = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "wikipedia": "https://www.wikipedia.org",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chat.openai.com",
    "openai": "https://openai.com",
    "spotify": "https://open.spotify.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.in",
}

WEB_ALTERNATIVES = {
    "chrome": ("Google", "https://www.google.com"),
    "notepad": ("Online Notepad", "https://anotepad.com"),
    "paint": ("Photopea", "https://www.photopea.com"),
    "calculator": ("Calculator", "https://www.google.com/search?q=calculator"),
    "cmd": ("Command Line Docs", "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands"),
    "command prompt": ("Command Line Docs", "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands"),
    "powershell": ("PowerShell Docs", "https://learn.microsoft.com/en-us/powershell/"),
    "vscode": ("VS Code Web", "https://vscode.dev"),
    "vs code": ("VS Code Web", "https://vscode.dev"),
}

DESKTOP_ONLY_APPS = {
    "chrome",
    "notepad",
    "paint",
    "calculator",
    "cmd",
    "command prompt",
    "powershell",
    "vscode",
    "vs code",
}

KNOWN_CITIES = {
    "agra",
    "ahmedabad",
    "ajmer",
    "amritsar",
    "bengaluru",
    "bangalore",
    "bhopal",
    "chandigarh",
    "chennai",
    "coimbatore",
    "dehradun",
    "delhi",
    "faridabad",
    "ghaziabad",
    "goa",
    "gurgaon",
    "guwahati",
    "hyderabad",
    "indore",
    "jaipur",
    "jammu",
    "jodhpur",
    "kanpur",
    "kochi",
    "kolkata",
    "lucknow",
    "ludhiana",
    "mangalore",
    "meerut",
    "mumbai",
    "mysore",
    "nagpur",
    "nashik",
    "noida",
    "patna",
    "pune",
    "raipur",
    "ranchi",
    "shimla",
    "srinagar",
    "surat",
    "thane",
    "udaipur",
    "vadodara",
    "varanasi",
    "vijayawada",
    "visakhapatnam",
}

MOTIVATION_LINES = (
    "Systems stable. Keep building.",
    "Momentum is on your side today.",
    "Focus mode engaged. One step at a time.",
    "You bring the mission. I will handle the routine.",
    "Signal is clean. Let us ship something good.",
)


@dataclass
class CommandResult:
    response: str
    action: Optional[str] = None
    payload: Optional[dict] = None


class SafeEvaluator(ast.NodeVisitor):
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.FloorDiv,
    )

    def visit(self, node):
        if not isinstance(node, self.allowed_nodes):
            raise ValueError("Unsupported expression")
        return super().visit(node)

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if not isinstance(node.value, (int, float)):
            raise ValueError("Only numbers are allowed")
        return node.value

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            return left**right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        raise ValueError("Unsupported operator")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError("Unsupported unary operator")


class JarvisAssistant:
    def __init__(self) -> None:
        self.voice_engine = self._init_tts()
        self.ai_client = self._init_ai_client()

    def _init_tts(self):
        if pyttsx3 is None:
            return None
        try:
            engine = pyttsx3.init("sapi5")
            voices = engine.getProperty("voices")
            if voices:
                engine.setProperty("voice", voices[0].id)
            engine.setProperty("rate", 170)
            return engine
        except Exception:
            return None

    def _init_ai_client(self):
        if OpenAI is None:
            return None
        if not os.getenv("OPENAI_API_KEY"):
            return None
        try:
            return OpenAI()
        except Exception:
            return None

    def speak(self, text: str) -> None:
        if self.voice_engine is None:
            return
        try:
            self.voice_engine.say(text)
            self.voice_engine.runAndWait()
        except Exception:
            pass

    def take_voice_command(self) -> Optional[str]:
        if sr is None:
            return None
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening...")
                recognizer.pause_threshold = 1
                recognizer.energy_threshold = 300
                audio = recognizer.listen(source, timeout=4, phrase_time_limit=6)
            print("Understanding...")
            return recognizer.recognize_google(audio, language="en-in")
        except Exception:
            return None

    def run_console(self) -> None:
        self.speak("Jarvis is ready.")
        print("Jarvis is ready. Type a command, or press Enter to try voice input.")
        while True:
            typed = input("You: ").strip()
            command = typed or self.take_voice_command()
            if not command:
                print("Jarvis: I couldn't hear you. Please type your command.")
                continue
            result = self.handle_command(command)
            print(f"Jarvis: {result.response}")
            self.speak(result.response)
            if result.action == "exit":
                break

    def get_status(self, memory: str = "", history_count: int = 0) -> dict:
        now = dt.datetime.now()
        return {
            "assistant": "online",
            "mode": "web",
            "ai_available": self.ai_client is not None,
            "voice_input": "browser-supported",
            "voice_output": "browser-supported",
            "platform": platform.system(),
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%A, %d %B %Y"),
            "memory": memory or "No memory stored",
            "motd": random.choice(MOTIVATION_LINES),
            "history_count": history_count,
            "capabilities": [
                "Open websites and search in new tabs",
                "Weather, news, time, and date",
                "Math, notes, motivation, dice, and coin flip",
                "Browser voice chat and spoken replies",
                "Optional real AI answers with API key",
                "Vercel-friendly web actions",
            ],
        }

    def handle_command(self, raw_command: str, client_state: Optional[dict] = None) -> CommandResult:
        state = client_state or {}
        memory = str(state.get("memory", "") or "").strip()
        history = state.get("history") or []
        settings = state.get("settings") or {}
        last_topic = self._infer_last_topic(history)

        command = raw_command.strip()
        if not command:
            return CommandResult("Please say or type a command.")

        normalized = command.lower().replace("jarvis", "").strip()
        normalized = " ".join(normalized.split())
        tokens = set(normalized.split())

        if normalized in {"exit", "quit", "stop", "go to sleep", "sleep"}:
            return CommandResult("Going to sleep. Call me anytime.", action="exit")

        if normalized in {"hello", "hi", "hey"}:
            return CommandResult("Hello. How can I help you?")

        if "how are you" in normalized:
            return CommandResult("I am doing well and ready to help.")

        if any(phrase in normalized for phrase in {"what is your name", "what's your name", "whats your name", "who are you"}):
            return CommandResult("I am Jarvis, your browser-based assistant.")

        if any(phrase in normalized for phrase in {"who made you", "who created you", "who built you"}):
            return CommandResult("I am part of your Jarvis project and I am here to help through this web control plane.")

        if "thank you" in normalized or normalized == "thanks":
            return CommandResult("You are welcome. Ready for the next command.")

        if normalized in {"bye", "goodbye"}:
            return CommandResult("Goodbye. I will be here when you need me.")

        if "status" in normalized or "system report" in normalized:
            status = self.get_status(memory=memory, history_count=len(history))
            return CommandResult(
                f"System {status['assistant']}. Web mode is active. Local time is {status['time']}.",
                payload={"status": status, "card": {"type": "status", "data": status}},
            )

        if "motivate me" in normalized or "motivation" in normalized:
            return CommandResult(random.choice(MOTIVATION_LINES))

        if normalized.startswith("remember that "):
            note = normalized.replace("remember that ", "", 1).strip()
            if not note:
                return CommandResult("Tell me what you want me to remember.")
            return CommandResult(
                f"I will remember that {note}.",
                action="set_memory",
                payload={"memory": note},
            )

        if "what do you remember" in normalized or "remembered" in normalized:
            if not memory:
                return CommandResult("You have not asked me to remember anything yet.")
            return CommandResult(f"You asked me to remember that {memory}.")

        if "forget everything" in normalized or "clear memory" in normalized:
            return CommandResult("Memory cleared.", action="clear_memory", payload={"memory": ""})

        if "time" in normalized:
            return CommandResult(f"The time is {dt.datetime.now().strftime('%I:%M %p')}.")

        if "date" in tokens or normalized.startswith("what day") or normalized == "day":
            return CommandResult(f"Today is {dt.datetime.now().strftime('%A, %d %B %Y')}.")

        if normalized.startswith("open "):
            return self._open_target(normalized[5:].strip())

        if normalized.startswith("close "):
            return self._close_target(normalized[6:].strip())

        inferred_search = self._infer_search_command(normalized)
        if inferred_search is not None:
            return inferred_search

        if "google" in normalized:
            return self._google_search(normalized)

        if "youtube" in normalized:
            return self._youtube_search(normalized)

        if "wikipedia" in normalized:
            return self._wikipedia_search(normalized)

        if "news" in normalized:
            return self._with_topic(self._news_headlines(), "news")

        if self._is_cricket_score_query(normalized):
            return self._with_topic(self._cricket_score(normalized), "sports")

        if "weather" in normalized or "temperature" in normalized:
            return self._with_topic(self._weather(normalized), "weather")

        contextual = self._handle_contextual_followup(normalized, last_topic)
        if contextual is not None:
            return contextual

        if normalized.startswith("calculate ") or normalized.startswith("what is "):
            return self._calculate(normalized)

        if "history" in normalized and "clear" not in normalized:
            if not history:
                return CommandResult("No recent command history is available.", payload={"history": []})
            preview = [item.get("command", "") for item in history[-5:]]
            return CommandResult(
                "Recent commands: " + " | ".join(preview),
                payload={"history": history},
            )

        if "clear history" in normalized:
            return CommandResult("Command history cleared.", action="clear_history", payload={"history": []})

        if "roll a dice" in normalized or "roll dice" in normalized:
            return CommandResult(f"I rolled a {random.randint(1, 6)}.")

        if "flip a coin" in normalized or "toss a coin" in normalized:
            return CommandResult(f"It is {random.choice(['heads', 'tails'])}.")

        if normalized.startswith("launch ") or normalized.startswith("search for "):
            query = normalized.replace("launch ", "", 1).replace("search for ", "", 1).strip()
            return self._google_search(f"google {query}")

        if "help" in normalized or "what can you do" in normalized:
            return CommandResult(
                "I can open websites in new tabs, search Google, YouTube, and Wikipedia, tell the time or date, "
                "check weather, read news, calculate answers, remember notes in your browser, show system status, "
                "and keep recent command history for this web session."
            )

        ai_result = self._maybe_ai_answer(command, history, memory, settings)
        if ai_result is not None:
            return ai_result

        return self._fallback_web_assist(command)

    def _with_topic(self, result: CommandResult, topic: str) -> CommandResult:
        payload = dict(result.payload or {})
        payload["topic"] = topic
        result.payload = payload
        return result

    def _with_card(self, result: CommandResult, card_type: str, data: dict) -> CommandResult:
        payload = dict(result.payload or {})
        payload["card"] = {"type": card_type, "data": data}
        result.payload = payload
        return result

    def _infer_last_topic(self, history: list[dict]) -> Optional[str]:
        for item in reversed(history):
            response = str(item.get("response", "")).lower()
            command = str(item.get("command", "")).lower()
            if "weather" in command or "temperature" in command:
                return "weather"
            if "news" in command or "top headlines" in response:
                return "news"
            if "who is" in command or "tell me about" in command:
                return "summary"
        return None

    def _handle_contextual_followup(self, command: str, last_topic: Optional[str]) -> Optional[CommandResult]:
        if not last_topic:
            return None

        if last_topic == "weather":
            city = self._extract_city_from_weather_command(command)
            if city:
                return self._with_topic(self._weather(f"weather in {city}"), "weather")

        return None

    def _is_cricket_score_query(self, command: str) -> bool:
        cricket_terms = ("cricket", "ipl", "match", "score", "live score")
        score_terms = ("score", "live", "match", "ipl")
        return any(term in command for term in cricket_terms) and any(term in command for term in score_terms)

    def _infer_search_command(self, command: str) -> Optional[CommandResult]:
        normalized = command
        lead_ins = (
            "can you tell me who is ",
            "can you tell me about ",
            "hello can you search ",
            "can you search ",
            "search for ",
            "search ",
            "find ",
            "look up ",
            "tell me about ",
            "who is ",
            "what is ",
        )

        for lead_in in lead_ins:
            if normalized.startswith(lead_in):
                query = normalized[len(lead_in) :].strip()
                if not query:
                    return CommandResult("Tell me what you want me to search for.")

                if lead_in in {"can you tell me who is ", "can you tell me about ", "who is ", "tell me about "}:
                    return self._answer_topic_summary(query, fallback="wikipedia")

                if lead_in == "what is " and not any(ch.isdigit() for ch in query):
                    return self._answer_topic_summary(query, fallback="google")

                if lead_in != "what is ":
                    return CommandResult(
                        f"Searching Google for {query}.",
                        action="open_url",
                        payload={
                            "url": f"https://www.google.com/search?q={quote_plus(query)}",
                            "target": "_blank",
                        },
                    )

        return None

    def _answer_topic_summary(self, query: str, fallback: str) -> CommandResult:
        try:
            page = quote_plus(query.replace(" ", "_"))
            response = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{page}",
                timeout=10,
                headers={"User-Agent": "Jarvis/1.0"},
            )
            if response.status_code == 200:
                data = response.json()
                extract = " ".join(str(data.get("extract", "")).split())
                title = str(data.get("title", "")).strip()
                content_url = (
                    data.get("content_urls", {})
                    .get("desktop", {})
                    .get("page")
                )
                if extract:
                    summary = extract
                    if len(summary) > 420:
                        trimmed = summary[:420]
                        sentence_cut = trimmed.rfind(". ")
                        if sentence_cut > 80:
                            summary = trimmed[: sentence_cut + 1].strip()
                        else:
                            summary = trimmed.rsplit(" ", 1)[0].rstrip(" ,;:")
                    if title and not summary.lower().startswith(title.lower()):
                        summary = f"{title} is {summary[0].lower() + summary[1:]}" if summary else title
                    if summary and summary[-1] not in ".!?":
                        summary = summary + "."
                    result = CommandResult(summary, payload={"source_url": content_url} if content_url else None)
                    return self._with_card(
                        result,
                        "summary",
                        {
                            "title": title or query.title(),
                            "summary": summary,
                            "source_url": content_url,
                        },
                    )
        except Exception:
            pass

        if fallback == "wikipedia":
            return CommandResult(
                f"I could not summarize {query} right now, so I will open Wikipedia results.",
                action="open_url",
                payload={
                    "url": f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(query)}",
                    "target": "_blank",
                    "card": {
                        "type": "action",
                        "data": {
                            "title": "Open Wikipedia Search",
                            "description": f"View search results for {query}.",
                            "cta": "Open Wikipedia",
                        },
                    },
                },
            )

        return CommandResult(
            f"I could not summarize {query} right now, so I will search Google for it.",
            action="open_url",
            payload={
                "url": f"https://www.google.com/search?q={quote_plus(query)}",
                "target": "_blank",
                "card": {
                    "type": "action",
                    "data": {
                        "title": "Search Google",
                        "description": f"Search the web for {query}.",
                        "cta": "Open Search",
                    },
                },
            },
        )

    def _open_target(self, target: str) -> CommandResult:
        if not target:
            return CommandResult("Tell me what you want to open.")

        cleaned = target.replace("website", "").strip()
        if cleaned in DESKTOP_ONLY_APPS:
            alt_name, alt_url = WEB_ALTERNATIVES.get(
                cleaned,
                ("Web Search", f"https://www.google.com/search?q={quote_plus(cleaned)}"),
            )
            return CommandResult(
                f"{cleaned} is a desktop app, so I cannot control it from a deployed web app. I can open {alt_name} instead.",
                action="open_url",
                payload={
                    "url": alt_url,
                    "target": "_blank",
                    "card": {
                        "type": "action",
                        "data": {
                            "title": f"Open {alt_name}",
                            "description": f"Use a web alternative for {cleaned}.",
                            "cta": "Open Alternative",
                        },
                    },
                },
            )

        if cleaned in WEB_APPS:
            return CommandResult(
                f"Opening {cleaned}.",
                action="open_url",
                payload={
                    "url": WEB_APPS[cleaned],
                    "target": "_blank",
                    "card": {
                        "type": "action",
                        "data": {
                            "title": f"Open {cleaned.title()}",
                            "description": f"Launch {cleaned.title()} in a new tab.",
                            "cta": "Open",
                        },
                    },
                },
            )

        if "." in cleaned or cleaned.startswith(("http://", "https://")):
            url = cleaned
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            return CommandResult(
                f"Opening {url}.",
                action="open_url",
                payload={
                    "url": url,
                    "target": "_blank",
                    "card": {
                        "type": "action",
                        "data": {
                            "title": "Open Website",
                            "description": url,
                            "cta": "Visit",
                        },
                    },
                },
            )

        return CommandResult(
            f"I could not find a direct website for {cleaned}, so I will search for it.",
            action="open_url",
            payload={
                "url": f"https://www.google.com/search?q={quote_plus(cleaned)}",
                "target": "_blank",
                "card": {
                    "type": "action",
                    "data": {
                        "title": "Search Website",
                        "description": f"Find the best match for {cleaned}.",
                        "cta": "Search",
                    },
                },
            },
        )

    def _close_target(self, target: str) -> CommandResult:
        if not target:
            return CommandResult("Tell me what you want to close.")
        return CommandResult(
            f"I cannot close browser tabs or desktop apps from a deployed web app. You can close {target} manually, and I can help you open something else instead."
        )

    def _google_search(self, command: str) -> CommandResult:
        query = (
            command.replace("google search", "")
            .replace("search google for", "")
            .replace("google", "")
            .strip()
        )
        if not query:
            return CommandResult("Tell me what to search on Google.")
        return CommandResult(
            f"Searching Google for {query}.",
            action="open_url",
            payload={
                "url": f"https://www.google.com/search?q={quote_plus(query)}",
                "target": "_blank",
                "card": {
                    "type": "action",
                    "data": {
                        "title": "Google Search",
                        "description": f"Search results for {query}.",
                        "cta": "Open Results",
                    },
                },
            },
        )

    def _youtube_search(self, command: str) -> CommandResult:
        query = command.replace("youtube search", "").replace("youtube", "").strip()
        if not query:
            return CommandResult("Tell me what to search on YouTube.")
        return CommandResult(
            f"Searching YouTube for {query}.",
            action="open_url",
            payload={
                "url": f"https://www.youtube.com/results?search_query={quote_plus(query)}",
                "target": "_blank",
                "card": {
                    "type": "action",
                    "data": {
                        "title": "YouTube Search",
                        "description": f"Video results for {query}.",
                        "cta": "Open Videos",
                    },
                },
            },
        )

    def _wikipedia_search(self, command: str) -> CommandResult:
        query = command.replace("search wikipedia", "").replace("wikipedia", "").strip()
        if not query:
            return CommandResult("Tell me what to search on Wikipedia.")
        return CommandResult(
            f"Opening Wikipedia results for {query}.",
            action="open_url",
            payload={
                "url": f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(query)}",
                "target": "_blank",
                "card": {
                    "type": "action",
                    "data": {
                        "title": "Wikipedia Search",
                        "description": f"Reference results for {query}.",
                        "cta": "Open Wikipedia",
                    },
                },
            },
        )

    def _news_headlines(self) -> CommandResult:
        try:
            response = requests.get(
                "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
                timeout=10,
            )
            response.raise_for_status()
            parts = response.text.split("<item>")[1:5]
            titles = []
            for item in parts:
                start = item.find("<title>")
                end = item.find("</title>")
                if start != -1 and end != -1:
                    titles.append(item[start + 7 : end])
            if not titles:
                return CommandResult("I could not read the latest news right now.")
            result = CommandResult("Top headlines: " + " | ".join(titles))
            return self._with_card(result, "news", {"items": titles})
        except Exception:
            return CommandResult("I could not fetch the latest news right now.")

    def _weather(self, command: str) -> CommandResult:
        city = self._extract_city_from_weather_command(command) or "Delhi"

        try:
            response = requests.get(f"https://wttr.in/{quote_plus(city)}?format=%l:+%t,+%C", timeout=10)
            response.raise_for_status()
            text = response.text.strip().encode("ascii", "ignore").decode("ascii")
            if not text:
                return CommandResult(f"I fetched the weather for {city}, but the response was unreadable.")
            parts = [part.strip() for part in text.split(": ", 1)]
            summary = parts[1] if len(parts) > 1 else text
            temp, _, condition = summary.partition(",")
            result = CommandResult(f"The current temperature in {city} is {temp.strip()} with {condition.strip() or 'current conditions available'}.")
            return self._with_card(
                result,
                "weather",
                {
                    "city": city,
                    "temperature": temp.strip(),
                    "condition": condition.strip() or "Current conditions available",
                },
            )
        except Exception:
            return CommandResult(f"I could not fetch the weather for {city} right now.")

    def _cricket_score(self, command: str) -> CommandResult:
        query = command.strip()
        cleaned = (
            query.replace("can you", "")
            .replace("could you", "")
            .replace("please", "")
            .replace("tell me", "")
            .replace("show me", "")
            .strip()
        )

        search_query = cleaned or "live cricket score"
        if "score" not in search_query:
            search_query = f"{search_query} score"

        return CommandResult(
            f"I am opening the latest cricket results for {search_query}.",
            action="open_url",
            payload={
                "url": f"https://www.google.com/search?q={quote_plus(search_query)}",
                "target": "_blank",
                "card": {
                    "type": "sports",
                    "data": {
                        "title": "Cricket Score Lookup",
                        "description": f"Open current results for {search_query}.",
                        "cta": "Open Scores",
                    },
                },
            },
        )

    def _extract_city_from_weather_command(self, command: str) -> Optional[str]:
        normalized = " " + " ".join(command.lower().split()) + " "

        if " in " in normalized:
            tail = normalized.split(" in ", 1)[1].strip()
            tail = self._strip_weather_fillers(tail)
            if tail:
                return tail.title()

        for city in sorted(KNOWN_CITIES, key=len, reverse=True):
            if f" {city} " in normalized:
                return city.title()

        stripped = self._strip_weather_fillers(normalized).strip()
        if stripped and stripped not in {"weather", "temperature"}:
            words = [word for word in stripped.split() if word not in {"weather", "temperature"}]
            if words:
                return " ".join(words[-2:]).title()

        return None

    def _strip_weather_fillers(self, text: str) -> str:
        fillers = {
            "can",
            "could",
            "would",
            "will",
            "you",
            "please",
            "tell",
            "me",
            "the",
            "what",
            "is",
            "temperature",
            "weather",
            "of",
            "for",
            "show",
            "give",
            "i",
            "am",
            "talking",
            "about",
            "to",
        }
        words = [word for word in text.lower().replace("?", " ").replace(",", " ").split() if word not in fillers]
        return " ".join(words)

    def _calculate(self, command: str) -> CommandResult:
        expression = command.replace("calculate", "").replace("what is", "").strip()
        word_map = {
            "plus": "+",
            "minus": "-",
            "multiply by": "*",
            "multiplied by": "*",
            "times": "*",
            "divide by": "/",
            "divided by": "/",
            "mod": "%",
        }
        for source, target in word_map.items():
            expression = expression.replace(source, target)
        expression = expression.replace("^", "**")

        try:
            parsed = ast.parse(expression, mode="eval")
            result = SafeEvaluator().visit(parsed)
            calc_result = CommandResult(f"The answer is {result}.")
            return self._with_card(calc_result, "calculation", {"expression": expression, "result": str(result)})
        except Exception:
            return CommandResult("I could not calculate that. Try a simpler math expression.")

    def _maybe_ai_answer(self, command: str, history: list[dict], memory: str, settings: dict) -> Optional[CommandResult]:
        if not settings.get("aiEnabled"):
            return None
        if self.ai_client is None:
            return CommandResult(
                "AI mode is enabled in settings, but no OpenAI API key is configured on the server."
            )

        response_mode = settings.get("responseMode", "balanced")
        detail_instruction = {
            "concise": "Answer briefly in 2-4 sentences.",
            "balanced": "Answer clearly in 1 short paragraph.",
            "detailed": "Answer with a helpful short explanation in 2 short paragraphs.",
        }.get(response_mode, "Answer clearly in 1 short paragraph.")

        recent_turns = history[-4:]
        conversation_lines = []
        for item in recent_turns:
            conversation_lines.append(f"User: {item.get('command', '')}")
            conversation_lines.append(f"Jarvis: {item.get('response', '')}")
        if memory:
            conversation_lines.append(f"Stored memory: {memory}")
        conversation_lines.append(f"User: {command}")

        try:
            response = self.ai_client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-5.2"),
                input="\n".join(conversation_lines),
                instructions=(
                    "You are Jarvis, a helpful AI assistant inside a browser control panel. "
                    "Give direct, natural answers without mentioning internal tools unless necessary. "
                    f"{detail_instruction}"
                ),
            )
            text = (response.output_text or "").strip()
            if not text:
                return None
            result = CommandResult(text)
            return self._with_card(
                result,
                "ai",
                {
                    "title": "AI Answer",
                    "description": text,
                    "mode": response_mode,
                },
            )
        except Exception:
            return CommandResult("I tried to use AI mode for that request, but the model request failed.")

    def _fallback_web_assist(self, command: str) -> CommandResult:
        cleaned = " ".join(command.split()).strip()
        if not cleaned:
            return CommandResult("Please say or type a command.")

        return CommandResult(
            f"I do not have a direct web action for \"{cleaned}\", so I am searching the web for it.",
            action="open_url",
            payload={
                "url": f"https://www.google.com/search?q={quote_plus(cleaned)}",
                "target": "_blank",
                "card": {
                    "type": "action",
                    "data": {
                        "title": "Smart Web Fallback",
                        "description": f"Search the web for {cleaned}.",
                        "cta": "Search Web",
                    },
                },
            },
        )
