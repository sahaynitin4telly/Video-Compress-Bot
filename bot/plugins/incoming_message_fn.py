#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K / Akshay C / @AbirHasan2005

# the logging things

import datetime
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)
import math
import os
import time
import json
from bot.database import Database
import os
import asyncio
from bot.localisation import Localisation
import math
from bot import (
  DOWNLOAD_LOCATION, 
  AUTH_USERS,
  LOG_CHANNEL,
  UPDATES_CHANNEL,
  DATABASE_URL,
  SESSION_NAME,
)
from bot.config import Config
from bot.helper_funcs.ffmpeg import (
  convert_video,
  media_info,
  take_screen_shot
)

from bot import (
    FINISHED_PROGRESS_STR,
    UN_FINISHED_PROGRESS_STR,
    DOWNLOAD_LOCATION
)

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.types import Message
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid


start = time.time()

from bot.helper_funcs.utils import(
  delete_downloads
)

LOGS_CHANNEL = -1001283278354
db = Database(DATABASE_URL, SESSION_NAME)
CURRENT_PROCESSES = {}
CHAT_FLOOD = {}
broadcast_ids = {}
        
# Test   
    
async def progress_for_pyrogram(
    current,
    total,
    bot,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        status = DOWNLOAD_LOCATION + "/status.json"
        if os.path.exists(status):
            with open(status, 'r+') as f:
                statusMsg = json.load(f)
                if not statusMsg["running"]:
                    bot.stop_transmission()
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] \n📊 <b>Progress:</b> {2}%\n".format(
            ''.join([FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]),
            ''.join([UN_FINISHED_PROGRESS_STR for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            if not message.photo:
                await message.edit_text(
                    text="{}\n {}".format(
                        ud_type,
                        tmp
                    )
                )
            else:
                await message.edit_caption(
                    caption="{}\n {}".format(
                        ud_type,
                        tmp
                    )
                )
        except:
            pass


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]
# Test  
    
async def incoming_start_message_f(bot, update):
    """/start command"""
    if not await db.is_user_exist(update.chat.id):
        await db.add_user(update.chat.id)
    ##Force Sub##
    if update.chat.id in Config.BANNED_USERS:
        await bot.send_message(
            chat_id=message.chat.id,
            text="**You are banned 🚫 to use me 🤭. Contact @Mr_Developer_Support**",
            reply_to_message_id=message.message_id
        )
        return
    update_channel = UPDATES_CHANNEL
    if update_channel:
        try:
            user = await bot.get_chat_member(update_channel, update.chat.id)
            if user.status == "kicked":
               await bot.send_message(
                   chat_id=update.chat.id,
                   text="Sorry Sir, You are Banned to use me 🤭. Contact my [Support Group](https://t.me/Mr_Developer_Support).",
                   parse_mode="markdown",
                   disable_web_page_preview=True
               )
               return
        except UserNotParticipant:
            await bot.send_message(
                chat_id=update.chat.id,
                text="**Please Join My Updates Channel to use this Bot! 🤭**",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("Join Updates Channel 😎", url=f"https://t.me/{update_channel}")
                        ]
                    ]
                ),
                parse_mode="markdown"
            )
            return
        except Exception:
            await bot.send_message(
                chat_id=update.chat.id,
                text="Something went Wrong. Contact my [Support Group](https://t.me/Mr_Developer_Support).",
                parse_mode="markdown",
                disable_web_page_preview=True)
            return
    await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.START_TEXT,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Updates Channel 📡', url='https://t.me/Mr_Bot_Developer')
                ],
                [
                    InlineKeyboardButton('Support Group 🛰️', url='https://t.me/Mr_Developer_Support')
                ]
            ]
        ),
        reply_to_message_id=update.message_id,
    )
    
async def incoming_compress_message_f(bot, update, current, total):
  """/compress command"""
  if not await db.is_user_exist(update.chat.id):
      await db.add_user(update.chat.id)
  update_channel = UPDATES_CHANNEL
  start = time.time()
  if update_channel:
      try:
          user = await bot.get_chat_member(update_channel, update.chat.id)
          if user.status == "kicked":
             await bot.send_message(
                 chat_id=update.chat.id,
                 text="Sorry Sir, You are Banned to use me 🤭. Contact my [Support Group](https://t.me/Mr_Developer_Support).",
                 parse_mode="markdown",
                 disable_web_page_preview=True
             )
             return
      except UserNotParticipant:
          await bot.send_message(
              chat_id=update.chat.id,
              text="**Please Join My Updates Channel to use this Bot! 🤭**",
              reply_markup=InlineKeyboardMarkup(
                  [
                      [
                          InlineKeyboardButton("Join Updates Channel 😎", url=f"https://t.me/{update_channel}")
                      ]
                  ]
              ),
              parse_mode="markdown"
          )
          return
      except Exception:
          await bot.send_message(
              chat_id=update.chat.id,
              text="Something went Wrong 😢. Contact my [Support Group](https://t.me/Mr_Developer_Support).",
              parse_mode="markdown",
              disable_web_page_preview=True
          )
          return
  if update.reply_to_message is None:
    try:
      await bot.send_message(
        chat_id=update.chat.id,
        text="🤬 Reply To Telegram Media 🤬",
        reply_to_message_id=update.message_id
      )
    except:
      pass
    return
  target_percentage = 50
  isAuto = False
  if len(update.command) > 1:
    try:
      if int(update.command[1]) <= 90 and int(update.command[1]) >= 10:
        target_percentage = int(update.command[1])
      else:
        try:
          await bot.send_message(
            chat_id=update.chat.id,
            text="🤬 Value should be from 10 to 90",
            reply_to_message_id=update.message_id
          )
          return
        except:
          pass
    except:
      pass
  else:
    isAuto = True
  user_file = str(update.from_user.id) + ".FFMpegRoBot.mkv"
  saved_file_path = DOWNLOAD_LOCATION + "/" + user_file
  LOGGER.info(saved_file_path)
  d_start = time.time()
  c_start = time.time()
  u_start = time.time()
  status = DOWNLOAD_LOCATION + "/status.json"
  if not os.path.exists(status):
    sent_message = await bot.send_message(
      chat_id=update.chat.id,
      text=Localisation.DOWNLOAD_START,
      reply_to_message_id=update.message_id
    )
    chat_id = LOG_CHANNEL
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
    ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
    start = time.time()
    bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
    bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
    now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
    now2 = time.time()
    diff = now2 - start
    percentage = current * 100 / total
    speed = current / diff
    eta = round((total - current) / speed)
    prog_str = "`[{0}{1}] {2}%`".format(
        "".join("▰" for i in range(math.floor(percentage / 10))),
        "".join("▱" for i in range(10 - math.floor(percentage / 10))),
        round(percentage, 2),
    )
    download_start = await bot.send_message(chat_id, f"""**Bot Become Busy Now !!**\n\n
    **📊 Process Status 📊**`\n {prog_str}`\n\n
    Download Started at `{now}`\n
    **Progress Speed 🚀 :** `{humanbytes(speed)}`\n
    **ETA ⏰ :** `{time_formatter(eta)}`""",
    parse_mode="markdown")
    try:
      d_start = time.time()
      status = DOWNLOAD_LOCATION + "/status.json"
      with open(status, 'w') as f:
        statusMsg = {
          'running': True,
          'message': sent_message.message_id
        }

        json.dump(statusMsg, f, indent=2)
      video = await bot.download_media(
        message=update.reply_to_message,
        file_name=saved_file_path,
        progress=progress_for_pyrogram,
        progress_args=(
          bot,
          Localisation.DOWNLOAD_START,
          sent_message,
          d_start
        )
      )
      LOGGER.info(video)
      if( video is None ):
        try:
          await sent_message.edit_text(
            text="Download stopped"
          )
          chat_id = LOG_CHANNEL
          utc_now = datetime.datetime.utcnow()
          ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
          ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
          bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
          bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
          now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
          await bot.send_message(chat_id, f"**Download Stopped 🚫, Bot is Free Now 😴!!** \n\nProcess Done at `{now}`", parse_mode="markdown")
          await download_start.delete()
        except:
          pass
        delete_downloads()
        LOGGER.info("Download stopped")
        return
    except (ValueError) as e:
      try:
        await sent_message.edit_text(
          text=str(e)
        )
      except:
          pass
      delete_downloads()            
    try:
      await sent_message.edit_text(                
        text=Localisation.SAVED_RECVD_DOC_FILE                
      )
    except:
      pass            
  else:
    try:
      await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.FF_MPEG_RO_BOT_STOR_AGE_ALREADY_EXISTS,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Show Bot Status 😎', url=f'https://t.me/{LOG_CHANNEL}') # That's Username na ...
                ]
            ]
        ),
        reply_to_message_id=update.message_id
      )
    except:
      pass
    return
  
  if os.path.exists(saved_file_path):
    downloaded_time = TimeFormatter((time.time() - d_start)*1000)
    duration, bitrate = await media_info(saved_file_path)
    if duration is None or bitrate is None:
      try:
        await sent_message.edit_text(                
          text="⚠️ Getting video meta data failed ⚠️"                
        )
        chat_id = LOG_CHANNEL
        utc_now = datetime.datetime.utcnow()
        ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
        ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
        bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
        bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
        now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
        await bot.send_message(chat_id, f"**Download Failed, Bot is Free Now !!** \n\nProcess Done at `{now}`", parse_mode="markdown")
        await download_start.delete()
      except:
          pass          
      delete_downloads()
      return
    thumb_image_path = await take_screen_shot(
      saved_file_path,
      os.path.dirname(os.path.abspath(saved_file_path)),
      (duration / 2)
    )
    chat_id = LOG_CHANNEL
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
    ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
    bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
    bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
    now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
    now2 = time.time()
    diff = now2 - start
    percentage = current / total * 100
    speed = round(current / diff, 2)
    eta = round((total - current) / speed)
    prog_str = "`[{0}{1}] {2}%`".format(
        "".join("▰" for i in range(math.floor(percentage / 10))),
        "".join("▱" for i in range(10 - math.floor(percentage / 10))),
        round(percentage, 2),
    )
    await download_start.delete()
    compress_start = await bot.send_message(chat_id, f"""**Compressing Video 🎥 ...**\n\n
    **📊 Process Status 📊**`\n {prog_str}`\n\n
    Download Started at `{now}`\n
    **Progress Speed 🚀 :** `{humanbytes(speed)}`\n
    **ETA ⏰ :** `{time_formatter(eta)}`""",
    parse_mode="markdown")
    await sent_message.edit_text(                    
      text=Localisation.COMPRESS_START                    
    )
    c_start = time.time()
    o = await convert_video(
           saved_file_path, 
           DOWNLOAD_LOCATION, 
           duration, 
           bot, 
           sent_message, 
           target_percentage, 
           isAuto
         )
    compressed_time = TimeFormatter((time.time() - c_start)*1000)
    LOGGER.info(o)
    if o == 'stopped':
      return
    if o is not None:
      chat_id = LOG_CHANNEL
      utc_now = datetime.datetime.utcnow()
      ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
      ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
      bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
      bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
      now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
      await compress_start.delete()
      upload_start = await bot.send_message(chat_id, f"**Uploading Video ...** \n\nProcess Started at `{now}`", parse_mode="markdown")
      await sent_message.edit_text(                    
        text=Localisation.UPLOAD_START,                    
      )
      u_start = time.time()
      caption = Localisation.COMPRESS_SUCCESS.replace('{}', downloaded_time, 1).replace('{}', compressed_time, 1)
      upload = await bot.send_video(
        chat_id=update.chat.id,
        video=o,
        caption=caption,
        supports_streaming=True,
        duration=duration,
        thumb=thumb_image_path,
        reply_to_message_id=update.message_id,
        progress=progress_for_pyrogram,
        progress_args=(
          bot,
          Localisation.UPLOAD_START,
          sent_message,
          u_start
        )
      )
      if(upload is None):
        try:
          await sent_message.edit_text(
            text="Upload stopped"
          )
          chat_id = LOG_CHANNEL
          utc_now = datetime.datetime.utcnow()
          ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
          ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
          bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
          bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
          now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
          await bot.send_message(chat_id, f"**Upload Stopped 🛑, Bot is Free Now !! 😴** \n\nProcess Done at `{now}`", parse_mode="markdown")
          await upload_start.delete()
        except:
          pass
        delete_downloads()
        return
      uploaded_time = TimeFormatter((time.time() - u_start)*1000)
      await sent_message.delete()
      delete_downloads()
      chat_id = LOG_CHANNEL
      utc_now = datetime.datetime.utcnow()
      ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
      ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
      bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
      bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
      now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
      await upload_start.delete()
      await bot.send_message(chat_id, f"**Upload Done ✅, Bot is Free Now !! 🤪** \n\nProcess Done at `{now}`", parse_mode="markdown")
      LOGGER.info(upload.caption);
      try:
        await upload.edit_caption(
          caption=upload.caption.replace('{}', uploaded_time)
        )
      except:
        pass
    else:
      delete_downloads()
      try:
        await sent_message.edit_text(                    
          text="⚠️ Compression Failed ⚠️"               
        )
        chat_id = LOG_CHANNEL
        now = datetime.datetime.now()
        await bot.send_message(chat_id, f"**Compression Failed 🛑, Bot is Free Now !! 😴** \n\nProcess Done at `{now}`", parse_mode="markdown")
        await download_start.delete()
      except:
        pass
      
  else:
    delete_downloads()
    try:
      await sent_message.edit_text(                    
        text="⚠️ Failed Downloaded Path Not Exist ⚠️"               
      )
      chat_id = LOG_CHANNEL
      utc_now = datetime.datetime.utcnow()
      ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
      ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
      bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
      bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
      now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
      await bot.send_message(chat_id, f"**Download Error, Bot is Free Now !!** \n\nProcess Done at `{now}`", parse_mode="markdown")
      await download_start.delete()
    except:
      pass
    
async def incoming_cancel_message_f(bot, update):
  """/cancel command"""
  if update.from_user.id not in AUTH_USERS:
    try:
      await update.message.delete()
    except:
      pass
    return

  status = DOWNLOAD_LOCATION + "/status.json"
  if os.path.exists(status):
    inline_keyboard = []
    ikeyboard = []
    ikeyboard.append(InlineKeyboardButton("Yes 🚫", callback_data=("fuckingdo").encode("UTF-8")))
    ikeyboard.append(InlineKeyboardButton("No 🤗", callback_data=("fuckoff").encode("UTF-8")))
    inline_keyboard.append(ikeyboard)
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await update.reply_text("Are you sure? 🚫 This will stop the compression!", reply_markup=reply_markup, quote=True)
  else:
    delete_downloads()
    await bot.send_message(
      chat_id=update.chat.id,
      text="No active compression exists",
      reply_to_message_id=update.message_id
    )
