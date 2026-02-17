# Telegram Remote Controller Setup Guide

## 🤖 Create Telegram Bot

1. **Message @BotFather on Telegram**:
   ```
   /newbot
   ```

2. **Choose bot name**: `NVIDIA Gravity Controller` (or your preference)

3. **Choose username**: `nvidia_gravity_bot` (or available alternative)

4. **Get your token**: BotFather will give you a token like:
   ```
   123456789:ABCdefGhIJKlmNOPqrsTUVwxyz
   ```

## 🔐 Get Your Telegram User ID

1. **Message @userinfobot on Telegram**

2. **Send any message** to get your user ID (numbers like: `987654321`)

## ⚙️ Configure Environment

Add to your `.env` file:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNOPqrsTUVwxyz
AUTHORIZED_USER_ID=987654321
```

## 🚀 Start Remote Controller

```bash
# Terminal 1: Start the Telegram controller (keep running)
python remote_controller.py

# Terminal 2: Your bot is now ready for commands!
```

## 📱 Telegram Commands

- `/start` - Welcome message and system check
- `/run` - Execute NVIDIA prediction workflow  
- `/status` - Check if system is running

## 🔒 Security Features

- **Single User Access**: Only your Telegram ID can control the system
- **Process Locking**: Prevents multiple simultaneous executions
- **Secure Parsing**: Safe extraction of results from subprocess output

## 🌊 Example Workflow

1. Send `/start` - Confirm connection
2. Send `/run` - Start gravity analysis
3. Get real-time feedback: "🚀 Gravity Engine Started..."
4. Receive formatted results with predictions and confidence levels
5. Use `/status` to check system state

The controller runs independently and safely triggers your main prediction system via subprocess execution.