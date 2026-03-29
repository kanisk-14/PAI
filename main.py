import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

print("AI Chat — type 'quit' to exit")
print("-" * 30)

while True:
    user_input = input("You: ")

    if user_input.lower() == "quit":
        print("Bye!")
        break

    if user_input.strip() == "":
        continue

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": user_input}]
    )

    print(f"AI: {response.choices[0].message.content}")
    print()