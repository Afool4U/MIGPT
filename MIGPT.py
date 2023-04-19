#!/usr/bin/env python3
import asyncio
import json
import os
import subprocess
from http.cookies import SimpleCookie
from pathlib import Path
import threading
import time
from aiohttp import ClientSession
from minaservice import MiNAService
from miaccount import MiAccount
from requests.utils import cookiejar_from_dict
from V3 import Chatbot

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"

HARDWARE_COMMAND_DICT = {
    "LX06": "5-1",  # 小爱音箱Pro（黑色）
    "L05B": "5-3",  # 小爱音箱Play
    "S12A": "5-1",  # 小爱音箱
    "LX01": "5-1",  # 小爱音箱mini
    "L06A": "5-1",  # 小爱音箱
    "LX04": "5-1",  # 小爱触屏音箱
    "L05C": "5-3",  # 小爱音箱Play增强版
    "L17A": "7-3",  # 小爱音箱Sound Pro
    "X08E": "7-3",  # 红米小爱触屏音箱Pro
    "LX05A": "5-1",  # 小爱音箱遥控版（黑色）
    "LX5A": "5-1",  # 小爱音箱遥控版（黑色）
    # add more here
}
MI_USER = "你的小米账号"  # 小米账号（手机号）
MI_PASS = "你的小米账号密码"  # 小米账号密码
OPENAI_API_KEY = "你的API KEY"  # openai的api key
SOUND_TYPE = "你的音箱型号"  # 音箱型号

# 检查必要的数据
if MI_USER == "你的小米账号":
    raise ValueError("请先在MIGPT.py中填写小米账号！")
if MI_PASS == "你的小米账号密码":
    raise ValueError("请先在MIGPT.py中填写小米账号密码！")
if OPENAI_API_KEY == "你的API KEY":
    raise ValueError("请先在MIGPT.py中填写openai的api key！")
if SOUND_TYPE == "你的音箱型号":
    raise ValueError("请先在MIGPT.py中填写音箱型号！")
if SOUND_TYPE not in HARDWARE_COMMAND_DICT:
    raise ValueError("{}不在型号列表中！请检查型号是否正确。".format(SOUND_TYPE))

SWITCH = True  # 是否开启chatgpt回答
PROMPT = "请用100字以内回答，第一句一定不要超过10个汉字或5个单词，并且请快速生成前几句话"  # 限制回答字数在100以内

loop = asyncio.get_event_loop()


### HELP FUNCTION ###
def parse_cookie_string(cookie_string):
    cookie = SimpleCookie()
    cookie.load(cookie_string)
    cookies_dict = {}
    cookiejar = None
    for k, m in cookie.items():
        cookies_dict[k] = m.value
        cookiejar = cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
    return cookiejar


class MiGPT:
    def __init__(
            self,
            hardware=SOUND_TYPE,
            use_command=False,
    ):
        self.mi_token_home = os.path.join(Path.home(), "." + MI_USER + ".mi.token")
        self.hardware = hardware
        self.cookie_string = ""
        self.last_timestamp = 0  # timestamp last call mi speaker
        self.session = None
        self.chatbot = None  # a little slow to init we move it after xiaomi init
        self.user_id = ""
        self.device_id = ""
        self.service_token = ""
        self.cookie = ""
        self.use_command = use_command
        self.tts_command = HARDWARE_COMMAND_DICT.get(hardware, "5-1")
        self.conversation_id = None
        self.parent_id = None
        self.miboy_account = None
        self.mina_service = None

    async def init_all_data(self, session):
        await self.login_miboy(session)
        await self._init_data_hardware()
        with open(self.mi_token_home) as f:
            user_data = json.loads(f.read())
        self.user_id = user_data.get("userId")
        self.service_token = user_data.get("micoapi")[1]
        self._init_cookie()
        await self._init_first_data_and_chatbot()

    async def login_miboy(self, session):
        self.session = session
        self.account = MiAccount(
            session,
            MI_USER,
            MI_PASS,
            str(self.mi_token_home),
        )
        # Forced login to refresh token
        await self.account.login("micoapi")
        self.mina_service = MiNAService(self.account)

    async def _init_data_hardware(self):
        if self.cookie:
            # cookie does not need init
            return
        hardware_data = await self.mina_service.device_list()
        for h in hardware_data:
            if h.get("hardware", "") == self.hardware:
                self.device_id = h.get("deviceID")
                break
        else:
            raise Exception(f"we have no hardware: {self.hardware} please check")

    def _init_cookie(self):
        if self.cookie:
            self.cookie = parse_cookie_string(self.cookie)
        else:
            self.cookie_string = COOKIE_TEMPLATE.format(
                device_id=self.device_id,
                service_token=self.service_token,
                user_id=self.user_id,
            )
            self.cookie = parse_cookie_string(self.cookie_string)

    async def _init_first_data_and_chatbot(self):
        data = await self.get_latest_ask_from_xiaoai()
        self.last_timestamp, self.last_record = self.get_last_timestamp_and_record(data)
        self.chatbot = Chatbot(api_key=OPENAI_API_KEY)

    async def get_latest_ask_from_xiaoai(self):
        r = await self.session.get(
            LATEST_ASK_API.format(
                hardware=self.hardware, timestamp=str(int(time.time() * 1000))
            ),
            cookies=parse_cookie_string(self.cookie),
        )
        return await r.json()

    def get_last_timestamp_and_record(self, data):
        if d := data.get("data"):
            records = json.loads(d).get("records")
            if not records:
                return 0, None
            last_record = records[0]
            timestamp = last_record.get("time")
            return timestamp, last_record

    async def do_tts(self, value):
        if not self.use_command:
            try:
                await self.mina_service.text_to_speech(self.device_id, value)
            except:
                # do nothing is ok
                pass
        else:
            subprocess.check_output(["micli", self.tts_command, value])

    async def get_if_xiaoai_is_playing(self):
        playing_info = await self.mina_service.player_get_status(self.device_id)
        # WTF xiaomi api
        is_playing = (
                json.loads(playing_info.get("data", {}).get("info", "{}")).get("status", -1)
                == 1
        )
        return is_playing

    async def stop_if_xiaoai_is_playing(self):
        is_playing = await self.get_if_xiaoai_is_playing()
        if is_playing:
            # stop it
            await self.mina_service.player_pause(self.device_id)

    async def check_new_query(self, session):
        try:
            r = await self.get_latest_ask_from_xiaoai()
        except Exception:
            # we try to init all again
            await self.init_all_data(session)
            r = await self.get_latest_ask_from_xiaoai()
        new_timestamp, last_record = self.get_last_timestamp_and_record(r)
        if new_timestamp > self.last_timestamp:
            return new_timestamp, last_record.get("query", "")
        return False, None

    async def run_forever(self):
        global SWITCH
        print("正在运行 MiGPT, 请用\"打开/关闭高级对话\"控制对话模式。")
        async with ClientSession() as session:
            await self.init_all_data(session)
            while True:
                try:
                    r = await self.get_latest_ask_from_xiaoai()
                except Exception:
                    # we try to init all again
                    await self.init_all_data(session)
                    r = await self.get_latest_ask_from_xiaoai()
                new_timestamp, last_record = self.get_last_timestamp_and_record(r)
                if new_timestamp > self.last_timestamp:
                    self.last_timestamp = new_timestamp
                    query = last_record.get("query", "")
                    if query.startswith('闭嘴') or query.startswith('停止'):  # 反悔操作
                        await self.stop_if_xiaoai_is_playing()
                        continue
                    if query.startswith('打开高级对话') or query.startswith('开启高级对话'):
                        SWITCH = True
                        print("\033[1;32m高级对话已开启\033[0m")
                        await self.do_tts("高级对话已开启")
                        continue
                    if query.startswith('关闭高级对话'):
                        SWITCH = False
                        print("\033[1;32m高级对话已关闭\033[0m")
                        await self.do_tts("高级对话已关闭")
                        continue
                    if SWITCH:
                        commas = 0
                        wait_times = 3
                        await self.stop_if_xiaoai_is_playing()
                        query = f"{query}，{PROMPT}"
                        try:
                            print(
                                "以下是小爱的回答: ",
                                last_record.get("answers")[0]
                                .get("tts", {})
                                .get("text").strip(),
                            )
                        except:
                            print("小爱没回")
                        print("以下是GPT的回答:  ", end="")
                        lock = threading.Lock()
                        stop_event = threading.Event()
                        thread = threading.Thread(target=self.chatbot.ask_stream, args=(query, lock, stop_event))
                        thread.start()
                        while 1:
                            success = lock.acquire(blocking=False)
                            if success:  # 如果成功获取锁
                                try:
                                    this_sentence = self.chatbot.sentence  # 获取句子（目前的）
                                    if this_sentence == "" and not thread.is_alive():
                                        break
                                    is_a_sentence = False
                                    for x in (("，", "。", "？", "！", "；", ",", ".", "?", "!", ";")
                                    if commas <= wait_times else ("。", "？", "！", "；", ".", "?", "!", ";")):
                                        pos = this_sentence.rfind(x)
                                        if pos != -1:
                                            is_a_sentence = True
                                            # 取出完整的句组，剩下的放回去
                                            self.chatbot.sentence = this_sentence[pos + 1:]
                                            this_sentence = this_sentence[:pos + 1]
                                            break
                                finally:
                                    lock.release()
                            else:
                                time.sleep(0.01)
                                continue
                            if not is_a_sentence:
                                time.sleep(0.01)
                                continue
                            if not await self.get_if_xiaoai_is_playing():
                                if commas <= wait_times:
                                    commas += sum([1 for x in this_sentence if
                                                   x in {"，", "。", "？", "！", "；", ",", ".", "?", "!", ";"}]) + 1
                                await self.do_tts(this_sentence)
                                while await self.get_if_xiaoai_is_playing() and not \
                                        (await self.check_new_query(session))[0]:
                                    await asyncio.sleep(0.1)
                                time_stamp, query = await self.check_new_query(session)
                                if time_stamp:
                                    stop_event.set()
                                    while True:
                                        success = lock.acquire(blocking=False)
                                        if success:
                                            try:
                                                self.chatbot.sentence = ""
                                            finally:
                                                lock.release()
                                            break
                                    await self.stop_if_xiaoai_is_playing()
                                    await self.do_tts('')  # 空串施法打断
                                    if not self.chatbot.has_printed:
                                        print()
                                    if query.startswith('闭嘴'):
                                        self.last_timestamp = time_stamp
                                        # 打印彩色信息
                                        print('\033[1;34m' + 'INFO: ' + '\033[0m', end='')
                                        print('\033[1;31m' + 'ChatGPT暂停回答' + '\033[0m')
                                    else:
                                        print('\033[1;34m' + 'INFO: ' + '\033[0m', end='')
                                        print('\033[1;33m' + '有新的问答，ChatGPT停止当前回答' + '\033[0m')
                                    break


if __name__ == "__main__":
    miboy = MiGPT()
    asyncio.run(miboy.run_forever())
