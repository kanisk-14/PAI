import os
import json
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MEMORY_FILE = "memory.json"

# ── Memory ──────────────────────────────────────────────
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"facts": [], "history": []}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def extract_facts(user_input, memory):
    triggers = ["my name is", "i am", "i'm", "i like", "i love", "i hate", "i study", "i live"]
    for trigger in triggers:
        if trigger in user_input.lower():
            fact = user_input.strip()
            if fact not in memory["facts"]:
                memory["facts"].append(fact)
                print("🧠 PAI remembered that.")
    return memory

# ── Web Search ───────────────────────────────────────────
def needs_search(user_input):
    keywords = ["latest", "news", "today", "current", "price", "weather", "who is", "what is happening", "happening", "war", "update", "recently", "2024", "2025", "right now", "now", "this week", "this year", "live"]
    return any(k in user_input.lower() for k in keywords)

def web_search(query):
    print("🔍 Searching the web...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return None
        summary = ""
        for r in results:
            summary += f"- {r['title']}: {r['body']}\n"
        return summary
    except Exception:
        return None

# ── Build system prompt ──────────────────────────────────
def build_system_prompt(memory):
    prompt = "You are PAI, a personal AI assistant. You are helpful, concise, and friendly.\n"
    if memory["facts"]:
        prompt += "\nHere is what you know about the user:\n"
        for fact in memory["facts"]:
            prompt += f"- {fact}\n"
    return prompt

# ── Main chat loop ───────────────────────────────────────
def chat():
    memory = load_memory()
    print("PAI v0.2 — type 'quit' to exit, 'memory' to see what PAI remembers")
    print("-" * 50)

    while True:
        user_input = input("You: ")

        if user_input.lower() == "quit":
            print("PAI: Bye! See you next time.")
            save_memory(memory)
            break

        if user_input.strip() == "":
            continue

        if user_input.lower() == "memory":
            print("🧠 PAI remembers:")
            if memory["facts"]:
                for f in memory["facts"]:
                    print(f"  - {f}")
            else:
                print("  Nothing yet.")
            continue

        # Extract any facts from input
        memory = extract_facts(user_input, memory)

        # Build messages
        messages = [{"role": "system", "content": build_system_prompt(memory)}]

        # Add conversation history (last 6 exchanges)
        for msg in memory["history"][-6:]:
            messages.append(msg)

        # Web search if needed
        if needs_search(user_input):
            search_results = web_search(user_input)
            if search_results:
                messages.append({
                    "role": "user",
                    "content": f"{user_input}\n\nHere is some fresh info from the web:\n{search_results}"
                    })
    else:
        print("⚠️  Web search unavailable, answering from memory...")
        messages.append({"role": "user", "content": user_input})

        # Call Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
        )

        reply = response.choices[0].message.content
        print(f"\nPAI: {reply}\n")

        # Save to history
        memory["history"].append({"role": "user", "content": user_input})
        memory["history"].append({"role": "assistant", "content": reply})
        save_memory(memory)

if __name__ == "__main__":
    chat()