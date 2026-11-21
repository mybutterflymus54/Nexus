- Help with programming.
- Solve mathematical problems.
- Discuss science, history, and technology.
- Have normal conversations.

Memory:
- You can access information supplied in the user's saved memory.
- Use relevant memories when answering questions.
- Never claim to remember something that isn't in your supplied memory.

You are NEXUS AI version 5.0.
"""

def load_memory():
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

memory = load_memory()
chat_history = []

def save_memory():
    MEMORY_FILE.write_text(
        json.dumps(memory, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

def ask_nexus(user_message):
    memory_text = "\n".join("- " + str(item) for item in memory)
    if not memory_text:
        memory_text = "No saved memories yet."

    system_message = SYSTEM_PROMPT + "\n\nUSER MEMORY:\n" + memory_text

    messages = [{"role": "system", "content": system_message}]
    messages.extend(chat_history[-12:])
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.8}
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.loads(response.read().decode("utf-8"))

    answer = result["message"]["content"]

    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": answer})
    return answer

app = FastAPI(title="NEXUS AI v5.0 local bridge")

# Allow the published NEXUSCREATIONS page and common local preview addresses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mybutterflymus54.github.io",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def health():
    return {"status": "online", "name": "NEXUS AI", "version": "5.0"}

@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Please enter a message.")

    lowered = user_message.lower()

    if lowered == "/help":
        return {"reply": "NEXUS commands:\n/help - Show commands\n/remember <information> - Save a memory\n/memory - View saved memories\n/new - Start a new chat"}
    if lowered == "/memory":
        if not memory:
            return {"reply": "My memory is empty."}
        return {"reply": "========== NEXUS MEMORY ==========\n" +
                "\n".join(f"{i}. {item}" for i, item in enumerate(memory, 1))}
    if lowered.startswith("/remember "):
        information = user_message[len("/remember "):].strip()
        if not information:
            return {"reply": "What should I remember?"}
        if information not in memory:
            memory.append(information)
            save_memory()
            return {"reply": "Got it! I've saved that to my memory."}
        return {"reply": "I already remember that!"}
    if lowered == "/new":
        chat_history.clear()
        return {"reply": "New conversation started."}
    if lowered in ("/exit", "exit"):
        return {"reply": "I can't shut down the server from the website."}

    try:
        return {"reply": ask_nexus(user_message)}
    except urllib.error.URLError:
        raise HTTPException(
            status_code=503,
            detail="I can't connect to Ollama. Make sure Ollama is running and the Gemma model is installed."
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="My response took too long. Please try again.")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"NEXUS encountered an error: {error}")
