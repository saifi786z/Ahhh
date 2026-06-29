# 🤖 UPI Giveaway 2026 - Telegram Bot

A feature-rich Telegram bot for channel verification, referral system, and admin management.

## 📋 Features

### User Features
- **Channel Join Verification** - Users must join configured channels to proceed
- **Two-Page System** - Page 1 & Page 2 channels with separate verification
- **Referral System** - Users need 3 referrals to claim reward
- **Premium Emojis** - Dynamic custom emoji support
- **Auto DM** - Bot sends DMs when users join/request channels

### Admin Features
- **Admin Panel** - `/admin` command for full control
- **Channel Management** - Add/Remove channels for Page 1 & Page 2
- **Broadcast** - Send messages to all users (supports all media types)
- **Start Image** - Set custom start image
- **Start Caption** - Customize welcome message
- **Statistics** - View bot analytics
- **Multi-Admin** - Add/remove additional admins

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Bot
Edit `bot.py` and update:
- `BOT_TOKEN` - Your bot token (already set)
- `ADMIN_ID` - Main admin ID (already set)

### 3. Run Bot
```bash
python bot.py
```

## 🎮 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and show channels |
| `/admin` | Open admin panel (admin only) |
| `/cancel` | Cancel current operation |

## 📝 Admin Panel Options

1. **Add Channel (Page 1/2)** - Add channels with name, link, and optional ID
2. **Remove Channel** - Remove channels from Page 1 or 2
3. **List Channels** - View all configured channels
4. **Set Start Image** - Upload a start image
5. **Set Caption** - Customize welcome text
6. **Broadcast** - Send messages to all users
7. **Add/Remove Admin** - Manage admin access
8. **Stats** - View bot statistics

## 🔄 How It Works

1. User clicks `/start`
2. Bot shows start image + Page 1 channels
3. User joins all channels and clicks "Joined"
4. Bot verifies membership, then shows Page 2 channels
5. User joins Page 2 channels and clicks "Recharge"
6. Bot shows referral system
7. User needs 3 referrals to get contact info

## 📁 Data Storage

All data is stored in `bot_data/` directory:
- `users.json` - User data
- `channels.json` - Channel configurations
- `admins.json` - Admin list
- `settings.json` - Bot settings
- `referrals.json` - Referral tracking

## ⚠️ Important Notes

1. **Bot must be admin** in channels for auto-approve and DM features
2. **Channel IDs** are needed for accurate membership checking
3. **Rate limits** apply for broadcasting to many users
4. **Premium emojis** require Telegram Premium to display properly

## 🛠️ Technical Details

- Built with `python-telegram-bot` v20.7
- Uses ConversationHandler for admin operations
- Supports all update types for monitoring
- JSON-based data persistence
