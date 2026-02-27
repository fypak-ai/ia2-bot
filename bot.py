import os
import re
import json
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── Config ────────────────────────────────────────────────────────────────────
SLACK_BOT_TOKEN  = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN  = os.environ["SLACK_APP_TOKEN"]
OPENROUTER_KEY   = os.environ["OPENROUTER_API_KEY"]
TARGET_CHANNEL   = os.environ.get("TARGET_CHANNEL_ID", "C0AH9ADCTUK")  # #ia2
DEFAULT_MODEL    = os.environ.get("DEFAULT_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
FALLBACK_MODEL   = "meta-llama/llama-3.2-3b-instruct:free"
OPENROUTER_URL   = "https://openrouter.ai/api/v1/chat/completions"

# ── Model alias map ───────────────────────────────────────────────────────────
ALIAS_MAP = {
    "gpt-4o":            "openai/gpt-4o",
    "gpt-4o-mini":       "openai/gpt-4o-mini",
    "o3-mini":           "openai/o3-mini",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "claude-3.5-haiku":  "anthropic/claude-3.5-haiku",
    "claude-3-opus":     "anthropic/claude-3-opus",
    "gemini-2.0-flash":  "google/gemini-2.0-flash-001",
    "gemini-2.0-pro":    "google/gemini-2.0-pro-exp-02-05",
    "llama-3.3-70b":     "meta-llama/llama-3.3-70b-instruct",
    "llama-3.1-8b":      "meta-llama/llama-3.1-8b-instruct",
    "deepseek":          "deepseek/deepseek-chat-v3-0324",
    "deepseek-r1":       "deepseek/deepseek-r1",
    "mistral":           "mistralai/mistral-large",
    "mistral-small":     "mistralai/mistral-small",
    "qwen":              "qwen/qwen-2.5-72b-instruct",
    "llama-3.2-3b":      "meta-llama/llama-3.2-3b-instruct:free",
    "gemma-2-9b":        "google/gemma-2-9b-it:free",
    # modelos gratuitos adicionais
    "gemma3":            "google/gemma-3-27b-it:free",
    "mistral-7b":        "mistralai/mistral-7b-instruct:free",
    "phi-3":             "microsoft/phi-3-medium-128k-instruct:free",
}

app = App(token=SLACK_BOT_TOKEN)


def parse_message(text: str) -> tuple[str, str]:
    """Return (model_id, prompt). Detects 'alias: prompt' prefix."""
    text = text.strip()
    match = re.match(r'^([\w.:\-]+):\s*(.+)', text, re.DOTALL)
    if match:
        alias = match.group(1).lower()
        prompt = match.group(2).strip()
        model = ALIAS_MAP.get(alias)
        if model:
            return model, prompt
        # Unknown alias — try as raw OpenRouter model id
        if "/" in alias:
            return alias, prompt
    return DEFAULT_MODEL, text


def call_openrouter(model: str, prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/fypak-ai/ia2-bot",
        "X-Title": "ia2-bot",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)

    # Se der 402 (créditos insuficientes) e o modelo não for gratuito, usa fallback
    if resp.status_code == 402 and not model.endswith(":free"):
        payload["model"] = FALLBACK_MODEL
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
        return f"_{model} requer créditos — usando {FALLBACK_MODEL}_\n\n{answer}"

    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


@app.message(re.compile(r'.*'))
def handle_message(message, say, client):
    # Only respond in the target channel
    if message.get("channel") != TARGET_CHANNEL:
        return
    # Ignore bots and thread replies (avoid loops)
    if message.get("bot_id") or message.get("subtype"):
        return

    text = message.get("text", "").strip()
    if not text:
        return

    model_id, prompt = parse_message(text)
    model_name = next((k for k, v in ALIAS_MAP.items() if v == model_id), model_id)

    # Send thinking indicator in thread
    thread_ts = message.get("thread_ts") or message["ts"]
    thinking = client.chat_postMessage(
        channel=TARGET_CHANNEL,
        thread_ts=thread_ts,
        text=f"_🤔 Consultando `{model_name}`..._",
    )

    try:
        answer = call_openrouter(model_id, prompt)
        # Delete thinking message
        client.chat_delete(
            channel=TARGET_CHANNEL,
            ts=thinking["ts"],
        )
        say(
            text=f"💬 *{model_name}*\n\n{answer}",
            thread_ts=thread_ts,
        )
    except Exception as e:
        client.chat_update(
            channel=TARGET_CHANNEL,
            ts=thinking["ts"],
            text=f"❌ Erro ao chamar `{model_name}`: {str(e)}",
        )


if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    print("⚡ ia2-bot online via Socket Mode")
    handler.start()
