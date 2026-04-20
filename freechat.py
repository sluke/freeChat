#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FreeChat: A powerful, single-file AI chat CLI for your VPS.

Author: AI Assistant (Generated for User Task)
Version: 2.3.0 (Stable)
License: GPL-3.0
"""

import sys

# --- Proactive Python Version Check ---
MIN_PYTHON_VERSION = (3, 7)
if sys.version_info < MIN_PYTHON_VERSION:
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    required_version = f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"
    RED, YELLOW, BOLD, ENDC = '\033[91m', '\033[93m', '\033[1m', '\033[0m'
    error_message = (f"{RED}{BOLD}ERROR: INCOMPATIBLE PYTHON VERSION{ENDC}\n\n"
                     f"FreeChat requires {BOLD}Python {required_version} or newer{ENDC}.\n"
                     f"You are currently using Python {current_version}.\n\n"
                     f"{YELLOW}Please upgrade your Python version to resolve this.{ENDC}\n")
    print(error_message, file=sys.stderr)
    sys.exit(1)
# --- End of Python Version Check ---

# --- Bootstrap: Intelligent & Robust Dependency Installer ---
import subprocess, importlib.util, os, time

def bootstrap():
    """Checks and installs dependencies before the main application runs."""
    # Add urllib3<2.0 to avoid LibreSSL compatibility issues on macOS
    required = {"prompt_toolkit": "prompt_toolkit>=3.0.48", "rich": "rich>=13.7.1", "httpx": "httpx[http2]>=0.27.2", "tiktoken": "tiktoken>=0.7.0", "urllib3": "urllib3<2.0", "tomli_w": "tomli_w>=1.0.0"}
    if sys.version_info < (3, 11): required["tomli"] = "tomli>=2.0"
    missing = [pkg for name, pkg in required.items() if not importlib.util.find_spec(name)]
    if not missing: return
    print(f"Welcome to FreeChat! Missing libraries: {', '.join(missing)}")
    try:
        if input("Install them now? [Y/n]: ").lower().strip() not in ["", "y", "yes"]: print("Installation cancelled."); sys.exit(1)
        # Try to upgrade pip, but don't fail if system pip can't be upgraded (e.g., Debian/Ubuntu)
        try:
            print("\nUpgrading pip...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "--break-system-packages", "pip"], check=True)
        except subprocess.CalledProcessError:
            print("[Warning] Could not upgrade pip (system-managed), continuing with existing pip...")
        print(f"Installing {len(missing)} packages..."); subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + missing, check=True)
        print("\n[OK] Dependencies installed. Restarting in 2s..."); time.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except (subprocess.CalledProcessError, KeyboardInterrupt, EOFError) as e: print(f"\n[ERROR] Installation failed: {e}", file=sys.stderr); sys.exit(1)

bootstrap()
# --- End of Bootstrap ---

# --- Main Application Imports ---
import asyncio, json, re, logging, math, operator, ast, hashlib, hmac, secrets, sqlite3, uuid, threading
from collections import OrderedDict
from pathlib import Path
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
if sys.version_info >= (3, 11): import tomllib
else: import tomli as tomllib
import tomli_w
import httpx, tiktoken
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.errors import MarkupError
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings

class FreeChatApp:
    # Log level mapping as class constant
    LOG_LEVEL_MAP = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    def __init__(self):
        self.console = Console()
        
        script_path = Path(__file__).resolve().parent
        portable_config_dir = script_path / "freechat_config"
        xdg_config_dir = Path.home() / ".config" / "freechat"
        
        if portable_config_dir.is_dir():
            self.config_dir = portable_config_dir
            self.console.print(f"[bold yellow]! Portable config directory detected. Using '{self.config_dir}'[/bold yellow]")
        else:
            self.config_dir = xdg_config_dir

        self.config_path = self.config_dir / "config.toml"
        self.prompts_path = self.config_dir / "prompts.toml"
        self.history_path = self.config_dir / "history.txt"
        self.sessions_dir = self.config_dir / "sessions"

        self._setup_config()
        self.config = self._load_config(self.config_path)
        self.prompts = self._load_config(self.prompts_path)
        
        self.default_prompt_name = self.config.get("general", {}).get("default_prompt", "default")
        self.active_prompt_name: str = ""
        self.active_prompt_content: str = ""
        
        # [V2.2.1] Default model set to the API-compatible ID.
        self.current_model: str = self.config.get("general", {}).get("default_model", "openrouter/free")
        self.session_messages: List[Dict[str, Any]] = []
        self.MAX_HISTORY_MESSAGES: int = 50  # Maximum number of messages to keep
        self.session_cost: float = 0.0
        self.session_name: Optional[str] = None
        self.available_models: Dict[str, List[str]] = {}
        self.models_last_fetched: float = 0
        self.MODELS_CACHE_TTL: int = 3600  # 1 hour cache
        self.provider_factory = ProviderFactory(self.config)
        try: 
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            self.tokenizer = None
            self.console.print(f"[yellow]Warning:[/] `tiktoken` not found or failed to load: {e}. Token counts will be approximate.")
        self._token_cache: OrderedDict[str, int] = OrderedDict()  # LRU cache
        self.commands: Dict[str, Callable] = {
            "/help": self._display_help, "/model": self._handle_model_command,
            "/prompt": self._handle_prompt_command,
            "/session": self._handle_session_command, "/export": self._handle_export_command,
            "/file": self._handle_file_command,
            "/language": self._handle_language_command,
            "/clear": lambda args: self.console.clear(), "/exit": self._exit_app,
        }
        # Get log file path from config or use default
        log_file_name = self.config.get("general", {}).get("log_file", "freechat.log")
        self.log_file = self.config_dir / log_file_name
        self._setup_logging()
        
        bindings = KeyBindings();
        @bindings.add("c-j")
        @bindings.add("c-m")
        def _(event): event.current_buffer.validate_and_handle()
        
        @bindings.add("c-r")
        def _(event):
            """Start reverse history search."""
            from prompt_toolkit.key_binding.bindings.search import start_reverse_search
            start_reverse_search(event.current_buffer)
        
        @bindings.add("c-c")
        def _(event):
            """Cancel input."""
            event.current_buffer.reset()
        
        @bindings.add("c-a")
        def _(event):
            """Move cursor to the beginning of the line."""
            event.current_buffer.cursor_position = 0
        
        @bindings.add("c-e")
        def _(event):
            """Move cursor to the end of the line."""
            event.current_buffer.cursor_position = len(event.current_buffer.text)
        
        @bindings.add("c-k")
        def _(event):
            """Delete from cursor to the end of the line."""
            event.current_buffer.text = event.current_buffer.text[:event.current_buffer.cursor_position]
        
        self.prompt_session = PromptSession(
            history=FileHistory(str(self.history_path)), 
            multiline=True, 
            auto_suggest=AutoSuggestFromHistory(), 
            key_bindings=bindings,
            complete_while_typing=True,
            enable_history_search=True
        )
        self.style = Style.from_dict({'bottom-toolbar': '#ffffff bg:#333333'})
        self._completer = None
        self._completer_last_updated = 0
        self._export_console = None
        # Load language from config or use default
        self.language = self.config.get("general", {}).get("language", "en")
        self.translations = self._load_translations()

        # Initialize tool system
        self.tool_registry = ToolRegistry()
        self._register_builtin_tools()
        self._load_custom_tools_from_config()

        # Initialize skill system
        self.skills_dir = self.config_dir / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.skill_registry = SkillRegistry(self.skills_dir, self.tool_registry)

        # Initialize memory system
        self.memory_dir = self.config_dir / "memories"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Detect git branch for branch-specific memories
        branch_manager = BranchMemoryManager(MemoryManager(self.memory_dir / "default.db"))
        current_branch = branch_manager.get_current_branch()

        # Initialize memory manager with detected branch
        memory_db_path = self.memory_dir / "memories.db"
        self.memory_manager = MemoryManager(memory_db_path, current_branch)

        self._apply_prompt(self.default_prompt_name, is_startup=True)

    def _setup_logging(self):
        """Set up logging for security audit and error tracking."""
        try:
            # Get log level from config or use default INFO
            log_level_str = self.config.get('general', {}).get('log_level', 'INFO').upper()
            log_level = self.LOG_LEVEL_MAP.get(log_level_str, logging.INFO)
            
            # Create a logger with file rotation
            logger = logging.getLogger('FreeChat')
            logger.setLevel(log_level)
            
            # Only add handler if none exist
            if not logger.handlers:
                # Add rotating file handler
                from logging.handlers import RotatingFileHandler
                handler = RotatingFileHandler(
                    str(self.log_file),
                    maxBytes=10485760,  # 10MB
                    backupCount=5  # Keep up to 5 backup files
                )
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                
                # Log application startup
                logger.info("FreeChat started")
        except Exception as e:
            self.console.print(f"[yellow]Warning: Logging setup failed: {e}[/yellow]")

    def _log(self, level: str, message: str):
        """Log a message with the specified level."""
        try:
            log_level = self.LOG_LEVEL_MAP.get(level.upper(), logging.INFO)
            logger = logging.getLogger('FreeChat')
            logger.log(log_level, message)
        except Exception as e:
            # If logging fails, print a warning to the console
            self.console.print(f"[yellow]Warning: Logging failed: {e}[/yellow]")

    def _load_translations(self):
        """Load translations for different languages."""
        translations_path = self.config_dir / "translations.json"
        try:
            if translations_path.exists():
                with open(translations_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to load translations: {e}[/yellow]")
            self._log("error", f"Failed to load translations: {e}")
        
        # Fallback to default translations if file not found or invalid
        return {
            "en": {
                "welcome": "FreeChat v{version} (Stable)",
                "help_text": "Type /help for commands, /exit to quit. Press Control or Command + Enter to send.",
                "prompt": "Prompt: {prompt} | Model: {model} | Cost: ${cost:.4f} | (Ctrl+Enter)",
                "startup": "Fetching available models...",
                "model_switched": "✓ Switched model to: {model}",
                "model_error": "Error: Provider for '{model}' not found.",
                "session_new": "✓ New session started with default prompt '{prompt}'.",
                "session_save": "✓ Session saved as '{name}'.",
                "session_save_error": "Error saving session: {error}",
                "session_load": "✓ Session '{name}' loaded successfully.",
                "session_load_error": "Error loading session: {error}",
                "session_not_found": "Session '{name}' not found.",
                "session_list": "Saved sessions:",
                "session_no_sessions": "No saved sessions found.",
                "file_upload": "✓ File '{name}' uploaded and added to chat context.",
                "file_upload_error": "Error uploading file: {error}",
                "file_not_found": "Error: File '{path}' not found.",
                "file_size_error": "Error: File size exceeds 10MB limit.",
                "file_format_error": "Error: Unsupported file format '{format}'.",
                "pdf_error": "PDF file upload failed: {error}",
                "export_success": "✓ Session exported to {file}",
                "export_error": "Error exporting session: {error}",
                "command_help": "Show this help message.",
                "command_model": "Switch AI model.",
                "command_prompt": "Manage system prompts: list, view, <name>.",
                "command_session": "Start a new chat session with the default prompt.",
                "command_session_save": "Save the current session with a name.",
                "command_session_load": "Load a previously saved session.",
                "command_session_list": "List all saved sessions.",
                "command_file": "Upload and process a file.",
                "command_export": "Export session: md, json, html, md-rendered.",
                "command_clear": "Clear the terminal screen.",
                "command_exit": "Exit the application.",
                "usage": "Type a message and press Control or Command + Enter to send.",
                "goodbye": "Goodbye!",
                "error": "Error: {error}",
                "api_error": "API Error {code}: {message}",
                "warning": "Warning: {message}",
                "info": "Info: {message}"
            },
            "zh": {
                "welcome": "FreeChat v{version} (稳定版)",
                "help_text": "输入 /help 查看命令，/exit 退出。按 Control 或 Command + Enter 发送消息。",
                "prompt": "提示: {prompt} | 模型: {model} | 费用: ${cost:.4f} | (Ctrl+Enter)",
                "startup": "正在获取可用模型...",
                "model_switched": "✓ 模型已切换为: {model}",
                "model_error": "错误: 未找到 '{model}' 的提供商。",
                "session_new": "✓ 已开始新会话，使用默认提示 '{prompt}'。",
                "session_save": "✓ 会话已保存为 '{name}'。",
                "session_save_error": "保存会话失败: {error}",
                "session_load": "✓ 会话 '{name}' 加载成功。",
                "session_load_error": "加载会话失败: {error}",
                "session_not_found": "会话 '{name}' 未找到。",
                "session_list": "已保存的会话:",
                "session_no_sessions": "未找到已保存的会话。",
                "file_upload": "✓ 文件 '{name}' 已上传并添加到聊天上下文。",
                "file_upload_error": "上传文件失败: {error}",
                "file_not_found": "错误: 文件 '{path}' 未找到。",
                "file_size_error": "错误: 文件大小超过 10MB 限制。",
                "file_format_error": "错误: 不支持的文件格式 '{format}'。",
                "pdf_error": "PDF 文件上传失败: {error}",
                "export_success": "✓ 会话已导出到 {file}",
                "export_error": "导出会话失败: {error}",
                "command_help": "显示此帮助信息。",
                "command_model": "切换 AI 模型。",
                "command_prompt": "管理系统提示: list, view, <name>。",
                "command_session": "开始一个新的聊天会话，使用默认提示。",
                "command_session_save": "以指定名称保存当前会话。",
                "command_session_load": "加载之前保存的会话。",
                "command_session_list": "列出所有已保存的会话。",
                "command_file": "上传并处理文件。",
                "command_export": "导出会话: md, json, html, md-rendered。",
                "command_clear": "清空当前终端屏幕。",
                "command_exit": "退出应用程序。",
                "usage": "输入消息并按 Control 或 Command + Enter 发送。",
                "goodbye": "再见！",
                "error": "错误: {error}",
                "api_error": "API 错误 {code}: {message}",
                "warning": "警告: {message}",
                "info": "信息: {message}"
            }
        }

    def _translate(self, key, **kwargs):
        """Translate a key to the current language."""
        lang = self.language
        if lang not in self.translations:
            lang = "en"
        if key in self.translations[lang]:
            return self.translations[lang][key].format(**kwargs)
        return key

    def _setup_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        self.history_path.touch(exist_ok=True)
        
        first_run = False
        if not self.config_path.is_file():
            first_run = True
            # [V2.2.1] Default model set to the API-compatible ID.
            default_config = """# FreeChat Main Configuration
[general]
# The format is "provider_name/model_identifier".
# NOTE: Use the exact model ID required by the API (e.g., without ':free').
default_model = "openrouter/openrouter/free"
default_prompt = "default"
[providers]
openai_api_key = ""
openrouter_api_key = ""
gemini_api_key = ""
anthropic_api_key = ""
mistral_api_key = ""
"""
            with open(self.config_path, "w", encoding="utf-8") as f: f.write(default_config.strip() + "\n")
            self.console.print(f"[bold green]✓ Main config created at: {self.config_path}[/bold green]")
            self._log("info", f"Created main config at: {self.config_path}")

        if not self.prompts_path.is_file():
            first_run = True
            default_prompts = '''# FreeChat System Prompts
[default]
prompt = """You are FreeChat, a helpful and concise AI assistant running in a terminal."""
[coder]
prompt = """You are an expert programmer. Provide only code solutions."""
[translator]
prompt = """You are a multilingual translator. Your task is to translate the user's text into English."""
'''
            with open(self.prompts_path, "w", encoding="utf-8") as f: f.write(default_prompts.strip() + "\n")
            self.console.print(f"[bold green]✓ Prompts file created at: {self.prompts_path}[/bold green]")
            self._log("info", f"Created prompts file at: {self.prompts_path}")
        
        if first_run:
            self.console.print("[bold yellow]! Please add API keys to config.toml and restart.[/bold yellow]")
            self._log("info", "First run: API keys need to be configured")
            sys.exit(0)

    def _load_config(self, path: Path) -> Dict[str, Any]:
        config = {}
        if path.exists():
            try:
                with open(path, "rb") as f: config = tomllib.load(f)
            except tomllib.TOMLDecodeError as e: self.console.print(f"[bold red]Error: Invalid config file '{path}': {e}[/bold red]"); sys.exit(1)
        
        # Load API keys from environment variables if not in config
        providers = config.get("providers", {})
        env_keys = {
            "openai_api_key": "OPENAI_API_KEY",
            "openrouter_api_key": "OPENROUTER_API_KEY",
            "gemini_api_key": "GEMINI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "mistral_api_key": "MISTRAL_API_KEY"
        }
        
        # Get environment variable override setting
        general_config = config.get("general", {})
        allow_env_override = general_config.get("allow_env_override", True)
        
        for key, env_var in env_keys.items():
            env_value = os.environ.get(env_var)
            # Only use environment variable if allowed and key doesn't exist in config or value is empty
            if allow_env_override and (key not in providers or not providers.get(key) or not str(providers.get(key)).strip()) and env_value and env_value.strip():
                if "providers" not in config:
                    config["providers"] = {}
                config["providers"][key] = env_value
                self.console.print(f"[bold green]✓ Loaded {key} from environment variable.[/bold green]")
        
        return config

    def _save_config(self):
        """Save the current configuration to the config file."""
        try:
            with open(self.config_path, "wb") as f:
                tomli_w.dump(self.config, f)
            self._log("info", "Configuration saved")
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to save configuration: {e}[/yellow]")
            self._log("error", f"Failed to save configuration: {e}")

    def _apply_prompt(self, prompt_name: str, is_startup: bool = False):
        prompt_data = self.prompts.get(prompt_name)
        if prompt_data and "prompt" in prompt_data:
            self.active_prompt_name = prompt_name
            self.active_prompt_content = prompt_data["prompt"]
            self.session_messages = [{"role": "system", "content": self.active_prompt_content}]
            self.session_cost, self.session_name = 0.0, None
            if not is_startup: self.console.print(f"[bold green]✓ Prompt '{prompt_name}' applied. New session started.[/bold green]")
        else:
            self.console.print(f"[bold red]Error: Prompt '{prompt_name}' not found in prompts.toml.[/bold red]")
            if is_startup: self.active_prompt_name, self.active_prompt_content, self.session_messages = "none", "", []

    async def _handle_prompt_command(self, args: List[str]):
        if not args or args[0] == "view":
            self.console.print(f"[bold]Active prompt:[/] [cyan]{self.active_prompt_name}[/cyan]")
            self.console.print(Panel(self.active_prompt_content or "No system prompt active."))
        elif args[0] == "list":
            table = Table("Name", "Content Preview")
            for name, data in self.prompts.items(): table.add_row(name, data.get("prompt", "N/A").split('\n')[0])
            self.console.print(table)
        else: self._apply_prompt(args[0])

    async def _fetch_models(self, force_refresh: bool = False):
        current_time = time.time()
        if not force_refresh and self.available_models and (current_time - self.models_last_fetched) < self.MODELS_CACHE_TTL:
            return
        
        self.console.print("[dim]Fetching available models...[/dim]")
        tasks = [p.get_models() for n in self.provider_factory.get_available_providers() if (p := self.provider_factory.get_provider(f"{n}/any"))]
        if not tasks:
            return
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, tuple): self.available_models[r[0]] = r[1]
            elif isinstance(r, Exception): self.console.print(f"[yellow]Warning: Failed to fetch models: {r}[/yellow]")
        
        self.models_last_fetched = current_time

    def _get_bottom_toolbar(self) -> FormattedText:
        text = f"Prompt: {self.active_prompt_name} | Model: {self.current_model} | Cost: ${self.session_cost:.4f} | (Ctrl+Enter)"
        return FormattedText([("class:bottom-toolbar", text)])

    def _count_tokens(self, text: str) -> int:
        """Count tokens with caching to avoid repeated calculations."""
        if not self.tokenizer:
            return 0
        if text in self._token_cache:
            # Move to end to mark as recently used
            self._token_cache.move_to_end(text)
            return self._token_cache[text]
        count = len(self.tokenizer.encode(text))
        self._token_cache[text] = count
        # Limit cache size to prevent memory issues
        if len(self._token_cache) > 1000:
            # Remove oldest item (first item in OrderedDict)
            self._token_cache.popitem(last=False)
        return count
    
    def _manage_message_history(self):
        """Manage message history to keep it within limits."""
        if len(self.session_messages) > self.MAX_HISTORY_MESSAGES:
            # Extract system prompt if present
            system_prompt = next((msg for msg in self.session_messages if msg['role'] == 'system'), None)
            
            # Get all non-system messages
            non_system_messages = [msg for msg in self.session_messages if msg['role'] != 'system']
            
            # Calculate how many non-system messages we can keep
            max_non_system = self.MAX_HISTORY_MESSAGES - (1 if system_prompt else 0)
            
            # Keep the most recent non-system messages
            # This maintains the conversation flow while respecting the limit
            kept_messages = non_system_messages[-max_non_system:]
            
            # Reconstruct the history with system prompt first
            self.session_messages = []
            if system_prompt:
                self.session_messages.append(system_prompt)
            self.session_messages.extend(kept_messages)
    
    def _create_completer(self) -> FuzzyCompleter:
        current_time = time.time()
        cmds = list(self.commands.keys())
        models = [f"{p}/{m}" for p, ml in self.available_models.items() for m in ml]
        prompts = list(self.prompts.keys())
        
        # Check if we need to recreate the completer
        if (not self._completer or 
            current_time - self._completer_last_updated > 300):  # 5 minutes
            self._completer = FuzzyCompleter(WordCompleter(cmds + models + prompts, ignore_case=True))
            self._completer_last_updated = current_time
        
        return self._completer

    def _display_welcome(self):
        banner = Text("FreeChat v2.3.0 (Stable)", style="bold magenta", justify="center")
        info = Text("Type /help for commands, /exit to quit. Press Control or Command + Enter to send.", style="dim", justify="center")
        self.console.print(Panel.fit(Text.assemble(banner, "\n", info), padding=(1, 4)))
        
    async def _display_help(self, args: List[str]):
        help_text = """[bold]Welcome to FreeChat! ✨[/bold]
[bold]Commands:[/bold]
  [cyan]/help[/cyan]                  Show this help message.
  [cyan]/model <name>[/cyan]          Switch AI model.
  [cyan]/prompt <action>[/cyan]        Manage system prompts: [dim]list, view, <name>[/dim].
  [cyan]/session new[/cyan]           Start a new chat session with the default prompt.
  [cyan]/session save <name>[/cyan]      Save the current session with a name.
  [cyan]/session load <name>[/cyan]      Load a previously saved session.
  [cyan]/session list[/cyan]          List all saved sessions.
  [cyan]/file upload <path>[/cyan]     Upload and process a file. Supported formats: txt, md, json, csv, py, js, html, css, pdf.
  [cyan]/tool <action>[/cyan]         Manage tools: [dim]list, enable <name>, disable <name>, call <name> [args][/dim].
  [cyan]/language <code>[/cyan]       Switch interface language. Use without arguments to list available languages.
  [cyan]/export <format>[/cyan]       Export session: [dim]md, json, html, md-rendered[/dim].
  [cyan]/clear[/cyan]                 Clear the terminal screen.
  [cyan]/exit[/cyan]                  Exit the application.
[bold]Usage:[/bold]
- Type a message and press [bold]Control or Command + Enter[/bold] to send.
- When tools are enabled, the AI can use them to help answer your questions.
"""
        try: self.console.print(Panel(Text.from_markup(help_text), title="Help", border_style="blue"))
        except MarkupError: self.console.print("[bold red]Internal Warning:[/bold red] Help text markup is invalid.")
    
    def _exit_app(self, args: List[str]): raise EOFError

    async def _handle_command(self, user_input: str):
        parts = user_input.strip().split(maxsplit=1)
        cmd, args = parts[0], parts[1].split() if len(parts) > 1 else []
        if func := self.commands.get(cmd): await func(args) if asyncio.iscoroutinefunction(func) else func(args)
        else: self.console.print(f"[yellow]Unknown command: {cmd}. Type /help.[/yellow]")

    async def _handle_model_command(self, args: List[str]):
        if not args:
            self.console.print(f"[yellow]Current model: {self.current_model}. Usage: /model <name> or /model list[/yellow]")
            return

        if args[0] == 'list':
            # List available models from all providers
            table = Table("Provider", "Model ID", title="Available Models")
            for provider_name, provider in self.provider_factory.providers.items():
                try:
                    _, models = await provider.get_models()
                    for model in models[:10]:  # Show first 10 models per provider
                        table.add_row(provider_name, model)
                    if len(models) > 10:
                        table.add_row("", f"... and {len(models) - 10} more")
                except Exception as e:
                    table.add_row(provider_name, f"[Error: {e}]")
            self.console.print(table)
            return

        new_model = args[0]
        if new_model.split('/')[0] in self.provider_factory.get_available_providers():
            old_model = self.current_model
            self.current_model = new_model
            self.console.print(f"[bold green]✓ Switched model to: {self.current_model}[/bold green]")
            self._log("info", f"Switched model from {old_model} to {new_model}")
        else:
            self.console.print(f"[bold red]Error: Provider for '{new_model}' not found.[/bold red]")
            self._log("error", f"Failed to switch model: Provider for '{new_model}' not found")

    async def _handle_session_command(self, args: List[str]):
        if not args:
            self.console.print("[yellow]Usage: /session new|save|load|list[/yellow]"); return
        
        if args[0] == 'new':
            self._apply_prompt(self.default_prompt_name)
            self.console.print(f"[bold green]✓ New session started with default prompt '{self.default_prompt_name}'.[/bold green]")
            self._log("info", f"Started new session with prompt '{self.default_prompt_name}'")
        elif args[0] == 'save':
            if len(args) < 2:
                self.console.print("[yellow]Usage: /session save <name>[/yellow]"); return
            session_name = args[1]
            session_file = self.sessions_dir / f"{session_name}.json"
            try:
                with open(session_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "messages": self.session_messages,
                        "cost": self.session_cost,
                        "prompt": self.active_prompt_name,
                        "model": self.current_model
                    }, f, ensure_ascii=False, indent=2)
                self.console.print(f"[bold green]✓ Session saved as '{session_name}'.[/bold green]")
                self._log("info", f"Saved session as '{session_name}'")
            except Exception as e:
                self.console.print(f"[bold red]Error saving session: {e}[/bold red]")
                self._log("error", f"Failed to save session '{session_name}': {e}")
        elif args[0] == 'load':
            if len(args) < 2:
                self.console.print("[yellow]Usage: /session load <name>[/yellow]"); return
            session_name = args[1]
            session_file = self.sessions_dir / f"{session_name}.json"
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                self.session_messages = session_data.get("messages", [])
                self.session_cost = session_data.get("cost", 0.0)
                self.active_prompt_name = session_data.get("prompt", self.default_prompt_name)
                self.current_model = session_data.get("model", self.current_model)
                self.console.print(f"[bold green]✓ Session '{session_name}' loaded successfully.[/bold green]")
                self._log("info", f"Loaded session '{session_name}'")
            except FileNotFoundError:
                self.console.print(f"[bold red]Session '{session_name}' not found.[/bold red]")
                self._log("error", f"Session '{session_name}' not found")
            except Exception as e:
                self.console.print(f"[bold red]Error loading session: {e}[/bold red]")
                self._log("error", f"Failed to load session '{session_name}': {e}")
        elif args[0] == 'list':
            try:
                sessions = [f.stem for f in self.sessions_dir.glob("*.json")]
                if sessions:
                    self.console.print("[bold]Saved sessions:[/bold]")
                    for session in sessions:
                        self.console.print(f"  - {session}")
                else:
                    self.console.print("[yellow]No saved sessions found.[/yellow]")
                self._log("info", f"Listed {len(sessions)} saved sessions")
            except Exception as e:
                self.console.print(f"[bold red]Error listing sessions: {e}[/bold red]")
                self._log("error", f"Failed to list sessions: {e}")
        else:
            self.console.print("[yellow]Usage: /session new|save|load|list[/yellow]")
        
    async def _handle_file_command(self, args: List[str]):
        if not args:
            self.console.print("[yellow]Usage: /file upload <path>[/yellow]"); return
        
        if args[0] == 'upload':
            if len(args) < 2:
                self.console.print("[yellow]Usage: /file upload <path>[/yellow]"); return
            file_path = args[1]
            try:
                file = Path(file_path)
                if not file.exists() or not file.is_file():
                    self.console.print(f"[bold red]Error: File '{file_path}' not found.[/bold red]"); 
                    self._log("error", f"File upload failed: File '{file_path}' not found")
                    return
                
                file_size = file.stat().st_size
                if file_size > 10 * 1024 * 1024:  # 10MB limit
                    self.console.print("[bold red]Error: File size exceeds 10MB limit.[/bold red]"); 
                    self._log("error", f"File upload failed: File size exceeds 10MB limit")
                    return
                
                # Read file content based on extension
                extension = file.suffix.lower()
                if extension in ['.txt', '.md', '.json', '.csv', '.py', '.js', '.html', '.css']:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Add file content to chat context
                    file_info = f"[File: {file.name}]\n\n{content}"
                    self.session_messages.append({"role": "user", "content": file_info})
                    self.console.print(f"[bold green]✓ File '{file.name}' uploaded and added to chat context.[/bold green]")
                    self._log("info", f"Uploaded file '{file.name}' ({file_size} bytes)")
                elif extension in ['.pdf']:
                    try:
                        import PyPDF2
                        with open(file, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            content = "\n".join([page.extract_text() for page in reader.pages])
                        file_info = f"[PDF File: {file.name}]\n\n{content}"
                        self.session_messages.append({"role": "user", "content": file_info})
                        self.console.print(f"[bold green]✓ PDF file '{file.name}' uploaded and added to chat context.[/bold green]")
                        self._log("info", f"Uploaded PDF file '{file.name}' ({file_size} bytes)")
                    except ImportError:
                        self.console.print("[bold red]Error: PyPDF2 is not installed. Please install it with 'pip install PyPDF2'.[/bold red]")
                        self._log("error", "PDF file upload failed: PyPDF2 is not installed")
                    except Exception as e:
                        self.console.print(f"[bold red]Error reading PDF file: {e}[/bold red]")
                        self._log("error", f"PDF file upload failed: {e}")
                else:
                    self.console.print(f"[bold red]Error: Unsupported file format '{extension}'.[/bold red]")
                    self._log("error", f"File upload failed: Unsupported file format '{extension}'")
            except Exception as e:
                self.console.print(f"[bold red]Error uploading file: {e}[/bold red]")
                self._log("error", f"File upload failed: {e}")
        else:
            self.console.print("[yellow]Usage: /file upload <path>[/yellow]")

    async def _handle_language_command(self, args: List[str]):
        """Handle language commands: view current language, list available languages, or switch language."""
        if not args:
            # Show current language
            language_names = {
                "en": "English",
                "zh": "中文"
            }
            current_language_name = language_names.get(self.language, self.language)
            self.console.print(f"[bold]Current language:[/bold] {current_language_name} ({self.language})")
            self.console.print("[bold]Available languages:[/bold]")
            for lang_code, lang_name in language_names.items():
                self.console.print(f"  - {lang_name} ({lang_code})")
            self.console.print("[bold]Usage:[/bold] /language <code> to switch language")
            return
        
        new_language = args[0].lower()
        if new_language in self.translations:
            old_language = self.language
            self.language = new_language
            # Save language setting to config
            self.config.setdefault('general', {})['language'] = new_language
            self._save_config()
            language_names = {
                "en": "English",
                "zh": "中文"
            }
            new_language_name = language_names.get(new_language, new_language)
            self.console.print(f"[bold green]✓ Switched language to {new_language_name} ({new_language})[/bold green]")
            self._log("info", f"Switched language from {old_language} to {new_language}")
        else:
            self.console.print(f"[bold red]Error: Language '{new_language}' not supported.[/bold red]")
            self._log("error", f"Failed to switch language: Language '{new_language}' not supported")
        
    async def _handle_export_command(self, args: List[str]):
        if not args: self.console.print("[yellow]Usage: /export <md|json|html|md-rendered>[/yellow]"); return
        fmt = args[0].lower(); filename = f"freechat_session_{self.session_name or int(time.time())}.{fmt if fmt != 'md-rendered' else 'html'}"
        try:
            if fmt == "md":
                content = "".join(f"**{'You' if m['role']=='user' else 'AI'}:**\n\n{m['content']}\n\n---\n\n" for m in self.session_messages if m['role'] != 'system')
                with open(self.sessions_dir.parent / filename, "w", encoding="utf-8") as f: f.write(content)
            elif fmt == "json":
                with open(self.sessions_dir.parent / filename, "w", encoding="utf-8") as f: json.dump(self.session_messages, f, ensure_ascii=False, indent=2)
            elif fmt == "html": self.console.save_html(str(self.sessions_dir.parent / filename))
            elif fmt == "md-rendered":
                # Create HTML file with rendered Markdown content
                from rich.markdown import Markdown
                from rich.console import Console as RichConsole
                from io import StringIO
                
                # Create a string buffer to capture rendered output
                buffer = StringIO()
                # Use cached RichConsole instance or create a new one
                if not self._export_console:
                    self._export_console = RichConsole(file=buffer, width=80, force_terminal=False, force_interactive=False)
                else:
                    # Reset the file object for the console
                    self._export_console.file = buffer
                render_console = self._export_console
                
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset=\"utf-8\">
    <title>FreeChat Session</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji'; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .message {{ margin-bottom: 20px; }}
        .user {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .ai {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; }}
        .role {{ font-weight: bold; margin-bottom: 5px; }}
        hr {{ border: 0; border-top: 1px solid #eee; margin: 20px 0; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        code {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }}
        .rendered-md {{ white-space: pre-wrap; font-family: inherit; }}
    </style>
</head>
<body>
"""
                for msg in self.session_messages:
                    if msg['role'] != 'system':
                        role = 'You' if msg['role'] == 'user' else 'AI'
                        css_class = 'user' if msg['role'] == 'user' else 'ai'
                        html_content += f'<div class=\"message {css_class}\">\n<div class=\"role\">{role}:</div>\n'
                        # Render markdown content using Rich
                        md = Markdown(msg['content'])
                        render_console.print(md)
                        rendered_content = buffer.getvalue()
                        buffer.seek(0)
                        buffer.truncate(0)
                        # Convert to HTML-safe content
                        rendered_content = rendered_content.replace("&", "&").replace("<", "<").replace(">", ">")
                        html_content += f'<div class=\"rendered-md\">{rendered_content}</div>\n</div>\n<hr>\n'
                html_content += "</body>\n</html>"
                with open(self.sessions_dir.parent / filename, "w", encoding="utf-8") as f: f.write(html_content)
            else: self.console.print(f"[bold red]Error: Unknown format '{fmt}'.[/bold red]"); return
            self.console.print(f"[bold green]✓ Session exported to {filename}[/bold green]")
        except Exception as e: self.console.print(f"[bold red]Error exporting session: {e}[/bold red]")

    def _register_builtin_tools(self):
        """Register built-in tools into the tool registry."""
        # Calculator tool
        calc_tool = ToolDefinition(
            name="calculator",
            description="Safely evaluate a mathematical expression. Supports basic math operations and functions like sqrt, sin, cos, tan, log, exp, pow, abs, ceil, floor, round, and constants pi and e.",
            parameters=[
                ToolParameter(name="expression", type="string", description="The mathematical expression to evaluate.", required=True)
            ],
            handler=lambda args: _safe_calculator(args.get("expression", "")),
            dangerous=False
        )
        self.tool_registry.register(calc_tool)

        # File read tool
        file_read = ToolDefinition(
            name="file_read",
            description="Read the contents of a file. The file must be within the home directory or current working directory.",
            parameters=[
                ToolParameter(name="path", type="string", description="Path to the file to read.", required=True),
                ToolParameter(name="max_size", type="integer", description="Maximum file size in bytes (default: 1MB).", required=False)
            ],
            handler=_file_read_tool,
            dangerous=False
        )
        self.tool_registry.register(file_read)

        # File write tool
        file_write = ToolDefinition(
            name="file_write",
            description="Write content to a file. Creates parent directories if needed. Backs up existing files before overwriting.",
            parameters=[
                ToolParameter(name="path", type="string", description="Path to the file to write.", required=True),
                ToolParameter(name="content", type="string", description="Content to write to the file.", required=True),
                ToolParameter(name="mode", type="string", description="Write mode: 'write' (default) or 'append'.", required=False, enum=["write", "append"])
            ],
            handler=_file_write_tool,
            dangerous=True
        )
        self.tool_registry.register(file_write)

        # Web fetch tool
        web_fetch = ToolDefinition(
            name="web_fetch",
            description="Fetch and extract text content from a web URL.",
            parameters=[
                ToolParameter(name="url", type="string", description="The URL to fetch.", required=True),
                ToolParameter(name="max_length", type="integer", description="Maximum content length (default: 50000 chars).", required=False)
            ],
            handler=_web_fetch_tool,
            dangerous=False
        )
        self.tool_registry.register(web_fetch)

    def _load_custom_tools_from_config(self):
        """Load custom tool configurations from config.toml [tools] section."""
        tools_config = self.config.get("tools", {})
        
        # Auto-enable tools listed in config
        enabled_tools = tools_config.get("enabled", [])
        if isinstance(enabled_tools, list):
            for tool_name in enabled_tools:
                if not self.tool_registry.enable(tool_name):
                    self.console.print(f"[yellow]Warning: Tool '{tool_name}' listed in config but not found in registry.[/yellow]")

    async def _handle_prompt(self, prompt: str):
        self.console.print(f"[bold cyan]You:[/bold cyan] {prompt}")
        if not (provider := self.provider_factory.get_provider(self.current_model)): self.console.print(f"[bold red]Error: Provider for '{self.current_model}' not found.[/bold red]"); return
        self.session_messages.append({"role": "user", "content": prompt})
        prompt_tokens = self._count_tokens(prompt)
        
        # [V2.2.1] Removed smart cleaning. The exact model name is used.
        provider_name, model_name = self.current_model.split('/', 1)
        
        full_response, start_time = "", time.time()
        try:
            self.console.print("[bold magenta]AI:[/bold magenta] ", end="")
            stream = provider.stream_chat(self.session_messages, model_name)
            async for chunk in stream:
                full_response += chunk
                sys.stdout.write(chunk); sys.stdout.flush()
            self.console.print()
        except httpx.HTTPStatusError as e:
            try: await e.response.aread(); error_body = e.response.text
            except Exception: error_body = str(e)
            self.console.print(f"\n[bold red]API Error {e.response.status_code}:[/bold red] {error_body}"); self.session_messages.pop(); return
        except Exception as e: self.console.print(f"\n[bold red]Error: {e}[/bold red]"); self.session_messages.pop(); return
        self.session_messages.append({"role": "assistant", "content": full_response})
        self._manage_message_history()  # Manage message history after adding response
        cost = provider.calculate_cost(prompt_tokens, self._count_tokens(full_response), model_name)
        if cost is not None: self.session_cost += cost
        self.console.print(f"[dim]Time: {(time.time() - start_time):.2f}s | Cost: {'N/A' if cost is None else f'${cost:.6f}'}[/dim]")
        
    async def close_providers(self):
        """Close all provider HTTP clients to free resources."""
        for provider in self.provider_factory.providers.values():
            try:
                await provider.close()
            except Exception:
                pass
    
    async def run(self):
        self._display_welcome(); await self._fetch_models()
        while True:
            try:
                inp = await self.prompt_session.prompt_async(">", bottom_toolbar=self._get_bottom_toolbar, style=self.style, completer=self._create_completer(), refresh_interval=0.5)
                if inp.strip(): await (self._handle_command if inp.startswith('/') else self._handle_prompt)(inp)
            except (EOFError, KeyboardInterrupt): 
                await self.close_providers()
                self.console.print("\n[bold]Goodbye![/bold]"); return

# --- Tool System ---
@dataclass
class ToolParameter:
    """Represents a single parameter for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = {"type": self.type, "description": self.description}
        if self.enum:
            schema["enum"] = self.enum
        return schema


@dataclass
class ToolDefinition:
    """Represents a tool definition."""
    name: str
    description: str
    parameters: List[ToolParameter]
    handler: Callable[[Dict[str, Any]], Union[str, Dict[str, Any]]]
    dangerous: bool = False  # For commands that modify system state

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI Function Calling format."""
        properties = {p.name: p.to_schema() for p in self.parameters}
        required = [p.name for p in self.parameters if p.required]

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def to_gemini_schema(self) -> Dict[str, Any]:
        """Convert to Gemini Function Calling format."""
        # Gemini uses similar schema format
        properties = {p.name: p.to_schema() for p in self.parameters}
        required = [p.name for p in self.parameters if p.required]

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


# --- Skill System ---

class SkillMetadata:
    """Metadata for a skill package."""
    __slots__ = ['name', 'version', 'description', 'author', 'entry_point', 'dependencies']

    def __init__(self, name: str, version: str = "1.0.0", description: str = "",
                 author: str = "", entry_point: str = "", dependencies: Optional[List[str]] = None):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.entry_point = entry_point
        self.dependencies = dependencies or []

    @classmethod
    def from_toml(cls, data: Dict[str, Any]) -> "SkillMetadata":
        """Create metadata from TOML data."""
        skill_data = data.get("skill", {})
        return cls(
            name=skill_data.get("name", ""),
            version=skill_data.get("version", "1.0.0"),
            description=skill_data.get("description", ""),
            author=skill_data.get("author", ""),
            entry_point=skill_data.get("entry_point", ""),
            dependencies=skill_data.get("dependencies", [])
        )


class SkillSecurityManager:
    """Manages skill security including signatures, permissions, and sandboxing."""

    # Permission flags for skills
    PERMISSION_FILE_READ = "file_read"
    PERMISSION_FILE_WRITE = "file_write"
    PERMISSION_NETWORK = "network"
    PERMISSION_SHELL = "shell"
    PERMISSION_ENV = "env"

    # Default trusted skill authors (public key hashes)
    _trusted_authors: Dict[str, str] = {}

    # Skill permission profiles (skill_name -> [permissions])
    _skill_permissions: Dict[str, List[str]] = {}

    @classmethod
    def compute_signature(cls, skill_path: Path, secret_key: str) -> str:
        """Compute HMAC-SHA256 signature for a skill package."""
        if not skill_path.exists():
            return ""

        files_to_sign = sorted([f for f in skill_path.rglob("*") if f.is_file()])
        hasher = hmac.new(secret_key.encode('utf-8'), digestmod=hashlib.sha256)

        for file_path in files_to_sign:
            if file_path.name == ".signature":
                continue
            try:
                rel_path = str(file_path.relative_to(skill_path))
                hasher.update(rel_path.encode('utf-8'))
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
            except Exception:
                continue

        return hasher.hexdigest()

    @classmethod
    def verify_signature(cls, skill_path: Path, trusted_public_key_hash: Optional[str] = None) -> bool:
        """Verify skill package signature."""
        sig_file = skill_path / ".signature"
        if not sig_file.exists():
            return trusted_public_key_hash is None

        try:
            with open(sig_file, 'r') as f:
                signature = f.read().strip()

            if trusted_public_key_hash:
                expected = cls._trusted_authors.get(trusted_public_key_hash)
                if expected and hmac.compare_digest(signature, expected):
                    return True

            return True
        except Exception:
            return False

    @classmethod
    def set_permissions(cls, skill_name: str, permissions: List[str]) -> None:
        """Set permissions for a skill."""
        cls._skill_permissions[skill_name] = permissions

    @classmethod
    def get_permissions(cls, skill_name: str) -> List[str]:
        """Get permissions for a skill."""
        return cls._skill_permissions.get(skill_name, [])

    @classmethod
    def has_permission(cls, skill_name: str, permission: str) -> bool:
        """Check if a skill has a specific permission."""
        perms = cls._skill_permissions.get(skill_name, [])
        return permission in perms

    @classmethod
    def validate_skill_path(cls, skill_path: Path) -> Tuple[bool, str]:
        """Validate skill path for security issues."""
        try:
            resolved = skill_path.resolve()
            home = Path.home().resolve()
            if not str(resolved).startswith(str(home)):
                return False, "Skill path must be within home directory"
            return True, "OK"
        except Exception as e:
            return False, f"Path validation error: {e}"

    @classmethod
    def generate_install_token(cls, skill_name: str) -> str:
        """Generate a unique install token for verification."""
        token = secrets.token_urlsafe(32)
        return f"{skill_name}:{token}"


class SkillSandbox:
    """Sandbox environment for skill execution with restricted permissions."""

    def __init__(self, skill_name: str, allowed_permissions: List[str]):
        self.skill_name = skill_name
        self.allowed_permissions = set(allowed_permissions)
        self._original_env = None
        self._restricted_env = {}

    def __enter__(self):
        """Enter sandbox environment."""
        import os
        self._original_env = dict(os.environ)

        self._restricted_env = {
            k: v for k, v in self._original_env.items()
            if k in ('PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'LC_ALL')
        }

        if SkillSecurityManager.has_permission(self.skill_name, SkillSecurityManager.PERMISSION_ENV):
            self._restricted_env.update({
                k: v for k, v in self._original_env.items()
                if not k.startswith(('AWS_', 'GCP_', 'AZURE_', 'SECRET', 'TOKEN', 'KEY', 'PASSWORD'))
            })

        os.environ.clear()
        os.environ.update(self._restricted_env)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox environment."""
        import os
        if self._original_env is not None:
            os.environ.clear()
            os.environ.update(self._original_env)
        return False

    def check_permission(self, permission: str) -> bool:
        """Check if a permission is allowed in this sandbox."""
        return permission in self.allowed_permissions

    def validate_file_access(self, file_path: Path, mode: str = 'read') -> Tuple[bool, str]:
        """Validate file access within sandbox constraints."""
        if mode == 'write' and not self.check_permission(SkillSecurityManager.PERMISSION_FILE_WRITE):
            return False, "Write permission not granted to this skill"
        if mode == 'read' and not self.check_permission(SkillSecurityManager.PERMISSION_FILE_READ):
            return False, "Read permission not granted to this skill"

        try:
            resolved = file_path.resolve()
            home = Path.home().resolve()
            if not str(resolved).startswith(str(home)):
                return False, "Access outside home directory not allowed"
            return True, "OK"
        except Exception as e:
            return False, f"Path validation error: {e}"


class SkillDefinition:

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def version(self) -> str:
        return self.metadata.version

    @classmethod
    def from_directory(cls, path: Path) -> Optional["SkillDefinition"]:
        """Load skill definition from a directory."""
        try:
            # Load skill.toml
            toml_path = path / "skill.toml"
            if not toml_path.exists():
                return None

            with open(toml_path, "rb") as f:
                data = tomllib.load(f)

            metadata = SkillMetadata.from_toml(data)

            # Parse tools if defined
            tools = []
            tools_data = data.get("tools", [])
            for tool_data in tools_data:
                params = [
                    ToolParameter(
                        name=p.get("name", ""),
                        type=p.get("type", "string"),
                        description=p.get("description", ""),
                        required=p.get("required", True),
                        enum=p.get("enum")
                    )
                    for p in tool_data.get("parameters", [])
                ]

                tools.append(ToolDefinition(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    parameters=params,
                    handler=lambda args: "Not implemented"  # Placeholder
                ))

            return cls(
                metadata=metadata,
                tools=tools,
                config_schema=data.get("config", {})
            )

        except Exception as e:
            print(f"[Warning] Failed to load skill from {path}: {e}")
            return None


# --- Memory System ---

@dataclass
class MemoryEntry:
    """A single memory entry with metadata for auction-based compression."""
    id: str
    content: str
    category: str  # user_facts, preferences, knowledge, context, decisions
    source: str
    created_at: float
    updated_at: float
    access_count: int = 0
    last_accessed: float = 0
    importance: int = 5  # 1-10
    tags: List[str] = field(default_factory=list)
    branch: Optional[str] = None  # None = global
    compressed: bool = False
    original_length: int = 0
    value_score: float = 0.0

    def compute_value_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Compute auction value score using weighted factors."""
        if weights is None:
            weights = {'importance': 0.4, 'relevance': 0.3, 'recency': 0.2, 'frequency': 0.1}

        # Importance: 1-10 scale
        importance_score = self.importance / 10.0

        # Recency: exponential decay (30-day half-life)
        days_old = (time.time() - self.created_at) / 86400
        recency_score = math.exp(-days_old / 30)

        # Frequency: normalized access count
        freq_score = min(self.access_count / 10.0, 1.0)

        # Relevance: based on tags (simplified)
        relevance_score = 0.5 + (len(self.tags) * 0.05) if self.tags else 0.5
        relevance_score = min(relevance_score, 1.0)

        score = (weights['importance'] * importance_score +
                weights['relevance'] * relevance_score +
                weights['recency'] * recency_score +
                weights['frequency'] * freq_score)

        self.value_score = score
        return score


class SQLiteMemoryStore:
    """SQLite-based storage for memories with FTS5 full-text search."""

    SCHEMA = '''
    -- Main memories table
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        content_compressed TEXT,
        category TEXT NOT NULL,
        source TEXT,
        branch TEXT,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        accessed_at REAL,
        access_count INTEGER DEFAULT 0,
        importance INTEGER DEFAULT 5,
        value_score REAL,
        is_compressed BOOLEAN DEFAULT 0,
        is_archived BOOLEAN DEFAULT 0,
        original_length INTEGER DEFAULT 0
    );

    -- Tags many-to-many
    CREATE TABLE IF NOT EXISTS memory_tags (
        memory_id TEXT NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY (memory_id, tag),
        FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
    );

    -- Full-text search virtual table
    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
        content,
        content='memories',
        content_rowid='rowid'
    );

    -- Triggers to sync FTS index
    CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
        INSERT INTO memories_fts(rowid, content) VALUES (new.rowid, new.content);
    END;

    CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
        INSERT INTO memories_fts(memories_fts, rowid, content)
        VALUES ('delete', old.rowid, old.content);
    END;

    CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
        INSERT INTO memories_fts(memories_fts, rowid, content)
        VALUES ('delete', old.rowid, old.content);
        INSERT INTO memories_fts(rowid, content) VALUES (new.rowid, new.content);
    END;

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_memories_branch ON memories(branch);
    CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
    CREATE INDEX IF NOT EXISTS idx_memories_value ON memories(value_score DESC);
    CREATE INDEX IF NOT EXISTS idx_memories_accessed ON memories(accessed_at DESC);
    CREATE INDEX IF NOT EXISTS idx_memories_archived ON memories(is_archived) WHERE is_archived = 0;
    CREATE INDEX IF NOT EXISTS idx_memory_tags_tag ON memory_tags(tag);
    '''

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._local = threading.local()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            self._local.connection = conn
        return self._local.connection

    def _init_database(self) -> None:
        """Initialize database schema."""
        # Ensure directory exists
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()

    def insert_memory(self, entry: MemoryEntry) -> bool:
        """Insert a memory entry."""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    INSERT INTO memories
                    (id, content, content_compressed, category, source, branch,
                     created_at, updated_at, accessed_at, access_count,
                     importance, value_score, is_compressed, is_archived, original_length)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.id, entry.content, None, entry.category, entry.source,
                    entry.branch, entry.created_at, entry.updated_at,
                    entry.last_accessed if entry.last_accessed else None,
                    entry.access_count, entry.importance, entry.value_score,
                    entry.compressed, False, entry.original_length
                ))

                # Insert tags
                if entry.tags:
                    conn.executemany(
                        'INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?, ?)',
                        [(entry.id, tag) for tag in entry.tags]
                    )

                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Failed to insert memory: {e}")
            return False

    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a memory by ID."""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM memories WHERE id = ?', (memory_id,)
                ).fetchone()

                if not row:
                    return None

                # Get tags
                tags = [r['tag'] for r in conn.execute(
                    'SELECT tag FROM memory_tags WHERE memory_id = ?', (memory_id,)
                )]

                return self._row_to_entry(row, tags)
        except sqlite3.Error as e:
            logging.error(f"Failed to get memory: {e}")
            return None

    def search_memories(self, query: str = "", branch: Optional[str] = None,
                       category: Optional[str] = None, tags: List[str] = None,
                       limit: int = 10, include_archived: bool = False) -> List[MemoryEntry]:
        """Search memories with various filters."""
        try:
            conditions = []
            params = []

            # Full-text search
            if query:
                # Use FTS5 for content search
                conditions.append("m.id IN (SELECT rowid FROM memories_fts WHERE content MATCH ?)")
                params.append(query)

            if branch is not None:
                conditions.append("m.branch = ?")
                params.append(branch)
            else:
                conditions.append("m.branch IS NULL")

            if category:
                conditions.append("m.category = ?")
                params.append(category)

            if not include_archived:
                conditions.append("m.is_archived = 0")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            with self._get_connection() as conn:
                rows = conn.execute(f'''
                    SELECT m.* FROM memories m
                    WHERE {where_clause}
                    ORDER BY m.value_score DESC, m.accessed_at DESC
                    LIMIT ?
                ''', params + [limit]).fetchall()

                results = []
                for row in rows:
                    memory_id = row['id']
                    tags_list = [r['tag'] for r in conn.execute(
                        'SELECT tag FROM memory_tags WHERE memory_id = ?', (memory_id,)
                    )]
                    results.append(self._row_to_entry(row, tags_list))

                return results
        except sqlite3.Error as e:
            logging.error(f"Failed to search memories: {e}")
            return []

    def update_memory(self, entry: MemoryEntry) -> bool:
        """Update an existing memory."""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    UPDATE memories SET
                        content = ?,
                        content_compressed = ?,
                        category = ?,
                        source = ?,
                        branch = ?,
                        updated_at = ?,
                        accessed_at = ?,
                        access_count = ?,
                        importance = ?,
                        value_score = ?,
                        is_compressed = ?,
                        is_archived = ?,
                        original_length = ?
                    WHERE id = ?
                ''', (
                    entry.content, None, entry.category, entry.source,
                    entry.branch, entry.updated_at,
                    entry.last_accessed if entry.last_accessed else None,
                    entry.access_count, entry.importance, entry.value_score,
                    entry.compressed, False, entry.original_length,
                    entry.id
                ))

                # Update tags
                conn.execute('DELETE FROM memory_tags WHERE memory_id = ?', (entry.id,))
                if entry.tags:
                    conn.executemany(
                        'INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?, ?)',
                        [(entry.id, tag) for tag in entry.tags]
                    )

                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Failed to update memory: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        try:
            with self._get_connection() as conn:
                # Tags will be deleted by cascade
                cursor = conn.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Failed to delete memory: {e}")
            return False

    def archive_old_memories(self, min_score: float, days_old: int) -> int:
        """Archive memories below score threshold and older than specified days."""
        try:
            cutoff_time = time.time() - (days_old * 86400)
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE memories
                    SET is_archived = 1
                    WHERE value_score < ?
                    AND created_at < ?
                    AND is_archived = 0
                ''', (min_score, cutoff_time))
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            logging.error(f"Failed to archive memories: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                total = conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0]
                archived = conn.execute('SELECT COUNT(*) FROM memories WHERE is_archived = 1').fetchone()[0]
                global_memories = conn.execute('SELECT COUNT(*) FROM memories WHERE branch IS NULL').fetchone()[0]
                branches = conn.execute('SELECT COUNT(DISTINCT branch) FROM memories WHERE branch IS NOT NULL').fetchone()[0]
                avg_score = conn.execute('SELECT AVG(value_score) FROM memories').fetchone()[0] or 0

                return {
                    'total_memories': total,
                    'active_memories': total - archived,
                    'archived_memories': archived,
                    'global_memories': global_memories,
                    'branches': branches,
                    'average_score': round(avg_score, 2)
                }
        except sqlite3.Error as e:
            logging.error(f"Failed to get stats: {e}")
            return {}

    def _row_to_entry(self, row: sqlite3.Row, tags: List[str]) -> MemoryEntry:
        """Convert a database row to MemoryEntry."""
        return MemoryEntry(
            id=row['id'],
            content=row['content'],
            category=row['category'],
            source=row['source'] or '',
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            access_count=row['access_count'],
            last_accessed=row['accessed_at'] or 0,
            importance=row['importance'],
            tags=tags,
            branch=row['branch'],
            compressed=bool(row['is_compressed']),
            original_length=row['original_length'],
            value_score=row['value_score'] or 0.0
        )

    def close(self) -> None:
        """Close all database connections."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


class AuctionEngine:
    """Auction-based memory compression engine."""

    DEFAULT_WEIGHTS = {
        'importance': 0.4,
        'relevance': 0.3,
        'recency': 0.2,
        'frequency': 0.1
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def calculate_value_score(self, entry: MemoryEntry) -> float:
        """Calculate value score for auction bidding."""
        w = self.weights

        # Importance: 1-10 scale
        importance_score = entry.importance / 10.0

        # Recency: exponential decay (30-day half-life)
        days_old = (time.time() - entry.created_at) / 86400
        recency_score = math.exp(-days_old / 30)

        # Frequency: normalized access count
        freq_score = min(entry.access_count / 10.0, 1.0)

        # Relevance: based on tags
        relevance_score = 0.5 + (len(entry.tags) * 0.05) if entry.tags else 0.5
        relevance_score = min(relevance_score, 1.0)

        score = (w['importance'] * importance_score +
                w['relevance'] * relevance_score +
                w['recency'] * recency_score +
                w['frequency'] * freq_score)

        entry.value_score = score
        return score

    def run_auction(self, entries: List[MemoryEntry], max_keep: int) -> Tuple[List[MemoryEntry], List[MemoryEntry]]:
        """Run auction to determine which memories to keep vs compress."""
        if not entries:
            return [], []

        # Calculate scores
        scored = [(entry, self.calculate_value_score(entry)) for entry in entries]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Split into keep and compress
        keep = [entry for entry, _ in scored[:max_keep]]
        compress = [entry for entry, _ in scored[max_keep:]]

        return keep, compress


class MemoryManager:
    """High-level memory management interface with auction-based compression."""

    def __init__(self, db_path: Path, current_branch: Optional[str] = None,
                 max_global: int = 100, max_branch: int = 50):
        self._store = SQLiteMemoryStore(db_path)
        self._current_branch = current_branch
        self._max_global = max_global
        self._max_branch = max_branch
        self._auction = AuctionEngine()

    def remember(self, content: str, category: str = "context",
                 importance: int = 5, tags: List[str] = None,
                 branch: Optional[str] = None, source: str = "user") -> str:
        """Store a new memory. Returns memory ID."""
        now = time.time()
        memory_id = f"mem_{int(now * 1000)}_{uuid.uuid4().hex[:8]}"

        entry = MemoryEntry(
            id=memory_id,
            content=content,
            category=category,
            source=source,
            created_at=now,
            updated_at=now,
            importance=importance,
            tags=tags or [],
            branch=branch if branch is not None else self._current_branch,
            original_length=len(content)
        )

        # Calculate initial value score
        self._auction.calculate_value_score(entry)

        if self._store.insert_memory(entry):
            return memory_id
        return ""

    def recall(self, query: str = "", branch: Optional[str] = None,
               category: Optional[str] = None, tags: List[str] = None,
               limit: int = 10) -> List[MemoryEntry]:
        """Retrieve relevant memories."""
        # Use provided branch or current branch
        target_branch = branch if branch is not None else self._current_branch

        return self._store.search_memories(
            query=query,
            branch=target_branch,
            category=category,
            tags=tags,
            limit=limit
        )

    def forget(self, memory_id: str) -> bool:
        """Delete a memory."""
        return self._store.delete_memory(memory_id)

    def update_memory(self, memory_id: str, **kwargs) -> bool:
        """Update a memory's fields."""
        entry = self._store.get_memory(memory_id)
        if not entry:
            return False

        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        entry.updated_at = time.time()
        return self._store.update_memory(entry)

    def touch_memory(self, memory_id: str) -> bool:
        """Update access count and last accessed time."""
        try:
            with self._store._get_connection() as conn:
                conn.execute('''
                    UPDATE memories
                    SET access_count = access_count + 1,
                        accessed_at = ?
                    WHERE id = ?
                ''', (time.time(), memory_id))
                conn.commit()
                return True
        except sqlite3.Error:
            return False

    def compress_memories(self, branch: Optional[str] = None) -> int:
        """Run auction-based compression."""
        # Get all active memories for branch
        memories = self._store.search_memories(
            query="",
            branch=branch if branch is not None else self._current_branch,
            limit=10000  # Get all
        )

        if not memories:
            return 0

        # Determine max based on branch
        max_keep = self._max_branch if branch is not None else self._max_global

        # Run auction
        keep, compress = self._auction.run_auction(memories, max_keep)

        # Archive compressed memories
        compressed_count = 0
        for entry in compress:
            if not entry.compressed:
                entry.compressed = True
                entry.content = self._summarize_content(entry.content)
                self._store.update_memory(entry)
                compressed_count += 1

        return compressed_count

    def _summarize_content(self, content: str, max_length: int = 200) -> str:
        """Create a summary of content for compression."""
        if len(content) <= max_length:
            return content
        return content[:max_length] + "... [compressed]"

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return self._store.get_stats()

    def close(self) -> None:
        """Close the memory store."""
        self._store.close()


class BranchMemoryManager:
    """Manages memory synchronization with Git branches."""

    def __init__(self, memory_manager: MemoryManager):
        self._mm = memory_manager
        self._repo_path: Optional[Path] = None
        self._detect_git_repo()

    def _detect_git_repo(self) -> bool:
        """Detect if we're in a git repo."""
        try:
            # Look for .git directory
            cwd = Path.cwd()
            for path in [cwd] + list(cwd.parents):
                git_dir = path / ".git"
                if git_dir.exists() and git_dir.is_dir():
                    self._repo_path = path
                    return True
            return False
        except Exception:
            return False

    def get_current_branch(self) -> Optional[str]:
        """Get current git branch name."""
        if not self._repo_path:
            return None

        try:
            git_head = self._repo_path / ".git" / "HEAD"
            if not git_head.exists():
                return None

            content = git_head.read_text().strip()
            if content.startswith("ref: refs/heads/"):
                return content[16:]  # Extract branch name
            return "detached"  # Detached HEAD state
        except Exception:
            return None

    def sync_branch_memories(self) -> None:
        """Sync memories when switching branches."""
        current_branch = self.get_current_branch()
        if current_branch and current_branch != self._mm._current_branch:
            # Update current branch in memory manager
            self._mm._current_branch = current_branch
            logging.info(f"Switched to branch: {current_branch}")

    def merge_branch_memories(self, from_branch: str, to_branch: str) -> int:
        """Merge memories from one branch to another."""
        try:
            # Get all memories from source branch
            from_memories = self._mm._store.search_memories(
                query="", branch=from_branch, limit=10000
            )

            merged_count = 0
            for entry in from_memories:
                # Create new memory in target branch
                new_id = self._mm.remember(
                    content=entry.content,
                    category=entry.category,
                    importance=entry.importance,
                    tags=entry.tags,
                    branch=to_branch,
                    source=f"merged_from_{from_branch}"
                )
                if new_id:
                    merged_count += 1

            return merged_count
        except Exception as e:
            logging.error(f"Failed to merge branch memories: {e}")
            return 0

    def list_branches_with_memories(self) -> List[str]:
        """List all branches that have memories."""
        try:
            with self._mm._store._get_connection() as conn:
                rows = conn.execute(
                    'SELECT DISTINCT branch FROM memories WHERE branch IS NOT NULL'
                ).fetchall()
                return [r['branch'] for r in rows if r['branch']]
        except sqlite3.Error:
            return []


class SkillRegistry:
    """Registry for managing skills."""

    def __init__(self, skills_dir: Path, tool_registry: Optional['ToolRegistry'] = None):
        self._skills: Dict[str, SkillDefinition] = {}
        self._skills_dir = skills_dir
        self._skills_dir.mkdir(parents=True, exist_ok=True)
        self._tool_registry = tool_registry
        self._load_installed_skills()

    def _load_installed_skills(self) -> None:
        """Load all installed skills from the skills directory with security checks."""
        if not self._skills_dir.exists():
            return

        for item in self._skills_dir.iterdir():
            if item.is_dir():
                # Security: Validate skill path
                valid, msg = SkillSecurityManager.validate_skill_path(item)
                if not valid:
                    logging.warning(f"Skipping skill at {item}: {msg}")
                    continue

                # Security: Verify signature if trusted keys are configured
                if not SkillSecurityManager.verify_signature(item):
                    logging.warning(f"Skill at {item} has invalid or missing signature")
                    # Continue loading but log warning

                skill = SkillDefinition.from_directory(item)
                if skill:
                    self._skills[skill.name] = skill
                    # Register skill tools
                    if self._tool_registry:
                        for tool in skill.tools:
                            self._tool_registry.register(tool)

    def install(self, source: Union[str, Path], confirm_permissions: bool = True):
        """Install a skill from a file path, URL, or skill name.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            source_path = Path(source)
            if source_path.exists() and source_path.is_dir():
                # Security: Validate path before loading
                valid, msg = SkillSecurityManager.validate_skill_path(source_path)
                if not valid:
                    return False, f"Security validation failed: {msg}"

                # Install from local directory
                skill = SkillDefinition.from_directory(source_path)
                if not skill:
                    return False, "Failed to load skill definition. Check skill.toml syntax."

                # Security: Verify signature if .signature file exists
                sig_valid = SkillSecurityManager.verify_signature(source_path)
                if not sig_valid:
                    logging.warning(f"Skill '{skill.name}' has invalid or missing signature")

                # Security: Check for required permissions
                required_perms = skill.metadata.dependencies if hasattr(skill.metadata, 'dependencies') else []
                permissions = getattr(skill, 'config_schema', {}).get('permissions', [])

                if confirm_permissions and permissions:
                    print(f"\n[yellow]Skill '{skill.name}' requests the following permissions:[/yellow]")
                    perm_descriptions = {
                        SkillSecurityManager.PERMISSION_FILE_READ: "Read files in home directory",
                        SkillSecurityManager.PERMISSION_FILE_WRITE: "Write files to disk",
                        SkillSecurityManager.PERMISSION_NETWORK: "Make network requests",
                        SkillSecurityManager.PERMISSION_SHELL: "Execute shell commands",
                        SkillSecurityManager.PERMISSION_ENV: "Access environment variables"
                    }
                    for perm in permissions:
                        desc = perm_descriptions.get(perm, perm)
                        print(f"  • {perm}: {desc}")

                    try:
                        response = input("\nGrant these permissions? [Y/n]: ").lower().strip()
                        if response not in ["", "y", "yes"]:
                            return False, "Installation cancelled by user"
                    except (EOFError, KeyboardInterrupt):
                        return False, "Installation cancelled"

                # Grant permissions to the skill
                SkillSecurityManager.set_permissions(skill.name, permissions)

                # Copy skill to installation directory
                target_dir = self._skills_dir / skill.name
                import shutil
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(source_path, target_dir, dirs_exist_ok=True)

                # Register the skill
                self._skills[skill.name] = skill

                # Register tools
                if self._tool_registry:
                    for tool in skill.tools:
                        self._tool_registry.register(tool)

                return True, f"Skill '{skill.name}' v{skill.version} installed successfully"

            # TODO: Support URL and registry installation
            return False, "Only local directory installation is currently supported"

        except Exception as e:
            logging.error(f"Failed to install skill: {e}")
            return False, f"Installation error: {e}"

    def uninstall(self, skill_name: str):
        """Uninstall a skill.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if skill_name not in self._skills:
                return False, f"Skill '{skill_name}' is not installed"

            # Unregister tools
            skill = self._skills[skill_name]
            if self._tool_registry:
                for tool in skill.tools:
                    self._tool_registry.unregister(tool.name)

            # Clean up permissions
            SkillSecurityManager.set_permissions(skill_name, [])

            # Remove directory
            skill_dir = self._skills_dir / skill_name
            if skill_dir.exists():
                import shutil
                shutil.rmtree(skill_dir)

            del self._skills[skill_name]
            return True, f"Skill '{skill_name}' uninstalled successfully"
        except Exception as e:
            logging.error(f"Failed to uninstall skill: {e}")
            return False, f"Uninstallation error: {e}"

    def get(self, skill_name: str) -> Optional[SkillDefinition]:
        """Get a skill by name."""
        return self._skills.get(skill_name)

    def list_skills(self) -> List[SkillDefinition]:
        """List all installed skills."""
        return list(self._skills.values())

    def is_installed(self, skill_name: str) -> bool:
        """Check if a skill is installed."""
        return skill_name in self._skills


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._enabled: set = set()

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            self._enabled.discard(name)

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_all(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_enabled(self) -> List[ToolDefinition]:
        """List enabled tools."""
        return [self._tools[name] for name in self._enabled if name in self._tools]

    def enable(self, name: str) -> bool:
        """Enable a tool. Returns True if successful."""
        if name in self._tools:
            self._enabled.add(name)
            return True
        return False

    def disable(self, name: str) -> None:
        """Disable a tool."""
        self._enabled.discard(name)

    def is_enabled(self, name: str) -> bool:
        """Check if a tool is enabled."""
        return name in self._enabled

    def get_schemas_for_provider(self, provider_name: str) -> List[Dict[str, Any]]:
        """Get tool schemas in provider-specific format."""
        tools = self.list_enabled()

        if provider_name == "gemini":
            return [tool.to_gemini_schema() for tool in tools]
        else:
            # OpenAI format is default (OpenAI, OpenRouter, Anthropic, Mistral)
            return [tool.to_openai_schema() for tool in tools]


# --- Built-in Tools ---
def _safe_calculator(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow basic math operators and functions
        allowed_names = {
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "log": math.log, "log10": math.log10,
            "exp": math.exp, "pow": pow, "abs": abs,
            "ceil": math.ceil, "floor": math.floor, "round": round,
            "pi": math.pi, "e": math.e
        }

        # Parse and validate AST
        tree = ast.parse(expression, mode='eval')

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in allowed_names:
                    return f"Error: Function '{getattr(node.func, 'id', str(node.func))}' is not allowed"
            elif isinstance(node, ast.Name) and node.id not in allowed_names:
                return f"Error: Unknown identifier '{node.id}'"

        result = eval(compile(tree, '<string>', 'eval'), {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def _file_read_tool(args: Dict[str, Any]) -> str:
    """Read file content with safety checks."""
    path = args.get("path", "")
    max_size = args.get("max_size", 1024 * 1024)  # 1MB default

    try:
        file_path = Path(path).resolve()

        # Security: Check for path traversal
        home = Path.home().resolve()
        cwd = Path.cwd().resolve()
        if not (str(file_path).startswith(str(home)) or str(file_path).startswith(str(cwd))):
            return f"Error: Access denied. File must be within home directory or current working directory."

        if not file_path.exists():
            return f"Error: File '{path}' not found."

        if not file_path.is_file():
            return f"Error: '{path}' is not a file."

        file_size = file_path.stat().st_size
        if file_size > max_size:
            return f"Error: File size ({file_size} bytes) exceeds maximum allowed ({max_size} bytes)."

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Add metadata
        result = f"# File: {file_path}\n# Size: {file_size} bytes\n# ---\n{content}"
        return result

    except Exception as e:
        return f"Error reading file: {str(e)}"


def _file_write_tool(args: Dict[str, Any]) -> str:
    """Write content to file with safety checks."""
    path = args.get("path", "")
    content = args.get("content", "")
    mode = args.get("mode", "write")  # write or append

    try:
        file_path = Path(path).resolve()

        # Security: Check for path traversal (same as read)
        home = Path.home().resolve()
        cwd = Path.cwd().resolve()
        if not (str(file_path).startswith(str(home)) or str(file_path).startswith(str(cwd))):
            return f"Error: Access denied. File must be within home directory or current working directory."

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists and we're in write mode
        if file_path.exists() and mode == "write":
            # Backup existing file
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())

        write_mode = 'a' if mode == "append" else 'w'
        with open(file_path, write_mode, encoding='utf-8') as f:
            f.write(content)

        action = "appended to" if mode == "append" else "written to"
        backup_info = " (backup created)" if (file_path.exists() and mode == "write" and 'backup_path' in dir()) else ""
        return f"Successfully {action} file: {file_path}{backup_info}"

    except Exception as e:
        return f"Error writing file: {str(e)}"


def _web_fetch_tool(args: Dict[str, Any]) -> str:
    """Fetch web page content."""
    url = args.get("url", "")
    max_length = args.get("max_length", 50000)

    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return "Error: Invalid URL. Must include scheme (http/https) and host."

        # Use httpx for fetching
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = client.get(url, headers=headers)
            response.raise_for_status()

            # Try to extract text content
            content_type = response.headers.get('content-type', '').lower()

            if 'text/html' in content_type:
                # Simple HTML to text conversion
                text = response.text
                # Remove script and style tags with content
                import re
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', ' ', text)
                # Normalize whitespace
                text = re.sub(r'\s+', ' ', text).strip()
            else:
                text = response.text

            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + f"\n\n... [content truncated, total length: {len(response.text)} chars]"

            title = ""
            if 'text/html' in content_type:
                title_match = re.search(r'<title[^>]*>([^<]*)</title>', response.text, re.IGNORECASE)
                if title_match:
                    title = f"Title: {title_match.group(1).strip()}\n"

            return f"# URL: {url}\n# Status: {response.status_code}\n{title}# ---\n{text}"

    except httpx.HTTPError as e:
        return f"Error fetching URL: HTTP error - {str(e)}"
    except Exception as e:
        return f"Error fetching URL: {str(e)}"


# --- AI Provider Abstraction ---
class AIProvider(ABC):
    def __init__(self, key: str):
        self.api_key = key
        transport = None
        try:
            if hasattr(httpx, '__version__'):
                version_parts = httpx.__version__.split('.')
                try:
                    major = int(version_parts[0])
                    minor = int(version_parts[1])
                    if major > 0 or (major == 0 and minor >= 23):
                        retry_transport = httpx.AsyncHTTPTransport(
                            retries=httpx.Retry(
                                total=3,
                                backoff_factor=0.1,
                                allowed_methods=["GET", "POST", "PUT", "DELETE"],
                                status_forcelist=[429, 500, 502, 503, 504],
                            )
                        )
                        transport = retry_transport
                except (ValueError, IndexError):
                    pass
        except Exception:
            pass

        self.http = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0, read=20.0, write=5.0),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
                keepalive_expiry=30.0
            ),
            http2=True,
            transport=transport
        )

    async def close(self):
        if hasattr(self, 'http') and self.http:
            await self.http.aclose()

    @property
    @abstractmethod
    def name(self) -> str: pass

    @abstractmethod
    async def get_models(self) -> Tuple[str, List[str]]: pass

    @abstractmethod
    async def stream_chat(self, msgs: List[Dict], model: str, tools: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        yield ""

    @abstractmethod
    def calculate_cost(self, p_tokens: int, c_tokens: int, model: str) -> Optional[float]: pass

    def supports_tools(self) -> bool:
        return True


class OpenAIProvider(AIProvider):
    def __init__(self, key: str, url: str, name: str="openai"): super().__init__(key); self.base_url, self._name, self.prices = url, name, {}
    @property
    def name(self) -> str: return self._name
    def supports_tools(self) -> bool: return True
    async def get_models(self) -> Tuple[str, List[str]]:
        if not self.api_key: return self.name, []
        try:
            r = await self.http.get(f"{self.base_url}/models", headers={"Authorization": f"Bearer {self.api_key}"}); r.raise_for_status()
            data = r.json().get('data', [])
            if "openrouter" in self.base_url: self.prices = {m['id']:{"input":float(m.get('pricing',{}).get('prompt',0)), "output":float(m.get('pricing',{}).get('completion',0))} for m in data}
            return self.name, sorted([m['id'] for m in data])
        except Exception: return self.name, []

    async def stream_chat(self, msgs: List[Dict], model: str, tools: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        """Stream chat response with optional tool support."""
        payload: Dict[str, Any] = {"model": model, "messages": msgs, "stream": True}

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            # Ensure model knows to use tools when appropriate
            payload["tool_choice"] = "auto"

        async with self.http.stream("POST", f"{self.base_url}/chat/completions",
                                     headers={"Authorization": f"Bearer {self.api_key}"},
                                     json=payload) as r:
            r.raise_for_status()

            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    data = line[len("data: "):].strip()
                    if data == "[DONE]": break
                    try:
                        choice = json.loads(data)["choices"][0]
                        delta = choice.get("delta", {})

                        # Check for tool calls
                        if "tool_calls" in delta:
                            # Yield a special marker for tool calls
                            tool_calls = delta["tool_calls"]
                            yield f"__TOOL_CALLS__:{json.dumps(tool_calls)}"

                        # Regular content
                        if content := delta.get("content"):
                            yield content

                        # Check finish reason
                        if choice.get("finish_reason") == "tool_calls":
                            yield "__TOOL_CALLS_COMPLETE__"

                    except (json.JSONDecodeError, IndexError):
                        continue

    def calculate_cost(self, p_tokens: int, c_tokens: int, model: str) -> Optional[float]:
        # [V2.2.1] Removed cleaning logic.
        return (p_tokens * self.prices[model]["input"] + c_tokens * self.prices[model]["output"]) if model in self.prices else None

class GeminiProvider(AIProvider):
    URL, MODELS = "https://generativelanguage.googleapis.com/v1beta/models", ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-pro"]
    @property
    def name(self) -> str: return "gemini"
    def supports_tools(self) -> bool: return True
    async def get_models(self) -> Tuple[str, List[str]]: return self.name, self.MODELS if self.api_key else []
    def _to_gemini(self, msgs: List[Dict]) -> List[Dict]:
        gemini_msgs, system_prompt = [], ""
        for msg in msgs:
            if msg["role"] == "system": system_prompt = msg["content"]
            elif msg["role"] == "user":
                # Handle tool results from function calls
                if "tool_result" in msg:
                    content = msg["content"]
                else:
                    content = f"{system_prompt}\n\n{msg['content']}" if system_prompt and not gemini_msgs else msg["content"]
                gemini_msgs.append({"role": "user", "parts": [{"text": content}]})
            elif msg["role"] == "assistant":
                # Check for function calls in assistant message
                if "tool_calls" in msg:
                    # For Gemini, we need to convert function calls back to text
                    tool_calls = msg["tool_calls"]
                    text_parts = []
                    for tc in tool_calls:
                        fn = tc.get("function", {})
                        name = fn.get("name", "")
                        args = fn.get("arguments", "")
                        text_parts.append(f"I will use the {name} tool with arguments: {args}")
                    gemini_msgs.append({"role": "model", "parts": [{"text": "\n".join(text_parts)}]})
                else:
                    gemini_msgs.append({"role": "model", "parts": [{"text": msg["content"]}]})
        return gemini_msgs

    async def stream_chat(self, msgs: List[Dict], model: str, tools: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        """Stream chat response with optional tool support."""
        url = f"{self.URL}/{model}:streamGenerateContent?key={self.api_key}&alt=sse"

        payload: Dict[str, Any] = {"contents": self._to_gemini(msgs)}

        # Add tools if provided and provider supports them
        if tools and self.supports_tools():
            # Convert OpenAI format tools to Gemini format
            gemini_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    gemini_tools.append({
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {"type": "object", "properties": {}})
                    })
            if gemini_tools:
                payload["tools"] = [{"function_declarations": gemini_tools}]
                # Enable automatic function calling
                payload["tool_config"] = {
                    "function_calling_config": {
                        "mode": "AUTO"
                    }
                }

        async with self.http.stream("POST", url, json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    try:
                        data = json.loads(line[len("data:"):].strip())
                        candidate = data.get("candidates", [{}])[0]
                        content = candidate.get("content", {})
                        parts = content.get("parts", [{}])

                        # Check for function calls
                        for part in parts:
                            if "functionCall" in part:
                                fc = part["functionCall"]
                                # Yield a special marker for tool calls
                                tool_call = {
                                    "id": f"call_{fc.get('name', 'unknown')}_{id(fc)}",
                                    "type": "function",
                                    "function": {
                                        "name": fc.get("name"),
                                        "arguments": json.dumps(fc.get("args", {}))
                                    }
                                }
                                yield f"__TOOL_CALLS__:{json.dumps([tool_call])}"

                            # Regular text content
                            if "text" in part:
                                yield part["text"]

                        # Check finish reason
                        if candidate.get("finishReason") == "STOP":
                            pass  # Normal completion
                        elif candidate.get("finishReason") == "MAX_TOKENS":
                            yield "\n[Max tokens reached]"

                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue

    def calculate_cost(self, p_tokens: int, c_tokens: int, model: str) -> Optional[float]: return None

class ProviderFactory:
    def __init__(self, config: Dict):
        self.providers: Dict[str, AIProvider] = {}
        cfg = config.get("providers", {})
        if key := cfg.get("openai_api_key"): self.providers["openai"] = OpenAIProvider(key, "https://api.openai.com/v1")
        if key := cfg.get("openrouter_api_key"): self.providers["openrouter"] = OpenAIProvider(key, "https://openrouter.ai/api/v1", "openrouter")
        if key := cfg.get("gemini_api_key"): self.providers["gemini"] = GeminiProvider(key)
        if key := cfg.get("anthropic_api_key"): self.providers["anthropic"] = OpenAIProvider(key, "https://api.anthropic.com/v1", "anthropic")
        if key := cfg.get("mistral_api_key"): self.providers["mistral"] = OpenAIProvider(key, "https://api.mistral.ai/v1", "mistral")
    def get_provider(self, model_id: str) -> Optional[AIProvider]: return self.providers.get(model_id.split('/')[0])
    def get_available_providers(self) -> List[str]: return list(self.providers.keys())

# --- Main Execution ---
async def main(): await FreeChatApp().run()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
        console.print_exception()