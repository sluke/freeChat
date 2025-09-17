# FreeChat 💬

**您的全功能、便携式终端 AI 聊天利器 - v2.2.1 支持 Markdown 渲染**

`FreeChat` 是一个功能强大、部署简单的单文件 AI 聊天命令行工具，专为在云端 VPS 上使用而设计。通过 SSH 连接后，它为您提供一个集成了多个主流 AI 提供商（如 OpenRouter, OpenAI, Gemini）的、功能丰富且响应迅速的聊天界面。

---

## ✨ 核心特性

*   ✅ **极致简化部署**: 真正的单脚本文件，无需复杂的环境配置。内置智能依赖安装程序，在 `Python 3.7+` 环境下开箱即用。
*   📦 **便携模式**: 支持将所有配置、历史记录和会话数据保存在脚本旁边的目录中，方便整体打包、备份与迁移。
*   📡 **多 AI 提供商支持**: 无缝集成 OpenRouter, OpenAI, Gemini 等，轻松切换，择优而用。
*   🧠 **通用模型接入**: 动态获取并连接不同提供商的任意模型，支持在 CLI 中即时选择与切换。
*   🎨 **可定制的 AI 角色**: 通过简单的配置文件，轻松定义和切换 AI 的系统提示 (System Prompt)，让它扮演程序员、翻译官等不同角色。
*   🚀 **纯文本流式交互**: 实时流式返回纯文本答案，响应迅速，兼容性强。
*   📊 **性能与计费可视化**: 在状态栏实时显示 Token 使用统计、响应时长、单次调用费用及会话总费用估算，成本尽在掌握。
*   💡 **智能命令行体验**: 拥有现代化的 CLI 功能，包括命令自动补全（Tab）、历史记录导航（↑↓）、反向历史搜索（Ctrl+R）和自动建议。
*   ⌨️ **现代快捷键**: 使用 `Control + Enter` 提交多行输入，符合现代应用习惯。
*   💾 **会话管理与导出**: 支持新建、保存和加载聊天会話，并可轻松将会话记录导出为 Markdown, JSON 或 HTML 格式。
*   🎨 **Markdown 渲染支持**: 使用新的 `md-rendered` 导出选项，以美观的格式导出带有渲染 Markdown 内容的会话。

## 🚀 安装与设置

`FreeChat` 的设计理念是“开箱即用”。您只需要一个安装了 `Python 3.7+` 和 `pip` 的 Linux 环境。

**只需 4 步即可开始：**

1.  **下载脚本**  
    将最新的脚本文件 `freechat.py` 下载到您的 VPS。
    ```bash
    wget <URL_to_your_script>/freechat.py
    ```

2.  **首次运行 (自动安装依赖)**  
    直接使用 Python 3 运行脚本。它会自动检测缺失的依赖库，并提示您进行安装。
    ```bash
    python3 freechat.py
    ```
    当看到提示 `Do you want to proceed with the installation? [Y/n]:` 时，按 `Enter` 或输入 `y` 即可。脚本会自动完成安装并重启。

3.  **配置 API 密钥 (关键步骤)**  
    依赖安装完成后，脚本会检测到没有配置文件，并自动在默认位置 `~/.config/freechat/` 创建 `config.toml` 和 `prompts.toml` 文件。
    
    您需要编辑主配置文件，填入您的 API 密钥。
    ```bash
    nano ~/.config/freechat/config.toml
    ```
    根据文件内的注释，填入您从 OpenAI, OpenRouter 等平台获取的 API Key。

4.  **再次运行，开始聊天！**  
    配置完成后，再次运行脚本，即可进入聊天界面。
    ```bash
    python3 freechat.py
    ```

---

## 📁 配置文件地址管理 (全局 vs. 便携)

`FreeChat` 支持两种配置模式，您**无需修改任何代码**即可轻松切换。

### 模式一: 全局模式 (默认)

默认情况下，`FreeChat` 会将所有配置文件和数据存储在您的用户主目录下的标准位置：
*   **地址**: `~/.config/freechat/`

这是 Linux 应用的推荐做法，可以保持您的主目录整洁。

### 模式二: 便携模式 (推荐用于备份和迁移)

如果您希望将所有配置（API密钥、Prompts）、历史记录和会话数据与脚本文件放在一起，方便整体打包备份，可以激活便携模式。

**如何激活便携模式:**

非常简单，只需在 `freechat.py` 脚本所在的**同一个目录**下，创建一个名为 `freechat_config` 的文件夹即可。

```bash
# 假设 freechat.py 在 /home/user/my_apps/ 目录下
cd /home/user/my_apps/

# 创建配置文件夹
mkdir freechat_config
```

现在，您的目录结构如下：
```
my_apps/
├── freechat.py
└── freechat_config/   <-- 这个文件夹的存在激活了便携模式
```

当您再次运行 `python3 freechat.py` 时，它会**自动检测**到这个文件夹，并将所有数据读写操作都重定向到这里。如果是首次运行，它会在这里创建 `config.toml` 等文件。

**从全局模式迁移到便携模式:**

如果您想将已有的全局配置迁移到便携模式，只需将旧目录的内容移动到新目录即可：
```bash
# 确保已创建 freechat_config 文件夹
mv ~/.config/freechat/* /path/to/your/script/freechat_config/
```

---

## 📖 使用说明

*   **普通聊天**: 直接在 `>` 提示符后输入您的问题，然后按 `Control + Enter` 发送。
*   **使用命令**: 所有特殊功能都通过以斜杠 `/` 开头的命令实现。输入 `/` 然后按 `Tab` 键可以查看和补全所有可用命令。
*   **查看帮助**: 在应用内输入 `/help` 可以随时查看命令列表。

### 新功能：Markdown 渲染支持

FreeChat 现在支持导出带有渲染 Markdown 内容的会话。当您使用 `/export md-rendered` 命令时，它将生成一个 HTML 文件，其中包含格式正确的 Markdown 内容，包括粗体文本、斜体文本、代码块和其他 Markdown 元素，以视觉上吸引人的方式呈现。

### ⌨️ 命令参考

| 命令 | 参数 | 描述 |
| :--- | :--- | :--- |
| `/help` | (无) | 显示此帮助信息。 |
| `/model` | `<provider/model_name>` | 切换当前使用的 AI 模型。例如: `/model openai/gpt-4o`。不带参数则显示当前模型。 |
| `/prompt`| `list` | 列出所有在 `prompts.toml` 中定义的可用系统提示。|
| | `view` | 查看当前正在使用的系统提示的完整内容。|
| | `<name>` | 切换到指定的系统提示，并自动开始一个新会话。例如: `/prompt coder`。|
| `/session`| `new` | 开始一个全新的聊天会话，并应用默认的系统提示。|
| `/export` | `<format>` | 将当前会话导出为指定格式的文件。支持的格式: `md`, `json`, `html`, `md-rendered`。 |
| `/clear` | (无) | 清空当前终端屏幕。 |
| `/exit` | (无) | 退出 FreeChat 应用。 |

---

## ⚙️ 配置文件详解

`FreeChat` 使用两个配置文件，它们会在首次运行时自动创建。

### 1. 主配置文件: `config.toml`

此文件用于存放您的 API 密钥和通用设置。

```toml
# FreeChat Main Configuration

[general]
# 设置启动时默认加载的模型。
# 格式为 "provider_name/model_identifier"。
default_model = "openrouter/meta-llama/llama-3-8b-instruct:free"

# 设置启动时默认加载的系统提示名称，该名称对应 prompts.toml 中的一项。
default_prompt = "default"

[providers]
# 在这里填入您的 API 密钥。

# OpenAI: https://platform.openai.com/api-keys
openai_api_key = ""

# OpenRouter.ai: https://openrouter.ai/keys (推荐, 包含众多免费模型)
openrouter_api_key = ""

# Google Gemini: https://aistudio.google.com/app/apikey
gemini_api_key = ""
```

### 2. 系统提示文件: `prompts.toml`

此文件允许您定义多个 AI 角色或指令集。

```toml
# FreeChat System Prompts
# 在这里为 AI 定义不同的角色或指令。
# 在应用中使用 /prompt <name> 命令进行切换。
# TOML 格式支持使用三个引号定义多行字符串。

[default]
prompt = """You are FreeChat, a helpful and concise AI assistant running in a terminal."""

[coder]
prompt = """You are an expert programmer. Provide only code solutions."""

[translator]
prompt = """You are a multilingual translator. Your task is to translate the user's text into English."""
```

## 🤔 常见问题 (FAQ)

*   **Q: 启动时报错 `INCOMPATIBLE PYTHON VERSION`。**  
    A: `FreeChat` 需要 Python 3.7 或更高版本。您的系统 Python 版本太旧了。推荐使用 `pyenv` 等工具安装一个较新的 Python 版本。

*   **Q: 聊天时出现 `HTTP Error 401 Unauthorized`。**  
    A: 您的 API 密钥不正确。请检查 `config.toml` 文件中的 `api_key` 是否填写正确。

*   **Q: 聊天时出现 `HTTP Error 429 Too Many Requests`。**  
    A: 您已达到服务商的速率限制或用量额度。请登录服务商平台查看您的账户状态。

*   **Q: 我可以添加新的 AI 提供商吗？**  
    A: 当然可以。脚本的 `AIProvider` 抽象类设计使其易于扩展。您只需参考 `OpenAIProvider` 或 `GeminiProvider` 的实现，为新的 API 创建一个子类即可。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 授权。