import asyncio
import os
import time
from typing import Union
import subprocess

from telethon import TelegramClient, events, Button
from telethon.tl.types import Message
from telethon.tl import types

import config
from BrandrdXMusic.utils.formatters import (
    check_duration,
    convert_bytes,
    get_readable_time,
    seconds_to_min,
)
from BrandrdXMusic.platforms.Telegram import TeleAPI

# Initialize the Telegram client using values from config
client = TelegramClient('bot', config.API_ID, config.API_HASH).start(bot_token=config.BOT_TOKEN)

# Initialize TeleAPI
tele_api = TeleAPI(client)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply('Hello! Send me a video file, and I will convert it to MP4.')

@client.on(events.NewMessage(pattern='/mp4'))
async def convert_to_mp4(event):
    if not event.is_reply:
        await event.reply("Please reply to a video message with /mp4 command.")
        return

    replied_message = await event.get_reply_message()
    if not replied_message.video and not replied_message.document:
        await event.reply("Please reply to a video file.")
        return

    mystic = await event.reply("Downloading the video...")
    file_path = await tele_api.get_filepath(video=replied_message)
    if not await tele_api.download(replied_message, mystic, file_path):
        await mystic.edit("Failed to download the video.")
        return

    if not await tele_api.convert_to_mp4(replied_message, mystic, file_path):
        await mystic.edit("Failed to convert the video to MP4.")

# Start the client
client.run_until_disconnected()
