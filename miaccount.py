import base64
import hashlib
import json
import logging
import os
import random
import string
import time
import asyncio
from urllib import parse
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__package__)


def get_random(length):
    return "".join(random.sample(string.ascii_letters + string.digits, length))


class MiTokenStore:
    def __init__(self, token_path):
        self.token_path = token_path

    def load_token(self):
        if os.path.isfile(self.token_path):
            try:
                with open(self.token_path) as f:
                    return json.load(f)
            except Exception:
                _LOGGER.exception("Exception on load token from %s", self.token_path)
        return None

    def save_token(self, token=None):
        if token:
            try:
                with open(self.token_path, "w") as f:
                    json.dump(token, f, indent=2)
            except Exception:
                _LOGGER.exception("Exception on save token to %s", self.token_path)
        elif os.path.isfile(self.token_path):
            os.remove(self.token_path)


class MiAccount:
    def __init__(self, session: ClientSession, username, password, token_store=None):
        self.session = session
        self.username = username
        self.password = password
        self.token_store = (
            MiTokenStore(token_store) if isinstance(token_store, str) else token_store
        )
        self.token = token_store is not None and self.token_store.load_token()

    async def login(self, sid):
        # 检查会话是否存在
        if self.session is None:
            _LOGGER.error("会话对象为空，无法发送请求")
            return False
            
        # 如果没有提供用户名或密码，直接返回False
        if not self.username or not self.password:
            _LOGGER.warning("未提供小米账号或密码，跳过登录")
            return False

        if not self.token:
            self.token = {"deviceId": get_random(16).upper()}
            _LOGGER.debug(f"生成新的设备ID: {self.token['deviceId']}")
        
        try:
            _LOGGER.debug(f"开始登录小米账号: {self.username}, sid: {sid}")
            resp = await self._serviceLogin(f"serviceLogin?sid={sid}&_json=true")
            
            if resp["code"] != 0:
                _LOGGER.debug(f"serviceLogin返回非零代码: {resp['code']}, 尝试serviceLoginAuth2")
                data = {
                    "_json": "true",
                    "qs": resp["qs"],
                    "sid": resp["sid"],
                    "_sign": resp["_sign"],
                    "callback": resp["callback"],
                    "user": self.username,
                    "hash": hashlib.md5(self.password.encode()).hexdigest().upper(),
                }
                resp = await self._serviceLogin("serviceLoginAuth2", data)
                
                if resp["code"] != 0:
                    # 处理验证码错误
                    if resp["code"] == 87001 and resp.get("type") == "manMachine":
                        _LOGGER.error("登录需要验证码，请按照以下步骤解决：")
                        _LOGGER.error("1. 打开小米官网 https://account.xiaomi.com 手动登录一次")
                        _LOGGER.error("2. 登录成功后，删除token.json文件（如果存在）")
                        _LOGGER.error("3. 重新启动程序")
                        print("\n\n============= 验证码错误 =============")
                        print("登录需要验证码，请按照以下步骤解决：")
                        print("1. 打开小米官网 https://account.xiaomi.com 手动登录一次")
                        print("2. 登录成功后，删除token.json文件（如果存在）")
                        print("3. 重新启动程序")
                        print("========================================\n\n")
                        
                        # 删除可能存在的token文件，强制下次重新登录
                        if self.token_store:
                            self.token_store.save_token(None)  # 这会删除token文件
                            
                        return False
                    else:
                        _LOGGER.error(f"登录失败，错误码: {resp['code']}, 描述: {resp.get('desc', '未知错误')}")
                        return False

            _LOGGER.debug(f"登录成功，获取userId和passToken")
            self.token["userId"] = resp["userId"]
            self.token["passToken"] = resp["passToken"]

            _LOGGER.debug(f"获取serviceToken")
            serviceToken = await self._securityTokenService(
                resp["location"], resp["nonce"], resp["ssecurity"]
            )
            self.token[sid] = (resp["ssecurity"], serviceToken)
            
            if self.token_store:
                _LOGGER.debug(f"保存token到{self.token_store.token_path}")
                self.token_store.save_token(self.token)
            
            _LOGGER.info(f"小米账号 {self.username} 登录成功")
            return True

        except Exception as e:
            self.token = None
            if self.token_store:
                self.token_store.save_token()
            _LOGGER.exception(f"登录异常: {e}")
            return False

    async def _serviceLogin(self, uri, data=None):
        # 检查会话是否存在
        if self.session is None:
            raise Exception("会话对象为空，无法发送请求")
            
        headers = {
            "User-Agent": "APP/com.xiaomi.mihome APPV/6.0.103 iosPassportSDK/3.9.0 iOS/14.4 miHSTS"
        }
        cookies = {"sdkVersion": "3.9", "deviceId": self.token["deviceId"]}
        if "passToken" in self.token:
            cookies["userId"] = self.token["userId"]
            cookies["passToken"] = self.token["passToken"]
        url = "https://account.xiaomi.com/pass/" + uri
        
        _LOGGER.debug(f"发送请求到: {url}")
        _LOGGER.debug(f"请求方法: {'GET' if data is None else 'POST'}")
        _LOGGER.debug(f"请求cookies: {cookies}")
        
        try:
            async with self.session.request(
                "GET" if data is None else "POST",
                url,
                data=data,
                cookies=cookies,
                headers=headers,
                ssl = False,
                timeout=15,  # 增加超时时间
            ) as r:
                raw = await r.read()
                
                # 检查响应状态
                if r.status != 200:
                    _LOGGER.error(f"请求失败，状态码: {r.status}")
                    _LOGGER.debug(f"响应内容: {raw}")
                    raise Exception(f"HTTP错误: {r.status}")
                    
                # 处理响应内容
                if len(raw) < 11:
                    _LOGGER.error(f"响应内容过短: {raw}")
                    raise Exception("响应内容异常")
                    
                try:
                    resp = json.loads(raw[11:])
                    _LOGGER.debug(f"{uri}: {resp}")
                    return resp
                except json.JSONDecodeError as e:
                    _LOGGER.error(f"JSON解析错误: {e}")
                    _LOGGER.debug(f"原始响应: {raw}")
                    raise Exception(f"JSON解析错误: {e}")
        except asyncio.TimeoutError:
            _LOGGER.error("请求超时")
            raise Exception("请求超时")
        except Exception as e:
            _LOGGER.error(f"请求异常: {e}")
            raise

    async def _securityTokenService(self, location, nonce, ssecurity):
        # 检查会话是否存在
        if self.session is None:
            raise Exception("会话对象为空，无法发送请求")
            
        nsec = "nonce=" + str(nonce) + "&" + ssecurity
        clientSign = base64.b64encode(hashlib.sha1(nsec.encode()).digest()).decode()
        url = location + "&clientSign=" + parse.quote(clientSign)
        
        _LOGGER.debug(f"获取serviceToken: {url}")
        
        try:
            async with self.session.get(url, timeout=15) as r:
                if "serviceToken" not in r.cookies:
                    error_text = await r.text()
                    _LOGGER.error(f"未找到serviceToken，响应: {error_text}")
                    raise Exception(f"未找到serviceToken: {error_text}")
                    
                serviceToken = r.cookies["serviceToken"].value
                if not serviceToken:
                    error_text = await r.text()
                    _LOGGER.error(f"serviceToken为空，响应: {error_text}")
                    raise Exception(f"serviceToken为空: {error_text}")
                    
                _LOGGER.debug(f"成功获取serviceToken")
                return serviceToken
        except Exception as e:
            _LOGGER.error(f"获取serviceToken失败: {e}")
            raise

    async def mi_request(self, sid, url, data, headers, relogin=True):
        # 检查会话是否存在
        if self.session is None:
            _LOGGER.error("会话对象为空，无法发送请求")
            return False
            
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if (self.token and sid in self.token) or await self.login(sid):  # Ensure login
                    cookies = {
                        "userId": self.token["userId"],
                        "serviceToken": self.token[sid][1],
                    }
                    content = data(self.token, cookies) if callable(data) else data
                    method = "GET" if data is None else "POST"
                    _LOGGER.info("%s %s", url, content)
                    
                    async with self.session.request(
                        method, url, data=content, cookies=cookies, headers=headers, 
                        ssl=False, timeout=15  # 增加超时时间
                    ) as r:
                        status = r.status
                        if status == 200:
                            try:
                                resp = await r.json(content_type=None)
                                code = resp["code"]
                                if code == 0:
                                    return resp
                                
                                # 处理特定错误码
                                if code == 3:  # 一般为登录状态错误
                                    _LOGGER.warn("登录状态错误，尝试重新登录...")
                                    self.token = None  # 重置token
                                    if retry_count < max_retries:
                                        retry_count += 1
                                        await self.login(sid)
                                        continue
                                        
                                if "auth" in resp.get("message", "").lower():
                                    status = 401
                            except Exception as json_err:
                                _LOGGER.error("解析JSON响应失败: %s", json_err)
                                resp = await r.text()
                        else:
                            resp = await r.text()
                            
                    # 特殊处理401错误（认证错误）
                    if status == 401 and relogin:
                        _LOGGER.warn("身份验证错误，尝试重新登录... (尝试 %d/%d)", retry_count + 1, max_retries)
                        self.token = None  # 重置token
                        if retry_count < max_retries:
                            retry_count += 1
                            continue
                        else:
                            raise Exception(f"重新登录尝试{max_retries}次后仍然失败")
                            
                    # 特殊处理cookie相关错误
                    if isinstance(resp, str) and ("cookie" in resp.lower() or "userId" in resp.lower()):
                        _LOGGER.warn("Cookie错误，尝试重新登录... (尝试 %d/%d)", retry_count + 1, max_retries)
                        self.token = None  # 重置token
                        if retry_count < max_retries:
                            retry_count += 1
                            continue
                    
                    # 如果是其他类型的错误，直接抛出
                    if status != 200 or (isinstance(resp, dict) and resp.get("code", 0) != 0):
                        error_msg = f"请求失败: 状态码={status}, 响应={resp}"
                        _LOGGER.error(error_msg)
                        raise Exception(f"Error {url}: {resp}")
                        
                    return resp
                else:
                    if retry_count < max_retries:
                        retry_count += 1
                        _LOGGER.warn("登录失败，重试中... (尝试 %d/%d)", retry_count, max_retries)
                        continue
                    resp = "Login failed after multiple attempts"
            except Exception as e:
                if retry_count < max_retries:
                    retry_count += 1
                    _LOGGER.warn("请求发生错误，重试中... (尝试 %d/%d): %s", retry_count, max_retries, e)
                    continue
                raise e
                
        raise Exception(f"Error {url}: {resp}")

    async def mi_request_silent(self, sid, url, data, headers, relogin=True):
        """
        静默版本的mi_request，不输出日志信息
        专用于发送停止命令等不需要显示日志的场景
        """
        # 检查会话是否存在
        if self.session is None:
            return False
            
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if (self.token and sid in self.token) or await self.login(sid):  # Ensure login
                    cookies = {
                        "userId": self.token["userId"],
                        "serviceToken": self.token[sid][1],
                    }
                    content = data(self.token, cookies) if callable(data) else data
                    method = "GET" if data is None else "POST"
                    
                    async with self.session.request(
                        method, url, data=content, cookies=cookies, headers=headers, 
                        ssl=False, timeout=15  # 增加超时时间
                    ) as r:
                        status = r.status
                        if status == 200:
                            try:
                                resp = await r.json(content_type=None)
                                code = resp["code"]
                                if code == 0:
                                    return resp
                                
                                # 处理特定错误码
                                if code == 3:  # 一般为登录状态错误
                                    self.token = None  # 重置token
                                    if retry_count < max_retries:
                                        retry_count += 1
                                        await self.login(sid)
                                        continue
                                    
                                if "auth" in resp.get("message", "").lower():
                                    status = 401
                            except Exception:
                                resp = await r.text()
                        else:
                            resp = await r.text()
                            
                    # 特殊处理401错误（认证错误）
                    if status == 401 and relogin:
                        self.token = None  # 重置token
                        if retry_count < max_retries:
                            retry_count += 1
                            continue
                        else:
                            return False
                            
                    # 特殊处理cookie相关错误
                    if isinstance(resp, str) and ("cookie" in resp.lower() or "userId" in resp.lower()):
                        self.token = None  # 重置token
                        if retry_count < max_retries:
                            retry_count += 1
                            continue
                    
                    # 如果是其他类型的错误，直接返回False
                    if status != 200 or (isinstance(resp, dict) and resp.get("code", 0) != 0):
                        return False
                        
                    return resp
                else:
                    if retry_count < max_retries:
                        retry_count += 1
                        continue
                    else:
                        return False
            except Exception:
                if retry_count < max_retries:
                    retry_count += 1
                    continue
                else:
                    return False
                
        return False
