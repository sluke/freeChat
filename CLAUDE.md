# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FreeChat** is a single-file Python CLI application for AI chat with integrated Skill system, Memory system, and Tool calling. It's designed to be a portable, self-contained tool that runs on VPS/cloud servers via SSH.

- **Main file**: `freechat.py` (single-file architecture, ~2400 lines)
- **Version**: 2.3.0
- **Python requirement**: 3.7+
- **Key features**: Multi-provider AI support, Skill system, Memory system with auction compression, Tool calling, Session management

## Architecture

### Single-File Design
All functionality is contained in `freechat.py`:
- `FreeChatApp`: Main application class
- `AIProvider` (ABC): Abstract base for AI providers
- Provider implementations: `OpenAIProvider`, `GeminiProvider` (also handles Anthropic and Mistral via OpenAI-compatible APIs)
- `ProviderFactory`: Creates provider instances based on model IDs

### Configuration System
Two configuration modes detected automatically:

1. **Portable mode**: If `freechat_config/` directory exists alongside `freechat.py`, all config/data is stored there
2. **Global mode** (default): Uses `~/.config/freechat/`

Configuration files:
- `config.toml`: API keys, default model/prompt, language
- `prompts.toml`: System prompt definitions (role-based AI personas)
- `translations.json`: UI translations (i18n)
- `history.txt`: Command history for prompt_toolkit
- `sessions/`: Saved chat sessions (JSON format)

### Provider Architecture
Model format: `provider/model_name`

Supported providers:
- `openai/` - OpenAI API (GPT models)
- `openrouter/` - OpenRouter (aggregated model access)
- `gemini/` - Google Gemini API
- `anthropic/` - Anthropic Claude API
- `mistral/` - Mistral AI API
- `nvidia/` - NVIDIA API (OpenAI-compatible, https://integrate.api.nvidia.com)

Provider auto-detection via `ProviderFactory` which parses the model ID prefix.

## Common Commands

### Development

```bash
# Run the application
python3 freechat.py

# Run tests
python3 -m pytest test_freechat.py -v
# or
python3 test_freechat.py

# Run specific test
python3 -m pytest test_freechat.py::TestFreeChatApp::test_count_tokens -v

# Run performance test
python3 performance_test.py
```

### Docker

```bash
# Build and run with Docker
docker build -t freechat .
docker run -it --name freechat -v ./freechat_config:/app/freechat_config freechat

# Or use docker-compose
docker-compose up -d
docker-compose exec freechat python freechat.py
```

### Testing Approach

The test suite uses `unittest` with heavy mocking:
- API calls are mocked to avoid requiring real API keys
- Configuration directory is mocked to avoid polluting user config
- The `FreeChatApp._setup_config()` method is typically mocked to prevent sys.exit() on first-run config creation

When adding new tests:
1. Use `patch.object()` to mock methods that interact with the filesystem or network
2. Use `patch.dict()` to mock environment variables
3. Use `patch('freechat.Console.print')` to capture console output assertions

## Code Patterns

### Adding a New AI Provider

1. Create a new class inheriting from `AIProvider`:
```python
class NewProvider(AIProvider):
    def __init__(self, key: str):
        super().__init__(key)
        self.base_url = "https://api.provider.com/v1"
    
    def name(self) -> str: 
        return "newprovider"
    
    async def get_models(self) -> Tuple[str, List[str]]:
        # Return (provider_name, [model_list])
        pass
    
    async def stream_chat(self, msgs: List[Dict], model: str) -> AsyncGenerator[str, None]:
        # Yield response chunks
        pass
```

2. Register in `ProviderFactory.__init__()`:
```python
if (key := config.get("providers", {}).get("newprovider_api_key")):
    self.providers["newprovider"] = NewProvider(key)
```

### Configuration Handling

The config system supports environment variable overrides:
- Config file: `config.toml`
- Environment variables: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, etc.
- Override can be disabled with `allow_env_override = false` in `[general]` section

### Session Export Formats

- `md`: Markdown format with YAML frontmatter
- `json`: Full JSON export with all metadata
- `html`: Styled HTML export with conversation formatting
- `md-rendered`: HTML with rendered Markdown content

Export logic is in `_handle_export_command()`. Add new formats by extending the conditional chain.

## Skill System

FreeChat includes a comprehensive Skill system for extending functionality through installable skill packages.

### Core Classes

- `SkillMetadata`: Skill metadata (name, version, author, etc.)
- `SkillDefinition`: Complete skill package definition including tools and config schema
- `SkillRegistry`: Manages installed skills in `skills/` directory
- `SkillSecurityManager`: HMAC signature verification and permission management
- `SkillSandbox`: Execution sandbox for secure skill operations

### Skill Commands

- `/skill list` - List installed skills
- `/skill install <path>` - Install skill from directory
- `/skill uninstall <name>` - Remove a skill
- `/skill info <name>` - Show skill details
- `/skill verify <name>` - Verify skill signature
- `/skill sign <name> <key>` - Sign a skill

### Skill Package Format

```
skill_name/
├── skill.toml          # Metadata and tool definitions
├── README.md           # Documentation
└── (resource files)    # Additional resources
```

See `example_skill/` for a working example.

## Memory System

FreeChat includes an advanced memory system for long-term context preservation across sessions.

### Architecture

- `MemoryEntry`: Individual memory with metadata (value, importance, tags)
- `SQLiteMemoryStore`: SQLite-based storage with FTS5 full-text search
- `MemoryManager`: Core manager with value scoring and statistics
- `AuctionEngine`: Compression algorithm based on weighted value scoring
- `BranchMemoryManager`: Git branch-specific memory management

### Memory Commands

- `/memory remember <text>` - Store new memory
- `/memory recall <query>` - Search memories
- `/memory list` - List all memories with scores
- `/memory forget <id>` - Delete specific memory
- `/memory compress` - Run auction compression
- `/memory stats` - Display statistics
- `/memory branch <name>` - Show branch-specific memories

### Value Scoring (Auction Algorithm)

Memories are scored using weighted factors:
- **Importance** (40%): User-specified importance (1-10)
- **Relevance** (30%): Based on tag richness
- **Recency** (20%): Exponential decay (half-life 30 days)
- **Frequency** (10%): Normalized access count

Low-value memories are archived when storage limits are reached.

## Important Implementation Details

### Token Caching
The app uses an LRU cache (`OrderedDict`) for token counts to avoid re-tokenizing the same text. Cache size is limited to 1000 entries.

### Message History Management
`MAX_HISTORY_MESSAGES = 50` limits the conversation history. When exceeded, the system prompt is preserved and oldest non-system messages are removed.

### Connection Pooling
The `httpx` client is configured with connection pooling and HTTP/2 support for efficient API communication.

### Security Considerations
- API keys are stored in config files with 0600 permissions (where supported)
- Logging system uses rotating file handlers (10MB max, 5 backups)
- Log level can be configured via `log_level` in `[general]`
- First-run configuration exits after creating templates to prevent running without API keys
- Skill system includes HMAC signature verification via `SkillSecurityManager`
- Skill sandboxing via `SkillSandbox` controls file/network/shell access permissions
- Memory system uses parameterized queries to prevent SQL injection

## Testing

```bash
# Run all tests
python3 -m pytest test_freechat.py -v

# Run specific test class
python3 -m pytest test_freechat.py::TestFreeChatApp -v

# Run specific test method
python3 -m pytest test_freechat.py::TestFreeChatApp::test_count_tokens -v

# Run skill-specific tests
python3 -m pytest test_freechat.py::TestSkillSystem -v

# Run memory-specific tests
python3 -m pytest test_freechat.py::TestMemorySystem -v
```

## Documentation Files

- `readme.md` / `readme_cn.md` - Main documentation (English/Chinese)
- `CLAUDE.md` - This file - guidance for Claude Code
- `SKILL_SYSTEM_SUMMARY.md` - Skill system implementation details (Chinese)
- `SKILL_QUICK_START.md` - Quick start guide for skill development
- `example_skill/` - Working example skill package
- `TOOLS_README.md` - Tool calling system documentation
