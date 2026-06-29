# 🤖 UPI Giveaway 2026 - Telegram Bot (Fixed Version)

## ⚠️ Important Fix Applied

### Problem 1: Premium Emojis Not Working
**Cause**: The `<tg-emoji>` HTML tag requires:
1. The bot to be using **HTML parse mode** (✅ Fixed)
2. The emoji IDs must be valid **paid Telegram emoji stickers** from Telegram's sticker packs
3. The user viewing the message must have **Telegram Premium** to see them

**Solution**: The bot now properly uses `parse_mode=ParseMode.HTML` for all messages. However, if the emoji IDs you provided are not valid or the user doesn't have Premium, they'll see a fallback star (⭐) instead.

**To test if emojis work:**
- Send a message with `<tg-emoji emoji-id="6023898164732366954">⭐</tg-emoji>` manually
- If it shows as raw text, the emoji ID is invalid

### Problem 2: Button Colors (Success/Danger/Primary)
**Cause**: Telegram's Bot API does **NOT** support colored inline keyboard buttons directly. The `InlineKeyboardButton` class only supports URL and callback_data buttons without color customization.

**Solution**: The bot now uses **color emoji indicators** as a workaround:
- 🟢 **Success** (Green)
- 🔴 **Danger** (Red)
- 🔵 **Primary** (Blue)  
- 🟡 **Warning** (Yellow)

**Example buttons:**
```
🟢 Join Channel 1    🔴 Join Channel 2
🔵 Join Channel 3    🟡 Join Channel 4
🟢 Joined
```

**Note**: True colored buttons (like in web apps) require using `ReplyKeyboardMarkup` with `web_app` buttons or building a Mini App, which is much more complex.

---

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install python-telegram-bot==20.7
```

### 2. Configure Bot
Edit `bot.py` and verify:
- `BOT_TOKEN` - Already set to your token
- `ADMIN_ID` - Already set to your ID (8674318569)
- `BOT_USERNAME` - Set to `UPIGIVEAWAY2026_BOT`

### 3. Run Bot
```bash
python bot.py
```

---

## 🎮 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and show channels |
| `/admin` | Open admin panel (admin only) |
| `/cancel` | Cancel current operation |

---

## 📝 Admin Panel Options

1. **Add Channel (Page 1/2)** - Add channels with color style
   - Format: `Name | Link | ChannelID | Style`
   - Styles: `success` (🟢), `danger` (🔴), `primary` (🔵), `warning` (🟡)
   - Example: `My Channel | https://t.me/mychannel | @mychannel | success`

2. **Remove Channel** - Remove channels from Page 1 or 2
3. **List Channels** - View all configured channels with colors
4. **Set Start Image** - Upload a start image
5. **Set Caption** - Customize welcome text
6. **Broadcast** - Send messages to all users (supports all media types)
7. **Add/Remove Admin** - Manage admin access
8. **Stats** - View bot statistics

---

## 🔄 How It Works

1. User clicks `/start`
2. Bot shows start image + Page 1 channel buttons (with colors)
3. User joins all channels and clicks "🟢 Joined"
4. Bot verifies membership, then shows Page 2 channels
5. User joins Page 2 channels and clicks "🔵 Recharge"
6. Bot shows referral system
7. User needs 3 referrals to get contact info

---

## 📁 Data Storage

All data is stored in `bot_data/` directory:
- `users.json` - User data
- `channels.json` - Channel configurations (with styles)
- `admins.json` - Admin list
- `settings.json` - Bot settings
- `referrals.json` - Referral tracking

---

## 🛠️ Technical Details

- Built with `python-telegram-bot` v20.7
- Uses ConversationHandler for admin operations
- JSON-based data persistence
- HTML parse mode for premium emoji support
- Color emoji workaround for button styling
