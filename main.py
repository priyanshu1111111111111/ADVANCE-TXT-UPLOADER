# Don't Remove Credit Tg - @ytbr_67
# Ask Doubt on telegram @ytbr_67

import os
import re
import sys
import json
import time
import aiohttp
import asyncio
import requests
import subprocess
import urllib.parse
import cloudscraper
import datetime
import random
import ffmpeg
import logging 
import yt_dlp
from aiohttp import web
from core import *
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
import yt_dlp as youtube_dl
import cloudscraper
import m3u8
import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pytube import YouTube
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "PremiumBot"
COLLECTION_NAME = "PremiumUsers"

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
premium_collection = db[COLLECTION_NAME]

# Logging channel
LOG_CHANNEL = -1002504592081  # Replace with your actual log channel ID

cookies_file_path = os.getenv("COOKIES_FILE_PATH", "youtube_cookies.txt")

# Image URLs
cpimg = "https://graph.org/file/5ed50675df0faf833efef-e102210eb72c1d5a17.jpg"  

async def show_random_emojis(message):
    emojis = ['🎊', '🔮', '😎', '⚡️', '🚀', '✨', '💥', '🎉', '🥂', '🍾', '🦠', '🤖', '❤️‍🔥', '🕊️', '💃', '🥳','🐅','🦁']
    emoji_message = await message.reply_text(' '.join(random.choices(emojis, k=1)))
    return emoji_message
    
# Define the owner's user ID
OWNER_ID = 6200095481  # Replace with the actual owner's user ID

# List of sudo users (initially empty or pre-populated)
SUDO_USERS = [6200095481]

AUTH_CHANNEL = -1002504592081

# Premium system functions
def is_premium_user(user_id: int) -> bool:
    """Check if user is premium"""
    user = premium_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user.get("expiry_date")
        if expiry_date and datetime.datetime.now() < expiry_date:
            return True
    return False

async def add_premium_user(user_id: int, days: int):
    """Add premium user with expiry date"""
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
    premium_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )

async def remove_premium_user(user_id: int):
    """Remove premium user"""
    premium_collection.delete_one({"user_id": user_id})

async def get_premium_users():
    """Get all premium users"""
    return list(premium_collection.find({}))

# Function to check if a user is authorized
def is_authorized(user_id: int) -> bool:
    return (user_id == OWNER_ID or 
            user_id in SUDO_USERS or 
            user_id == AUTH_CHANNEL or 
            is_premium_user(user_id))

async def log_to_channel(bot: Client, text: str):
    """Log messages to the log channel"""
    try:
        await bot.send_message(LOG_CHANNEL, text)
    except Exception as e:
        print(f"Failed to log to channel: {e}")

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN)

# Premium commands
@bot.on_message(filters.command("addpremium") & filters.user(OWNER_ID))
async def add_premium_cmd(bot: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.reply_text("**Usage:** `/addpremium <user_id> <days>`")
            return

        user_id = int(args[1])
        days = int(args[2])
        
        await add_premium_user(user_id, days)
        await message.reply_text(f"✅ User {user_id} added as premium for {days} days.")
        await log_to_channel(bot, f"#PREMIUM_ADD\nUser: {user_id}\nDays: {days}\nBy: {message.from_user.id}")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

@bot.on_message(filters.command("removepremium") & filters.user(OWNER_ID))
async def remove_premium_cmd(bot: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text("**Usage:** `/removepremium <user_id>`")
            return

        user_id = int(args[1])
        await remove_premium_user(user_id)
        await message.reply_text(f"✅ User {user_id} removed from premium.")
        await log_to_channel(bot, f"#PREMIUM_REMOVE\nUser: {user_id}\nBy: {message.from_user.id}")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

@bot.on_message(filters.command("premiumlist") & filters.user(OWNER_ID))
async def premium_list_cmd(bot: Client, message: Message):
    try:
        premium_users = await get_premium_users()
        if not premium_users:
            await message.reply_text("No premium users found.")
            return

        text = "**Premium Users List:**\n\n"
        for user in premium_users:
            user_id = user["user_id"]
            expiry = user.get("expiry_date", "No expiry date")
            text += f"User ID: `{user_id}`\nExpiry: `{expiry}`\n\n"

        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

# Sudo command to add/remove sudo users
@bot.on_message(filters.command("sudo"))
async def sudo_command(bot: Client, message: Message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        await message.reply_text("**🚫 You are not authorized to use this command.**")
        return

    try:
        args = message.text.split(" ", 2)
        if len(args) < 2:
            await message.reply_text("**Usage:** `/sudo add <user_id>` or `/sudo remove <user_id>`")
            return

        action = args[1].lower()
        target_user_id = int(args[2])

        if action == "add":
            if target_user_id not in SUDO_USERS:
                SUDO_USERS.append(target_user_id)
                await message.reply_text(f"**✅ User {target_user_id} added to sudo list.**")
                await log_to_channel(bot, f"#SUDO_ADD\nUser: {target_user_id}\nBy: {message.from_user.id}")
            else:
                await message.reply_text(f"**⚠️ User {target_user_id} is already in the sudo list.**")
        elif action == "remove":
            if target_user_id == OWNER_ID:
                await message.reply_text("**🚫 The owner cannot be removed from the sudo list.**")
            elif target_user_id in SUDO_USERS:
                SUDO_USERS.remove(target_user_id)
                await message.reply_text(f"**✅ User {target_user_id} removed from sudo list.**")
                await log_to_channel(bot, f"#SUDO_REMOVE\nUser: {target_user_id}\nBy: {message.from_user.id}")
            else:
                await message.reply_text(f"**⚠️ User {target_user_id} is not in the sudo list.**")
        else:
            await message.reply_text("**Usage:** `/sudo add <user_id>` or `/sudo remove <user_id>`")
    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")

# Inline keyboard for start command
keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🇮🇳ʙᴏᴛ ᴍᴀᴅᴇ ʙʏ🇮🇳", url=f"https://t.me/ytbr_67") ],
                    [
                    InlineKeyboardButton("🔔ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ🔔", url="https://t.me/ytbr_67") ],
                    [
                    InlineKeyboardButton("🦋ғᴏʟʟᴏᴡ ᴜs🦋", url="https://t.me/ytbr_67")                              
                ],           
            ]
      )
    
# Image URLs for the random image feature
image_urls = [
    "https://graph.org/file/996d4fc24564509244988-a7d93d020c96973ba8.jpg",
    "https://graph.org/file/96d25730136a3ea7e48de-b0a87a529feb485c8f.jpg",
    "https://graph.org/file/6593f76ddd8c735ae3ce2-ede9fa2df40079b8a0.jpg",
    # Add more image URLs as needed
]
random_image_url = random.choice(image_urls) 

# Caption for the image
caption = (
        "**ʜᴇʟʟᴏ👋**\n\n"
        "➠ **ɪ ᴀᴍ ᴛxᴛ ᴛᴏ ᴠɪᴅᴇᴏ ᴜᴘʟᴏᴀᴅᴇʀ ʙᴏᴛ.**\n"
        "➠ **ғᴏʀ ᴜsᴇ ᴍᴇ sᴇɴᴅ /gaurav.\n"
        "➠ **ғᴏʀ ɢᴜɪᴅᴇ sᴇɴᴅ /help."
)
    
# Start command handler
@bot.on_message(filters.command(["start"]))
async def start_command(bot: Client, message: Message):
    await bot.send_photo(chat_id=message.chat.id, photo=random_image_url, caption=caption, reply_markup=keyboard)
    
# Stop command handler
@bot.on_message(filters.command("stop"))
async def restart_handler(_, m: Message):
    if not is_authorized(m.from_user.id):
        await m.reply_text("**🚫 You are not authorized to use this command.**")
        return
        
    await m.reply_text("**𝗦𝘁𝗼𝗽𝗽𝗲𝗱**🚦", True)
    await log_to_channel(bot, f"#BOT_STOPPED\nBy: {m.from_user.id}")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("restart"))
async def restart_handler(_, m):
    if not is_authorized(m.from_user.id):
        await m.reply_text("**🚫 You are not authorized to use this command.**")
        return
    await m.reply_text("🔮Restarted🔮", True)
    await log_to_channel(bot, f"#BOT_RESTARTED\nBy: {m.from_user.id}")
    os.execl(sys.executable, sys.executable, *sys.argv)

COOKIES_FILE_PATH = "youtube_cookies.txt"

@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    if not is_authorized(m.from_user.id):
        await m.reply_text("🚫 You are not authorized to use this command.")
        return
        
    await m.reply_text("𝗣𝗹𝗲𝗮𝘀𝗲 𝗨𝗽𝗹𝗼𝗮𝗱 𝗧𝗵𝗲 𝗖𝗼𝗼𝗸𝗶𝗲𝘀 𝗙𝗶𝗹𝗲 (.𝘁𝘅𝘁 𝗳𝗼𝗿𝗺𝗮𝘁).", quote=True)

    try:
        input_message: Message = await client.listen(m.chat.id)

        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        downloaded_path = await input_message.download()

        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        with open(COOKIES_FILE_PATH, "w") as target_file:
            target_file.write(cookies_content)

        await input_message.reply_text("✅ 𝗖𝗼𝗼𝗸𝗶𝗲𝘀 𝗨𝗽𝗱𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆.\n\𝗻📂 𝗦𝗮𝘃𝗲𝗱 𝗜𝗻 youtube_cookies.txt.")
        await log_to_channel(bot, f"#COOKIES_UPDATED\nBy: {m.from_user.id}")
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

# Define paths for uploaded file and processed file
UPLOAD_FOLDER = '/path/to/upload/folder'
EDITED_FILE_PATH = '/path/to/save/edited_output.txt'

@bot.on_message(filters.command('e2t'))
async def edit_txt(client, message: Message):
    if not is_authorized(message.from_user.id):
        await message.reply_text("🚫 You are not authorized to use this command.")
        return

    await message.reply_text(
        "🎉 **Welcome to the .txt File Editor!**\n\n"
        "Please send your `.txt` file containing subjects, links, and topics."
    )

    input_message: Message = await bot.listen(message.chat.id)
    if not input_message.document:
        await message.reply_text("🚨 **Error**: Please upload a valid `.txt` file.")
        return

    file_name = input_message.document.file_name.lower()
    uploaded_file_path = os.path.join(UPLOAD_FOLDER, file_name)
    uploaded_file = await input_message.download(uploaded_file_path)

    await message.reply_text(
        "🔄 **Send your .txt file name, or type 'd' for the default file name.**"
    )

    user_response: Message = await bot.listen(message.chat.id)
    if user_response.text:
        user_response_text = user_response.text.strip().lower()
        if user_response_text == 'd':
            final_file_name = file_name
        else:
            final_file_name = user_response_text + '.txt'
    else:
        final_file_name = file_name

    try:
        with open(uploaded_file, 'r', encoding='utf-8') as f:
            content = f.readlines()
    except Exception as e:
        await message.reply_text(f"🚨 **Error**: Unable to read the file.\n\nDetails: {e}")
        return

    subjects = {}
    current_subject = None
    for line in content:
        line = line.strip()
        if line and ":" in line:
            title, url = line.split(":", 1)
            title, url = title.strip(), url.strip()

            if title in subjects:
                subjects[title]["links"].append(url)
            else:
                subjects[title] = {"links": [url], "topics": []}

            current_subject = title
        elif line.startswith("-") and current_subject:
            subjects[current_subject]["topics"].append(line.strip("- ").strip())

    sorted_subjects = sorted(subjects.items())
    for title, data in sorted_subjects:
        data["topics"].sort()

    try:
        final_file_path = os.path.join(UPLOAD_FOLDER, final_file_name)
        with open(final_file_path, 'w', encoding='utf-8') as f:
            for title, data in sorted_subjects:
                for link in data["links"]:
                    f.write(f"{title}:{link}\n")
                for topic in data["topics"]:
                    f.write(f"- {topic}\n")
    except Exception as e:
        await message.reply_text(f"🚨 **Error**: Unable to write the edited file.\n\nDetails: {e}")
        return

    try:
        await message.reply_document(
            document=final_file_path,
            caption="📥**𝗘𝗱𝗶𝘁𝗲𝗱 𝗕𝘆 ➤ Gaurav**"
        )
        await log_to_channel(bot, f"#TXT_EDITED\nBy: {message.from_user.id}")
    except Exception as e:
        await message.reply_text(f"🚨 **Error**: Unable to send the file.\n\nDetails: {e}")
    finally:
        if os.path.exists(uploaded_file_path):
            os.remove(uploaded_file_path)

from pytube import Playlist
import youtube_dl

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Utility Functions ---

def sanitize_filename(name):
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')

def get_videos_with_ytdlp(url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if 'entries' in result:
                title = result.get('title', 'Unknown Title')
                videos = {}
                for entry in result['entries']:
                    video_url = entry.get('url', None)
                    video_title = entry.get('title', None)
                    if video_url:
                        videos[video_title if video_title else "Unknown Title"] = video_url
                return title, videos
            return None, None
    except Exception as e:
        logging.error(f"Error retrieving videos: {e}")
        return None, None

def save_to_file(videos, name):
    filename = f"{sanitize_filename(name)}.txt"
    with open(filename, 'w', encoding='utf-8') as file:
        for title, url in videos.items():
            if title == "Unknown Title":
                file.write(f"{url}\n")
            else:
                file.write(f"{title}: {url}\n")
    return filename

# --- Bot Command ---

@bot.on_message(filters.command('yt2txt'))
async def ytplaylist_to_txt(client: Client, message: Message):
    user_id = message.chat.id
    if user_id != OWNER_ID:
        await message.reply_text("**🚫 You are not authorized to use this command.\n\n🫠 This Command is only for owner.**")
        return

    await message.delete()
    editable = await message.reply_text("📥 **Please enter the YouTube Playlist Url :**")
    input_msg = await client.listen(editable.chat.id)
    youtube_url = input_msg.text
    await input_msg.delete()
    await editable.delete()

    title, videos = get_videos_with_ytdlp(youtube_url)
    if videos:
        file_name = save_to_file(videos, title)
        await message.reply_document(
            document=file_name, 
            caption=f"`{title}`\n\n📥 𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗕𝘆 ➤ Gaurav"
        )
        await log_to_channel(bot, f"#YT2TXT\nURL: {youtube_url}\nBy: {message.from_user.id}")
        os.remove(file_name)
    else:
        await message.reply_text("⚠️ **Unable to retrieve videos. Please check the URL.**")

# List users command
@bot.on_message(filters.command("userlist") & filters.user(SUDO_USERS))
async def list_users(client: Client, msg: Message):
    if SUDO_USERS:
        users_list = "\n".join([f"User ID : `{user_id}`" for user_id in SUDO_USERS])
        await msg.reply_text(f"SUDO_USERS :\n{users_list}")
    else:
        await msg.reply_text("No sudo users.")

# Help command
@bot.on_message(filters.command("help"))
async def help_command(client: Client, msg: Message):
    help_text = (
        "`/start` - Start the bot⚡\n\n"
        "`/gaurav` - Download and upload files (sudo)🎬\n\n"
        "`/restart` - Restart the bot🔮\n\n" 
        "`/stop` - Stop ongoing process🛑\n\n"
        "`/cookies` - Upload cookies file🍪\n\n"
        "`/e2t` - Edit txt file📝\n\n"
        "`/yt2txt` - Create txt of yt playlist (owner)🗃️\n\n"
        "`/sudo add` - Add user or group or channel (owner)🎊\n\n"
        "`/sudo remove` - Remove user or group or channel (owner)❌\n\n"
        "`/userlist` - List of sudo user or group or channel📜\n\n"
        "`/addpremium` - Add premium user (owner)💰\n\n"
        "`/removepremium` - Remove premium user (owner)🚫\n\n"
        "`/premiumlist` - List premium users (owner)📋\n\n"
    )
    await msg.reply_text(help_text)

# Upload command handler - Renamed from tushar to gaurav
@bot.on_message(filters.command(["gaurav"]))
async def upload(bot: Client, m: Message):
    if not is_authorized(m.chat.id):
        await m.reply_text("**🚫You are not authorized to use this bot.**")
        await log_to_channel(bot, f"#UNAUTHORIZED_ACCESS\nUser: {m.from_user.id} tried to access /gaurav")
        return

    editable = await m.reply_text(f"⚡𝗦𝗘𝗡𝗗 𝗧𝗫𝗧 𝗙𝗜𝗟𝗘⚡")
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    pdf_count = 0
    img_count = 0
    zip_count = 0
    video_count = 0
    
    try:    
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        
        links = []
        for i in content:
            if "://" in i:
                url = i.split("://", 1)[1]
                links.append(i.split("://", 1))
                if ".pdf" in url:
                    pdf_count += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    img_count += 1
                elif ".zip" in url:
                    zip_count += 1
                else:
                    video_count += 1
        os.remove(x)
    except:
        await m.reply_text("😶𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗙𝗶𝗹𝗲 𝗜𝗻𝗽𝘂𝘁😶")
        os.remove(x)
        return
   
    await editable.edit(f"`𝗧𝗼𝘁𝗮𝗹 🔗 𝗟𝗶𝗻𝗸𝘀 𝗙𝗼𝘂𝗻𝗱 𝗔𝗿𝗲 {len(links)}\n\n🔹Img : {img_count}  🔹Pdf : {pdf_count}\n🔹Zip : {zip_count}  🔹Video : {video_count}\n\n𝗦𝗲𝗻𝗱 𝗙𝗿𝗼𝗺 𝗪𝗵𝗲𝗿𝗲 𝗬𝗼𝘂 𝗪𝗮𝗻𝘁 𝗧𝗼 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱.`")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except:
        arg = 1
    await editable.edit("📚 𝗘𝗻𝘁𝗲𝗿 𝗬𝗼𝘂𝗿 𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 📚\n\n🦠 𝗦𝗲𝗻𝗱 `1` 𝗙𝗼𝗿 𝗨𝘀𝗲 𝗗𝗲𝗳𝗮𝘂𝗹𝘁 🦠")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    
