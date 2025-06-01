#!/usr/bin/env python3
"""
MI-GPT - 小爱同学与ChatGPT集成的智能助手
基于API流式对话的低延迟版MIGPT

作者: AIOTVR (周友康)
版本: v1.0.0
最后更新: 2025年5月
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
import threading
import importlib
import traceback

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'migpt.log'), encoding='utf-8')
    ]
)

logger = logging.getLogger("MIGPT")

# 确保能够导入mi_gpt包中的模块
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 延迟导入，避免在未安装依赖时报错
try:
    from config import config
except ImportError:
    logger.error("无法导入配置模块，请确保已安装所有依赖")
    logger.error("可以运行 'pip install -r requirements.txt' 安装依赖")
    sys.exit(1)

def start_api_server_if_enabled():
    """
    如果配置中启用了API服务器，则启动它
    
    返回:
        bool: 是否成功启动API服务器
    """
    try:
        # 从配置中获取API服务器设置
        ha_config = config.get("homeassistant", {})
        api_server_config = ha_config.get("api_server", {})
        
        # 检查API服务器是否启用
        if api_server_config.get("enabled", "关闭") == "开启":
            logger.info("正在启动API服务器...")
            
            # 导入api_server模块
            try:
                api_server = importlib.import_module("api_server")
            except ImportError:
                logger.error("无法导入api_server模块，请确保文件存在")
                return False
            
            # 获取配置参数
            host = api_server_config.get("host", "0.0.0.0")
            port = int(api_server_config.get("port", 5001))
            enable_cors = api_server_config.get("cors_enabled", "开启") == "开启"
            rate_limit = int(api_server_config.get("rate_limit", 60))
            
            # 在后台线程中启动API服务器
            thread = threading.Thread(
                target=api_server.run_api_server,
                args=(host, port, enable_cors, rate_limit),
                daemon=True
            )
            thread.start()
            logger.info(f"API服务器已启动，地址: http://{host}:{port}")
            return True
    except Exception as e:
        logger.error(f"启动API服务器时出错: {e}")
        logger.debug(traceback.format_exc())
    
    return False

def check_dependencies():
    """
    检查必要的依赖是否已安装
    
    返回:
        bool: 是否所有依赖都已安装
    """
    required_modules = [
        'aiohttp', 'requests', 'tiktoken', 'flask', 'flask_cors'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"缺少以下依赖: {', '.join(missing_modules)}")
        logger.error("请运行 'pip install -r requirements.txt' 安装所有依赖")
        return False
    
    return True

def check_config_files():
    """
    检查必要的配置文件是否存在
    
    返回:
        bool: 是否所有必要的配置文件都存在
    """
    config_path = os.path.join(current_dir, "config.json")
    
    if not os.path.exists(config_path):
        logger.warning(f"未找到配置文件: {config_path}")
        logger.warning("将使用默认配置")
        
        # 检查是否有GUI模块可用
        try:
            importlib.import_module("config_gui")
            logger.info("检测到GUI配置模块，建议运行 'python config_gui.py' 进行配置")
        except ImportError:
            logger.warning("未检测到GUI配置模块，请手动创建配置文件")
    
    return True

def create_data_directories():
    """创建必要的数据目录"""
    directories = [
        os.path.join(current_dir, "data"),
        os.path.join(current_dir, "data", "history"),
        os.path.join(current_dir, "data", "set"),
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logger.debug(f"创建目录: {directory}")
            except Exception as e:
                logger.warning(f"创建目录 {directory} 失败: {e}")

async def start_mi_gpt():
    """启动MI-GPT应用"""
    try:
        # 导入MI-GPT模块
        from MIGPT import main as migpt_main
        
        # 运行MI-GPT主函数
        await migpt_main()
    except ImportError:
        logger.error("无法导入MIGPT模块，请确保文件存在")
        return 1
    except Exception as e:
        logger.error(f"运行MIGPT时出错: {e}")
        logger.debug(traceback.format_exc())
        return 1
    
    return 0

def main():
    """主函数，启动MI-GPT应用"""
    logger.info("正在启动MI-GPT智能助手...")
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 检查配置文件
    check_config_files()
    
    # 创建必要的数据目录
    create_data_directories()
    
    # 启动API服务器（如果配置中启用）
    start_api_server_if_enabled()
    
    try:
        # 启动应用
        return asyncio.run(start_mi_gpt())
    except KeyboardInterrupt:
        logger.info("\n程序已被用户中断")
        return 0
    except Exception as e:
        logger.error(f"运行时出错: {e}")
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())