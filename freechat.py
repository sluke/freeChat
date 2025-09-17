#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FreeChat: A powerful, single-file AI chat CLI for your VPS.
This version removes the smart model name cleaning logic.

Author: AI Assistant (Generated for User Task)
Version: 2.2.2 (Stable)
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
    required = {"prompt_toolkit": "prompt_toolkit>=3.0", "rich": "rich>=13.0", "httpx": "httpx[http2]>=0.25", "tiktoken": "tiktoken>=0.5"}
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
import asyncio, json, re
from pathlib import Path
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple, Callable
if sys.version_info >= (3, 11): import tomllib
else: import tomli as tomllib
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
        self.current_model: str = self.config.get("general", {}).get("default_model", "openrouter/deepseek/deepseek-chat-v3.1:free")
        self.session_messages: List[Dict[str, Any]] = []
        self.session_cost: float = 0.0
        self.session_name: Optional[str] = None
        self.available_models: Dict[str, List[str]] = {}
        self.provider_factory = ProviderFactory(self.config)
        try: self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception: self.tokenizer = None; self.console.print("[yellow]Warning:[/] `tiktoken` not found. Token counts approximate.")
        self.commands: Dict[str, Callable] = {
            "/help": self._display_help, "/model": self._handle_model_command,
            "/prompt": self._handle_prompt_command,
            "/session": self._handle_session_command, "/export": self._handle_export_command,
            "/clear": lambda args: self.console.clear(), "/exit": self._exit_app,
        }
        
        bindings = KeyBindings();
        @bindings.add("c-j")
        @bindings.add("c-m")
        def _(event): event.current_buffer.validate_and_handle()
            
        self.prompt_session = PromptSession(history=FileHistory(str(self.history_path)), multiline=True, auto_suggest=AutoSuggestFromHistory(), key_bindings=bindings)
        self.style = Style.from_dict({'bottom-toolbar': '#ffffff bg:#333333'})
        
        self._apply_prompt(self.default_prompt_name, is_startup=True)

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
default_model = "openrouter/deepseek/deepseek-chat-v3.1:free"
default_prompt = "default"
[providers]
openai_api_key = ""
openrouter_api_key = ""
gemini_api_key = ""
"""
            with open(self.config_path, "w", encoding="utf-8") as f: f.write(default_config.strip() + "\n")
            self.console.print(f"[bold green]✓ Main config created at: {self.config_path}[/bold green]")

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
        
        if first_run:
            self.console.print("[bold yellow]! Please add API keys to config.toml and restart.[/bold yellow]")
            sys.exit(0)

    def _load_config(self, path: Path) -> Dict[str, Any]:
        if not path.exists(): return {}
        try:
            with open(path, "rb") as f: return tomllib.load(f)
        except tomllib.TOMLDecodeError as e: self.console.print(f"[bold red]Error: Invalid config file '{path}': {e}[/bold red]"); sys.exit(1)

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

    async def _fetch_models(self):
        self.console.print("[dim]Fetching available models...[/dim]")
        tasks = [p.get_models() for n in self.provider_factory.get_available_providers() if (p := self.provider_factory.get_provider(f"{n}/any"))]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, tuple): self.available_models[r[0]] = r[1]
            elif isinstance(r, Exception): self.console.print(f"[yellow]Warning: Failed to fetch models: {r}[/yellow]")

    def _get_bottom_toolbar(self) -> FormattedText:
        text = f"Prompt: {self.active_prompt_name} | Model: {self.current_model} | Cost: ${self.session_cost:.4f} | (Ctrl+Enter)"
        return [("class:bottom-toolbar", text)]

    def _create_completer(self) -> FuzzyCompleter:
        cmds = list(self.commands.keys())
        models = [f"{p}/{m}" for p, ml in self.available_models.items() for m in ml]
        prompts = list(self.prompts.keys())
        return FuzzyCompleter(WordCompleter(cmds + models + prompts, ignore_case=True))

    def _display_welcome(self):
        banner = Text("FreeChat v2.2.1 (Stable)", style="bold magenta", justify="center")
        info = Text("Type /help for commands, /exit to quit. Press Control or Command + Enter to send.", style="dim", justify="center")
        self.console.print(Panel.fit(Text.assemble(banner, "\n", info), padding=(1, 4)))
        
    async def _display_help(self, args: List[str]):
        help_text = """[bold]Welcome to FreeChat! ✨[/bold]
[bold]Commands:[/bold]
  [cyan]/help[/cyan]                  Show this help message.
  [cyan]/model <name>[/cyan]          Switch AI model.
  [cyan]/prompt <action>[/cyan]        Manage system prompts: [dim]list, view, <name>[/dim].
  [cyan]/session new[/cyan]           Start a new chat session with the default prompt.
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
            self.current_model = new_model
            self.console.print(f"[bold green]✓ Switched model to: {self.current_model}[/bold green]")
        else: self.console.print(f"[bold red]Error: Provider for '{new_model}' not found.[/bold red]")

    async def _handle_session_command(self, args: List[str]):
        if not args or args[0] != 'new': self.console.print("[yellow]Usage: /session new[/yellow]"); return
        self._apply_prompt(self.default_prompt_name)
        self.console.print(f"[bold green]✓ New session started with default prompt '{self.default_prompt_name}'.[/bold green]")
        
    async def _handle_export_command(self, args: List[str]):
        if not args: self.console.print("[yellow]Usage: /export <md|json|html|md-rendered>[/yellow]"); return
        fmt = args[0].lower(); filename = f"freechat_session_{self.session_name or int(time.time())}.{fmt if fmt != 'md-rendered' else 'html'}"
        try:
            if fmt == "md":
                content = "".join(f"**{'You' if m['role']=='user' else 'AI'}:**\n\n{m['content']}\n\n---\n\n" for m in self.session_messages if m['role'] != 'system')
                with open(self.sessions_dir.parent / filename, "w", encoding="utf-8") as f: f.write(content)
            elif fmt == "json":
                with open(self.sessions_dir.parent / filename, "w", encoding="utf-8") as f: json.dump(self.session_messages, f, ensure_ascii=False, indent=2)
            elif fmt == "html": self.console.save_html(str(self.sessions_dir.parent / filename), clear_console=False)
            elif fmt == "md-rendered":
                # Create HTML file with rendered Markdown content
                from rich.markdown import Markdown
                from rich.console import Console as RichConsole
                from io import StringIO
                
                # Create a string buffer to capture rendered output
                buffer = StringIO()
                # Create a console that outputs to the buffer
                render_console = RichConsole(file=buffer, width=80, force_terminal=False, force_interactive=False)
                
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
                        rendered_content = rendered_content.replace('&', '&').replace('<', '<').replace('>', '>')
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
        prompt_tokens = len(self.tokenizer.encode(prompt)) if self.tokenizer else 0
        
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
        cost = provider.calculate_cost(prompt_tokens, len(self.tokenizer.encode(full_response)) if self.tokenizer else 0, model_name)
        if cost is not None: self.session_cost += cost
        self.console.print(f"[dim]Time: {(time.time() - start_time):.2f}s | Cost: {'N/A' if cost is None else f'${cost:.6f}'}[/dim]")
        
    async def run(self):
        self._display_welcome(); await self._fetch_models()
        while True:
            try:
                inp = await self.prompt_session.prompt_async(">", bottom_toolbar=self._get_bottom_toolbar, style=self.style, completer=self._create_completer(), refresh_interval=0.5)
                if inp.strip(): await (self._handle_command if inp.startswith('/') else self._handle_prompt)(inp)
            except (EOFError, KeyboardInterrupt): self.console.print("\n[bold]Goodbye![/bold]"); return

# --- AI Provider Abstraction ---
class AIProvider(ABC):
    def __init__(self, key: str): self.api_key, self.http = key, httpx.AsyncClient(timeout=120.0)
    @property
    @abstractmethod
    def name(self) -> str: pass
    @abstractmethod
    async def get_models(self) -> Tuple[str, List[str]]: pass
    @abstractmethod
    async def stream_chat(self, msgs: List[Dict], model: str) -> AsyncGenerator[str, None]: yield
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
    def calculate_cost(self, p_tok: int, c_tok: int, model: str) -> Optional[float]:
        # [V2.2.1] Removed cleaning logic.
        return (p_tok * self.prices[model]["input"] + c_tok * self.prices[model]["output"]) if model in self.prices else None

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
    def calculate_cost(self, p_tok: int, c_tok: int, model: str) -> Optional[float]: return None

class ProviderFactory:
    def __init__(self, config: Dict):
        self.providers: Dict[str, AIProvider] = {}
        cfg = config.get("providers", {})
        if key := cfg.get("openai_api_key"): self.providers["openai"] = OpenAIProvider(key, "https://api.openai.com/v1")
        if key := cfg.get("openrouter_api_key"): self.providers["openrouter"] = OpenAIProvider(key, "https://openrouter.ai/api/v1", "openrouter")
        if key := cfg.get("gemini_api_key"): self.providers["gemini"] = GeminiProvider(key)
    def get_provider(self, model_id: str) -> Optional[AIProvider]: return self.providers.get(model_id.split('/')[0])
    def get_available_providers(self) -> List[str]: return list(self.providers.keys())

# --- Main Execution ---
async def main(): await FreeChatApp().run()
if __name__ == "__main__":
    try: asyncio.run(main())
    except Exception: Console().print_exception()