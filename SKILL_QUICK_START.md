# FreeChat Skill System - 快速入门

## 安装技能

```bash
# 从本地目录安装
> /skill install /path/to/skill

# 示例
> /skill install ./example_skill
✓ Skill installed successfully
```

## 管理技能

```bash
# 列出已安装的技能
> /skill list
Name          Version  Description                    Tools
example-skill 1.0.0    An example skill               2

# 查看技能详情
> /skill info example-skill

# 卸载技能
> /skill uninstall example-skill
✓ Skill 'example-skill' uninstalled
```

## 使用技能工具

安装技能后，其工具会自动注册到系统中。你可以：

```bash
# 直接使用工具
> /tool call example_hello name="World"

# 或在对话中让 AI 使用
> 你好，请使用 example_hello 工具向 World 打招呼
```

## 创建自定义技能

### 1. 创建目录结构

```bash
mkdir my_custom_skill
cd my_custom_skill
```

### 2. 创建 skill.toml

```toml
[skill]
name = "my-custom-skill"
version = "1.0.0"
description = "My custom skill for FreeChat"
author = "Your Name"
entry_point = "main:initialize"
dependencies = []

[[tools]]
name = "my_hello"
description = "Returns a personalized greeting"
parameters = [
    { name = "name", type = "string", required = true, description = "Name to greet" }
]
```

### 3. 安装并使用

```bash
# 在 FreeChat 中安装
> /skill install /path/to/my_custom_skill
✓ Skill installed successfully

# 使用工具
> /tool call my_hello name="Alice"
Hello, Alice! Welcome to FreeChat!
```

## 故障排除

### 技能无法安装
- 检查 `skill.toml` 格式是否正确
- 确保目录路径正确
- 查看错误信息了解详情

### 工具未显示
- 确认技能已启用
- 使用 `/tool list` 查看所有可用工具
- 重新安装技能

### 依赖问题
- 确保技能依赖的其他技能已安装
- 检查依赖版本兼容性

## 更多信息

- [技能系统详细文档](SKILL_SYSTEM_SUMMARY.md)
- [示例技能](example_skill/)
- 使用 `/help` 查看所有可用命令
