import asyncio
import os
import time
import json # JSON के लिए आयात
import subprocess # FFprobe को चलाने के लिए आयात
from typing import Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Voice

import config
from BrandrdXMusic import app
from BrandrdXMusic.utils.formatters import (
    check_duration,
    convert_bytes,
    get_readable_time,
    seconds_to_min,
)


class TeleAPI:
    def __init__(self):
        self.chars_limit = 4096
        self.sleep = 5

    async def send_split_text(self, message, string):
        n = self.chars_limit
        out = [(string[i : i + n]) for i in range(0, len(string), n)]
        j = 0
        for x in out:
            if j <= 2:
                j += 1
                await message.reply_text(x, disable_web_page_preview=True)
        return True

    async def get_link(self, message):
        return message.link

    async def get_filename(self, file, audio: Union[bool, str] = None):
        try:
            file_name = file.file_name
            if file_name is None:
                file_name = "ᴛᴇʟᴇɢʀᴀᴍ ᴀᴜᴅɪᴏ" if audio else "ᴛᴇʟᴇɢʀᴀᴍ ᴠɪᴅᴇᴏ"
        except:
            file_name = "ᴛᴇʟᴇɢʀᴀᴍ ᴀᴜᴅɪᴏ" if audio else "ᴛᴇʟᴇɢʀᴀᴍ ᴠɪᴅᴇᴏ"
        return file_name

    async def get_duration(self, file):
        try:
            dur = seconds_to_min(file.duration)
        except:
            dur = "Unknown"
        return dur

    async def get_duration(self, filex, file_path):
        try:
            dur = seconds_to_min(filex.duration)
        except:
            try:
                dur = await asyncio.get_event_loop().run_in_executor(
                    None, check_duration, file_path
                )
                dur = seconds_to_min(dur)
            except:
                return "Unknown"
        return dur

    async def get_filepath(
        self,
        audio: Union[bool, str] = None,
        video: Union[bool, str] = None,
    ):
        if audio:
            try:
                file_name = (
                    audio.file_unique_id
                    + "."
                    + (
                        ((audio.file_name.split(".")[-1]))
                        if (not isinstance(audio, Voice))
                        else "ogg"
                    )
                )
            except:
                file_name = audio.file_unique_id + "." + "ogg"
            file_name = os.path.join(os.path.realpath("downloads"), file_name)
        if video:
            try:
                file_name = (
                    video.file_unique_id + "." + (video.file_name.split(".")[-1])
                )
            except:
                file_name = video.file_unique_id + "." + "mp4"
            file_name = os.path.join(os.path.realpath("downloads"), file_name)
        return file_name

    # नया फ़ंक्शन HEVC का पता लगाने के लिए
    async def is_hevc_video(self, file_path: str) -> bool:
        """
        यह जांचता है कि दी गई वीडियो फ़ाइल HEVC (H.265) कोडेक का उपयोग करती है या नहीं।
        FFprobe को आवश्यकता होती है कि आपके सिस्टम पर इंस्टॉल हो और PATH में उपलब्ध हो।
        """
        if not os.path.exists(file_path):
            return False

        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0", # केवल पहले वीडियो स्ट्रीम का चयन करें
            "-show_entries", "stream=codec_name",
            "-of", "json",
            file_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"FFprobe error: {stderr.decode()}")
                return False

            data = json.loads(stdout.decode())
            if "streams" in data and len(data["streams"]) > 0:
                codec_name = data["streams"][0].get("codec_name")
                if codec_name and "hevc" in codec_name.lower():
                    return True
            return False
        except FileNotFoundError:
            print("FFprobe not found. Please ensure FFmpeg is installed and in your system's PATH.")
            return False
        except json.JSONDecodeError:
            print(f"Could not parse FFprobe output for {file_path}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while checking for HEVC: {e}")
            return False


    async def download(self, _, message, mystic, fname):
        lower = [0, 8, 17, 38, 64, 77, 96]
        higher = [5, 10, 20, 40, 66, 80, 99]
        checker = [5, 10, 20, 40, 66, 80, 99]
        speed_counter = {}
        if os.path.exists(fname):
            # फ़ाइल पहले से मौजूद है, इसकी HEVC स्थिति की जांच करें
            is_hevc = await self.is_hevc_video(fname)
            if is_hevc:
                await mystic.reply_text(
                    "यह एक HEVC (H.265) वीडियो है। इसे चलाने के लिए एक संगत मीडिया प्लेयर (जैसे VLC) की आवश्यकता हो सकती है।"
                )
            return True

        async def down_load():
            async def progress(current, total):
                if current == total:
                    return
                current_time = time.time()
                start_time = speed_counter.get(message.id)
                check_time = current_time - start_time
                upl = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="ᴄᴀɴᴄᴇʟ",
                                callback_data="stop_downloading",
                            ),
                        ]
                    ]
                )
                percentage = current * 100 / total
                percentage = str(round(percentage, 2))
                speed = current / check_time
                eta = int((total - current) / speed)
                eta = get_readable_time(eta)
                if not eta:
                    eta = "0 sᴇᴄᴏɴᴅs"
                total_size = convert_bytes(total)
                completed_size = convert_bytes(current)
                speed = convert_bytes(speed)
                percentage = int((percentage.split("."))[0])
                for counter in range(7):
                    low = int(lower[counter])
                    high = int(higher[counter])
                    check = int(checker[counter])
                    if low < percentage <= high:
                        if high == check:
                            try:
                                await mystic.edit_text(
                                    text=_["tg_1"].format(
                                        app.mention,
                                        total_size,
                                        completed_size,
                                        percentage[:5],
                                        speed,
                                        eta,
                                    ),
                                    reply_markup=upl,
                                )
                                checker[counter] = 100
                            except:
                                pass

            speed_counter[message.id] = time.time()
            try:
                await app.download_media(
                    message.reply_to_message,
                    file_name=fname,
                    progress=progress,
                )
                try:
                    elapsed = get_readable_time(
                        int(int(time.time()) - int(speed_counter[message.id]))
                    )
                except:
                    elapsed = "0 sᴇᴄᴏɴᴅs"
                await mystic.edit_text(_["tg_2"].format(elapsed))
                
                # डाउनलोड सफल होने के बाद HEVC की जांच करें
                # सुनिश्चित करें कि message.reply_to_message एक वीडियो है
                if message.reply_to_message.video:
                    is_hevc = await self.is_hevc_video(fname)
                    if is_hevc:
                        await message.reply_text(
                            "⚠️ **महत्वपूर्ण: यह एक HEVC (H.265) वीडियो है!** ⚠️\n\nइस वीडियो को चलाने के लिए आपको एक संगत मीडिया प्लेयर की आवश्यकता होगी (जैसे VLC मीडिया प्लेयर)। यदि आपको प्लेबैक में समस्या आती है तो नवीनतम VLC इंस्टॉल करें।"
                        )

            except Exception as e:
                await mystic.edit_text(_["tg_3"])
                print(f"Download failed: {e}") # Debugging के लिए एरर प्रिंट करें

        task = asyncio.create_task(down_load())
        config.lyrical[mystic.id] = task
        await task
        verify = config.lyrical.get(mystic.id)
        if not verify:
            return False
        config.lyrical.pop(mystic.id)
        return True
