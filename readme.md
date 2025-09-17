# FreeChat 💬

**Your all-in-one, portable terminal AI chat tool - v2.2.2 with Markdown Rendering Support**

`FreeChat` is a powerful, easy-to-deploy single-file AI chat command line tool, designed specifically for use on cloud VPS. After connecting via SSH, it provides you with a feature-rich and responsive chat interface that integrates multiple mainstream AI providers (such as OpenRouter, OpenAI, Gemini).

---

## ✨ Core Features

*   ✅ **Ultimate Simplified Deployment**: A true single-script file with no complex environment configuration required. Built-in intelligent dependency installer works out-of-the-box in a `Python 3.7+` environment.
*   📦 **Portable Mode**: Supports saving all configuration, history, and session data in a directory alongside the script, making it easy to package, backup, and migrate as a whole.
*   📡 **Multi-AI Provider Support**: Seamlessly integrates with OpenRouter, OpenAI, Gemini, and more, allowing for easy switching and optimal selection.
*   🧠 **Universal Model Access**: Dynamically retrieves and connects to any model from different providers, supporting instant selection and switching directly in the CLI.
*   🎨 **Customizable AI Roles**: Easily define and switch AI system prompts through a simple configuration file, allowing it to play different roles such as programmer, translator, etc.
*   🚀 **Pure Text Streaming Interaction**: Returns real-time streaming of plain text answers, ensuring rapid response and strong compatibility.
*   📊 **Performance and Cost Visualization**: Displays token usage statistics, response time, per-call cost, and estimated total session cost in real-time on the status bar, giving you full control over costs.
*   💡 **Intelligent Command Line Experience**: Features a modern CLI with command autocompletion (Tab), history navigation (↑↓), reverse history search (Ctrl+R), and auto-suggestions.
*   ⌨️ **Modern Shortcuts**: Use `Control + Enter` to submit multi-line input, conforming to modern application habits.
*   💾 **Session Management and Export**: Supports creating, saving, and loading chat sessions, with the ability to easily export session records in Markdown, JSON, or HTML formats.
*   🎨 **Markdown Rendering Support**: Export sessions with beautifully rendered Markdown content in HTML format using the new `md-rendered` export option.

## 🚀 Installation and Setup

`FreeChat` is designed to be "out-of-the-box." You only need a Linux environment with `Python 3.7+` and `pip` installed.

**Get started in just 4 steps:**

1.  **Download the script**  
    Download the latest script file `freechat.py` to your VPS.
    ```bash
    wget <URL_to_your_script>/freechat.py
    ```

2.  **First run (automatic dependency installation)**  
    Run the script directly with Python 3. It will automatically detect missing dependencies and prompt you to install them.
    ```bash
    python3 freechat.py
    ```
    When you see the prompt `Do you want to proceed with the installation? [Y/n]:`, press `Enter` or type `y`. The script will automatically complete the installation and restart.

3.  **Configure API Keys (critical step)**  
    After dependencies are installed, the script will detect that there's no configuration file and automatically create `config.toml` and `prompts.toml` files in the default location `~/.config/freechat/`.
    
    You need to edit the main configuration file and enter your API keys.
    ```bash
    nano ~/.config/freechat/config.toml
    ```
    Fill in the API Key you obtained from platforms like OpenAI, OpenRouter, etc., following the comments in the file.

4.  **Run again and start chatting!**  
    After configuration, run the script again to enter the chat interface.
    ```bash
    python3 freechat.py
    ```

---

## 📁 Configuration File Address Management (Global vs. Portable)

`FreeChat` supports two configuration modes that you can easily switch between **without modifying any code**.

### Mode One: Global Mode (Default)

By default, `FreeChat` stores all configuration files and data in the standard location under your user's home directory:
*   **Address**: `~/.config/freechat/`

This is the recommended approach for Linux applications, keeping your home directory organized.

### Mode Two: Portable Mode (Recommended for Backup and Migration)

If you want to keep all configuration (API keys, prompts), history, and session data together with the script file for easy packaging and backup, you can activate portable mode.

**How to activate portable mode:**

Very simple. Just create a folder named `freechat_config` in the **same directory** as the `freechat.py` script.

```bash
# Assuming freechat.py is in /home/user/my_apps/ directory
cd /home/user/my_apps/

# Create configuration folder
mkdir freechat_config
```

Now your directory structure looks like this:
```
my_apps/
├── freechat.py
└── freechat_config/   <-- The existence of this folder activates portable mode
```

When you run `python3 freechat.py` again, it will automatically detect this folder and redirect all data read/write operations here. If it's the first run, it will create files like `config.toml` here.

**Migrating from global mode to portable mode:**

If you want to migrate existing global configuration to portable mode, simply move the contents of the old directory to the new directory:
```bash
# Make sure the freechat_config folder has been created
mv ~/.config/freechat/* /path/to/your/script/freechat_config/
```

---

## 📖 Usage Guide

*   **Normal Chat**: Simply type your question after the `>` prompt and press `Control + Enter` to send.
*   **Using Commands**: All special functions are implemented through commands starting with a slash `/`. Type `/` and press the `Tab` key to view and autocomplete all available commands.
*   **View Help**: Type `/help` at any time within the application to see the command list.

### New Feature: Markdown Rendering Support

FreeChat now supports exporting sessions with rendered Markdown content. When you use the `/export md-rendered` command, it will generate an HTML file with properly formatted Markdown content, including bold text, italic text, code blocks, and other Markdown elements rendered in a visually appealing way.

### ⌨️ Command Reference

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/help` | (none) | Display this help message. |
| `/model` | `<provider/model_name>` | Switch the currently used AI model. Example: `/model openai/gpt-4o`. Without parameters, shows current model. |
| `/prompt`| `list` | Lists all available system prompts defined in `prompts.toml`. |
| | `view` | View the full content of the currently used system prompt. |
| | `<name>` | Switch to the specified system prompt and automatically start a new session. Example: `/prompt coder`. |
| `/session`| `new` | Start a completely new chat session with the default system prompt applied. |
| `/export` | `<format>` | Export the current session to a file in the specified format. Supported formats: `md`, `json`, `html`, `md-rendered`. |
| `/clear` | (none) | Clear the current terminal screen. |
| `/exit` | (none) | Exit the FreeChat application. |

---

## ⚙️ Configuration Files Explained

`FreeChat` uses two configuration files that are automatically created on the first run.

### 1. Main Configuration File: `config.toml`

This file stores your API keys and general settings.

```toml
# FreeChat Main Configuration

[general]
# Set the model to load by default at startup.
# Format is "provider_name/model_identifier".
default_model = "openrouter/meta-llama/llama-3-8b-instruct:free"

# Set the system prompt name to load by default at startup. This name corresponds to an entry in prompts.toml.
default_prompt = "default"

[providers]
# Enter your API keys here.

# OpenAI: https://platform.openai.com/api-keys
openai_api_key = ""

# OpenRouter.ai: https://openrouter.ai/keys (recommended, includes many free models)
openrouter_api_key = ""

# Google Gemini: https://aistudio.google.com/app/apikey
gemini_api_key = ""
```

### 2. System Prompts File: `prompts.toml`

This file allows you to define multiple AI roles or instruction sets.

```toml
# FreeChat System Prompts
# Define different roles or instructions for the AI here.
# Switch between them in the app using the /prompt <name> command.
# TOML format supports using triple quotes to define multi-line strings.

[default]
prompt = """You are FreeChat, a helpful and concise AI assistant running in a terminal."""

[coder]
prompt = """You are an expert programmer. Provide only code solutions."""

[translator]
prompt = """You are a multilingual translator. Your task is to translate the user's text into English."""
```

## 🤔 Frequently Asked Questions (FAQ)

*   **Q: Error `INCOMPATIBLE PYTHON VERSION` on startup.**  
    A: `FreeChat` requires Python 3.7 or higher. Your system's Python version is too old. It's recommended to install a newer Python version using tools like `pyenv`.

*   **Q: `HTTP Error 401 Unauthorized` during chat.**  
    A: Your API key is incorrect. Please check that the `api_key` in the `config.toml` file is filled in correctly.

*   **Q: `HTTP Error 429 Too Many Requests` during chat.**  
    A: You have reached the service provider's rate limit or usage quota. Please log in to the service provider's platform to check your account status.

*   **Q: Can I add new AI providers?**  
    A: Absolutely. The script's `AIProvider` abstract class is designed for easy extension. You just need to create a subclass for the new API, referring to the implementation of `OpenAIProvider` or `GeminiProvider`.

## 📄 License

This project is licensed under the [MIT License](LICENSE).