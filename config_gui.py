import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import threading
import importlib

# 导入配置模块
from config import config, DEFAULT_CONFIG

class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIGPT配置工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"))
        except:
            pass
        
        # 创建选项卡
        self.tab_control = ttk.Notebook(root)
        
        # 基本设置选项卡
        self.tab_basic = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_basic, text="基本设置")
        
        # API设置选项卡
        self.tab_api = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_api, text="API设置")
        
        # HomeAssistant选项卡
        self.tab_ha = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_ha, text="HomeAssistant")
        
        # 高级设置选项卡
        self.tab_advanced = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_advanced, text="高级设置")
        
        # 关于选项卡
        self.tab_about = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_about, text="关于")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # 初始化各选项卡的内容
        self.init_basic_tab()
        self.init_api_tab()
        self.init_ha_tab()  # 新增HomeAssistant选项卡初始化
        self.init_advanced_tab()
        self.init_about_tab()
        
        # 底部按钮
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(self.button_frame, text="保存配置", command=self.save_config).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text="重置为默认", command=self.reset_to_default).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text="启动程序", command=self.start_program).pack(side="right", padx=5)
        
        # API服务器状态
        self.api_server_running = False
        self.api_server_thread = None
        
        # 加载配置
        self.load_config()
    
    def init_basic_tab(self):
        """初始化基本设置选项卡"""
        # 保持原有代码不变
        frame = ttk.LabelFrame(self.tab_basic, text="小米账号设置")
        frame.pack(fill="x", padx=10, pady=10)
        
        # 小米账号
        ttk.Label(frame, text="小米账号:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.mi_user_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.mi_user_var).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 小米密码
        ttk.Label(frame, text="小米密码:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.mi_pass_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.mi_pass_var, show="*").grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # 音箱型号
        frame2 = ttk.LabelFrame(self.tab_basic, text="设备设置")
        frame2.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(frame2, text="音箱型号:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.sound_type_var = tk.StringVar()
        
        # 从配置中获取所有支持的音箱型号
        hardware_types = list(config.get("hardware_command_dict", {}).keys())
        sound_type_combo = ttk.Combobox(frame2, textvariable=self.sound_type_var, values=hardware_types)
        sound_type_combo.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 添加默认设备选择功能
        ttk.Label(frame2, text="默认设备选择:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.default_device_var = tk.BooleanVar()
        ttk.Checkbutton(frame2, text="启动时跳过设备选择菜单", variable=self.default_device_var).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # 添加设备编号输入框 - 放在音箱型号下面
        ttk.Label(frame2, text="设备编号(如:1,2,3或all):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.device_numbers_var = tk.StringVar()
        ttk.Entry(frame2, textvariable=self.device_numbers_var).grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # 日志级别 - 调整行号，避免与设备编号重叠
        ttk.Label(frame2, text="日志级别:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.log_level_var = tk.IntVar()
        ttk.Radiobutton(frame2, text="静默模式", variable=self.log_level_var, value=0).grid(row=3, column=1, padx=10, pady=2, sticky="w")
        ttk.Radiobutton(frame2, text="基本信息", variable=self.log_level_var, value=1).grid(row=4, column=1, padx=10, pady=2, sticky="w")
        ttk.Radiobutton(frame2, text="详细信息", variable=self.log_level_var, value=2).grid(row=5, column=1, padx=10, pady=2, sticky="w")
        
        # AI触发关键词
        frame3 = ttk.LabelFrame(self.tab_basic, text="AI触发设置")
        frame3.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(frame3, text="AI触发关键词(逗号分隔):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.ai_keywords_var = tk.StringVar()
        ttk.Entry(frame3, textvariable=self.ai_keywords_var).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 是否开启AI回答
        self.switch_var = tk.BooleanVar()
        ttk.Checkbutton(frame3, text="开启AI回答", variable=self.switch_var).grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # 设置列的权重
        frame.columnconfigure(1, weight=1)
        frame2.columnconfigure(1, weight=1)
        frame3.columnconfigure(1, weight=1)
    
    def init_api_tab(self):
        """初始化API设置选项卡"""
        # 保持原有代码不变
        frame = ttk.LabelFrame(self.tab_api, text="API设置")
        frame.pack(fill="x", padx=10, pady=10)
        
        # API类型
        ttk.Label(frame, text="API类型:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.api_type_var = tk.StringVar()
        api_types = ["openai", "bigmodel", "custom"]
        api_type_names = {
            "openai": "OpenAI (官方)",
            "bigmodel": "智谱GLM (官方)",
            "custom": "兼容接口 (通义/火山/文心等)"
        }
        self.api_type_display_map = {v: k for k, v in api_type_names.items()}
        api_type_combo = ttk.Combobox(frame, textvariable=self.api_type_var, values=[api_type_names[t] for t in api_types])
        api_type_combo.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        api_type_combo.bind("<<ComboboxSelected>>", self.on_api_type_change)
        
        # API密钥
        ttk.Label(frame, text="API密钥:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.api_key_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.api_key_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # API基础URL
        ttk.Label(frame, text="API基础URL:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.api_base_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.api_base_var).grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # 模型名称
        ttk.Label(frame, text="模型名称:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.model_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.model_name_var).grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # 预设选择
        frame2 = ttk.LabelFrame(self.tab_api, text="预设选择")
        frame2.pack(fill="x", padx=10, pady=10)
        
        # 获取所有预设并添加中文名称
        presets = list(config.get("api_presets", {}).keys())
        preset_names = {
            "openai": "OpenAI (GPT-3.5)",
            "bigmodel": "智谱 (GLM-4-Flash)",
            "deepseek": "DeepSeek (深度求索)",
            "moonshot": "Moonshot (月之暗面)",
            "qwen": "通义千问 (Qwen-Turbo)",
            "claude": "Claude (Anthropic)",
            "volcengine": "豆包 (火山引擎)",
            "siliconflow": "硅基流动 (Siliconflow)",
            "qianfan": "百度千帆 (文心一言)"
        }
        # 为预设添加未知类型的默认显示
        self.preset_display_map = {}
        preset_displays = []
        for preset in presets:
            if preset in preset_names:
                display_name = preset_names[preset]
                self.preset_display_map[display_name] = preset
                preset_displays.append(display_name)
            else:
                self.preset_display_map[preset] = preset
                preset_displays.append(preset)
        
        ttk.Label(frame2, text="选择预设:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(frame2, textvariable=self.preset_var, values=preset_displays)
        preset_combo.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        preset_combo.bind("<<ComboboxSelected>>", self.on_preset_change)
        
        # 系统提示词
        frame3 = ttk.LabelFrame(self.tab_api, text="系统提示词")
        frame3.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.prompt_text = scrolledtext.ScrolledText(frame3, wrap=tk.WORD, height=5)
        self.prompt_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 设置列的权重
        frame.columnconfigure(1, weight=1)
        frame2.columnconfigure(1, weight=1)
    
    def init_ha_tab(self):
        """初始化HomeAssistant选项卡"""
        # HomeAssistant服务器设置
        frame1 = ttk.LabelFrame(self.tab_ha, text="HomeAssistant服务器设置")
        frame1.pack(fill="x", padx=10, pady=10)
        
        # HomeAssistant服务器IP
        ttk.Label(frame1, text="服务器地址:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.ha_url_var = tk.StringVar()
        ttk.Entry(frame1, textvariable=self.ha_url_var).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(frame1, text="例如: http://192.168.1.100:8123").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        
        # HomeAssistant Token
        ttk.Label(frame1, text="Token:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.ha_token_var = tk.StringVar()
        ttk.Entry(frame1, textvariable=self.ha_token_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(frame1, text="长期访问令牌").grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        # 文本指令实体ID
        ttk.Label(frame1, text="文本指令实体ID:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.ha_text_entity_var = tk.StringVar()
        ttk.Entry(frame1, textvariable=self.ha_text_entity_var).grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # 语音API实体ID
        ttk.Label(frame1, text="语音API实体ID:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.ha_voice_agent_var = tk.StringVar()
        ttk.Entry(frame1, textvariable=self.ha_voice_agent_var).grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # HAAI关键词
        ttk.Label(frame1, text="语音指令关键词(逗号分隔):").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.ha_ai_keywords_var = tk.StringVar()
        ttk.Entry(frame1, textvariable=self.ha_ai_keywords_var).grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(frame1, text="例如: 小周,小洲,小舟").grid(row=4, column=2, padx=10, pady=5, sticky="w")
        
        # HA文本指令关键词
        ttk.Label(frame1, text="文本指令关键词(逗号分隔):").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.ha_text_keywords_var = tk.StringVar()
        ttk.Entry(frame1, textvariable=self.ha_text_keywords_var).grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(frame1, text="例如: 小爱").grid(row=5, column=2, padx=10, pady=5, sticky="w")
        
        # API服务器设置
        frame2 = ttk.LabelFrame(self.tab_ha, text="API服务器设置")
        frame2.pack(fill="x", padx=10, pady=10)
        
        # API服务器启用状态
        ttk.Label(frame2, text="API服务器:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.api_server_enabled_var = tk.StringVar()
        ttk.Radiobutton(frame2, text="自动启动", variable=self.api_server_enabled_var, value="开启").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        ttk.Radiobutton(frame2, text="禁用", variable=self.api_server_enabled_var, value="关闭").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        ttk.Label(frame2, text="(启动MIGPT时自动启动API服务器)").grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # API服务器端口
        ttk.Label(frame2, text="端口:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.api_server_port_var = tk.StringVar()
        ttk.Entry(frame2, textvariable=self.api_server_port_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(frame2, text="默认: 5001").grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        # API服务器主机
        ttk.Label(frame2, text="主机:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.api_server_host_var = tk.StringVar()
        ttk.Entry(frame2, textvariable=self.api_server_host_var).grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(frame2, text="默认: 0.0.0.0 (所有网络接口)").grid(row=2, column=2, padx=10, pady=5, sticky="w")
        
        # CORS设置
        ttk.Label(frame2, text="CORS支持:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.api_cors_enabled_var = tk.StringVar()
        ttk.Radiobutton(frame2, text="开启", variable=self.api_cors_enabled_var, value="开启").grid(row=3, column=1, padx=10, pady=5, sticky="w")
        ttk.Radiobutton(frame2, text="关闭", variable=self.api_cors_enabled_var, value="关闭").grid(row=3, column=2, padx=10, pady=5, sticky="w")
        
        # 速率限制
        ttk.Label(frame2, text="速率限制(每分钟请求数):").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.api_rate_limit_var = tk.StringVar()
        ttk.Entry(frame2, textvariable=self.api_rate_limit_var).grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(frame2, text="默认: 60").grid(row=4, column=2, padx=10, pady=5, sticky="w")
        
        # API服务器控制按钮
        button_frame = ttk.Frame(frame2)
        button_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=10)
        
        self.start_api_button = ttk.Button(button_frame, text="启动API服务器", command=self.start_api_server)
        self.start_api_button.pack(side="left", padx=5)
        
        self.stop_api_button = ttk.Button(button_frame, text="停止API服务器", command=self.stop_api_server, state="disabled")
        self.stop_api_button.pack(side="left", padx=5)
        
        # 状态标签
        self.api_status_var = tk.StringVar(value="API服务器状态: 未运行")
        ttk.Label(button_frame, textvariable=self.api_status_var).pack(side="left", padx=20)
        
        # 自动启动说明
        note_frame = ttk.Frame(frame2)
        note_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=5)
        ttk.Label(note_frame, text="注意: 设置为\"自动启动\"后，启动MIGPT程序时将自动启动API服务器，无需手动点击启动按钮。").pack(anchor="w")
        
        # 设置列的权重
        frame1.columnconfigure(1, weight=1)
        frame2.columnconfigure(1, weight=1)
    
    def init_advanced_tab(self):
        """初始化高级设置选项卡"""
        # 保持原有代码不变
        frame = ttk.LabelFrame(self.tab_advanced, text="高级设置")
        frame.pack(fill="x", padx=10, pady=10)
        
        # 添加一个文本编辑器，用于直接编辑JSON配置
        ttk.Label(frame, text="直接编辑配置文件 (JSON格式):").pack(anchor="w", padx=10, pady=5)
        
        self.config_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=20)
        self.config_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 添加按钮用于刷新和应用JSON
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(button_frame, text="刷新JSON", command=self.refresh_json).pack(side="left", padx=5)
        ttk.Button(button_frame, text="应用JSON", command=self.apply_json).pack(side="left", padx=5)
    
    def init_about_tab(self):
        """初始化关于选项卡"""
        # 保持原有代码不变
        frame = ttk.Frame(self.tab_about)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        about_text = """
        MIGPT-易 - 小爱同学与ChatGPT集成的智能助手
        基于API流式对话的低延迟版MIGPT
        
        本项目利用了OpenAI官方API的原生流式传输对话方式，无需等待，即刻对话！
        
        使用方法：
        1. 在基本设置中填写小米账号和密码
        2. 在API设置中配置API信息
        3. 在HomeAssistant选项卡中配置HomeAssistant服务器和API服务器
        4. 点击保存配置
        5. 点击启动程序
        
        使用技巧：
        1. 运行过程中，可用"打开/关闭高级对话"控制是否打开ChatGPT
        2. 当ChatGPT正在回答问题时，可用"闭嘴"或"停止"终止回答
        3. 可随时提问新的问题打断ChatGPT的回答
        4. 可以通过HomeAssistant选项卡启动API服务器，使用OpenAI兼容接口访问HomeAssistant
        
        项目原作者: Afool4U
        项目优化者: AIOTVR (周友康)
        
        QQ: 3228675807
        QQ交流群: 1034819300
        哔哩哔哩: AIOTVR
        
        GitHub: https://github.com/zhouyoukang/MIGPT-easy
        
        最后更新: 2025年5月
        """
        
        text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert(tk.END, about_text)
        text_widget.config(state="disabled")
    
    def load_config(self):
        """加载配置到界面"""
        # 基本设置 - 保持原有代码不变
        self.mi_user_var.set(config.get("mi_user", ""))
        self.mi_pass_var.set(config.get("mi_pass", ""))
        self.sound_type_var.set(config.get("sound_type", "LX06"))
        self.log_level_var.set(config.get("log_level", 1))
        self.ai_keywords_var.set(", ".join(config.get("ai_keywords", ["请", "帮我", "问一下", "AI"])))
        self.switch_var.set(config.get("switch", True))
        # 添加默认设备选择加载
        self.default_device_var.set(config.get("skip_device_selection", False))
        self.device_numbers_var.set(config.get("device_numbers", ""))
        
        # API设置 - 更新为添加中文名称后的代码
        api_type = config.get("api_type", "custom")
        api_type_names = {
            "openai": "OpenAI (官方)",
            "bigmodel": "智谱GLM (官方)",
            "custom": "兼容接口 (通义/火山/文心等)"
        }
        self.api_type_var.set(api_type_names.get(api_type, api_type))
        self.api_key_var.set(config.get("api_key", ""))
        self.api_base_var.set(config.get("api_base", ""))
        self.model_name_var.set(config.get("model_name", ""))
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(tk.END, config.get("prompt", ""))
        
        # 预设选择
        preset_names = {
            "openai": "OpenAI (GPT-3.5)",
            "bigmodel": "智谱 (GLM-4-Flash)",
            "deepseek": "DeepSeek (深度求索)",
            "moonshot": "Moonshot (月之暗面)",
            "qwen": "通义千问 (Qwen-Turbo)",
            "claude": "Claude (Anthropic)",
            "volcengine": "豆包 (火山引擎)",
            "siliconflow": "硅基流动 (Siliconflow)",
            "qianfan": "百度千帆 (文心一言)"
        }
        # 设置当前API类型对应的预设
        if api_type in preset_names:
            self.preset_var.set(preset_names[api_type])
        
        # 加载HomeAssistant配置
        self.load_ha_config()
        
        # 高级设置 - JSON编辑器
        self.refresh_json()
    
    def load_ha_config(self):
        """加载HomeAssistant配置"""
        try:
            # 从config.json加载HomeAssistant配置
            ha_config = config.get("homeassistant", {})
            
            # 设置HomeAssistant服务器配置
            self.ha_url_var.set(ha_config.get("url", ""))
            self.ha_token_var.set(ha_config.get("token", ""))
            self.ha_text_entity_var.set(ha_config.get("text_entity_id", ""))
            self.ha_voice_agent_var.set(ha_config.get("voice_agent_id", ""))
            
            # 设置HAAI关键词
            ha_ai_keywords = ha_config.get("ai_keywords", [])
            self.ha_ai_keywords_var.set(", ".join(ha_ai_keywords))
            
            # 设置HA文本指令关键词
            ha_text_keywords = ha_config.get("text_keywords", [])
            self.ha_text_keywords_var.set(", ".join(ha_text_keywords))
            
            # 设置API服务器配置
            api_server = ha_config.get("api_server", {})
            self.api_server_enabled_var.set(api_server.get("enabled", "关闭"))
            self.api_server_port_var.set(api_server.get("port", "5001"))
            self.api_server_host_var.set(api_server.get("host", "0.0.0.0"))
            self.api_cors_enabled_var.set(api_server.get("cors_enabled", "开启"))
            self.api_rate_limit_var.set(api_server.get("rate_limit", "60"))
            
            # 尝试从more_set.json加载配置（如果config.json中没有配置）
            if not ha_config:
                more_set_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'set', 'more_set.json')
                if os.path.exists(more_set_file):
                    with open(more_set_file, 'r', encoding='utf-8') as f:
                        more_config = json.load(f)
                        
                        # 设置HomeAssistant服务器配置
                        self.ha_url_var.set(more_config.get("HomeAssistant服务器IP", ""))
                        self.ha_token_var.set(more_config.get("HomeAssistant Token", ""))
                        self.ha_text_entity_var.set(more_config.get("文本指令实体ID", ""))
                        self.ha_voice_agent_var.set(more_config.get("语音API实体ID", ""))
                        
                        # 设置HAAI关键词
                        ha_ai_keywords = more_config.get("HAAI关键词", [])
                        self.ha_ai_keywords_var.set(", ".join(ha_ai_keywords))
                        
                        # 设置HA文本指令关键词
                        ha_text_keywords = more_config.get("HA文本指令关键词", [])
                        self.ha_text_keywords_var.set(", ".join(ha_text_keywords))
                        
                        # 设置API服务器配置
                        self.api_server_enabled_var.set(more_config.get("api_server_enabled", "关闭"))
                        self.api_server_port_var.set(more_config.get("api_server_port", "5001"))
                        self.api_server_host_var.set(more_config.get("api_server_host", "0.0.0.0"))
                        self.api_cors_enabled_var.set(more_config.get("api_cors_enabled", "开启"))
                        self.api_rate_limit_var.set(more_config.get("api_rate_limit", "60"))
        except Exception as e:
            print(f"加载HomeAssistant配置出错: {e}")
    
    def save_ha_config(self):
        """保存HomeAssistant配置"""
        try:
            # 创建HomeAssistant配置字典
            ha_config = {
                "url": self.ha_url_var.get(),
                "token": self.ha_token_var.get(),
                "text_entity_id": self.ha_text_entity_var.get(),
                "voice_agent_id": self.ha_voice_agent_var.get(),
                "ai_keywords": [kw.strip() for kw in self.ha_ai_keywords_var.get().split(",") if kw.strip()],
                "text_keywords": [kw.strip() for kw in self.ha_text_keywords_var.get().split(",") if kw.strip()],
                "api_server": {
                    "enabled": self.api_server_enabled_var.get(),
                    "port": self.api_server_port_var.get(),
                    "host": self.api_server_host_var.get(),
                    "cors_enabled": self.api_cors_enabled_var.get(),
                    "rate_limit": self.api_rate_limit_var.get()
                }
            }
            
            # 保存到config.json
            config.set("homeassistant", ha_config)
            
            # 同时保存到more_set.json文件（兼容性考虑）
            more_set_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'set', 'more_set.json')
            
            # 先读取现有配置
            if os.path.exists(more_set_file):
                with open(more_set_file, 'r', encoding='utf-8') as f:
                    more_config = json.load(f)
            else:
                more_config = {}
            
            # 更新HomeAssistant服务器设置
            more_config["HomeAssistant服务器IP"] = self.ha_url_var.get()
            more_config["HomeAssistant Token"] = self.ha_token_var.get()
            more_config["文本指令实体ID"] = self.ha_text_entity_var.get()
            more_config["语音API实体ID"] = self.ha_voice_agent_var.get()
            
            # 更新HAAI关键词
            more_config["HAAI关键词"] = ha_config["ai_keywords"]
            
            # 更新HA文本指令关键词
            more_config["HA文本指令关键词"] = ha_config["text_keywords"]
            
            # 更新API服务器设置
            more_config["api_server_enabled"] = self.api_server_enabled_var.get()
            more_config["api_server_port"] = self.api_server_port_var.get()
            more_config["api_server_host"] = self.api_server_host_var.get()
            more_config["api_cors_enabled"] = self.api_cors_enabled_var.get()
            more_config["api_rate_limit"] = self.api_rate_limit_var.get()
            
            # 保存配置
            with open(more_set_file, 'w', encoding='utf-8') as f:
                json.dump(more_config, f, ensure_ascii=False, indent=4)
                
            return True
        except Exception as e:
            print(f"保存HomeAssistant配置出错: {e}")
            return False
    
    def save_config(self):
        """保存配置"""
        try:
            # 基本设置
            config.set("mi_user", self.mi_user_var.get())
            config.set("mi_pass", self.mi_pass_var.get())
            config.set("sound_type", self.sound_type_var.get())
            config.set("log_level", self.log_level_var.get())
            # 添加默认设备选择保存
            config.set("skip_device_selection", self.default_device_var.get())
            config.set("device_numbers", self.device_numbers_var.get())
            
            # 处理AI关键词列表
            keywords = [kw.strip() for kw in self.ai_keywords_var.get().split(",") if kw.strip()]
            config.set("ai_keywords", keywords)
            
            config.set("switch", self.switch_var.get())
            
            # API设置 - 更新为添加中文名称后的代码
            api_type_display = self.api_type_var.get()
            api_type = self.api_type_display_map.get(api_type_display, api_type_display)
            config.set("api_type", api_type)
            config.set("api_key", self.api_key_var.get())
            config.set("api_base", self.api_base_var.get())
            config.set("model_name", self.model_name_var.get())
            config.set("prompt", self.prompt_text.get(1.0, tk.END).strip())
            
            # 保存HomeAssistant配置
            self.save_ha_config()
            
            # 保存配置
            config.save_config()
            
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置时出错: {e}")
    
    def reset_to_default(self):
        """重置为默认配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗？这将覆盖当前的所有设置。"):
            try:
                # 重置配置
                config.config = DEFAULT_CONFIG.copy()
                config.save_config()
                
                # 重新加载配置到界面
                self.load_config()
                
                messagebox.showinfo("成功", "已重置为默认配置")
            except Exception as e:
                messagebox.showerror("错误", f"重置配置时出错: {e}")
    
    def start_program(self):
        """启动程序"""
        try:
            # 先保存配置
            self.save_config()
            
            # 关闭GUI
            self.root.destroy()
            
            # 启动主程序
            os.system("start cmd /k python -m MIGPT")
        except Exception as e:
            messagebox.showerror("错误", f"启动程序时出错: {e}")
    
    def refresh_json(self):
        """刷新JSON编辑器"""
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(tk.END, json.dumps(config.config, indent=4, ensure_ascii=False))
    
    def apply_json(self):
        """应用JSON编辑器中的配置"""
        try:
            # 获取JSON文本
            json_text = self.config_text.get(1.0, tk.END)
            
            # 解析JSON
            new_config = json.loads(json_text)
            
            # 更新配置
            config.config = new_config
            config.save_config()
            
            # 重新加载配置到界面
            self.load_config()
            
            messagebox.showinfo("成功", "JSON配置已应用")
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"JSON格式错误: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"应用JSON配置时出错: {e}")
    
    def on_api_type_change(self, event=None):
        """API类型变更时的处理"""
        api_type_display = self.api_type_var.get()
        api_type = self.api_type_display_map.get(api_type_display, api_type_display)
        api_presets = config.get("api_presets", {})
        
        if api_type in api_presets:
            preset = api_presets[api_type]
            self.api_base_var.set(preset.get("api_base", ""))
            self.model_name_var.set(preset.get("model", ""))
    
    def on_preset_change(self, event=None):
        """预设变更时的处理"""
        preset_display = self.preset_var.get()
        preset_name = self.preset_display_map.get(preset_display, preset_display)
        api_presets = config.get("api_presets", {})
        
        if preset_name in api_presets:
            preset = api_presets[preset_name]
            api_type = preset.get("api_type", "custom")
            api_type_names = {
                "openai": "OpenAI (官方)",
                "bigmodel": "智谱GLM (官方)",
                "custom": "兼容接口 (通义/火山/文心等)"
            }
            self.api_type_var.set(api_type_names.get(api_type, api_type))
            self.api_base_var.set(preset.get("api_base", ""))
            self.model_name_var.set(preset.get("model", ""))
    
    def start_api_server(self):
        """启动API服务器"""
        if self.api_server_running:
            messagebox.showinfo("提示", "API服务器已经在运行中")
            return
        
        # 先保存配置
        if not self.save_ha_config():
            messagebox.showerror("错误", "保存配置失败，无法启动API服务器")
            return
        
        try:
            # 导入api_server模块
            api_server = importlib.import_module("api_server")
            
            # 获取配置
            ha_config = config.get("homeassistant", {})
            api_server_config = ha_config.get("api_server", {})
            
            host = api_server_config.get("host", "0.0.0.0")
            port = int(api_server_config.get("port", 5001))
            enable_cors = api_server_config.get("cors_enabled", "开启") == "开启"
            rate_limit = int(api_server_config.get("rate_limit", 60))
            
            # 启动API服务器
            self.api_server_thread = threading.Thread(
                target=api_server.run_api_server,
                args=(host, port, enable_cors, rate_limit),
                daemon=True
            )
            self.api_server_thread.start()
            
            # 更新状态
            self.api_server_running = True
            self.api_status_var.set(f"API服务器状态: 运行中 (http://{host}:{port})")
            self.start_api_button.config(state="disabled")
            self.stop_api_button.config(state="normal")
            
            messagebox.showinfo("成功", f"API服务器已启动，地址: http://{host}:{port}")
        except Exception as e:
            messagebox.showerror("错误", f"启动API服务器失败: {e}")
    
    def stop_api_server(self):
        """停止API服务器"""
        # 实现停止API服务器的逻辑
        if not self.api_server_running:
            messagebox.showinfo("提示", "API服务器未运行")
            return
            
        try:
            # 导入api_server模块
            api_server = importlib.import_module("api_server")
            # 调用停止函数
            api_server.stop_api_server()
            
            # 更新状态
            self.api_server_running = False
            self.api_status_var.set("API服务器状态: 未运行")
            self.start_api_button.config(state="normal")
            self.stop_api_button.config(state="disabled")
            
            messagebox.showinfo("成功", "API服务器已停止")
        except Exception as e:
            messagebox.showerror("错误", f"停止API服务器失败: {e}")

# 主函数
def main():
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()