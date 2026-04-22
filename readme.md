# FreeChat 💬

**Your all-in-one, portable terminal AI chat tool - v2.3.0 with Memory System & Performance Optimizations**

`FreeChat` is a powerful, easy-to-deploy single-file AI chat command line tool, designed specifically for use on cloud VPS. After connecting via SSH, it provides you with a feature-rich and responsive chat interface that integrates multiple mainstream AI providers (such as OpenRouter, OpenAI, Gemini).

---

## ✨ Core Features

*   ✅ **Ultimate Simplified Deployment**: A true single-script file with no complex environment configuration required. Built-in intelligent dependency installer works out-of-the-box in a `Python 3.7+` environment.
*   📦 **Portable Mode**: Supports saving all configuration, history, and session data in a directory alongside the script, making it easy to package, backup, and migrate as a whole.
*   📡 **Multi-AI Provider Support**: Seamlessly integrates with OpenRouter, OpenAI, Gemini, NVIDIA, and more, allowing for easy switching and optimal selection.
*   🧠 **Universal Model Access**: Dynamically retrieves and connects to any model from different providers, supporting instant selection and switching directly in the CLI.
*   🎨 **Customizable AI Roles**: Easily define and switch AI system prompts through a simple configuration file, allowing it to play different roles such as programmer, translator, etc.
*   🚀 **Pure Text Streaming Interaction**: Returns real-time streaming of plain text answers, ensuring rapid response and strong compatibility.
*   📊 **Performance and Cost Visualization**: Displays token usage statistics, response time, per-call cost, and estimated total session cost in real-time on the status bar, giving you full control over costs.
*   💡 **Intelligent Command Line Experience**: Features a modern CLI with command autocompletion (Tab), history navigation (↑↓), reverse history search (Ctrl+R), and auto-suggestions.
*   ⌨️ **Modern Shortcuts**: Use `Control + Enter` to submit multi-line input, conforming to modern application habits.
*   💾 **Session Management and Export**: Supports creating, saving, and loading chat sessions, with the ability to easily export session records in Markdown, JSON, or HTML formats.
*   🎨 **Markdown Rendering Support**: Export sessions with beautifully rendered Markdown content in HTML format using the new `md-rendered` export option.
*   🧠 **Memory System with Auction Compression**: Advanced long-term memory with automatic value-based compression using auction algorithms. Supports global and Git branch-specific memories with SQLite storage and full-text search.
*   ⚡ **Performance Optimizations**: Includes connection pooling, model caching, token counting optimization, and memory management for faster response times and reduced resource usage.

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

## 🧠 Memory System

FreeChat includes an advanced memory system for long-term context preservation across sessions. This system uses SQLite for efficient storage with full-text search capabilities and implements intelligent auction-based compression to manage storage limits.

### Core Features

- **Global and Branch-Specific Memories**: Support global memory storage or associate memories with specific Git branches for context-aware branch switching
- **Automatic Value Scoring**: Calculates comprehensive scores for each memory based on importance, relevance, recency, and access frequency
- **Auction Compression Mechanism**: Automatically compresses or archives low-value memories when storage limits are reached
- **Full-Text Search**: Fast memory retrieval based on SQLite FTS5
- **Git Integration**: Automatic detection of Git branch switches to load corresponding branch-specific memories

### Memory Commands

```bash
# Store a new memory
> /memory remember "User prefers Python over JavaScript"
✓ Recorded (mem_abc123)

# Search memories
> /memory recall "programming preferences"
[Displays matching memories]

# List all memories (with scores)
> /memory list
ID       Category    Content                           Score    Access
mem_abc  preference  User prefers dark mode interface   0.85     5
...

# Run auction compression
> /memory compress
✓ Compressed 15 memories (archived low-value memories)

# View statistics
> /memory stats
Total memories: 42
Active: 37 | Archived: 5
Average score: 0.72

# Show branch-specific memories
> /memory branch feature/new-ui
[Displays memories for feature/new-ui branch]
```

### Storage

Memories are stored in an SQLite database at `~/.config/freechat/memories/memories.db` (or `freechat_config/memories/memories.db` in portable mode). The database includes:

- Main `memories` table with full-text search index
- `memory_tags` table for tag management
- FTS5 virtual table for efficient content search
- Automatic triggers to keep search indexes synchronized

### Auction Algorithm

The auction-based compression uses weighted scoring:

- **Importance** (40%): User-specified importance (1-10)
- **Relevance** (30%): Based on tag richness
- **Recency** (20%): Exponential decay (half-life 30 days)
- **Frequency** (10%): Normalized access count

Memories below the storage limit threshold are compressed or archived to maintain optimal memory performance.

---

## 🛠️ Skill System

FreeChat includes a powerful Skill system that allows you to extend functionality through installable skill packages. Skills can provide custom tools that AI can use to help answer your questions.

### Skill Package Structure

A skill package is a directory containing:

```
my_skill/
├── skill.toml          # Skill metadata (required)
└── README.md           # Documentation (optional)
```

### Creating a Skill

Create a `skill.toml` file:

```toml
[skill]
name = "weather-skill"
version = "1.0.0"
description = "Get weather information for any city"
author = "Your Name"
entry_point = "main:initialize"
dependencies = []

[[tools]]
name = "get_weather"
description = "Get current weather for a city"
parameters = [
    { name = "city", type = "string", required = true, description = "City name" },
    { name = "units", type = "string", required = false, description = "Temperature units (celsius/fahrenheit)" }
]
```

### Skill Commands

#### Install a Skill

```bash
> /skill install /path/to/your_skill
✓ Skill 'weather-skill' v1.0.0 installed successfully
```

#### List Installed Skills

```bash
> /skill list
Name          Version  Description                    Tools
weather-skill 1.0.0    Get weather information        1
example-skill 1.0.0    An example skill               2
```

#### View Skill Information

```bash
> /skill info weather-skill
╭──────────────────── Skill Information ─────────────────────╮
│ weather-skill v1.0.0                                        │
│ Author: Your Name                                           │
│ Description: Get weather information for any city           │
│ Tools: get_weather                                          │
╰─────────────────────────────────────────────────────────────╯
```

#### Uninstall a Skill

```bash
> /skill uninstall weather-skill
✓ Skill 'weather-skill' uninstalled successfully
```

### Using Skills in Conversation

Once a skill is installed, its tools are automatically available to the AI. You don't need to do anything special - just chat naturally:

```bash
> 北京今天天气怎么样？
[AI will automatically use the get_weather tool with city=

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

### Memory System

FreeChat includes an advanced memory system for long-term context preservation across sessions.

**Memory Commands:**
- `/memory remember <text>` - Store a new memory with automatic categorization
- `/memory recall <query>` - Search memories using full-text search
- `/memory list` - List all memories with value scores and access counts
- `/memory forget <id>` - Delete a specific memory by ID
- `/memory compress` - Run auction-based compression to archive low-value memories
- `/memory stats` - Display memory statistics
- `/memory branch <name>` - Show memories specific to a Git branch

The memory system uses SQLite with FTS5 full-text search and implements an auction algorithm for intelligent compression based on importance, relevance, recency, and access frequency.

### Markdown Rendering Support

FreeChat now supports exporting sessions with rendered Markdown content. When you use the `/export md-rendered` command, it will generate an HTML file with properly formatted Markdown content, including bold text, italic text, code blocks, and other Markdown elements rendered in a visually appealing way.

### ⌨️ Command Reference

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/help` | (none) | Display this help message. |
| `/model` | (none) | Show the current model with detailed information (provider, status, favorites). |
| | `<provider/model_name>` | Switch the currently used AI model. Example: `/model openai/gpt-4o`. Automatically records to recent models. |
| | `list` | List all available models from all configured providers. |
| | `list <provider>` | List models from a specific provider (e.g., `/model list openai`). |
| | `search <keyword>` | Search models by keyword across all providers. |
| | `info <name>` | Show detailed information about a model, including pricing (if available). |
| | `recent` | Display recently used models (up to 10). |
| | `fav` | Display your favorite models list. |
| | `fav <name>` | Add or remove a model from favorites. |
| `/prompt`| `list` | Lists all available system prompts defined in `prompts.toml`. |
| | `view` | View the full content of the currently used system prompt. |
| | `<name>` | Switch to the specified system prompt and automatically start a new session. Example: `/prompt coder`. |
| `/session`| `new` | Start a completely new chat session with the default system prompt applied. |
| | `save <name>` | Save the current session with a name. |
| | `load <name>` | Load a previously saved session. |
| | `list` | List all saved sessions. |
| `/file` | `upload <path>` | Upload and process a file. Supported formats: txt, md, json, csv, py, js, html, css, pdf. |
| `/language` | `<code>` | Switch interface language. Use without arguments to list available languages. |
| `/export` | `<format>` | Export the current session to a file in the specified format. Supported formats: `md`, `json`, `html`, `md-rendered`. |
| `/clear` | (none) | Clear the current terminal screen. |
| `/exit` | (none) | Exit the FreeChat application. |
| `/memory` | `remember <text>` | Store a new memory with automatic categorization. |
| | `recall <query>` | Search memories using full-text search. |
| | `list [branch]` | List all memories with value scores and access counts. |
| | `forget <id>` | Delete a specific memory by ID. |
| | `compress` | Run auction-based compression to archive low-value memories. |
| | `stats` | Display memory statistics including total, active, and archived counts. |
| | `branch <name>` | Show memories specific to a Git branch. |
| `/skill` | `list` | List all installed skills. |
| | `install <path>` | Install a skill from a local directory. |
| | `uninstall <name>` | Remove an installed skill. |
| | `info <name>` | Display detailed information about a skill. |

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
default_model = "openrouter/openrouter/free"

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

# Anthropic: https://console.anthropic.com/settings/keys
anthropic_api_key = ""

# Mistral: https://console.mistral.ai/api-keys
mistral_api_key = ""

# NVIDIA: https://build.nvidia.com/explore/discover
nvidia_api_key = ""
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

## 🚀 Deployment Options

### Docker Deployment

FreeChat can be deployed using Docker for easier management and isolation.

**Steps to deploy with Docker:**

1. **Build the Docker image**
   ```bash
   docker build -t freechat .
   ```

2. **Run the Docker container**
   ```bash
   docker run -it --name freechat -v ./freechat_config:/app/freechat_config freechat
   ```

3. **Using docker-compose**
   ```bash
   docker-compose up -d
   docker-compose exec freechat python freechat.py
   ```

### System Service Installation

FreeChat can be installed as a system service using systemd.

**Steps to install as a system service:**

1. **Edit the service file**
   ```bash
   nano freechat.service
   ```
   Replace `your_username` with your actual username and `/path/to/freechat` with the actual path to your FreeChat installation.

2. **Copy the service file**
   ```bash
   sudo cp freechat.service /etc/systemd/system/
   ```

3. **Reload systemd and start the service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable freechat
   sudo systemctl start freechat
   ```

4. **Check the service status**
   ```bash
   sudo systemctl status freechat
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

*   **Q: How to run FreeChat in Docker?**  
    A: Follow the Docker deployment instructions in the Deployment Options section.

*   **Q: How to install FreeChat as a system service?**  
    A: Follow the system service installation instructions in the Deployment Options section.

## 📄 License

This project is licensed under the [GNU General Public License v3.0](LICENSE).