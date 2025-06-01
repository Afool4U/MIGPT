import json
import asyncio
from miaccount import MiAccount, get_random

import logging

_LOGGER = logging.getLogger(__package__)


class MiNAService:
    def __init__(self, account: MiAccount):
        self.account = account
        self.max_retries = 3
        self.retry_delay = 1  # 初始重试延迟（秒）

    async def mina_request(self, uri, data=None):
        requestId = "app_ios_" + get_random(30)
        if data is not None:
            data["requestId"] = requestId
        else:
            uri += "&requestId=" + requestId
        headers = {
            "User-Agent": "MiHome/6.0.103 (com.xiaomi.mihome; build:6.0.103.1; iOS 14.4.0) Alamofire/6.0.103 MICO/iOSApp/appStore/6.0.103"
        }
        return await self.account.mi_request(
            "micoapi", "https://api2.mina.mi.com" + uri, data, headers
        )

    async def device_list(self, master=0):
        result = await self.mina_request("/admin/v2/device_list?master=" + str(master))
        return result.get("data") if result else None

    async def ubus_request(self, deviceId, method, path, message):
        message = json.dumps(message)
        result = await self.mina_request(
            "/remote/ubus",
            {"deviceId": deviceId, "message": message, "method": method, "path": path},
        )
        return result

    async def text_to_speech(self, deviceId, text):
        """带有重试逻辑的text_to_speech方法"""
        retries = 0
        delay = self.retry_delay
        last_error = None
        
        while retries <= self.max_retries:
            try:
                return await self.ubus_request(
                    deviceId, "text_to_speech", "mibrain", {"text": text}
                )
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # 检查是否为ROM端未响应错误
                if "ROM端未响应" in error_str and "3012" in error_str:
                    retries += 1
                    if retries <= self.max_retries:
                        # 指数退避策略
                        wait_time = delay * (2 ** (retries - 1))
                        print(f"设备 {deviceId} ROM端未响应，{wait_time}秒后重试 ({retries}/{self.max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"设备 {deviceId} ROM端未响应，已达到最大重试次数")
                        raise Exception(f"设备 {deviceId} ROM端未响应，已达到最大重试次数") from e
                else:
                    # 其他错误直接抛出
                    raise e
        
        # 如果所有重试都失败
        if last_error:
            raise last_error
        return False

    async def text_to_speech_silent(self, deviceId, text):
        """
        静默发送语音指令，不打印调试信息
        专用于发送停止命令等不需要显示日志的场景
        """
        try:
            # 直接调用ubus请求但不输出日志
            return await self.ubus_request_silent(
                deviceId, "text_to_speech", "mibrain", {"text": text}
            )
        except Exception as e:
            # 安静地处理错误
            return False

    async def ubus_request_silent(self, deviceId, method, path, message):
        """
        静默版本的ubus_request，不输出调试信息
        """
        message_json = json.dumps(message)
        try:
            result = await self.account.mi_request_silent(
                "micoapi", 
                "https://api2.mina.mi.com/remote/ubus",
                {"deviceId": deviceId, "message": message_json, "method": method, "path": path},
                {"User-Agent": "MiHome/6.0.103 (com.xiaomi.mihome; build:6.0.103.1; iOS 14.4.0) Alamofire/6.0.103 MICO/iOSApp/appStore/6.0.103"}
            )
            return result
        except Exception:
            return False

    async def player_set_volume(self, deviceId, volume):
        return await self.ubus_request(
            deviceId,
            "player_set_volume",
            "mediaplayer",
            {"volume": volume, "media": "app_ios"},
        )

    async def player_pause(self, deviceId):
        return await self.ubus_request(
            deviceId,
            "player_play_operation",
            "mediaplayer",
            {"action": "pause", "media": "app_ios"},
        )

    async def player_play(self, deviceId):
        return await self.ubus_request(
            deviceId,
            "player_play_operation",
            "mediaplayer",
            {"action": "play", "media": "app_ios"},
        )

    async def player_get_status(self, deviceId):
        return await self.ubus_request(
            deviceId,
            "player_get_play_status",
            "mediaplayer",
            {"media": "app_ios"},
        )

    async def play_by_url(self, deviceId, url):
        return await self.ubus_request(
            deviceId,
            "player_play_url",
            "mediaplayer",
            {"url": url, "type": 1, "media": "app_ios"},
        )

    async def send_message(self, devices, devno, message, volume=None, silent=False):  # -1/0/1...
        """
        发送消息到设备
        silent: 是否静默发送（不打印调试信息）
        """
        result = False
        for i in range(0, len(devices)):
            if (
                devno == -1
                or devno != i + 1
                or devices[i]["capabilities"].get("yunduantts")
            ):
                device_id = devices[i]["deviceID"]
                device_name = devices[i].get("name", device_id)
                
                try:
                    if not silent:
                        _LOGGER.debug(
                            "Send to devno=%d index=%d: %s", devno, i, message or volume
                        )
                    
                    # 设置音量（如果需要）
                    if volume is not None:
                        try:
                            vol_result = await self.player_set_volume(device_id, volume)
                            result = bool(vol_result)
                        except Exception as e:
                            if not silent:
                                print(f"设置设备 {device_name} 音量失败: {e}")
                            result = False
                    else:
                        result = True
                    
                    # 发送文本
                    if result and message:
                        try:
                            if silent:
                                tts_result = await self.text_to_speech_silent(device_id, message)
                            else:
                                tts_result = await self.text_to_speech(device_id, message)
                            result = bool(tts_result)
                        except Exception as e:
                            if not silent:
                                print(f"向设备 {device_name} 发送消息失败: {e}")
                            result = False
                    
                    # 记录结果
                    if not result and not silent:
                        _LOGGER.error("Send failed to device %s: %s", device_name, message or volume)
                    
                    # 如果不是要发送给所有设备，或者发送失败，则停止
                    if devno != -1 or not result:
                        break
                        
                except Exception as e:
                    if not silent:
                        print(f"与设备 {device_name} 通信时出错: {e}")
                    result = False
                    if devno != -1:
                        break
        
        return result
