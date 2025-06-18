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

class TeleAPI:
    def __init__(self, client: TelegramClient):
        self.client = client
        self.chars_limit = 4096
        self.sleep = 5

    async def send_split_text(self, message: Message, string: str):
        n = self.chars_limit
        out = [(string[i: i + n]) for i in range(0, len(string), n)]
        j = 0
        for x in out:
            if j <= 2:
                j += 1
                await message.reply(x, disable_web_page_preview=True)
        return True

    async def get_link(self, message: Message):
        return f"https://t.me/c/{message.chat_id}/{message.id}"

    async def get_filename(self, file, audio: Union[bool, str] = None):
        try:
            file_name = getattr(file, 'file_name', None)
            if file_name is None:
                file_name = "telegram_audio" if audio else "telegram_video"
        except:
            file_name = "telegram_audio" if audio else "telegram_video"
        return file_name

    async def get_duration(self, file):
        try:
            dur = seconds_to_min(file.duration)
        except:
            dur = "Unknown"
        return dur

    async def get_duration_from_path(self, file_path):
        try:
            dur = await asyncio.get_event_loop().run_in_executor(
                None, check_duration, file_path
            )
            dur = seconds_to_min(dur)
        except:
            dur = "Unknown"
        return dur

    async def get_filepath(self, audio: Union[bool, types.Message] = None, video: Union[bool, types.Message] = None):
        if audio:
            try:
                file_name = (
                    audio.file_unique_id
                    + "."
                    + (
                        (audio.file_name.split(".")[-1])
                        if (not hasattr(audio, 'voice'))
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

    async def download(self, message: Message, mystic: Message, fname: str):
        lower = [0, 8, 17, 38, 64, 77, 96]
        higher = [5, 10, 20, 40, 66, 80, 99]
        checker = [5, 10, 20, 40, 66, 80, 99]
        speed_counter = {}
        if os.path.exists(fname):
            return True

        async def down_load():
            async def progress(current, total):
                if current == total:
                    return
                current_time = time.time()
                start_time = speed_counter.get(message.id, current_time)
                check_time = current_time - start_time
                upl = [[Button.inline("Cancel", b"stop_downloading")]]
                percentage = current * 100 / total
                percentage = str(round(percentage, 2))
                speed = current / check_time
                eta = int((total - current) / speed)
                eta = get_readable_time(eta)
                if not eta:
                    eta = "0 seconds"
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
                                await mystic.edit(
                                    text=f"Downloading...\n"
                                         f"Total Size: {total_size}\n"
                                         f"Completed: {completed_size}\n"
                                         f"Progress: {percentage}%\n"
                                         f"Speed: {speed}/s\n"
                                         f"ETA: {eta}",
                                    buttons=upl,
                                )
                                checker[counter] = 100
                            except:
                                pass

            speed_counter[message.id] = time.time()
            try:
                await self.client.download_media(
                    message.reply_to_msg_id,
                    file=fname,
                    progress_callback=progress,
                )
                try:
                    elapsed = get_readable_time(
                        int(int(time.time()) - int(speed_counter[message.id]))
                    )
                except:
                    elapsed = "0 seconds"
                await mystic.edit(f"Download completed in {elapsed}")
            except Exception as e:
                await mystic.edit(f"Download failed: {str(e)}")

        task = asyncio.create_task(down_load())
        config.lyrical[mystic.id] = task
        await task
        verify = config.lyrical.get(mystic.id)
        if not verify:
            return False
        config.lyrical.pop(mystic.id)
        return True

    async def convert_to_mp4(self, message: Message, mystic: Message, file_path: str):
        output_file_path = os.path.join(os.path.realpath("downloads"), f"{message.id}.mp4")

        try:
            # Convert to MP4 using ffmpeg
            cmd = f"ffmpeg -i {file_path} -c:v libx264 -c:a aac {output_file_path}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                await mystic.edit(f"Conversion failed: {stderr.decode()}")
                return False

            await mystic.edit("Conversion completed! Sending the MP4 file...")
            await self.client.send_file(message.chat_id, output_file_path, reply_to=message.id)
            await mystic.delete()
            return True
        except Exception as e:
            await mystic.edit(f"An error occurred: {str(e)}")
            return False
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
