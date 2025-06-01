"""
A simple wrapper for the official ChatGPT API and BigModel API
"""
import json
import requests
import tiktoken
import threading  # 添加这一行导入threading模块


class Chatbot:
    """
    ChatGPT API with BigModel API support
    """

    def __init__(
            self,
            api_key: str,
            engine: str = "gpt-3.5-turbo",
            proxy: str = None,
            max_tokens: int = 3000,
            temperature: float = 0.5,
            top_p: float = 1.0,
            presence_penalty: float = 0.0,
            frequency_penalty: float = 0.0,
            reply_count: int = 1,
            system_prompt: str = "You are ChatGPT, a large language model trained by OpenAI. Respond conversationally",
            api_base: str = None,
            api_type: str = "openai",  # 新增参数，用于区分API类型
    ) -> None:
        """
        Initialize Chatbot with API key
        """
        self.engine = engine
        self.session = requests.Session()
        self.api_key = api_key
        self.proxy = proxy
        self.api_base = api_base
        self.api_type = api_type

        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.reply_count = reply_count

        self.sentence = ""
        self.temp = ""  # 确保初始化为空字符串
        self.has_printed = False

        if self.proxy:
            proxies = {
                "http": self.proxy,
                "https": self.proxy,
            }
            self.session.proxies = proxies
        self.conversation: dict = {
            "default": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
            ],
        }
        if max_tokens > 4000:
            raise Exception("Max tokens cannot be greater than 4000")

        if self.get_token_count("default") > self.max_tokens:
            raise Exception("System prompt is too long")

    def add_to_conversation(
            self,
            message: str,
            role: str,
            convo_id: str = "default",
    ) -> None:
        """
        Add a message to the conversation
        """
        self.conversation[convo_id].append({"role": role, "content": message})

    def __truncate_conversation(self, convo_id: str = "default") -> None:
        """
        Truncate the conversation
        """
        while True:
            if (
                    self.get_token_count(convo_id) > self.max_tokens
                    and len(self.conversation[convo_id]) > 1
            ):
                # Don't remove the first message
                self.conversation[convo_id].pop(1)
            else:
                break

    # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    def get_token_count(self, prompt):
        """
        Get token count for different models
        """
        # 为特定模型设置token计数方法
        if self.engine == "deepseek-chat":
            # DeepSeek 使用类似GPT-3.5的token计数方式，但简化处理
            return len(prompt) // 2  # 简单估算中文约为2个字符一个token
            
        # Volcengine (方舟平台)特定处理
        if "ark-model" in self.engine:
            return len(prompt) // 2  # 简单估算
        
        # Siliconflow QwQ-32B特定处理  
        if "QwQ-32B" in self.engine:
            return len(prompt) // 2  # 简单估算
            
        # 百度千帆平台特定处理
        if self.engine.startswith("ernie-"):
            return len(prompt) // 2  # 简单估算中文约为2个字符一个token
        
        # For BigModel API
        if self.api_type == "bigmodel":
            # 对于智谱AI的模型，使用默认的token计数方法
            return len(prompt) // 2  # 简单估算中文约为2个字符一个token
        
        # For OpenAI models
        if self.engine.startswith("gpt-3.5-turbo"):
            try:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                if isinstance(prompt, str):
                    return len(encoding.encode(prompt))
                elif isinstance(prompt, list):
                    return sum(len(encoding.encode(msg["content"])) for msg in prompt)
                elif isinstance(prompt, dict):
                    return sum(len(encoding.encode(str(val))) for val in prompt.values())
                else:
                    return len(prompt) // 4  # 回退到简单估算
            except Exception:
                return len(prompt) // 4  # 出错时回退到简单估算
        elif self.engine.startswith("gpt-4"):
            try:
                encoding = tiktoken.encoding_for_model("gpt-4")
                if isinstance(prompt, str):
                    return len(encoding.encode(prompt))
                elif isinstance(prompt, list):
                    return sum(len(encoding.encode(msg["content"])) for msg in prompt)
                elif isinstance(prompt, dict):
                    return sum(len(encoding.encode(str(val))) for val in prompt.values())
                else:
                    return len(prompt) // 4  # 回退到简单估算
            except Exception:
                return len(prompt) // 4  # 出错时回退到简单估算
        elif self.engine == "text-davinci-002-render-sha":
            try:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                if isinstance(prompt, str):
                    return len(encoding.encode(prompt))
                else:
                    return len(prompt) // 4  # 回退到简单估算
            except Exception:
                return len(prompt) // 4  # 出错时回退到简单估算
        elif self.engine == "glm-4-flash":
            # 添加对glm-4-flash的支持，使用简单的token估算
            return len(prompt) // 2  # 简单估算中文约为2个字符一个token
        elif self.engine == "ai-virtual-mate":
            # 添加对ai-virtual-mate的支持，使用简单的token估算
            return len(prompt) // 2  # 简单估算中文约为2个字符一个token
        else:
            # 默认处理方式
            return len(prompt) // 3  # 简单估算，大多数模型

    def get_max_tokens(self, convo_id: str) -> int:
        """
        Get max tokens
        """
        return self.max_tokens - self.get_token_count(convo_id)

    def ask_stream(
            self,
            prompt: str,
            lock: threading.Lock,
            stop_event: threading.Event,
            role: str = "user",
            convo_id: str = "default",
    ) -> None:
        """Ask a question"""
        self.has_printed = False
        # 确保初始化为空字符串
        self.sentence = ""
        self.temp = ""
        
        # Make conversation if it doesn't exist
        if convo_id not in self.conversation:
            self.reset(convo_id=convo_id, system_prompt=self.system_prompt)
        self.add_to_conversation(prompt, "user", convo_id=convo_id)
        self.__truncate_conversation(convo_id=convo_id)
        
        # 清理API密钥，移除可能的换行符和空白字符
        clean_api_key = self.api_key.strip() if self.api_key else ""
        
        # 统一的请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 设置Bearer令牌认证，针对不同API类型进行特殊处理
        if self.api_type == "custom" and "qianfan" in self.api_base:
            # 千帆API特殊处理，使用Bearer令牌格式
            if not clean_api_key.startswith("bce-v3"):
                # 如果不是bce-v3格式，尝试使用标准Bearer格式
                headers["Authorization"] = f"Bearer {clean_api_key}"
            else:
                # 如果是bce-v3格式，千帆要求直接使用此格式
                headers["Authorization"] = f"Bearer {clean_api_key}"
                
            # 添加可能需要的额外头部
            headers["Content-Type"] = "application/json"
        else:
            # 其他API类型使用标准Authorization头
            headers["Authorization"] = f"Bearer {clean_api_key}"
        
        # 基础payload
        payload = {
            "model": self.engine,
            "messages": self.conversation[convo_id],
            "stream": True,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        
        # 根据API类型添加特定参数
        if self.api_type == "openai":
            payload.update({
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
                "n": self.reply_count,
                "user": role,
                "max_tokens": self.get_max_tokens(convo_id=convo_id),
            })
            api_url = f"{self.api_base or 'https://api.openai.com/v1'}/chat/completions"
        elif self.api_type == "bigmodel":
            # 智谱AI特定参数
            api_url = f"{self.api_base}/chat/completions"
        elif self.engine == "deepseek-chat":
            # DeepSeek API特殊处理
            payload.update({
                "max_tokens": self.get_max_tokens(convo_id=convo_id),
            })
            # 确保API基础URL正确
            base_url = self.api_base
            if base_url.endswith('/v1'):
                base_url = base_url[:-3]  # 移除尾部的 /v1
            if not base_url:
                base_url = "https://api.deepseek.com"
                
            api_url = f"{base_url}/chat/completions"
            print(f"使用DeepSeek API: {api_url}")
        elif "ark-model" in self.engine or "DeepSeek" in self.engine or self.api_base and "volces.com" in self.api_base:
            # Volcengine (方舟平台) API特殊处理
            # 方舟平台模型ID可能需要修正
            # 根据文档，需要使用正确的Model ID
            
            # 从常见模型名称映射到方舟平台的正确模型ID
            volcengine_model_map = {
                "DeepSeek-R1": "deepseek-r1-250120",   # 添加版本号
                "deepseek-r1": "deepseek-r1-250120",   # 添加版本号
                "DeepSeek-V3": "deepseek-v3-250324",   # 添加最新推荐版本号
                "deepseek-v3": "deepseek-v3-250324",   # 添加最新推荐版本号
                "deepseek-v3-250324": "deepseek-v3-250324", # 完整ID直接保留
                "deepseek-v3-241226": "deepseek-v3-241226", # 完整ID直接保留
                "ark-model": "doubao-1.5-pro-32k-250115"    # 默认使用推荐模型
            }
            
            # 检查是否需要替换模型名称
            model_name = self.engine
            if model_name in volcengine_model_map:
                model_name = volcengine_model_map[model_name]
                print(f"方舟平台模型名称已映射: {self.engine} -> {model_name}")
            
            payload.update({
                "model": model_name,
                "max_tokens": self.get_max_tokens(convo_id=convo_id),
            })
            api_url = f"{self.api_base}/chat/completions"
            print(f"使用方舟API: {api_url}，模型: {model_name}")
            
            # 添加模型访问检查提示
            print("注意: 请确认您的API密钥有权限访问此模型，并且模型ID格式正确")
            print("方舟平台支持的模型可在控制台-模型列表中查看")
        elif "QwQ-32B" in self.engine or "Qwen/" in self.engine:
            # Siliconflow API特殊处理
            payload.update({
                "max_tokens": min(512, self.get_max_tokens(convo_id=convo_id)),
                "temperature": self.temperature,
                "top_p": self.top_p,
                "frequency_penalty": 0.5,  # Siliconflow特定默认值
                "top_k": 50,               # Siliconflow特定参数
                "response_format": {"type": "text"} # 指定返回格式
            })
            # 移除不支持的参数
            if "enable_thinking" in payload:
                del payload["enable_thinking"]
                
            # 尝试非流式请求，Siliconflow可能与流式请求有兼容性问题
            payload["stream"] = False
                
            api_url = f"{self.api_base}/chat/completions"
            print(f"使用Siliconflow API: {api_url}")
        elif self.engine.startswith("ernie-"):
            # 百度千帆API特殊处理
            payload.update({
                "max_completion_tokens": self.get_max_tokens(convo_id=convo_id),
                "stream": True
            })
            # 移除千帆API不支持的参数
            if "presence_penalty" in payload:
                del payload["presence_penalty"]
            if "frequency_penalty" in payload:
                del payload["frequency_penalty"]
                
            # 确保使用正确的ernie模型ID格式
            if self.engine == "ernie-3.5":
                self.engine = "ernie-3.5-8k"
                print(f"已修正模型名称为: {self.engine}")
                payload["model"] = self.engine
                
            api_url = f"{self.api_base}/chat/completions"
            print(f"使用百度千帆API: {api_url}")
            print("模型: " + self.engine)
        else:
            # 通用第三方API（custom类型）
            # 大多数第三方API都兼容OpenAI格式，但可能不支持所有参数
            payload.update({
                "max_tokens": self.get_max_tokens(convo_id=convo_id),
            })
            api_url = f"{self.api_base}/chat/completions"
        
        # 发送请求
        try:
            # 特别针对千帆API的调试信息
            if self.api_base and "qianfan" in self.api_base:
                print(f"千帆API请求URL: {api_url}")
                print(f"千帆API认证头: {headers['Authorization'][:15]}..." if 'Authorization' in headers else "无认证头")
                print(f"千帆API请求模型: {self.engine}")
                
            response = self.session.post(
                api_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=30,  # 添加超时设置
            )
                
            if response.status_code != 200:
                # 增强错误信息
                error_msg = f"错误状态码: {response.status_code} {response.reason}"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        if "error" in error_data:
                            error_detail = error_data["error"]
                            error_msg += f"\n错误详情: {error_detail.get('message', '')}"
                            error_msg += f"\n错误码: {error_detail.get('code', '')}"
                            error_msg += f"\n错误类型: {error_detail.get('type', '')}"
                            
                            # 针对特定错误提供解决方案
                            if "invalid_appId" in error_msg or "No permission" in error_msg:
                                error_msg += "\n\n可能的解决方案:"
                                error_msg += "\n1. 请确认您的API Key格式正确且未过期"
                                error_msg += "\n2. 请在千帆控制台(https://console.bce.baidu.com/qianfan)确认您有权限访问所选模型"
                                error_msg += "\n3. 尝试在控制台创建新的API Key并更新config.json"
                                error_msg += "\n4. 如果使用长效API Key，请尝试获取短期API Key"
                except:
                    error_msg += f"\n原始响应: {response.text}"
                    
                raise Exception(f"API请求失败: {error_msg}")
                
            response_role: str = None
            full_response: str = ""

            # 特殊处理非流式响应
            if not payload.get("stream", True):
                try:
                    resp_json = response.json()
                    if "choices" in resp_json and resp_json["choices"]:
                        message = resp_json["choices"][0].get("message", {})
                        if message and "content" in message:
                            content = message.get("content", "")
                            role = message.get("role", "assistant")
                            if content:  # 确保content不为None
                                self.sentence = content
                                print(content)
                                full_response = content
                                self.has_printed = True
                                self.add_to_conversation(full_response, role, convo_id=convo_id)
                                return
                except Exception as e:
                    print(f"\n处理非流式响应时出错: {str(e)}")
                    self.sentence = f"API响应解析错误: {str(e)}"
                    self.has_printed = True
                    return
            
            # 流式响应处理
            for line in response.iter_lines():
                if stop_event.is_set():
                    self.temp = ""
                    return
                if not line:
                    continue
                # Remove "data: "
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    resp: dict = json.loads(line)
                    choices = resp.get("choices")
                    if not choices:
                        continue
                    delta = choices[0].get("delta")
                    if not delta:
                        # 对于Siliconflow等一些API，可能直接返回完整消息
                        message = choices[0].get("message")
                        if message and message.get("content"):
                            content = message.get("content")
                            # 确保content不为None
                            if content is not None:
                                success = lock.acquire(blocking=False)
                                if success:
                                    try:
                                        # 确保self.temp是字符串
                                        temp_str = self.temp if self.temp is not None else ""
                                        content_str = content if content is not None else ""
                                        self.sentence += temp_str + content_str
                                        self.temp = ""
                                    finally:
                                        lock.release()
                                else:
                                    # 确保self.temp是字符串
                                    self.temp = (self.temp or "") + (content or "")
                                print(content, end="")
                                # 确保content不为None后再拼接
                                full_response = (full_response or "") + (content or "")
                        continue
                    if "role" in delta:
                        response_role = delta["role"]
                    if "content" in delta:
                        content = delta["content"]
                        # 确保content不为None
                        if content is not None:
                            success = lock.acquire(blocking=False)
                            if success:
                                try:
                                    # 确保所有变量都是字符串，防止None连接错误
                                    temp_str = self.temp if self.temp is not None else ""
                                    content_str = content if content is not None else ""
                                    self.sentence += temp_str + content_str
                                    self.temp = ""
                                finally:
                                    lock.release()
                            else:
                                # 确保self.temp始终是字符串
                                self.temp = (self.temp or "") + (content or "")
                            print(content, end="")
                            # 确保content不为None后再拼接
                            full_response = (full_response or "") + (content or "")
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON: {line}")
                    continue
                    
            print()
            self.has_printed = True
            # 确保full_response不为None
            if full_response:
                self.add_to_conversation(full_response, response_role or "assistant", convo_id=convo_id)
            else:
                self.add_to_conversation("", response_role or "assistant", convo_id=convo_id)
                
        except requests.exceptions.RequestException as e:
            print(f"\nAPI请求错误: {str(e)}")
            self.sentence = f"API请求错误: {str(e)}"
            self.has_printed = True

    def rollback(self, n: int = 1, convo_id: str = "default") -> None:
        """
        Rollback the conversation
        """
        for _ in range(n):
            self.conversation[convo_id].pop()

    def reset(self, convo_id: str = "default", system_prompt: str = None) -> None:
        """
        Reset the conversation
        """
        self.conversation[convo_id] = [
            {"role": "system", "content": system_prompt or self.system_prompt},
        ]

    def save(self, file: str, *convo_ids: str) -> bool:
        """
        Save the conversation to a JSON file
        """
        try:
            with open(file, "w", encoding="utf-8") as f:
                if convo_ids:
                    json.dump({k: self.conversation[k] for k in convo_ids}, f, indent=2)
                else:
                    json.dump(self.conversation, f, indent=2)
        except (FileNotFoundError, KeyError):
            return False
        return True
        # print(f"Error: {file} could not be created")

    def load(self, file: str, *convo_ids: str) -> bool:
        """
        Load the conversation from a JSON  file
        """
        try:
            with open(file, encoding="utf-8") as f:
                if convo_ids:
                    convos = json.load(f)
                    self.conversation.update({k: convos[k] for k in convo_ids})
                else:
                    self.conversation = json.load(f)
        except (FileNotFoundError, KeyError, json.decoder.JSONDecodeError):
            return False
        return True

    def load_config(self, file: str, no_api_key: bool = False) -> bool:
        """
        Load the configuration from a JSON file
        """
        try:
            with open(file, encoding="utf-8") as f:
                config = json.load(f)
                if config is not None:
                    self.api_key = config.get("api_key") or self.api_key
                    if self.api_key is None:
                        # Make sure the API key is set
                        raise Exception("Error: API key is not set")
                    
                    # 加载API类型
                    if config.get("api_type") is not None:
                        self.api_type = config.get("api_type")
                        
                    # 加载API基础URL
                    if config.get("api_base") is not None:
                        self.api_base = config.get("api_base") or self.api_base
                        
                    # 加载模型名称 (优先使用model_name，其次使用engine字段)
                    if config.get("model_name") is not None:
                        self.engine = config.get("model_name")
                    elif config.get("engine") is not None:
                        self.engine = config.get("engine")
                    
                    # 特殊处理千帆API
                    if self.api_base and "qianfan" in self.api_base:
                        print(f"已检测到千帆API配置:")
                        print(f"  - API基础URL: {self.api_base}")
                        print(f"  - 模型: {self.engine}")
                        print(f"  - API类型: {self.api_type}")
                        
                        # 尝试获取短期令牌
                        if self.api_key and self.api_key.startswith("bce-v3"):
                            try:
                                short_term_key = self.get_qianfan_short_term_token(self.api_key)
                                if short_term_key != self.api_key:
                                    print("已将长期令牌转换为短期令牌")
                                    self.api_key = short_term_key
                            except Exception as e:
                                print(f"转换短期令牌时出错: {str(e)}")
                        
                    self.temperature = config.get("temperature") or self.temperature
                    self.top_p = config.get("top_p") or self.top_p
                    self.presence_penalty = (
                            config.get("presence_penalty") or self.presence_penalty
                    )
                    self.frequency_penalty = (
                            config.get("frequency_penalty") or self.frequency_penalty
                    )
                    self.reply_count = config.get("reply_count") or self.reply_count
                    self.max_tokens = config.get("max_tokens") or self.max_tokens

                    if config.get("system_prompt") is not None:
                        self.system_prompt = (
                                config.get("system_prompt") or self.system_prompt
                        )
                        self.reset(system_prompt=self.system_prompt)

                    if config.get("proxy") is not None:
                        self.proxy = config.get("proxy") or self.proxy
                        proxies = {
                            "http": self.proxy,
                            "https": self.proxy,
                        }
                        self.session.proxies = proxies
                        
                    if config.get("key_name"):
                        # 处理 key_name 的代码
                        pass
        except (FileNotFoundError, KeyError, json.decoder.JSONDecodeError):
            return False
        return True

    def get_qianfan_short_term_token(self, api_key):
        """
        获取千帆短期API令牌
        """
        if not api_key.startswith("bce-v3"):
            # 如果不是bce-v3格式，直接返回原始密钥
            return api_key
            
        # 构建请求URL，设置过期时间为24小时
        url = "https://iam.bj.baidubce.com/v1/BCE-BEARER/token?expireInSeconds=86400"
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            print("正在获取千帆短期令牌...")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    short_term_token = data["token"]
                    print(f"成功获取短期令牌，有效期至: {data.get('expireTime', '未知')}")
                    return short_term_token
                else:
                    print("短期令牌响应中未找到token字段")
            else:
                print(f"获取短期令牌失败: 状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except Exception as e:
            print(f"获取短期令牌时出错: {str(e)}")
            
        # 失败时返回原始令牌
        return api_key