# FreeChat 💬

**您的全功能、便携式终端 AI 聊天利器 - v2.3.0 记忆系统与性能优化版**

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
*   🧠 **智能记忆系统与拍卖压缩**: 先进的长期记忆功能，基于价值评估的自动压缩算法。支持全局记忆和 Git 分支特定记忆，使用 SQLite 存储并提供全文搜索能力。
*   ⚡ **性能优化**: 包含连接池、模型缓存、令牌计数优化和内存管理，提供更快的响应速度和更低的资源消耗。

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

## 🧠 记忆系统

FreeChat 包含一个强大的记忆系统，支持跨会话的长期上下文保持。该系统使用 SQLite 进行高效存储，并提供全文搜索能力，同时实现了基于智能拍卖算法的压缩机制来管理存储限制。

### 核心特性

- **全局与分支特定记忆**：支持全局记忆存储，或将记忆与特定 Git 分支关联，实现上下文感知的分支切换
- **自动价值评分**：基于重要性、相关性、时效性和访问频率为每个记忆计算综合分数
- **拍卖压缩机制**：当达到存储限制时，自动压缩或归档低价值记忆
- **全文搜索**：基于 SQLite FTS5 的快速记忆检索
- **Git 集成**：自动检测 Git 分支切换，加载对应的分支特定记忆

### 记忆命令

```bash
# 存储新记忆
> /memory remember "用户喜欢 Python 胜过 JavaScript"
✓ 已记录 (mem_abc123)

# 搜索记忆
> /memory recall "编程偏好"
[显示匹配的记忆]

# 列出所有记忆（含分数）
> /memory list
ID       类别       内容                           分数    访问
mem_abc  偏好       用户喜欢深色模式界面            0.85     5
...

# 运行拍卖压缩
> /memory compress
✓ 已压缩 15 条记忆（归档低价值记忆）

# 查看统计信息
> /memory stats
记忆总数: 42
活跃: 37 | 归档: 5
平均分数: 0.72

# 显示分支特定记忆
> /memory branch feature/new-ui
[显示 feature/new-ui 分支的记忆]
```

### 存储

记忆存储在 SQLite 数据库中，位于 `~/.config/freechat/memories/memories.db`（便携模式下为 `freechat_config/memories/memories.db`）。数据库包括：

- 主 `memories` 表，带全文搜索索引
- `memory_tags` 表用于标签管理
- FTS5 虚拟表用于高效内容搜索
- 自动触发器保持搜索索引同步

### 拍卖算法

基于拍卖的压缩使用加权评分：

- **重要性** (40%)：用户指定的重要性 (1-10)
- **相关性** (30%)：基于标签丰富度
- **时效性** (20%)：随时间指数衰减（半衰期30天）
- **频率** (10%)：归一化访问次数

低于存储限制阈值的记忆会被压缩或归档，以保持最佳记忆性能。

---

## 🛠️ 技能系统

FreeChat 包含一个强大的技能系统，允许你通过安装技能包来扩展功能。技能可以提供自定义工具，供 AI 在回答问题时使用。

### 什么是技能？

技能是一个可复用的包，可以：
- 定义带有参数和描述的工具
- 提供元数据（名称、版本、作者、描述）
- 支持独立安装、更新和删除
- 与 AI 对话流程无缝集成

### 技能包结构

技能包是一个目录，包含：

```
my_skill/
├── skill.toml          # 技能元数据（必需）
└── README.md           # 说明文档（可选）
```

### 创建技能

创建 `skill.toml` 文件：

```toml
[skill]
name = "weather-skill"
version = "1.0.0"
description = "获取任意城市的天气信息"
author = "你的名字"
entry_point = "main:initialize"
dependencies = []

[[tools]]
name = "get_weather"
description = "获取城市的当前天气"
parameters = [
    { name = "city", type = "string", required = true, description = "城市名称" },
    { name = "units", type = "string", required = false, description = "温度单位（celsius/fahrenheit）" }
]
```

### 安装和使用技能

#### 安装技能

```bash
> /skill install /path/to/your_skill
✓ 技能 'weather-skill' v1.0.0 安装成功
```

你也可以从当前目录安装：
```bash
> /skill install .
```

#### 查看已安装技能

```bash
> /skill list
名称          版本  描述                    工具数
weather-skill 1.0.0  获取天气信息           1
example-skill 1.0.0  示例技能               2
```

#### 查看技能信息

```bash
> /skill info weather-skill
╭──────────────────── 技能信息 ─────────────────────╮
│ weather-skill v1.0.0                              │
│ 作者: 你的名字                                       │
│ 描述: 获取任意城市的天气信息                        │
│ 工具: get_weather                                  │
╰──────────────────────────────────────────────────╯
```

#### 卸载技能

```bash
> /skill uninstall weather-skill
✓ 技能 'weather-skill' 卸载成功
```

### 在对话中使用技能

技能安装后，其工具会自动对 AI 可用。你不需要做任何特殊操作——只需自然地聊天：

```bash
> 北京今天天气怎么样？
```

AI 会自动检测到它需要天气信息，并调用 `get_weather` 工具，参数为 `{"city": "北京"}`。

### 工作原理

1. **你提问** - 使用自然语言
2. **AI 分析** - 你的请求并判断是否需要工具
3. **AI 调用工具** - 使用正确的参数
4. **工具执行** - 并返回结果
5. **AI 整合** - 结果到回答中

### 创建有效技能的技巧

1. **清晰的工具描述**：编写详细描述，让 AI 知道何时使用你的工具
2. **有意义的参数名**：使用描述性名称如 `city` 而不是 `c`
3. **必需 vs 可选**：将真正必需的参数标记为 `required = true`
4. **好的示例**：在 README.md 中包含使用示例
5. **版本管理**：更改时更新版本号

### 示例：完整的天气技能工作流程

```bash
# 1. 创建技能目录
mkdir ~/my_skills/weather_skill
cd ~/my_skills/weather_skill

# 2. 创建 skill.toml
cat > skill.toml << 'EOF'
[skill]
name = "weather"
version = "1.0.0"
description = "获取城市的天气信息"
author = "用户"

[[tools]]
name = "get_weather"
description = "获取城市的当前天气"
parameters = [
    { name = "city", type = "string", required = true, description = "城市名称" }
]
EOF

# 3. 在 FreeChat 中安装并使用
> /skill install ~/my_skills/weather_skill
> /skill list
> 东京今天天气怎么样？
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
| `/model` | (无) | 显示当前模型详细信息（提供商、状态、收藏）。 |
| | `<provider/model_name>` | 切换当前使用的 AI 模型。例如: `/model openai/gpt-4o`。自动记录到最近使用列表。 |
| | `list` | 列出所有已配置提供商的可用模型。 |
| | `list <provider>` | 列出指定提供商的模型（例如: `/model list openai`）。 |
| | `search <keyword>` | 跨所有提供商按关键词搜索模型。 |
| | `info <name>` | 显示模型的详细信息，包括价格（如果可用）。 |
| | `recent` | 显示最近使用的模型（最多 10 个）。 |
| | `fav` | 显示收藏模型列表。 |
| | `fav <name>` | 添加或移除收藏模型。 |
| `/prompt`| `list` | 列出所有在 `prompts.toml` 中定义的可用系统提示。|
| | `view` | 查看当前正在使用的系统提示的完整内容。|
| | `<name>` | 切换到指定的系统提示，并自动开始一个新会话。例如: `/prompt coder`。|
| `/session`| `new` | 开始一个全新的聊天会话，并应用默认的系统提示。|
| | `save <name>` | 以指定名称保存当前会话。 |
| | `load <name>` | 加载之前保存的会话。 |
| | `list` | 列出所有已保存的会话。 |
| `/file` | `upload <path>` | 上传并处理文件。支持的格式: txt, md, json, csv, py, js, html, css, pdf。 |
| `/language` | `<code>` | 切换界面语言。不带参数可列出可用语言。 |
| `/export` | `<format>` | 将当前会话导出为指定格式的文件。支持的格式: `md`, `json`, `html`, `md-rendered`。 |
| `/clear` | (无) | 清空当前终端屏幕。 |
| `/exit` | (无) | 退出 FreeChat 应用。 |
| `/memory` | `remember <text>` | 存储新记忆，自动分类。 |
| | `recall <query>` | 使用全文搜索查找记忆。 |
| | `list [branch]` | 列出所有记忆，显示价值分数和访问次数。 |
| | `forget <id>` | 删除指定 ID 的记忆。 |
| | `compress` | 运行基于拍卖算法的压缩，归档低价值记忆。 |
| | `stats` | 显示记忆统计信息，包括总数、活跃数和归档数。 |
| | `branch <name>` | 显示特定 Git 分支的记忆。 |

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
default_model = "openrouter/openrouter/free"

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

# Anthropic: https://console.anthropic.com/settings/keys
anthropic_api_key = ""

# Mistral: https://console.mistral.ai/api-keys
mistral_api_key = ""
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

## 🚀 部署选项

### Docker 部署

FreeChat 可以使用 Docker 进行部署，以便更轻松地管理和隔离。

**Docker 部署步骤：**

1. **构建 Docker 镜像**
   ```bash
   docker build -t freechat .
   ```

2. **运行 Docker 容器**
   ```bash
   docker run -it --name freechat -v ./freechat_config:/app/freechat_config freechat
   ```

3. **使用 docker-compose**
   ```bash
   docker-compose up -d
   docker-compose exec freechat python freechat.py
   ```

### 系统服务安装

FreeChat 可以使用 systemd 安装为系统服务。

**安装为系统服务的步骤：**

1. **编辑服务文件**
   ```bash
   nano freechat.service
   ```
   将 `your_username` 替换为您的实际用户名，将 `/path/to/freechat` 替换为您的 FreeChat 安装的实际路径。

2. **复制服务文件**
   ```bash
   sudo cp freechat.service /etc/systemd/system/
   ```

3. **重新加载 systemd 并启动服务**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable freechat
   sudo systemctl start freechat
   ```

4. **检查服务状态**
   ```bash
   sudo systemctl status freechat
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

*   **Q: 如何在 Docker 中运行 FreeChat？**  
    A: 请按照部署选项部分中的 Docker 部署说明进行操作。

*   **Q: 如何将 FreeChat 安装为系统服务？**  
    A: 请按照部署选项部分中的系统服务安装说明进行操作。

## 📄 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 授权。