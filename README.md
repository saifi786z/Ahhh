# 🤖 UPI Giveaway 2026 - Telegram Bot (v22+ with Native Colored Buttons)

## ✨ New Features in This Version

### Native Colored Buttons (Telegram Bot API 9.4+)
Since Bot API 9.4, Telegram supports **native button colors** and **custom emoji icons**:

| Style | Color | Usage |
|-------|-------|-------|
| `SUCCESS` | 🟢 Green | Joined button, positive actions |
| `DANGER` | 🔴 Red | Warning buttons, negative actions |
| `PRIMARY` | 🔵 Blue | Main actions, Recharge button |

### Premium Emoji Icons on Buttons
Each button can have a **custom emoji icon** displayed before the text:
- Uses your provided emoji IDs
- Works with `icon_custom_emoji_id` parameter
- Displays natively in Telegram clients

---

## 🚀 Setup

### IMPORTANT: Upgrade python-telegram-bot
```bash
pip install --upgrade "python-telegram-bot>=22.0"
```

### Run the bot
```bash
python bot.py
```

---

## 🎮 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot with colored channel buttons |
| `/admin` | Open admin panel |
| `/cancel` | Cancel current operation |

---

## 📝 Admin Panel - Add Channel Format

```
Name | Link | ChannelID | Style | EmojiID
```

**Example:**
```
My Channel | https://t.me/mychannel | @mychannel | success | 6023898164732366954
```

| Field | Description |
|-------|-------------|
| Name | Button text |
| Link | Channel invite link |
| ChannelID | For membership checking (optional) |
| Style | `success`/`danger`/`primary` |
| EmojiID | Premium emoji ID for button icon |

---

## 🎨 Button Examples

### Channel Buttons (2 per row):
```
🟢 [emoji] Channel 1    🔴 [emoji] Channel 2
🔵 [emoji] Channel 3    🟢 [emoji] Channel 4
```

### Action Buttons:
```
🟢 [emoji] Joined
🔵 [emoji] Recharge
```

---

## ⚠️ Requirements

1. **python-telegram-bot >= 22.0** (has `style` and `icon_custom_emoji_id` support)
2. **Telegram client updated** to latest version (to see colored buttons)
3. **Premium emoji IDs** must be valid for icons to show

---

## 📁 Files

| File | Description |
|------|-------------|
| `bot.py` | Main bot code with colored buttons |
| `requirements.txt` | Dependencies (v22+) |
| `README.md` | This file |
| `start.sh` | Startup script |
