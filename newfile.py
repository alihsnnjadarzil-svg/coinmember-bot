import urllib.request
import urllib.parse
import json
import sqlite3
import time


# ==================================================
# SETTINGS
# ==================================================

BOT_TOKEN = "8811623243:AAFLB0GFFaOgDM2_Blny6DKaTmM01oBHtS0"

ADMIN_ID = 6957559313

API = "https://api.telegram.org/bot" + BOT_TOKEN + "/"


# ==================================================
# DATABASE
# ==================================================

db = sqlite3.connect("coinmember.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS required_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT UNIQUE
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS user_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    channel TEXT,
    status TEXT DEFAULT 'pending'
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS joins (
    user_id INTEGER,
    channel TEXT,
    UNIQUE(user_id, channel)
)
""")

db.commit()


# ==================================================
# TELEGRAM API
# ==================================================

def api(method, data=None):

    try:

        if data is None:
            data = {}

        encoded = urllib.parse.urlencode(
            data,
            encoding="utf-8"
        ).encode("utf-8")

        request = urllib.request.Request(
            API + method,
            data=encoded,
            headers={
                "Content-Type":
                "application/x-www-form-urlencoded; charset=utf-8"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=35
        ) as response:

            raw = response.read().decode("utf-8")

            return json.loads(raw)

    except Exception as e:

        print("API ERROR:", e)

        return None


# ==================================================
# SEND MESSAGE
# ==================================================

def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:

        data["reply_markup"] = json.dumps(
            keyboard,
            ensure_ascii=False
        )

    return api("sendMessage", data)


# ==================================================
# EDIT MESSAGE
# ==================================================

def edit_message(chat_id, message_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if keyboard:

        data["reply_markup"] = json.dumps(
            keyboard,
            ensure_ascii=False
        )

    return api("editMessageText", data)


# ==================================================
# CALLBACK ANSWER
# ==================================================

def answer_callback(callback_id, text=""):

    return api(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id,
            "text": text
        }
    )


# ==================================================
# BOT INFO
# ==================================================

bot_info = api("getMe")

if not bot_info or not bot_info.get("ok"):

    print("❌ خطا در اتصال به ربات")

    raise SystemExit

BOT_ID = bot_info["result"]["id"]
BOT_USERNAME = bot_info["result"]["username"]

print("Bot:", BOT_USERNAME)
print("Bot ID:", BOT_ID)


# ==================================================
# MAIN KEYBOARD
# ==================================================

def main_keyboard():

    return {
        "keyboard": [
            [
                {
                    "text": "🪙 کسب سکه"
                },
                {
                    "text": "💰 موجودی من"
                }
            ],
            [
                {
                    "text": "📢 ثبت کانال من"
                },
                {
                    "text": "📊 کانال من"
                }
            ],
            [
                {
                    "text": "ℹ️ راهنما"
                }
            ]
        ],
        "resize_keyboard": True
    }


# ==================================================
# ADMIN KEYBOARD
# ==================================================

def admin_keyboard():

    return {
        "keyboard": [
            [
                {
                    "text": "➕ افزودن کانال"
                },
                {
                    "text": "➖ حذف کانال"
                }
            ],
            [
                {
                    "text": "📋 لیست کانال‌ها"
                },
                {
                    "text": "📢 کانال‌های در انتظار"
                }
            ],
            [
                {
                    "text": "📊 آمار"
                }
            ],
            [
                {
                    "text": "🔙 بازگشت"
                }
            ]
        ],
        "resize_keyboard": True
    }


# ==================================================
# USER STATES
# ==================================================

user_states = {}


# ==================================================
# USER
# ==================================================

def ensure_user(user_id):

    cur.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    if not cur.fetchone():

        cur.execute(
            "INSERT INTO users(user_id, coins) VALUES(?,0)",
            (user_id,)
        )

        db.commit()


# ==================================================
# CHECK BOT ADMIN
# ==================================================

def check_bot_admin(channel):

    try:

        result = api(
            "getChatMember",
            {
                "chat_id": channel,
                "user_id": BOT_ID
            }
        )

        if not result or not result.get("ok"):

            return False

        status = result["result"]["status"]

        return status in ["administrator", "creator"]

    except:

        return False


# ==================================================
# CHECK USER MEMBERSHIP
# ==================================================

def check_membership(user_id, channel):

    result = api(
        "getChatMember",
        {
            "chat_id": channel,
            "user_id": user_id
        }
    )

    if not result or not result.get("ok"):

        return False

    status = result["result"]["status"]

    return status in [
        "member",
        "administrator",
        "creator"
    ]


# ==================================================
# START
# ==================================================

def start_command(message):

    user_id = message["from"]["id"]

    ensure_user(user_id)

    text = (
        "👋 سلام!\n\n"
        "به ربات Coin Member خوش اومدی 🪙\n\n"
        "از منوی زیر استفاده کن."
    )

    send_message(
        user_id,
        text,
        main_keyboard()
    )


# ==================================================
# BALANCE
# ==================================================

def balance(user_id):

    ensure_user(user_id)

    cur.execute(
        "SELECT coins FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    coins = row[0] if row else 0

    send_message(
        user_id,
        f"💰 موجودی شما:\n\n🪙 {coins} سکه",
        main_keyboard()
    )


# ==================================================
# HELP
# ==================================================

def help_command(user_id):

    text = (
        "ℹ️ راهنمای ربات\n\n"
        "🪙 کسب سکه\n"
        "با عضویت در کانال‌های مشخص‌شده سکه دریافت کن.\n\n"
        "💰 موجودی من\n"
        "مقدار سکه‌های خودت را ببین.\n\n"
        "📢 ثبت کانال من\n"
        "کانالت را برای بررسی ثبت کن.\n\n"
        "📊 کانال من\n"
        "وضعیت کانال‌های ثبت‌شده را ببین."
    )

    send_message(
        user_id,
        text,
        main_keyboard()
    )


# ==================================================
# EARN COINS
# ==================================================

def earn_coins(user_id):

    cur.execute(
        "SELECT channel FROM required_channels"
    )

    channels = cur.fetchall()

    if not channels:

        send_message(
            user_id,
            "❌ فعلاً کانالی برای کسب سکه وجود ندارد.",
            main_keyboard()
        )

        return

    keyboard = []

    for row in channels:

        channel = row[0]

        keyboard.append([
            {
                "text": f"📢 {channel}",
                "url": "https://t.me/" +
                       channel.replace("@", "")
            }
        ])

    keyboard.append([
        {
            "text": "✅ بررسی عضویت",
            "callback_data": "check_coins"
        }
    ])

    send_message(
        user_id,
        "🪙 برای دریافت سکه در کانال‌های زیر عضو شو و سپس روی «بررسی عضویت» بزن:",
        {
            "inline_keyboard": keyboard
        }
    )


# ==================================================
# CHECK COINS
# ==================================================

def check_coins(user_id, chat_id, message_id):

    cur.execute(
        "SELECT channel FROM required_channels"
    )

    channels = cur.fetchall()

    added = 0

    for row in channels:

        channel = row[0]

        if not check_membership(user_id, channel):

            continue

        cur.execute(
            """
            SELECT user_id FROM joins
            WHERE user_id=? AND channel=?
            """,
            (user_id, channel)
        )

        if cur.fetchone():

            continue

        cur.execute(
            """
            INSERT INTO joins(user_id, channel)
            VALUES(?,?)
            """,
            (user_id, channel)
        )

        cur.execute(
            """
            UPDATE users
            SET coins = coins + 1
            WHERE user_id=?
            """,
            (user_id,)
        )

        added += 1

    db.commit()

    cur.execute(
        "SELECT coins FROM users WHERE user_id=?",
        (user_id,)
    )

    coins = cur.fetchone()[0]

    if added:

        text = (
            f"✅ {added} سکه جدید دریافت کردی!\n\n"
            f"💰 موجودی: {coins} سکه"
        )

    else:

        text = (
            "ℹ️ سکه جدیدی دریافت نشد.\n\n"
            "اگر تازه عضو کانال شدی، مطمئن شو عضویتت کامل شده."
        )

    edit_message(
        chat_id,
        message_id,
        text
    )


# ==================================================
# REGISTER CHANNEL
# ==================================================

def register_channel(user_id):

    user_states[user_id] = "waiting_channel"

    send_message(
        user_id,
        "📢 آیدی کانال را بفرست.\n\n"
        "مثال:\n"
        "@mychannel\n\n"
        "یا:\n"
        "https://t.me/mychannel"
    )


# ==================================================
# PROCESS CHANNEL
# ==================================================

def process_channel(user_id, text):

    channel = text.strip()

    if channel.startswith("https://t.me/"):

        channel = "@" + channel.split("/")[-1]

    if not channel.startswith("@"):

        send_message(
            user_id,
            "❌ فرمت کانال درست نیست.\n\n"
            "مثال:\n"
            "@mychannel"
        )

        return

    user_states.pop(user_id, None)

    send_message(
        user_id,
        "⏳ در حال بررسی کانال..."
    )

    if not check_bot_admin(channel):

        send_message(
            user_id,
            "❌ ربات در این کانال ادمین نیست.\n\n"
            "ابتدا ربات را به عنوان ادمین کانال اضافه کن."
        )

        return

    cur.execute(
        """
        INSERT INTO user_channels(user_id, channel, status)
        VALUES(?,?,?)
        """,
        (user_id, channel, "pending")
    )

    db.commit()

    send_message(
        user_id,
        "✅ کانال با موفقیت ثبت شد.\n\n"
        "⏳ کانال برای بررسی ادمین ارسال شد."
    )

    # Notify admin

    send_message(
        ADMIN_ID,
        f"📢 کانال جدید برای بررسی:\n\n"
        f"👤 کاربر: {user_id}\n"
        f"📢 کانال: {channel}\n\n"
        f"برای تأیید یا رد از پنل ادمین استفاده کن.",
        {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ تأیید",
                        "callback_data":
                        f"approve_channel:{user_id}:{channel}"
                    },
                    {
                        "text": "❌ رد",
                        "callback_data":
                        f"reject_channel:{user_id}:{channel}"
                    }
                ]
            ]
        }
    )


# ==================================================
# MY CHANNELS
# ==================================================

def my_channels(user_id):

    cur.execute(
        """
        SELECT channel,status
        FROM user_channels
        WHERE user_id=?
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    if not rows:

        send_message(
            user_id,
            "📊 هنوز کانالی ثبت نکرده‌ای.",
            main_keyboard()
        )

        return

    text = "📊 کانال‌های شما:\n\n"

    for channel, status in rows:

        if status == "pending":

            s = "⏳ در انتظار بررسی"

        elif status == "approved":

            s = "✅ تأیید شده"

        else:

            s = "❌ رد شده"

        text += f"{channel}\n{s}\n\n"

    send_message(
        user_id,
        text,
        main_keyboard()
    )


# ==================================================
# ADMIN PANEL
# ==================================================

def admin_panel(user_id):

    if user_id != ADMIN_ID:

        return

    send_message(
        user_id,
        "👑 پنل مدیریت",
        admin_keyboard()
    )


# ==================================================
# ADMIN STATS
# ==================================================

def admin_stats(user_id):

    if user_id != ADMIN_ID:

        return

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )

    users = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM required_channels"
    )

    channels = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM user_channels WHERE status='pending'"
    )

    pending = cur.fetchone()[0]

    cur.execute(
        "SELECT COALESCE(SUM(coins),0) FROM users"
    )

    coins = cur.fetchone()[0]

    text = (
        "📊 آمار ربات\n\n"
        f"👤 کاربران: {users}\n"
        f"📢 کانال‌های اجباری: {channels}\n"
        f"⏳ کانال‌های در انتظار: {pending}\n"
        f"🪙 مجموع سکه‌ها: {coins}"
    )

    send_message(
        user_id,
        text,
        admin_keyboard()
    )


# ==================================================
# ADMIN REQUIRED CHANNELS
# ==================================================

def list_required_channels(user_id):

    if user_id != ADMIN_ID:

        return

    cur.execute(
        "SELECT id,channel FROM required_channels"
    )

    rows = cur.fetchall()

    if not rows:

        text = "📋 هیچ کانالی ثبت نشده."

    else:

        text = "📋 کانال‌های فعلی:\n\n"

        for channel_id, channel in rows:

            text += f"{channel_id}. {channel}\n"

    send_message(
        user_id,
        text,
        admin_keyboard()
    )


# ==================================================
# ADD REQUIRED CHANNEL
# ==================================================

def add_required_channel(user_id):

    if user_id != ADMIN_ID:

        return

    user_states[user_id] = "admin_add_channel"

    send_message(
        user_id,
        "➕ آیدی کانال را بفرست.\n\n"
        "مثال:\n"
        "@mychannel"
    )


# ==================================================
# REMOVE REQUIRED CHANNEL
# ==================================================

def remove_required_channel(user_id):

    if user_id != ADMIN_ID:

        return

    user_states[user_id] = "admin_remove_channel"

    send_message(
        user_id,
        "➖ آیدی کانالی که می‌خواهی حذف شود را بفرست."
    )


# ==================================================
# PROCESS ADMIN ADD
# ==================================================

def process_admin_add(user_id, text):

    channel = text.strip()

    if not channel.startswith("@"):

        send_message(
            user_id,
            "❌ فرمت اشتباه است.\nمثال: @mychannel"
        )

        return

    cur.execute(
        """
        INSERT OR IGNORE INTO required_channels(channel)
        VALUES(?)
        """,
        (channel,)
    )

    db.commit()

    user_states.pop(user_id, None)

    send_message(
        user_id,
        f"✅ کانال {channel} اضافه شد.",
        admin_keyboard()
    )


# ==================================================
# PROCESS ADMIN REMOVE
# ==================================================

def process_admin_remove(user_id, text):

    channel = text.strip()

    cur.execute(
        "DELETE FROM required_channels WHERE channel=?",
        (channel,)
    )

    db.commit()

    user_states.pop(user_id, None)

    send_message(
        user_id,
        f"✅ کانال {channel} حذف شد.",
        admin_keyboard()
    )


# ==================================================
# PENDING CHANNELS
# ==================================================

def pending_channels(user_id):

    if user_id != ADMIN_ID:

        return

    cur.execute(
        """
        SELECT id,user_id,channel
        FROM user_channels
        WHERE status='pending'
        """
    )

    rows = cur.fetchall()

    if not rows:

        send_message(
            user_id,
            "📢 کانال در انتظاری وجود ندارد.",
            admin_keyboard()
        )

        return

    for row_id, owner, channel in rows:

        send_message(
            user_id,
            f"📢 کانال در انتظار\n\n"
            f"👤 کاربر: {owner}\n"
            f"📢 کانال: {channel}",
            {
                "inline_keyboard": [
                    [
                        {
                            "text": "✅ تأیید",
                            "callback_data":
                            f"approve:{row_id}"
                        },
                        {
                            "text": "❌ رد",
                            "callback_data":
                            f"reject:{row_id}"
                        }
                    ]
                ]
            }
        )


# ==================================================
# CALLBACKS
# ==================================================

def handle_callback(callback):

    callback_id = callback["id"]

    from_user = callback["from"]

    user_id = from_user["id"]

    data = callback.get("data", "")

    answer_callback(callback_id)

    # ------------------------------
    # CHECK COINS
    # ------------------------------

    if data == "check_coins":

        message = callback["message"]

        check_coins(
            user_id,
            message["chat"]["id"],
            message["message_id"]
        )

        return

    # ------------------------------
    # ADMIN
    # ------------------------------

    if user_id != ADMIN_ID:

        return

    # ------------------------------
    # APPROVE OLD FORMAT
    # ------------------------------

    if data.startswith("approve:"):

        row_id = int(
            data.split(":")[1]
        )

        cur.execute(
            """
            UPDATE user_channels
            SET status='approved'
            WHERE id=?
            """,
            (row_id,)
        )

        db.commit()

        send_message(
            ADMIN_ID,
            "✅ کانال تأیید شد.",
            admin_keyboard()
        )

        return

    # ------------------------------
    # REJECT OLD FORMAT
    # ------------------------------

    if data.startswith("reject:"):

        row_id = int(
            data.split(":")[1]
        )

        cur.execute(
            """
            UPDATE user_channels
            SET status='rejected'
            WHERE id=?
            """,
            (row_id,)
        )

        db.commit()

        send_message(
            ADMIN_ID,
            "❌ کانال رد شد.",
            admin_keyboard()
        )

        return

    # ------------------------------
    # APPROVE NEW
    # ------------------------------

    if data.startswith("approve_channel:"):

        parts = data.split(":", 2)

        owner = int(parts[1])

        channel = parts[2]

        cur.execute(
            """
            UPDATE user_channels
            SET status='approved'
            WHERE user_id=? AND channel=? AND status='pending'
            """,
            (owner, channel)
        )

        db.commit()

        send_message(
            owner,
            f"✅ کانال شما تأیید شد.\n\n"
            f"📢 {channel}"
        )

        send_message(
            ADMIN_ID,
            "✅ کانال تأیید شد.",
            admin_keyboard()
        )

        return

    # ------------------------------
    # REJECT NEW
    # ------------------------------

    if data.startswith("reject_channel:"):

        parts = data.split(":", 2)

        owner = int(parts[1])

        channel = parts[2]

        cur.execute(
            """
            UPDATE user_channels
            SET status='rejected'
            WHERE user_id=? AND channel=? AND status='pending'
            """,
            (owner, channel)
        )

        db.commit()

        send_message(
            owner,
            f"❌ کانال شما رد شد.\n\n"
            f"📢 {channel}"
        )

        send_message(
            ADMIN_ID,
            "❌ کانال رد شد.",
            admin_keyboard()
        )

        return


# ==================================================
# MESSAGE HANDLER
# ==================================================

def handle_message(message):

    user = message.get("from", {})

    user_id = user.get("id")

    if not user_id:

        return

    chat_id = message["chat"]["id"]

    text = message.get("text", "")

    print(
        "MESSAGE:",
        user_id,
        user.get("username"),
        repr(text)
    )

    ensure_user(user_id)

    # ------------------------------
    # START
    # ------------------------------

    if text == "/start":

        start_command(message)

        return

    # ------------------------------
    # ADMIN PANEL COMMAND
    # ------------------------------

    if text == "/admin" and user_id == ADMIN_ID:

        admin_panel(user_id)

        return

    # ------------------------------
    # CURRENT STATE
    # ------------------------------

    state = user_states.get(user_id)

    if state == "waiting_channel":

        process_channel(
            user_id,
            text
        )

        return

    if state == "admin_add_channel":

        process_admin_add(
            user_id,
            text
        )

        return

    if state == "admin_remove_channel":

        process_admin_remove(
            user_id,
            text
        )

        return

    # ------------------------------
    # USER MENU
    # ------------------------------

    if text == "🪙 کسب سکه":

        earn_coins(user_id)

        return

    if text == "💰 موجودی من":

        balance(user_id)

        return

    if text == "📢 ثبت کانال من":

        register_channel(user_id)

        return

    if text == "📊 کانال من":

        my_channels(user_id)

        return

    if text == "ℹ️ راهنما":

        help_command(user_id)

        return

    # ------------------------------
    # ADMIN MENU
    # ------------------------------

    if user_id == ADMIN_ID:

        if text == "👑 پنل مدیریت":

            admin_panel(user_id)

            return

        if text == "➕ افزودن کانال":

            add_required_channel(user_id)

            return

        if text == "➖ حذف کانال":

            remove_required_channel(user_id)

            return

        if text == "📋 لیست کانال‌ها":

            list_required_channels(user_id)

            return

        if text == "📢 کانال‌های در انتظار":

            pending_channels(user_id)

            return

        if text == "📊 آمار":

            admin_stats(user_id)

            return

        if text == "🔙 بازگشت":

            send_message(
                user_id,
                "منوی اصلی",
                main_keyboard()
            )

            return


# ==================================================
# STARTUP
# ==================================================

print("")
print("=================================")
print("CoinMember Bot Started")
print("=================================")


# حذف webhook

print("Removing webhook...")

result = api(
    "deleteWebhook",
    {
        "drop_pending_updates": False
    }
)

print(result)


# ==================================================
# CLEAR OLD UPDATES
# ==================================================

print("Clearing old messages...")

old_updates = api(
    "getUpdates",
    {
        "offset": -1,
        "timeout": 1
    }
)

offset = 0

if old_updates and old_updates.get("ok"):

    old_list = old_updates.get("result", [])

    if old_list:

        offset = old_list[-1]["update_id"] + 1

print("Old messages cleared.")
print("Waiting for new messages...")


# ==================================================
# MAIN LOOP
# ==================================================

while True:

    try:

        result = api(
            "getUpdates",
            {
                "offset": offset,
                "timeout": 25,
                "allowed_updates":
                json.dumps(
                    [
                        "message",
                        "callback_query"
                    ]
                )
            }
        )

        if not result:

            time.sleep(2)

            continue

        if not result.get("ok"):

            print("Telegram error:", result)

            time.sleep(3)

            continue

        updates = result.get(
            "result",
            []
        )

        for update in updates:

            offset = update["update_id"] + 1

            print(
                "Update:",
                update["update_id"]
            )

            if "message" in update:

                handle_message(
                    update["message"]
                )

            elif "callback_query" in update:

                handle_callback(
                    update["callback_query"]
                )

    except KeyboardInterrupt:

        print("Bot stopped.")

        break

    except Exception as e:

        print(
            "MAIN LOOP ERROR:",
            e
        )

        time.sleep(3)