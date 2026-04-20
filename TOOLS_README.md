# FreeChat 工具系统使用指南

## 概述

FreeChat 现在支持工具调用（Function Calling）功能，允许 AI 在对话中使用各种工具来帮助回答问题。

## 内置工具

### 1. calculator - 计算器
安全地计算数学表达式。

**示例对话：**
```
用户: 计算 sqrt(144) * 2
AI: [使用 calculator 工具计算]
    结果是 24.0
```

### 2. file_read - 文件读取
读取文件内容（仅限用户主目录和当前工作目录）。

**示例对话：**
```
用户: 读取我的 README.md 文件
AI: [使用 file_read 工具读取]
    文件内容是：...
```

### 3. file_write - 文件写入
写入内容到文件（危险操作，默认禁用）。

**示例对话：**
```
用户: 写入 "Hello" 到 test.txt
AI: [使用 file_write 工具写入]
    文件已成功写入
```

### 4. web_fetch - 网页抓取
获取网页内容并转换为可读文本。

**示例对话：**
```
用户: 总结 https://example.com 的内容
AI: [使用 web_fetch 工具获取网页]
    网页内容是：...
```

## 工具管理命令

### 列出所有工具
```
/tool list
```
显示所有已注册的工具及其启用状态。

### 启用工具
```
/tool enable <工具名>
```
启用指定的工具。

### 禁用工具
```
/tool disable <工具名>
```
禁用指定的工具。

### 直接调用工具
```
/tool call <工具名> [参数]
```
直接调用工具并显示结果。

**示例：**
```
/tool call calculator expression="2+2"
/tool call file_read path="README.md"
```

## 自定义工具（高级）

你可以在 `prompts.toml` 中定义自定义工具：

```toml
[default]
prompt = "You are a helpful assistant."

[tools.my_custom_tool]
description = "My custom tool description"
type = "command"  # command, python, or template
command = "echo 'Hello {name}'"
dangerous = false

[[tools.my_custom_tool.parameters]]
name = "name"
type = "string"
description = "Name to greet"
required = true
```

## 安全注意事项

1. **危险工具**：`file_write` 等修改系统的工具被标记为 `dangerous`，默认禁用
2. **路径限制**：文件操作仅限于用户主目录和当前工作目录
3. **命令注入防护**：自定义工具中的命令参数会被转义
4. **网络限制**：web_fetch 只支持 HTTP/HTTPS 协议

## 故障排除

### 工具不工作
1. 确认工具已启用：`/tool list`
2. 检查工具参数是否正确
3. 查看日志文件了解详细错误

### 自定义工具加载失败
1. 检查 `prompts.toml` 语法是否正确
2. 确认工具定义包含所有必需字段
3. 检查日志中的错误信息

## API 使用

对于开发者，工具系统提供以下主要接口：

```python
# 获取工具注册表
tool_registry = app.tool_registry

# 获取启用的工具
enabled_tools = tool_registry.list_enabled()

# 获取工具 schema
schemas = tool_registry.get_schemas_for_provider('openai')

# 执行工具
tool = tool_registry.get('calculator')
result = tool.handler({'expression': '2+2'})
```

---

**注意**：工具系统是 FreeChat 2.3.0+ 版本的新功能。如果你使用的是旧版本，请先升级。