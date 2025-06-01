# HomeAssistant OpenAI兼容API服务器
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import sys
import uuid
import json
import time
from datetime import datetime
import threading
import asyncio
import traceback
import re
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

# 导入MIGPT相关模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import config, MI_USER, MI_PASS, API_TYPE, API_KEY, API_BASE, MODEL_NAME, PROMPT

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 启用CORS支持

# 全局变量
conversation_history = []  # 对话历史
mate_name = config.get("mate_name", "AI助手")  # 助手名称

# 加载HomeAssistant配置
def load_ha_config():
    """加载HomeAssistant配置"""
    try:
        # 从config模块加载配置
        from config import config
        ha_config = config.get("homeassistant", {})
        
        # 如果配置为空，尝试从more_set.json加载（兼容旧版本）
        if not ha_config:
            more_set_file = 'data/set/more_set.json'
            if os.path.exists(more_set_file):
                try:
                    with open(more_set_file, 'r', encoding='utf-8') as f:
                        more_config = json.load(f)
                        ha_config = {
                            "url": more_config.get("HomeAssistant服务器IP", ""),
                            "token": more_config.get("HomeAssistant Token", ""),
                            "text_entity_id": more_config.get("文本指令实体ID", ""),
                            "voice_agent_id": more_config.get("语音API实体ID", "")
                        }
                except Exception as e:
                    print(f"加载HomeAssistant配置文件失败: {str(e)}")
        
        return ha_config
    except Exception as e:
        print(f"加载HomeAssistant配置失败: {str(e)}")
        return {}

# 向HomeAssistant发送文本指令
def send_ha_command(command):
    """向HomeAssistant发送文本指令"""
    max_retries = 3  # 最大重试次数
    retry_delay = 1  # 初始重试延迟（秒）
    
    for retry in range(max_retries + 1):
        try:
            ha_config = load_ha_config()
            
            if not ha_config.get('url'):
                return "错误：HomeAssistant URL未配置"
            if not ha_config.get('token'):
                return "错误：HomeAssistant Token未配置"
            if not ha_config.get('text_entity_id'):
                return "错误：文本实体ID未配置"
            
            response = requests.post(
                f"{ha_config['url']}/api/services/text/set_value",
                headers={"Authorization": f"Bearer {ha_config['token']}"},
                json={"entity_id": ha_config["text_entity_id"], "value": command},
                timeout=10
            )

            response.raise_for_status()  # 如果状态码不是200，抛出异常
            
            result_list = response.json()
            if isinstance(result_list, list) and len(result_list) > 0:
                result = f"执行成功：{result_list[0].get('state', '操作完成')}".replace("{lv=stt}", command)
            else:
                result = "指令已执行"
                
            return result
            
        except Timeout:
            # 超时错误处理
            if retry < max_retries:
                wait_time = retry_delay * (2 ** retry)  # 指数增长等待时间
                print(f"请求超时，{wait_time}秒后重试... ({retry+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return "请求HomeAssistant超时，请检查网络连接"
                
        except ConnectionError:
            # 连接错误
            if retry < max_retries:
                wait_time = retry_delay * (2 ** retry)
                print(f"连接错误，{wait_time}秒后重试... ({retry+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return "无法连接到HomeAssistant，请检查网络连接和服务器地址"
                
        except RequestException as e:
            # 其他请求错误
            if retry < max_retries:
                wait_time = retry_delay * (2 ** retry)
                print(f"请求错误({str(e)})，{wait_time}秒后重试... ({retry+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return f"操作异常: {str(e)}"
                
        except Exception as e:
            return f"操作异常：{str(e)}"

# 向HomeAssistant发送语音指令
def send_ha_voice_command(text):
    """向HomeAssistant发送语音指令"""
    max_retries = 3  # 最大重试次数
    retry_delay = 1  # 初始重试延迟（秒）
    
    for retry in range(max_retries + 1):
        try:
            ha_config = load_ha_config()
            
            # 检查必要的配置是否存在
            if not ha_config.get("url"):
                return "语音指令失败: 缺少HomeAssistant服务器URL配置"
            if not ha_config.get("token"):
                return "语音指令失败: 缺少HomeAssistant Token配置"
            if not ha_config.get("voice_agent_id"):
                return "语音指令失败: 缺少语音Agent ID配置"
            
            response = requests.post(
                f"{ha_config['url']}/api/conversation/process",
                headers={"Authorization": f"Bearer {ha_config['token']}"},
                json={"agent_id": ha_config["voice_agent_id"], "text": text, "language": "zh-CN"},
                timeout=20
            )
            
            response.raise_for_status()  # 如果状态码不是200，抛出异常
            response_json = response.json()
            
            # 检查响应中是否包含我们期望的字段
            if ('response' in response_json and 
                'speech' in response_json['response'] and 
                'plain' in response_json['response']['speech'] and
                'speech' in response_json['response']['speech']['plain']):
                return response_json['response']['speech']['plain']['speech']
            else:
                return "处理成功，但返回格式不符合预期"

        except Timeout:
            # 超时错误处理
            if retry < max_retries:
                wait_time = retry_delay * (2 ** retry)  # 指数增长等待时间
                print(f"语音请求超时，{wait_time}秒后重试... ({retry+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return "请求HomeAssistant语音接口超时，请检查网络连接"
                
        except ConnectionError:
            # 连接错误
            if retry < max_retries:
                wait_time = retry_delay * (2 ** retry)
                print(f"语音连接错误，{wait_time}秒后重试... ({retry+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return "无法连接到HomeAssistant语音接口，请检查网络连接和服务器地址"
                
        except RequestException as e:
            # 其他请求错误
            if retry < max_retries:
                wait_time = retry_delay * (2 ** retry)
                print(f"语音请求错误({str(e)})，{wait_time}秒后重试... ({retry+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return f"语音指令失败: {str(e)}"

        except Exception as e:
            return f"语音指令失败: {str(e)}"

# 验证API密钥（使用HomeAssistant Token）
def verify_api_key():
    """验证API密钥"""
    # 从请求头获取API密钥
    api_key = request.headers.get('Authorization')
    if api_key:
        # 移除Bearer前缀(如果有)
        api_key = api_key.replace('Bearer ', '')
    
    # 如果请求头中没有，则从查询参数获取
    if not api_key:
        api_key = request.args.get('api_key')
    
    # 验证密钥
    if not api_key:
        return False, "缺少API密钥"
    
    # 加载HomeAssistant配置
    ha_config = load_ha_config()
    
    # 检查密钥是否与HomeAssistant Token匹配
    if ha_config.get("token") == api_key:
        return True, None
    
    return False, "无效的API密钥"

# 保存对话历史
def save_chat_history(username, user_message, bot_name, bot_response):
    """保存对话历史到文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_dir = 'data/history'
    os.makedirs(history_dir, exist_ok=True)
    
    with open(f'{history_dir}/api_chat_history.txt', 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {username}: {user_message}\n")
        f.write(f"[{timestamp}] {bot_name}: {bot_response}\n\n")

def clean_user_message(message):
    """清理用户消息中的时间戳和前缀"""
    # 匹配并移除类似 "2025年05月12日星期一 12:41 陆小千: " 的前缀
    cleaned_message = re.sub(r'^\d{4}年\d{2}月\d{2}日星期[一二三四五六日]\s+\d{2}:\d{2}\s+[^:]+:\s*', '', message)
    return cleaned_message

# API路由
@app.route('/', methods=['GET'])
def index():
    """API服务根路径"""
    return "HomeAssistant OpenAI兼容API服务正在运行"

@app.route('/v1/chat/completions', methods=['POST'])
def openai_chat_completions():
    """OpenAI兼容的聊天API接口"""
    print("收到OpenAI格式的聊天请求")
    
    # 验证API密钥
    is_valid, error_msg = verify_api_key()
    if not is_valid:
        print(f"API密钥验证失败: {error_msg}")
        return jsonify({
            "error": {
                "message": error_msg,
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        }), 401
    
    try:
        data = request.get_json()
        
        if not data or 'messages' not in data:
            print("缺少必要参数messages")
            return jsonify({"error": {"message": "缺少必要参数messages", "type": "invalid_request_error"}}), 400
        
        # 提取用户消息
        user_message = ""
        username = "用户"
        
        # 从messages数组中获取最后一条用户消息
        for msg in reversed(data['messages']):
            if msg.get('role') == 'user':
                user_message = msg.get('content', '').strip()
                # 清理用户消息中的时间戳和前缀
                user_message = clean_user_message(user_message)
                break
        
        if user_message == "":
            print("未找到用户消息")
            return jsonify({"error": {"message": "未找到用户消息", "type": "invalid_request_error"}}), 400
        
        print(f"处理用户消息: {user_message}")
        
        # 检查是否请求流式响应
        stream_mode = data.get('stream', False)
        
        # 加载配置文件
        more_set_file = 'data/set/more_set.json'
        if os.path.exists(more_set_file):
            with open(more_set_file, 'r', encoding='utf-8') as f:
                more_config = json.load(f)
        else:
            more_config = {}
        
        # 语音指令关键词读取
        VOICE_KEYWORDS = more_config.get("HAAI关键词", [])
        for kw in VOICE_KEYWORDS:
            if kw in user_message:
                command = user_message.replace(kw, "", 1).strip()
                bot_response = send_ha_voice_command(command)
                
                # 记录对话历史
                save_chat_history(username, user_message, mate_name, bot_response)
                
                # 如果是流式响应模式
                if stream_mode:
                    return Response(generate_stream_response_with_text(bot_response), 
                                  mimetype='text/event-stream')
                
                # 生成OpenAI格式的响应
                response_data = {
                    "id": f"chatcmpl-{str(uuid.uuid4())[:10]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "homeassistant-ai",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": bot_response
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(user_message),
                        "completion_tokens": len(bot_response),
                        "total_tokens": len(user_message) + len(bot_response)
                    }
                }
                
                return jsonify(response_data)
                
        # 文本指令关键词读取
        for kw in more_config.get("HA文本指令关键词", []):
            if kw in user_message:
                command = user_message.replace(kw, "", 1).strip()
                bot_response = send_ha_command(command)
                
                # 记录对话历史
                save_chat_history(username, user_message, mate_name, bot_response)
                
                # 如果是流式响应模式
                if stream_mode:
                    return Response(generate_stream_response_with_text(bot_response), 
                                  mimetype='text/event-stream')
                
                # 生成OpenAI格式的响应
                response_data = {
                    "id": f"chatcmpl-{str(uuid.uuid4())[:10]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "homeassistant-ai",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": bot_response
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(user_message),
                        "completion_tokens": len(bot_response),
                        "total_tokens": len(user_message) + len(bot_response)
                    }
                }
                
                return jsonify(response_data)
        
        # 直接发送到HomeAssistant语音助手
        try:
            bot_response = send_ha_voice_command(user_message)
            
            # 记录对话历史
            save_chat_history(username, user_message, mate_name, bot_response)
            
            # 如果是流式响应模式
            if stream_mode:
                return Response(generate_stream_response_with_text(bot_response), 
                              mimetype='text/event-stream')
            
            # 生成OpenAI格式的响应
            response_data = {
                "id": f"chatcmpl-{str(uuid.uuid4())[:10]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "homeassistant-ai",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": bot_response
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message),
                    "completion_tokens": len(bot_response),
                    "total_tokens": len(user_message) + len(bot_response)
                }
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            print(f"API出错: {str(e)}")
            return jsonify({"error": {"message": str(e), "type": "server_error"}}), 500
    
    except Exception as e:
        print(f"处理请求时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": {"message": str(e), "type": "server_error"}}), 500

def generate_stream_response_with_text(predefined_text):
    """生成带有预定义文本的流式响应"""
    # 生成唯一ID
    response_id = f"chatcmpl-{str(uuid.uuid4())[:10]}"
    created_time = int(time.time())
    
    # 使用预定义的文本
    bot_response = predefined_text
    
    # 发送开始事件
    start_data = {
        'id': response_id,
        'object': 'chat.completion.chunk',
        'created': created_time,
        'model': 'homeassistant-ai',
        'choices': [{
            'index': 0,
            'delta': {
                'role': 'assistant'
            },
            'finish_reason': None
        }]
    }
    yield f"data: {json.dumps(start_data)}\n\n"
    
    # 分块发送内容部分（每次发送10个字符）
    for i in range(0, len(bot_response), 10):
        chunk = bot_response[i:i+10]
        content_data = {
            'id': response_id, 
            'object': 'chat.completion.chunk', 
            'created': created_time, 
            'model': 'homeassistant-ai', 
            'choices': [{
                'index': 0, 
                'delta': {'content': chunk}, 
                'finish_reason': None
            }]
        }
        yield f"data: {json.dumps(content_data)}\n\n"
        time.sleep(0.05)  # 添加延迟模拟打字效果
    
    # 发送结束事件部分
    end_data = {
        'id': response_id, 
        'object': 'chat.completion.chunk', 
        'created': created_time, 
        'model': 'homeassistant-ai', 
        'choices': [{
            'index': 0, 
            'delta': {}, 
            'finish_reason': 'stop'
        }]
    }
    yield f"data: {json.dumps(end_data)}\n\n"
    
    # 发送[DONE]标记，表示流结束
    yield "data: [DONE]\n\n"

# 全局变量用于控制服务器运行状态
server_running = True
server_thread = None

# 运行API服务器的函数
def run_api_server(host='0.0.0.0', port=5001, enable_cors=True, rate_limit=60):
    """运行API服务器"""
    global server_running, server_thread
    
    try:
        # 设置CORS
        if enable_cors:
            CORS(app)
        
        # 设置速率限制
        # 这里可以添加速率限制的代码
        print(f"速率限制设置为: {rate_limit}次/分钟")
        
        print(f"正在启动HomeAssistant OpenAI兼容API服务器，地址: {host}:{port}...")
        
        # 验证配置
        ha_config = load_ha_config()
        if not ha_config.get("url"):
            print("警告: 未配置HomeAssistant服务器地址，API服务器可能无法正常工作")
        
        if not ha_config.get("token"):
            print("警告: 未配置HomeAssistant访问令牌，API服务器可能无法正常工作")
            
        # 使用线程安全的方式运行Flask
        try:
            from werkzeug.serving import make_server
            server = make_server(host, port, app)
            server_running = True
            
            # 在循环中运行服务器，允许外部停止
            while server_running:
                server.handle_request()
        except Exception as e:
            print(f"API服务器运行出错: {e}")
            server_running = False
            
    except Exception as e:
        print(f"API服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        server_running = False
        return False
    
    return True

def stop_api_server():
    """停止API服务器"""
    global server_running
    server_running = False
    print("HomeAssistant OpenAI兼容API服务器已停止")

# 如果直接运行此文件
if __name__ == '__main__':
    print("正在启动HomeAssistant OpenAI兼容API服务器，端口5001...")
    ha_config = load_ha_config()
    if ha_config.get("token"):
        print(f"使用HomeAssistant Token作为API密钥: {ha_config.get('token')[:8]}...{ha_config.get('token')[-4:]}")
        try:
            app.run(host='0.0.0.0', port=5001, debug=True)
        except Exception as e:
            print(f"API服务器启动失败: {str(e)}")
            sys.exit(1)
    else:
        print("未找到有效的HomeAssistant Token，请先在more_set.json中配置")
        sys.exit(1)