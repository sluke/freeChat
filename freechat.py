#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FreeChat: A powerful, single-file AI chat CLI for your VPS.

Author: AI Assistant (Generated for User Task)
Version: 2.2.22 (Stable)
License: MIT
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
        print("\nUpgrading pip..."); subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print(f"Installing {len(missing)} packages..."); subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
        print("\n[OK] Dependencies installed. Restarting in 2s..."); time.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except (subprocess.CalledProcessError, KeyboardInterrupt, EOFError) as e: print(f"\n[ERROR] Installation failed: {e}", file=sys.stderr); sys.exit(1)

bootstrap()
# --- End of Bootstrap ---

# --- Main Application Imports ---
import asyncio, json, re, logging
from collections import OrderedDict
from pathlib import Path
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple, Callable
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
        self.current_model: str = self.config.get("general", {}).get("default_model", "openrouter/stepfun/step-3.5-flash:free")
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
default_model = "openrouter/stepfun/step-3.5-flash:free"
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
        banner = Text("FreeChat v2.2.22 (Stable)", style="bold magenta", justify="center")
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
  [cyan]/language <code>[/cyan]       Switch interface language. Use without arguments to list available languages.
  [cyan]/export <format>[/cyan]       Export session: [dim]md, json, html, md-rendered[/dim].
  [cyan]/clear[/cyan]                 Clear the terminal screen.
  [cyan]/exit[/cyan]                  Exit the application.
[bold]Usage:[/bold]
- Type a message and press [bold]Control or Command + Enter[/bold] to send.
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
        if not args: self.console.print(f"[yellow]Current model: {self.current_model}. Usage: /model <name>[/yellow]"); return
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
        except httpx.HTTPStatusError as e: self.console.print(f"\n[bold red]API Error {e.response.status_code}:[/bold red] {e.response.text}"); self.session_messages.pop(); return
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

# --- AI Provider Abstraction ---
class AIProvider(ABC):
    def __init__(self, key: str): 
        self.api_key = key
        # Add retry mechanism for HTTP requests if available
        transport = None
        try:
            # Check if httpx version is >= 0.23.0
            if hasattr(httpx, '__version__'):
                version_parts = httpx.__version__.split('.')
                try:
                    major = int(version_parts[0])
                    minor = int(version_parts[1])
                    if major > 0 or (major == 0 and minor >= 23):
                        # Retry is available in httpx >= 0.23.0
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
                    # Invalid version format, skip retry
                    pass
        except Exception:
            # Fall back to default transport if retry mechanism is not available
            pass
        
        self.http = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0, read=20.0, write=5.0),
            limits=httpx.Limits(
                max_connections=20,  # Increased for better parallelism
                max_keepalive_connections=10,  # Increased for better reuse
                keepalive_expiry=30.0  # Keep connections alive longer
            ),
            http2=True,
            transport=transport
        )
    
    async def close(self):
        """Close the HTTP client to free resources."""
        if hasattr(self, 'http') and self.http:
            await self.http.aclose()
    @property
    @abstractmethod
    def name(self) -> str: pass
    @abstractmethod
    async def get_models(self) -> Tuple[str, List[str]]: pass
    @abstractmethod
    async def stream_chat(self, msgs: List[Dict], model: str) -> AsyncGenerator[str, None]:
        yield ""  # Abstract: subclasses should override and yield str chunks
    @abstractmethod
    def calculate_cost(self, p_tokens: int, c_tokens: int, model: str) -> Optional[float]: pass

class OpenAIProvider(AIProvider):
    def __init__(self, key: str, url: str, name: str="openai"): super().__init__(key); self.base_url, self._name, self.prices = url, name, {}
    @property
    def name(self) -> str: return self._name
    async def get_models(self) -> Tuple[str, List[str]]:
        if not self.api_key: return self.name, []
        try:
            r = await self.http.get(f"{self.base_url}/models", headers={"Authorization": f"Bearer {self.api_key}"}); r.raise_for_status()
            data = r.json().get('data', [])
            if "openrouter" in self.base_url: self.prices = {m['id']:{"input":float(m.get('pricing',{}).get('prompt',0)), "output":float(m.get('pricing',{}).get('completion',0))} for m in data}
            return self.name, sorted([m['id'] for m in data])
        except Exception: return self.name, []
    async def stream_chat(self, msgs: List[Dict], model: str) -> AsyncGenerator[str, None]:
        payload = {"model": model, "messages": msgs, "stream": True}
        async with self.http.stream("POST", f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    data = line[len("data: "):].strip()
                    if data == "[DONE]": break
                    try:
                        if content := json.loads(data)["choices"][0]["delta"].get("content"): yield content
                    except (json.JSONDecodeError, IndexError): continue
    def calculate_cost(self, p_tokens: int, c_tokens: int, model: str) -> Optional[float]:
        # [V2.2.1] Removed cleaning logic.
        return (p_tokens * self.prices[model]["input"] + c_tokens * self.prices[model]["output"]) if model in self.prices else None

class GeminiProvider(AIProvider):
    URL, MODELS = "https://generativelanguage.googleapis.com/v1beta/models", ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-pro"]
    @property
    def name(self) -> str: return "gemini"
    async def get_models(self) -> Tuple[str, List[str]]: return self.name, self.MODELS if self.api_key else []
    def _to_gemini(self, msgs: List[Dict]) -> List[Dict]:
        gemini_msgs, system_prompt = [], ""
        for msg in msgs:
            if msg["role"] == "system": system_prompt = msg["content"]
            elif msg["role"] == "user":
                content = f"{system_prompt}\n\n{msg['content']}" if system_prompt and not gemini_msgs else msg["content"]
                gemini_msgs.append({"role": "user", "parts": [{"text": content}]})
            elif msg["role"] == "assistant": gemini_msgs.append({"role": "model", "parts": [{"text": msg["content"]}]})
        return gemini_msgs
    async def stream_chat(self, msgs: List[Dict], model: str) -> AsyncGenerator[str, None]:
        url = f"{self.URL}/{model}:streamGenerateContent?key={self.api_key}&alt=sse"
        async with self.http.stream("POST", url, json={"contents": self._to_gemini(msgs)}) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    try:
                        if text := json.loads(line[len("data:"):].strip())["candidates"][0]["content"]["parts"][0]["text"]: yield text
                    except (json.JSONDecodeError, IndexError, KeyError): continue
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