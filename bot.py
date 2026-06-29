#!/usr/bin/env python3
"""
UPI Giveaway 2026 Bot
A Telegram bot for channel joining verification and referral system.
"""

import logging
import json
import os
import random
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ==================== CONFIGURATION ====================

BOT_TOKEN = "8618863127:AAETZui9nNScDi9Rjjjs7bHVJOSCR1CgfzE"
ADMIN_ID = 8674318569
BOT_NAME = "UPI Giveaway 2026"

# Premium Emoji IDs (Telegram custom emoji)
EMOJI_IDS = [
    "6023898164732366954", "6026106482297147601", "6026088864341299395",
    "6026322523447103813", "6023667769801707824", "6023974774064026637",
    "6023725524226937667", "6026056450223116307", "6026056450223116307",
    "6025881009399010995", "6026186540487548120", "6026031371909074667",
    "6026233591854272586", "6026140395358916313", "6026316720946286399",
    "6026243612012974483", "6026243289890427139", "6026329335265234977",
    "6026243289890427139", "6026321200597176575", "6030687219537154393",
    "6033108614724456536", "6035339257529242355", "6033006935668692007",
    "5785109764170060865", "6033059948450025914", "5782749628101300654",
    "5783164994388497098", "5782853931382084496", "6025878226260202192",
    "6026162407066309019", "5195033767969839232", "5312441427764989435",
    "5377535110289576661", "5195033767969839232", "5312441427764989435",
    "5287231198098117669", "5190806721286657692", "5312361253610475399",
    "5193177581888755275", "5411089297476441876", "5202113974312653146",
    "5399909394525737759", "5197269100878907942", "5202113974312653146",
    "5282843764451195532", "5224736245665511429", "5271604874419647061",
    "5323442290708985472", "5231012545799666522"
]

# Data files
DATA_DIR = "bot_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
REFERRALS_FILE = os.path.join(DATA_DIR, "referrals.json")

# Conversation states
ADMIN_PANEL = 1
ADD_CHANNEL = 2
REMOVE_CHANNEL = 3
SET_START_IMAGE = 4
BROADCAST_MSG = 5
ADD_ADMIN = 6
REMOVE_ADMIN = 7

# ==================== LOGGING ====================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATA MANAGEMENT ====================

def ensure_data_dir():
    """Create data directory if not exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_json(filename: str, default: dict = None) -> dict:
    """Load JSON data from file"""
    ensure_data_dir()
    if default is None:
        default = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
    return default

def save_json(filename: str, data: dict):
    """Save JSON data to file"""
    ensure_data_dir()
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")

# User data
def get_users() -> dict:
    return load_json(USERS_FILE, {})

def save_users(users: dict):
    save_json(USERS_FILE, users)

def get_user(user_id: int) -> dict:
    users = get_users()
    return users.get(str(user_id), {})

def update_user(user_id: int, data: dict):
    users = get_users()
    users[str(user_id)] = data
    save_users(users)

def add_user(user_id: int, username: str = None, first_name: str = None):
    users = get_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "joined_at": datetime.now().isoformat(),
            "channels_joined": [],
            "referrals": 0,
            "referred_by": None,
            "referral_code": f"REF{user_id}",
            "stage": "start"  # start, page1, page2, completed
        }
        save_users(users)

# Admin data
def get_admins() -> list:
    admins = load_json(ADMINS_FILE, [])
    if ADMIN_ID not in admins:
        admins.append(ADMIN_ID)
        save_json(ADMINS_FILE, admins)
    return admins

def is_admin(user_id: int) -> bool:
    return user_id in get_admins()

def add_admin(user_id: int) -> bool:
    admins = get_admins()
    if user_id not in admins:
        admins.append(user_id)
        save_json(ADMINS_FILE, admins)
        return True
    return False

def remove_admin(user_id: int) -> bool:
    admins = get_admins()
    if user_id in admins and user_id != ADMIN_ID:
        admins.remove(user_id)
        save_json(ADMINS_FILE, admins)
        return True
    return False

# Channel data
def get_channels() -> dict:
    return load_json(CHANNELS_FILE, {"page1": [], "page2": []})

def save_channels(channels: dict):
    save_json(CHANNELS_FILE, channels)

def add_channel(page: str, name: str, link: str, channel_id: str = None):
    channels = get_channels()
    if page not in channels:
        channels[page] = []
    channels[page].append({
        "name": name,
        "link": link,
        "channel_id": channel_id,
        "added_at": datetime.now().isoformat()
    })
    save_channels(channels)

def remove_channel(page: str, index: int):
    channels = get_channels()
    if page in channels and 0 <= index < len(channels[page]):
        channels[page].pop(index)
        save_channels(channels)
        return True
    return False

# Settings
def get_settings() -> dict:
    return load_json(SETTINGS_FILE, {
        "start_image": None,
        "start_caption": "🎉 Welcome to UPI Giveaway 2026! 🎉\n\nJoin all channels to participate!",
        "referral_target": 3,
        "contact_username": "colombusvi"
    })

def save_settings(settings: dict):
    save_json(SETTINGS_FILE, settings)

# Referrals
def get_referrals() -> dict:
    return load_json(REFERRALS_FILE, {})

def save_referrals(data: dict):
    save_json(REFERRALS_FILE, data)

def add_referral(referrer_id: int, referred_id: int):
    refs = get_referrals()
    if str(referrer_id) not in refs:
        refs[str(referrer_id)] = []
    if referred_id not in refs[str(referrer_id)]:
        refs[str(referrer_id)].append(referred_id)
        save_referrals(refs)

        # Update user referral count
        users = get_users()
        if str(referrer_id) in users:
            users[str(referrer_id)]["referrals"] = len(refs[str(referrer_id)])
            save_users(users)
        return True
    return False

def get_referral_count(user_id: int) -> int:
    refs = get_referrals()
    return len(refs.get(str(user_id), []))

# ==================== HELPER FUNCTIONS ====================

def get_random_emoji() -> str:
    """Get a random premium emoji"""
    emoji_id = random.choice(EMOJI_IDS)
    return f'<tg-emoji emoji-id="{emoji_id}">⭐</tg-emoji>'

def get_button_style(style: str) -> str:
    """Get button style color"""
    styles = {
        "success": "🟢",
        "danger": "🔴",
        "primary": "🔵",
        "warning": "🟡",
        "info": "⚪"
    }
    return styles.get(style, "🔵")

def create_channel_buttons(channels: list, page: str) -> List[List[InlineKeyboardButton]]:
    """Create channel link buttons in rows of 2"""
    buttons = []
    styles = ["success", "danger", "primary"]

    for i, ch in enumerate(channels):
        style = styles[i % len(styles)]
        emoji = get_random_emoji()
        btn = InlineKeyboardButton(
            text=f"{emoji} {ch['name']}",
            url=ch['link']
        )
        if i % 2 == 0:
            buttons.append([btn])
        else:
            buttons[-1].append(btn)

    return buttons

def get_channel_ids_from_links(channels: list) -> list:
    """Extract channel IDs from invite links"""
    ids = []
    for ch in channels:
        if ch.get("channel_id"):
            ids.append(ch["channel_id"])
        else:
            # Try to extract from link
            link = ch.get("link", "")
            if "t.me/" in link:
                parts = link.split("t.me/")
                if len(parts) > 1:
                    username = parts[1].split("/")[0].split("?")[0]
                    if username and not username.startswith("+"):
                        ids.append(f"@{username}")
    return ids

async def check_channel_membership(bot, user_id: int, channel_id: str) -> bool:
    """Check if user is member of a channel"""
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking membership for {channel_id}: {e}")
        return False

async def check_all_channels(bot, user_id: int, channels: list) -> tuple:
    """Check all channels and return (all_joined, not_joined_list)"""
    not_joined = []
    for ch in channels:
        ch_id = ch.get("channel_id") or ch.get("link")
        if ch_id:
            is_member = await check_channel_membership(bot, user_id, ch_id)
            if not is_member:
                not_joined.append(ch)
    return len(not_joined) == 0, not_joined

# ==================== KEYBOARD MARKUPS ====================

def get_start_keyboard() -> InlineKeyboardMarkup:
    """Get start page keyboard"""
    emoji = get_random_emoji()
    keyboard = [
        [InlineKeyboardButton(f"{emoji} Joined All Channels", callback_data="check_joined")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_page2_keyboard() -> InlineKeyboardMarkup:
    """Get page 2 keyboard"""
    emoji = get_random_emoji()
    keyboard = [
        [InlineKeyboardButton(f"{emoji} Recharge", callback_data="check_recharge")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_referral_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get referral keyboard"""
    bot_username = "UpiGiveaway2026Bot"  # Update this with actual bot username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    keyboard = [
        [InlineKeyboardButton("📤 Share Referral Link", url=f"https://t.me/share/url?url={referral_link}")],
        [InlineKeyboardButton("📋 Copy Link", callback_data="copy_ref_link")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Channel (Page 1)", callback_data="admin_add_ch1"),
         InlineKeyboardButton("➕ Add Channel (Page 2)", callback_data="admin_add_ch2")],
        [InlineKeyboardButton("➖ Remove Channel (Page 1)", callback_data="admin_rem_ch1"),
         InlineKeyboardButton("➖ Remove Channel (Page 2)", callback_data="admin_rem_ch2")],
        [InlineKeyboardButton("📊 List Channels", callback_data="admin_list_ch")],
        [InlineKeyboardButton("🖼 Set Start Image", callback_data="admin_set_img")],
        [InlineKeyboardButton("✏️ Set Caption", callback_data="admin_set_cap")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("➕ Add Admin", callback_data="admin_add_admin"),
         InlineKeyboardButton("➖ Remove Admin", callback_data="admin_rem_admin")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id

    # Add user to database
    add_user(user_id, user.username, user.first_name)

    # Handle referral
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id:
                add_referral(referrer_id, user_id)
                # Update referred_by
                users = get_users()
                if str(user_id) in users:
                    users[str(user_id)]["referred_by"] = referrer_id
                    save_users(users)
        except ValueError:
            pass

    settings = get_settings()
    channels = get_channels()
    page1_channels = channels.get("page1", [])

    # Build caption
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    caption = settings.get("start_caption", "Welcome to UPI Giveaway 2026!")
    caption += f"\n\n{emoji1} Join all channels then click on Joined!"

    # Build channel buttons
    channel_buttons = create_channel_buttons(page1_channels, "page1")

    # Add Joined button
    joined_button = [InlineKeyboardButton(f"{emoji2} Joined", callback_data="check_joined")]

    # Combine all buttons
    keyboard = channel_buttons + [joined_button]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send message with or without image
    if settings.get("start_image"):
        try:
            await update.message.reply_photo(
                photo=settings["start_image"],
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await update.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
    else:
        await update.message.reply_text(
            caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    # Update user stage
    update_user(user_id, {**get_user(user_id), "stage": "page1"})

async def check_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Joined button click - check channel membership"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    bot = context.bot
    channels = get_channels()
    page1_channels = channels.get("page1", [])

    if not page1_channels:
        await query.edit_message_text(
            "⚠️ No channels configured. Please contact admin.",
            parse_mode=ParseMode.HTML
        )
        return

    # Check all channels
    all_joined, not_joined = await check_all_channels(bot, user_id, page1_channels)

    if all_joined:
        # User joined all channels, proceed to page 2
        emoji = get_random_emoji()
        page2_channels = channels.get("page2", [])

        caption = f"{emoji} Join these channels also, then click Recharge!"

        channel_buttons = create_channel_buttons(page2_channels, "page2")
        recharge_button = [InlineKeyboardButton(f"{emoji} Recharge", callback_data="check_recharge")]

        keyboard = channel_buttons + [recharge_button]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(
                caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await query.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

        update_user(user_id, {**get_user(user_id), "stage": "page2"})
    else:
        # User hasn't joined all channels, show remaining ones
        emoji = get_random_emoji()
        caption = f"❌ You haven't joined all channels yet!\n\n{emoji} Please join these channels:"

        channel_buttons = create_channel_buttons(not_joined, "page1")
        joined_button = [InlineKeyboardButton(f"{emoji} Joined", callback_data="check_joined")]

        keyboard = channel_buttons + [joined_button]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(
                caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await query.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

async def check_recharge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Recharge button click - check page 2 channels and show referral"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    bot = context.bot
    channels = get_channels()
    page2_channels = channels.get("page2", [])
    settings = get_settings()

    if page2_channels:
        all_joined, not_joined = await check_all_channels(bot, user_id, page2_channels)

        if not all_joined:
            emoji = get_random_emoji()
            caption = f"❌ You haven't joined all channels yet!\n\n{emoji} Please join these channels:"

            channel_buttons = create_channel_buttons(not_joined, "page2")
            recharge_button = [InlineKeyboardButton(f"{emoji} Recharge", callback_data="check_recharge")]

            keyboard = channel_buttons + [recharge_button]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await query.edit_message_text(
                    caption,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                await query.message.reply_text(
                    caption,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            return

    # All channels joined, show referral system
    ref_count = get_referral_count(user_id)
    target = settings.get("referral_target", 3)
    contact = settings.get("contact_username", "colombusvi")

    emoji = get_random_emoji()

    if ref_count >= target:
        caption = (
            f"🎉 Congratulations! 🎉\n\n"
            f"You have completed {ref_count}/{target} referrals!\n\n"
            f"✅ Please contact @{contact} for your profit!"
        )
        keyboard = [[InlineKeyboardButton(f"📞 Contact @{contact}", url=f"https://t.me/{contact}")]]
    else:
        remaining = target - ref_count
        caption = (
            f"{emoji} Referral System\n\n"
            f"📊 Your Referrals: {ref_count}/{target}\n"
            f"⏳ Remaining: {remaining}\n\n"
            f"Share your referral link to get {target} referrals and claim your reward!"
        )
        keyboard = get_referral_keyboard(user_id).inline_keyboard

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(
            caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await query.message.reply_text(
            caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    update_user(user_id, {**get_user(user_id), "stage": "referral"})

async def copy_ref_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle copy referral link button"""
    query = update.callback_query
    user_id = query.from_user.id
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    await query.answer(f"Link: {referral_link}", show_alert=True)

# ==================== ADMIN PANEL ====================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ You are not authorized to access the admin panel.")
        return

    await update.message.reply_text(
        "🔧 <b>Admin Panel</b>\n\nWelcome to the admin dashboard!",
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.edit_message_text("❌ Unauthorized access.")
        return

    data = query.data

    if data == "admin_back":
        await query.edit_message_text(
            "🔧 <b>Admin Panel</b>\n\nWelcome to the admin dashboard!",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )

    elif data == "admin_add_ch1":
        context.user_data["add_channel_page"] = "page1"
        await query.edit_message_text(
            "➕ <b>Add Channel to Page 1</b>\n\n"
            "Send channel details in format:\n"
            "<code>Name | Link | ChannelID(optional)</code>\n\n"
            "Example:\n"
            "<code>My Channel | https://t.me/mychannel | @mychannel</code>\n\n"
            "Or send /cancel to abort.",
            parse_mode=ParseMode.HTML
        )
        return ADD_CHANNEL

    elif data == "admin_add_ch2":
        context.user_data["add_channel_page"] = "page2"
        await query.edit_message_text(
            "➕ <b>Add Channel to Page 2</b>\n\n"
            "Send channel details in format:\n"
            "<code>Name | Link | ChannelID(optional)</code>\n\n"
            "Example:\n"
            "<code>My Channel | https://t.me/mychannel | @mychannel</code>\n\n"
            "Or send /cancel to abort.",
            parse_mode=ParseMode.HTML
        )
        return ADD_CHANNEL

    elif data == "admin_rem_ch1":
        channels = get_channels()
        page1 = channels.get("page1", [])

        if not page1:
            await query.edit_message_text(
                "❌ No channels in Page 1.",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
            return

        text = "➖ <b>Remove Channel from Page 1</b>\n\n"
        keyboard = []
        for i, ch in enumerate(page1):
            text += f"{i+1}. {ch['name']} - {ch['link']}\n"
            keyboard.append([InlineKeyboardButton(f"❌ {ch['name']}", callback_data=f"rem_ch1_{i}")])

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    elif data == "admin_rem_ch2":
        channels = get_channels()
        page2 = channels.get("page2", [])

        if not page2:
            await query.edit_message_text(
                "❌ No channels in Page 2.",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
            return

        text = "➖ <b>Remove Channel from Page 2</b>\n\n"
        keyboard = []
        for i, ch in enumerate(page2):
            text += f"{i+1}. {ch['name']} - {ch['link']}\n"
            keyboard.append([InlineKeyboardButton(f"❌ {ch['name']}", callback_data=f"rem_ch2_{i}")])

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    elif data.startswith("rem_ch1_"):
        index = int(data.split("_")[2])
        if remove_channel("page1", index):
            await query.edit_message_text(
                "✅ Channel removed from Page 1!",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                "❌ Failed to remove channel.",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )

    elif data.startswith("rem_ch2_"):
        index = int(data.split("_")[2])
        if remove_channel("page2", index):
            await query.edit_message_text(
                "✅ Channel removed from Page 2!",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                "❌ Failed to remove channel.",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )

    elif data == "admin_list_ch":
        channels = get_channels()
        text = "📊 <b>Channel List</b>\n\n"

        text += "<b>Page 1 Channels:</b>\n"
        for i, ch in enumerate(channels.get("page1", []), 1):
            text += f"{i}. {ch['name']} - {ch['link']}\n"

        text += "\n<b>Page 2 Channels:</b>\n"
        for i, ch in enumerate(channels.get("page2", []), 1):
            text += f"{i}. {ch['name']} - {ch['link']}\n"

        await query.edit_message_text(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )

    elif data == "admin_set_img":
        await query.edit_message_text(
            "🖼 <b>Set Start Image</b>\n\n"
            "Send an image to set as the start image.\n"
            "Or send /cancel to abort.",
            parse_mode=ParseMode.HTML
        )
        return SET_START_IMAGE

    elif data == "admin_set_cap":
        await query.edit_message_text(
            "✏️ <b>Set Start Caption</b>\n\n"
            "Send the new caption text.\n"
            "Or send /cancel to abort.",
            parse_mode=ParseMode.HTML
        )
        context.user_data["setting"] = "caption"
        return BROADCAST_MSG

    elif data == "admin_broadcast":
        await query.edit_message_text(
            "📢 <b>Broadcast Message</b>\n\n"
            "Send the message you want to broadcast to all users.\n"
            "You can send text, photo, video, audio, or any media.\n\n"
            "Or send /cancel to abort.",
            parse_mode=ParseMode.HTML
        )
        context.user_data["setting"] = "broadcast"
        return BROADCAST_MSG

    elif data == "admin_add_admin":
        await query.edit_message_text(
            "➕ <b>Add Admin</b>\n\n"
            "Send the User ID of the new admin.\n"
            "Or send /cancel to abort.",
            parse_mode=ParseMode.HTML
        )
        return ADD_ADMIN

    elif data == "admin_rem_admin":
        admins = get_admins()
        text = "➖ <b>Remove Admin</b>\n\n"
        keyboard = []
        for admin_id in admins:
            if admin_id != ADMIN_ID:
                text += f"• {admin_id}\n"
                keyboard.append([InlineKeyboardButton(f"❌ {admin_id}", callback_data=f"rem_admin_{admin_id}")])

        if not keyboard:
            text += "No removable admins.\n"

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    elif data.startswith("rem_admin_"):
        admin_id = int(data.split("_")[2])
        if remove_admin(admin_id):
            await query.edit_message_text(
                f"✅ Admin {admin_id} removed!",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                "❌ Failed to remove admin.",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )

    elif data == "admin_stats":
        users = get_users()
        referrals = get_referrals()
        channels = get_channels()

        total_users = len(users)
        total_refs = sum(len(v) for v in referrals.values())
        completed_users = sum(1 for u in users.values() if u.get("referrals", 0) >= 3)

        text = (
            "📊 <b>Bot Statistics</b>\n\n"
            f"👥 Total Users: {total_users}\n"
            f"🔗 Total Referrals: {total_refs}\n"
            f"✅ Completed Users: {completed_users}\n"
            f"📢 Page 1 Channels: {len(channels.get('page1', []))}\n"
            f"📢 Page 2 Channels: {len(channels.get('page2', []))}\n"
        )

        await query.edit_message_text(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )

async def add_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding a new channel"""
    if update.message.text == "/cancel":
        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    page = context.user_data.get("add_channel_page", "page1")

    try:
        parts = update.message.text.split("|")
        name = parts[0].strip()
        link = parts[1].strip()
        channel_id = parts[2].strip() if len(parts) > 2 else None

        add_channel(page, name, link, channel_id)

        await update.message.reply_text(
            f"✅ Channel added to {page}!\n\n"
            f"Name: {name}\n"
            f"Link: {link}",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {e}\n\n"
            "Please use format: <code>Name | Link | ChannelID(optional)</code>",
            parse_mode=ParseMode.HTML
        )

    return ConversationHandler.END

async def set_start_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting start image"""
    if update.message.text == "/cancel":
        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    if update.message.photo:
        photo = update.message.photo[-1]
        file_id = photo.file_id

        settings = get_settings()
        settings["start_image"] = file_id
        save_settings(settings)

        await update.message.reply_text(
            "✅ Start image set successfully!",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            "❌ Please send an image. Try again or send /cancel.",
            parse_mode=ParseMode.HTML
        )
        return SET_START_IMAGE

    return ConversationHandler.END

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message"""
    setting = context.user_data.get("setting", "")

    if update.message.text == "/cancel":
        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    if setting == "caption":
        settings = get_settings()
        settings["start_caption"] = update.message.text
        save_settings(settings)

        await update.message.reply_text(
            "✅ Start caption updated!",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    # Broadcast
    users = get_users()
    sent = 0
    failed = 0

    await update.message.reply_text("📢 Broadcasting... Please wait.")

    for user_id in users.keys():
        try:
            if update.message.text:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=update.message.text,
                    parse_mode=ParseMode.HTML
                )
            elif update.message.photo:
                await context.bot.send_photo(
                    chat_id=int(user_id),
                    photo=update.message.photo[-1].file_id,
                    caption=update.message.caption,
                    parse_mode=ParseMode.HTML
                )
            elif update.message.video:
                await context.bot.send_video(
                    chat_id=int(user_id),
                    video=update.message.video.file_id,
                    caption=update.message.caption,
                    parse_mode=ParseMode.HTML
                )
            elif update.message.audio:
                await context.bot.send_audio(
                    chat_id=int(user_id),
                    audio=update.message.audio.file_id,
                    caption=update.message.caption,
                    parse_mode=ParseMode.HTML
                )
            elif update.message.voice:
                await context.bot.send_voice(
                    chat_id=int(user_id),
                    voice=update.message.voice.file_id,
                    caption=update.message.caption
                )
            elif update.message.document:
                await context.bot.send_document(
                    chat_id=int(user_id),
                    document=update.message.document.file_id,
                    caption=update.message.caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.copy_message(
                    chat_id=int(user_id),
                    from_chat_id=update.effective_chat.id,
                    message_id=update.message.message_id
                )
            sent += 1
            await asyncio.sleep(0.05)  # Rate limit
        except Exception as e:
            logger.error(f"Failed to send to {user_id}: {e}")
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast completed!\n\n"
        f"📤 Sent: {sent}\n"
        f"❌ Failed: {failed}",
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.HTML
    )

    return ConversationHandler.END

async def add_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding a new admin"""
    if update.message.text == "/cancel":
        await update.message.reply_text(
            "❌ Cancelled.",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    try:
        new_admin_id = int(update.message.text.strip())
        if add_admin(new_admin_id):
            await update.message.reply_text(
                f"✅ Admin {new_admin_id} added successfully!",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                "❌ User is already an admin.",
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid User ID. Please send a valid number.",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text(
        "❌ Cancelled.",
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

# ==================== CHANNEL JOIN MONITORING ====================

async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor channel join requests"""
    # This handles chat member updates
    if update.chat_member:
        chat = update.chat_member.chat
        user = update.chat_member.from_user
        new_status = update.chat_member.new_chat_member.status
        old_status = update.chat_member.old_chat_member.status

        # Check if user joined or sent request
        if old_status in ["left", "kicked"] and new_status in ["member", "restricted", "administrator", "creator"]:
            # User joined the channel
            logger.info(f"User {user.id} joined channel {chat.id}")

            # Check if bot is admin in this channel
            try:
                bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                if bot_member.status == "administrator":
                    # Send DM to user
                    try:
                        emoji = get_random_emoji()
                        await context.bot.send_message(
                            chat_id=user.id,
                            text=f"{emoji} Welcome! You've joined {chat.title}. Please return to the bot and click 'Joined' to continue.",
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        logger.error(f"Failed to send DM to {user.id}: {e}")
            except Exception as e:
                logger.error(f"Error checking bot status: {e}")

async def join_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle join requests"""
    if update.chat_join_request:
        chat = update.chat_join_request.chat
        user = update.chat_join_request.from_user

        logger.info(f"Join request from {user.id} for {chat.id}")

        # Auto-approve if bot is admin
        try:
            bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
            if bot_member.status == "administrator" and bot_member.can_invite_users:
                await context.bot.approve_chat_join_request(chat.id, user.id)

                # Send DM
                try:
                    emoji = get_random_emoji()
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=f"{emoji} Your request to join {chat.title} has been approved! Please return to the bot and click 'Joined' to continue.",
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Failed to send DM to {user.id}: {e}")
        except Exception as e:
            logger.error(f"Error handling join request: {e}")

# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
        except:
            pass

# ==================== MAIN ====================

def main():
    """Start the bot"""
    # Initialize data
    ensure_data_dir()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))

    # Admin conversation handler
    admin_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_callback, pattern="^admin_")
        ],
        states={
            ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_handler)],
            SET_START_IMAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, set_start_image_handler)],
            BROADCAST_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_handler)],
            ADD_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(admin_conv_handler)

    # Callback handlers
    application.add_handler(CallbackQueryHandler(check_joined_callback, pattern="^check_joined$"))
    application.add_handler(CallbackQueryHandler(check_recharge_callback, pattern="^check_recharge$"))
    application.add_handler(CallbackQueryHandler(copy_ref_link_callback, pattern="^copy_ref_link$"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^rem_ch"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^rem_admin_"))

    # Chat member handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.CHAT_MEMBER, chat_member_update))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, chat_member_update))

    # Error handler
    application.add_error_handler(error_handler)

    # Start bot
    logger.info("Starting UPI Giveaway 2026 Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
