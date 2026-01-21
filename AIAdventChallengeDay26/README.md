# День 26 — Общение с удалённой Ollama на VPS

Консольный чат с LLM, развёрнутой на удалённом сервере через Ollama API.

## Настройка клиента

### 1. Создать файл конфигурации

```bash
cp .env.example .env
```

### 2. Указать IP-адрес сервера

Отредактируй `.env`:

```bash
OLLAMA_HOST=your-vps-ip-here
OLLAMA_PORT=11434
OLLAMA_MODEL=qwen2.5
```

## Запуск

```bash
python3 chat.py
```

Или с параметрами (переопределяют .env):

```bash
python3 chat.py --host your-ip --model llama3
```

## Команды в чате

- `выход`, `exit`, `quit` — завершить
- `clear` — очистить историю
- `model <name>` — сменить модель

---

## Настройка сервера (VPS)

### 1. Установка Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5
```

### 2. Настройка удалённого доступа

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo nano /etc/systemd/system/ollama.service.d/override.conf
```

Содержимое:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Применить:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 3. Открыть порт

```bash
sudo ufw allow 11434/tcp
```

## Безопасность

Ollama не имеет встроенной аутентификации. Для защиты используй SSH-туннель:

```bash
ssh -L 11434:localhost:11434 user@your-vps-ip
```

Затем в `.env`:

```bash
OLLAMA_HOST=localhost
```
