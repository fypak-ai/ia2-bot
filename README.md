# ia2-bot 🤖

Bot Slack em tempo real para o canal **#ia2** — acessa qualquer LLM via [OpenRouter](https://openrouter.ai) usando Socket Mode (sem servidor HTTP, sem portas expostas).

## Uso no Slack

```
# Com modelo específico
gpt-4o: explique buracos negros
claude-3.5-sonnet: escreva um poema
deepseek-r1: resolva esta integral
llama-3.3-70b: me dê uma receita

# Sem prefixo → usa gpt-4o
qual a capital da Austrália?
```

## Modelos disponíveis

| Alias | Modelo OpenRouter |
|---|---|
| `gpt-4o` | openai/gpt-4o *(padrão)* |
| `gpt-4o-mini` | openai/gpt-4o-mini |
| `o3-mini` | openai/o3-mini |
| `claude-3.5-sonnet` | anthropic/claude-3.5-sonnet |
| `claude-3.5-haiku` | anthropic/claude-3.5-haiku |
| `claude-3-opus` | anthropic/claude-3-opus |
| `gemini-2.0-flash` | google/gemini-2.0-flash-001 |
| `gemini-2.0-pro` | google/gemini-2.0-pro-exp-02-05 |
| `llama-3.3-70b` | meta-llama/llama-3.3-70b-instruct |
| `deepseek` | deepseek/deepseek-chat-v3-0324 |
| `deepseek-r1` | deepseek/deepseek-r1 |
| `mistral` | mistralai/mistral-large |
| `qwen` | qwen/qwen-2.5-72b-instruct |
| `llama-3.2-3b` | meta-llama/llama-3.2-3b-instruct:free |
| `gemma2-9b` | google/gemma-2-9b-it:free |

## Deploy no Railway

### 1. Criar app Slack

1. Acesse https://api.slack.com/apps → **Create New App** → **From scratch**
2. **Socket Mode** → Ativar → gerar `SLACK_APP_TOKEN` (começa com `xapp-`)
3. **Event Subscriptions** → Ativar → Subscribe to bot events: `message.channels`
4. **OAuth & Permissions** → Bot Token Scopes:
   - `channels:history`
   - `chat:write`
   - `chat:write.public`
5. **Install App** → copiar `SLACK_BOT_TOKEN` (começa com `xoxb-`)
6. Convidar o bot para o canal `#ia2`: `/invite @nome-do-bot`

### 2. Deploy Railway

1. Acesse https://railway.app/new → **Deploy from GitHub repo** → selecione `fypak-ai/ia2-bot`
2. **Serviço tipo Worker** (não Web Service — o bot não precisa de porta HTTP)
3. Em **Variables**, adicione:
   ```
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   OPENROUTER_API_KEY=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
   TARGET_CHANNEL_ID=C0AH9ADCTUK
   ```
4. Deploy → Railway detecta `Procfile` e inicia `python bot.py`

### 3. Verificar

No log do Railway você verá:
```
⚡ ia2-bot online via Socket Mode
```

Envie uma mensagem no `#ia2` — resposta em segundos.
