import os
import asyncio
import logging
import sqlite3
import random
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Replit Secrets से टोकन लोड करेगा, बैकअप में आपका टोकन रहेगा
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8618863127:AAETZui9nNScDi9Rjjjs7bHVJOSCR1CgfzE")
MAIN_ADMIN_ID = 8674318569
DB_FILE = "upi_giveaway_bot.db"

# List of premium custom emoji IDs
PREMIUM_EMOJIS = [
    "6023898164732366954", "6026106482297147601", "6026088864341299395", "6026322523447103813",
    "6023667769801707824", "6023974774064026637", "6023725524226937667", "6026056450223116307",
    "6025881009399010995", "6026186540487548120", "6026031371909074667", "6026233591854272586",
    "6026140395358916313", "6026316720946286399", "6026243612012974483", "6026243289890427139",
    "6026329335265234977", "6026321200597176575", "6030687219537154393", "6033108614724456536",
    "6035339257529242355", "6033006935668692007", "5785109764170060865", "6033059948450025914",
    "5782749628101300654", "5783164994388497098", "5782853931382084496", "6025878226260202192",
    "6026162407066309019", "5195033767969839232", "5312441427764989435", "5377535110289576661",
    "5287231198098117669", "5190806721286657692", "5312361253610475399", "5193177581888755275",
    "5411089297476441876", "5202113974312653146", "5399909394525737759", "5197269100878907942",
    "5282843764451195532", "5224736245665511429", "5271604874419647061", "5323442290708985472",
    "5231012545799666522"
]

# Database helpers
def execute_query(query, params=(), fetchall=False, fetchone=False):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = None
    if fetchall:
        data = cursor.fetchall()
    elif fetchone:
        data = cursor.fetchone()
    conn.commit()
    conn.close()
    return data

def init_db():
    execute_query("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        referred_by INTEGER,
        referrals_count INTEGER DEFAULT 0,
        has_completed_all INTEGER DEFAULT 0,
        notified INTEGER DEFAULT 0
    )
    """)
    execute_query("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
    """)
    execute_query("""
    CREATE TABLE IF NOT EXISTS channels_primary (
        channel_id TEXT PRIMARY KEY,
        link TEXT,
        name TEXT
    )
    """)
    execute_query("""
    CREATE TABLE IF NOT EXISTS channels_secondary (
        channel_id TEXT PRIMARY KEY,
        link TEXT,
        name TEXT
    )
    """)
    execute_query("""
    CREATE TABLE IF NOT EXISTS join_requests (
        user_id INTEGER,
        channel_id TEXT,
        PRIMARY KEY (user_id, channel_id)
    )
    """)
    execute_query("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    execute_query("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (MAIN_ADMIN_ID,))
    execute_query("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("start_caption", "Join all channels then click joined."))
    execute_query("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("start_image", ""))

# Admin & User DB wrappers
def add_user(user_id, referred_by=None):
    execute_query("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))

def get_user(user_id):
    return execute_query("SELECT * FROM users WHERE user_id = ?", (user_id,), fetchone=True)

def is_admin(user_id):
    res = execute_query("SELECT user_id FROM admins WHERE user_id = ?", (user_id,), fetchone=True)
    return res is not None

def add_admin(user_id):
    execute_query("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))

def remove_admin(user_id):
    execute_query("DELETE FROM admins WHERE user_id = ?", (user_id,))

def get_all_admins():
    res = execute_query("SELECT user_id FROM admins", fetchall=True)
    return [row[0] for row in res]

def add_primary_channel(channel_id, link, name):
    execute_query("INSERT OR REPLACE INTO channels_primary (channel_id, link, name) VALUES (?, ?, ?)", (channel_id, link, name))

def remove_primary_channel(channel_id):
    execute_query("DELETE FROM channels_primary WHERE channel_id = ?", (channel_id,))

def get_primary_channels():
    return execute_query("SELECT channel_id, link, name FROM channels_primary", fetchall=True)

def add_secondary_channel(channel_id, link, name):
    execute_query("INSERT OR REPLACE INTO channels_secondary (channel_id, link, name) VALUES (?, ?, ?)", (channel_id, link, name))

def remove_secondary_channel(channel_id):
    execute_query("DELETE FROM channels_secondary WHERE channel_id = ?", (channel_id,))

def get_secondary_channels():
    return execute_query("SELECT channel_id, link, name FROM channels_secondary", fetchall=True)

def db_add_join_request(user_id, channel_id):
    execute_query("INSERT OR IGNORE INTO join_requests (user_id, channel_id) VALUES (?, ?)", (user_id, str(channel_id)))

def db_check_join_request(user_id, channel_id):
    res = execute_query("SELECT user_id FROM join_requests WHERE user_id = ? AND channel_id = ?", (user_id, str(channel_id)), fetchone=True)
    return res is not None

def get_setting(key):
    res = execute_query("SELECT value FROM settings WHERE key = ?", (key,), fetchone=True)
    return res[0] if res else ""

def set_setting(key, value):
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

def get_all_users():
    res = execute_query("SELECT user_id FROM users", fetchall=True)
    return [row[0] for row in res]

# Premium Emoji formatting
def get_premium_html(index, fallback="✨"):
    if 0 <= index < len(PREMIUM_EMOJIS):
        return f'<tg-emoji emoji-id="{PREMIUM_EMOJIS[index]}">{fallback}</tg-emoji>'
    return fallback

def get_random_premium_html():
    idx = random.randint(0, len(PREMIUM_EMOJIS) - 1)
    return get_premium_html(idx)

# Membership validation
async def check_user_joined(bot, user_id, channel_id):
    if db_check_join_request(user_id, channel_id):
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member', 'restricted']:
            return True
    except Exception:
        pass
    return False

async def get_missing_primary_channels(bot, user_id):
    channels = get_primary_channels()
    missing = []
    for ch_id, link, name in channels:
        joined = await check_user_joined(bot, user_id, ch_id)
        if not joined:
            missing.append((ch_id, link, name))
    return missing

async def get_missing_secondary_channels(bot, user_id):
    channels = get_secondary_channels()
    missing = []
    for ch_id, link, name in channels:
        joined = await check_user_joined(bot, user_id, ch_id)
        if not joined:
            missing.append((ch_id, link, name))
    return missing

# FSM States
class AdminStates(StatesGroup):
    waiting_for_primary_channel = State()
    waiting_for_secondary_channel = State()
    waiting_for_broadcast = State()
    waiting_for_caption = State()
    waiting_for_photo = State()
    waiting_for_admin_add = State()

# Initialize Bot & Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# UI Builder
def build_channel_keyboard(channels, action_btn_text, callback_data):
    buttons = []
    row = []
    styles = ["🟢", "🔴", "🔵"]  # Simulates success, danger, primary colors
    for idx, (ch_id, link, name) in enumerate(channels):
        style = styles[idx % len(styles)]
        row.append(InlineKeyboardButton(text=f"{style} {name}", url=link))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=action_btn_text, callback_data=callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Referral logic complete
async def complete_user_tasks(bot, user_id):
    user = get_user(user_id)
    if not user:
        return
    referred_by = user[1]
    has_completed_all = user[3]
    
    if has_completed_all == 1:
        return
        
    execute_query("UPDATE users SET has_completed_all = 1 WHERE user_id = ?", (user_id,))
    
    if referred_by:
        execute_query("UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = ?", (referred_by,))
        ref_user = get_user(referred_by)
        if ref_user:
            ref_count = ref_user[2]
            ref_notified = ref_user[4]
            if ref_count >= 3 and ref_notified == 0:
                execute_query("UPDATE users SET notified = 1 WHERE user_id = ?", (referred_by,))
                try:
                    emoji = get_random_premium_html()
                    await bot.send_message(
                        chat_id=referred_by,
                        text=f"{emoji} <b>Congratulations!</b> You have successfully referred 3 users.\n\nPlease contact @colombusvi for profit.",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

# Flow Handlers
async def show_primary_page(message_or_call, user_id, bot, missing_channels):
    caption_tmpl = get_setting("start_caption")
    image_val = get_setting("start_image")
    emoji1 = get_random_premium_html()
    emoji2 = get_random_premium_html()
    caption = f"{emoji1} <b>UPI GIVEAWAY 2026</b> {emoji2}\n\n" + caption_tmpl
    kb = build_channel_keyboard(missing_channels, "Joined ✅", "user_joined_primary")
    
    is_callback = isinstance(message_or_call, types.CallbackQuery)
    target = message_or_call.message if is_callback else message_or_call
    
    if image_val:
        try:
            await target.answer_photo(photo=image_val, caption=caption, reply_markup=kb, parse_mode="HTML")
            if is_callback:
                await message_or_call.answer()
            return
        except Exception:
            pass
            
    await target.answer(text=caption, reply_markup=kb, parse_mode="HTML")
    if is_callback:
        await message_or_call.answer()

async def show_secondary_page(call, user_id, bot, missing_channels):
    emoji1 = get_random_premium_html()
    emoji2 = get_random_premium_html()
    caption = f"{emoji1} <b>Join these channels also</b>, then click recharge {emoji2}"
    kb = build_channel_keyboard(missing_channels, "Recharge ⚡", "user_recharge")
    await call.message.answer(text=caption, reply_markup=kb, parse_mode="HTML")
    await call.answer()

async def show_referral_page(message_or_call, user_id, bot):
    user_info = get_user(user_id)
    if not user_info:
        return
    ref_count = user_info[2]
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    emoji1 = get_random_premium_html()
    emoji2 = get_random_premium_html()
    
    text = (
        f"{emoji1} <b>UPI GIVEAWAY 2026</b> {emoji2}\n\n"
        f"Share your referral link with your friends. Once 3 friends successfully join, you can claim your cash!\n\n"
        f"🔗 <b>Your Referral Link:</b>\n<code>https://t.me/{bot_username}?start={user_id}</code>\n\n"
        f"👥 <b>Total Referrals:</b> <code>{ref_count}/3</code>"
    )
    if ref_count >= 3:
        text += f"\n\n📢 Please contact @colombusvi for profit."
        
    is_callback = isinstance(message_or_call, types.CallbackQuery)
    target = message_or_call.message if is_callback else message_or_call
    await target.answer(text=text, parse_mode="HTML")
    if is_callback:
        await call.answer()

# Handlers
@dp.message(CommandStart())
async def start_cmd(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    args = message.text.split()
    referred_by = None
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id != user_id:
                referred_by = ref_id
        except ValueError:
            pass
            
    add_user(user_id, referred_by)
    
    user_info = get_user(user_id)
    if user_info and user_info[3] == 1:
        await show_referral_page(message, user_id, bot)
        return

    missing_prim = await get_missing_primary_channels(bot, user_id)
    if not missing_prim:
        missing_sec = await get_missing_secondary_channels(bot, user_id)
        if not missing_sec:
            await complete_user_tasks(bot, user_id)
            await show_referral_page(message, user_id, bot)
        else:
            await show_secondary_page(message, user_id, bot, missing_sec)
    else:
        await show_primary_page(message, user_id, bot, missing_prim)

@dp.callback_query(F.data == "user_joined_primary")
async def handle_joined_primary(call: types.CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    missing_prim = await get_missing_primary_channels(bot, user_id)
    if missing_prim:
        await call.answer("❌ You haven't joined all primary channels yet!", show_alert=True)
        kb = build_channel_keyboard(missing_prim, "Joined ✅", "user_joined_primary")
        try:
            await call.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass
    else:
        missing_sec = await get_missing_secondary_channels(bot, user_id)
        if not missing_sec:
            await complete_user_tasks(bot, user_id)
            await show_referral_page(call, user_id, bot)
        else:
            await show_secondary_page(call, user_id, bot, missing_sec)

@dp.callback_query(F.data == "user_recharge")
async def handle_user_recharge(call: types.CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    missing_prim = await get_missing_primary_channels(bot, user_id)
    if missing_prim:
        await call.answer("❌ You left some primary channels!", show_alert=True)
        await show_primary_page(call, user_id, bot, missing_prim)
        return
        
    missing_sec = await get_missing_secondary_channels(bot, user_id)
    if missing_sec:
        await call.answer("❌ You haven't joined all secondary channels yet!", show_alert=True)
        kb = build_channel_keyboard(missing_sec, "Recharge ⚡", "user_recharge")
        try:
            await call.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass
    else:
        await complete_user_tasks(bot, user_id)
        await show_referral_page(call, user_id, bot)

# Auto DM Join Request Handlers
@dp.chat_join_request()
async def chat_join_request_handler(update: types.ChatJoinRequest, bot: Bot):
    user_id = update.from_user.id
    channel_id = str(update.chat.id)
    db_add_join_request(user_id, channel_id)
    text = "Free recharge chahiye to niche Wale button pr click kro or request bhejo fast"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Button ⚡", url="https://t.me/+6zrihmlthXk1NWIx")]
    ])
    try:
        await bot.send_message(chat_id=user_id, text=text, reply_markup=kb)
    except Exception:
        pass

# Admin controls & keyboard
def get_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Add Primary", callback_data="adm_add_prim"),
            InlineKeyboardButton(text="❌ Remove Primary", callback_data="adm_rem_prim")
        ],
        [
            InlineKeyboardButton(text="➕ Add Secondary", callback_data="adm_add_sec"),
            InlineKeyboardButton(text="❌ Remove Secondary", callback_data="adm_rem_sec")
        ],
        [
            InlineKeyboardButton(text="🖼 Set Start Image", callback_data="adm_set_img"),
            InlineKeyboardButton(text="📝 Set Start Caption", callback_data="adm_set_cap")
        ],
        [
            InlineKeyboardButton(text="👤 Add Admin", callback_data="adm_add_adm"),
            InlineKeyboardButton(text="🗑 Remove Admin", callback_data="adm_rem_adm")
        ],
        [
            InlineKeyboardButton(text="📢 Broadcast", callback_data="adm_broadcast"),
            InlineKeyboardButton(text="📊 Stats", callback_data="adm_stats")
        ]
    ])

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("🔑 <b>Welcome to Admin Control Panel:</b>", reply_markup=get_admin_kb(), parse_mode="HTML")
    else:
        await message.answer("⚠️ You do not have access to this command.")

# Callback triggers for Admin options
@dp.callback_query(F.data == "adm_add_prim")
async def add_prim_cb(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await call.message.answer("Send primary channel details in this format:\n\n<code>channel_id | invite_link | Channel Name</code>\n\nExample:\n<code>-100123456789 | https://t.me/+xyz | Channel 1</code>", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_primary_channel)
    await call.answer()

@dp.callback_query(F.data == "adm_add_sec")
async def add_sec_cb(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await call.message.answer("Send secondary channel details in this format:\n\n<code>channel_id | invite_link | Channel Name</code>\n\nExample:\n<code>-100123456789 | https://t.me/+xyz | Channel 2</code>", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_secondary_channel)
    await call.answer()

@dp.callback_query(F.data == "adm_set_img")
async def set_img_cb(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await call.message.answer("Please send the photo you want to set as start image.")
    await state.set_state(AdminStates.waiting_for_photo)
    await call.answer()

@dp.callback_query(F.data == "adm_set_cap")
async def set_cap_cb(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await call.message.answer("Please send the new start caption text. You can use standard HTML.")
    await state.set_state(AdminStates.waiting_for_caption)
    await call.answer()

@dp.callback_query(F.data == "adm_add_adm")
async def add_adm_cb(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await call.message.answer("Please send the User ID of the new admin.")
    await state.set_state(AdminStates.waiting_for_admin_add)
    await call.answer()

@dp.callback_query(F.data == "adm_broadcast")
async def broadcast_cb(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await call.message.answer("Please send the message you want to broadcast. It can contain any text, image, stickers or audio!")
    await state.set_state(AdminStates.waiting_for_broadcast)
    await call.answer()

@dp.callback_query(F.data == "adm_stats")
async def stats_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id): return
    total_users = len(get_all_users())
    primary_count = len(get_primary_channels())
    secondary_count = len(get_secondary_channels())
    completed_count = execute_query("SELECT COUNT(*) FROM users WHERE has_completed_all = 1", fetchone=True)[0]
    
    text = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👤 Total registered users: <b>{total_users}</b>\n"
        f"✅ Completed referrals tasks: <b>{completed_count}</b>\n"
        f"🔌 Primary Channels: <b>{primary_count}</b>\n"
        f"🔌 Secondary Channels: <b>{secondary_count}</b>"
    )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

# State Processors
@dp.message(AdminStates.waiting_for_primary_channel)
async def process_primary_ch(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        parts = [p.strip() for p in message.text.split("|")]
        if len(parts) != 3:
            await message.answer("❌ Invalid format. Use: <code>channel_id | invite_link | Channel Name</code>", parse_mode="HTML")
            return
        ch_id, link, name = parts
        add_primary_channel(ch_id, link, name)
        await message.answer(f"✅ Primary channel <b>{name}</b> added!", parse_mode="HTML")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")

@dp.message(AdminStates.waiting_for_secondary_channel)
async def process_secondary_ch(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        parts = [p.strip() for p in message.text.split("|")]
        if len(parts) != 3:
            await message.answer("❌ Invalid format. Use: <code>channel_id | invite_link | Channel Name</code>", parse_mode="HTML")
            return
        ch_id, link, name = parts
        add_secondary_channel(ch_id, link, name)
        await message.answer(f"✅ Secondary channel <b>{name}</b> added!", parse_mode="HTML")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")

@dp.message(AdminStates.waiting_for_photo)
async def process_start_photo(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    if not message.photo:
        await message.answer("❌ Please send an image.")
        return
    file_id = message.photo[-1].file_id
    set_setting("start_image", file_id)
    await message.answer("✅ Start Image updated successfully!")
    await state.clear()

@dp.message(AdminStates.waiting_for_caption)
async def process_start_caption(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    set_setting("start_caption", message.html_text)
    await message.answer("✅ Start Caption updated successfully!")
    await state.clear()

@dp.message(AdminStates.waiting_for_admin_add)
async def process_admin_add(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    try:
        new_adm_id = int(message.text.strip())
        add_admin(new_adm_id)
        await message.answer(f"✅ Admin <code>{new_adm_id}</code> added successfully!", parse_mode="HTML")
        await state.clear()
    except ValueError:
        await message.answer("❌ Please send a valid numeric ID.")

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    await message.answer("📢 Broadcast started. Sending to all users...")
    all_users = get_all_users()
    success_count = 0
    fail_count = 0
    
    for user_id in all_users:
        try:
            await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1
            
    await message.answer(f"📢 <b>Broadcast Completed!</b>\n\n✅ Sent successfully: <b>{success_count}</b>\n❌ Failed: <b>{fail_count}</b>", parse_mode="HTML")
    await state.clear()

# Delete Lists Handlers
@dp.callback_query(F.data == "adm_rem_prim")
async def rem_prim_list(call: types.CallbackQuery):
    if not is_admin(call.from_user.id): return
    channels = get_primary_channels()
    if not channels:
        await call.message.answer("There are no primary channels.")
        await call.answer()
        return
    buttons = []
    for ch_id, link, name in channels:
        buttons.append([InlineKeyboardButton(text=f"❌ {name}", callback_data=f"del_prim_{ch_id}")])
    await call.message.answer("Select primary channel to delete:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@dp.callback_query(F.data.startswith("del_prim_"))
async def delete_prim_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id): return
    ch_id = call.data[len("del_prim_"):]
    remove_primary_channel(ch_id)
    await call.message.edit_text(f"✅ Primary channel removed!")
    await call.answer()

@dp.callback_query(F.data == "adm_rem_sec")
async def rem_sec_list(call: types.CallbackQuery):
    if not is_admin(call.from_user.id): return
    channels = get_secondary_channels()
    if not channels:
        await call.message.answer("There are no secondary channels.")
        await call.answer()
        return
    buttons = []
    for ch_id, link, name in channels:
        buttons.append([InlineKeyboardButton(text=f"❌ {name}", callback_data=f"del_sec_{ch_id}")])
    await call.message.answer("Select secondary channel to delete:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@dp.callback_query(F.data.startswith("del_sec_"))
async def delete_sec_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id): return
    ch_id = call.data[len("del_sec_"):]
    remove_secondary_channel(ch_id)
    await call.message.edit_text(f"✅ Secondary channel removed!")
    await call.answer()

@dp.callback_query(F.data == "adm_rem_adm")
async def rem_adm_list(call: types.CallbackQuery):
    if not is_admin(call.from_user.id): return
    admins = get_all_admins()
    buttons = []
    for adm_id in admins:
        if adm_id == MAIN_ADMIN_ID:
            continue
        buttons.append([InlineKeyboardButton(text=f"❌ Admin: {adm_id}", callback_data=f"del_adm_{adm_id}")])
    if not buttons:
        await call.message.answer("No additional admins to remove.")
        await call.answer()
        return
    await call.message.answer("Select admin to remove:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@dp.callback_query(F.data.startswith("del_adm_"))
async def delete_adm_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id): return
    adm_id = int(call.data[len("del_adm_"):])
    remove_admin(adm_id)
    await call.message.edit_text(f"✅ Admin removed!")
    await call.answer()


# Replit Keep-Alive Web Server
async def handle_ping(request):
    return web.Response(text="Upi Giveaway Bot is Online!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    # Replit automatically assigns port 8080 for web applications
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Keep-Alive Web Server started on port 8080!")

# Runner
async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    
    # Start web server for Replit
    try:
        await start_web_server()
    except Exception as e:
        print(f"Web server failed to start: {e}")

    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())