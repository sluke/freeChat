#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for FreeChat
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from freechat import (
    FreeChatApp, ProviderFactory, AIProvider,
    SkillSecurityManager, SkillSandbox, SQLiteMemoryStore,
    ToolRegistry, SkillMetadata, SkillDefinition, ToolParameter,
    MemoryEntry
)

class TestFreeChatApp(unittest.TestCase):
    """Test FreeChatApp class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary config directory for testing
        self.test_config_dir = Path("test_config")
        self.test_config_dir.mkdir(exist_ok=True)
        
        # Create a minimal config file
        config_content = """
[general]
default_model = "openrouter/openrouter/free"
default_prompt = "default"
[providers]
openrouter_api_key = "test_key"
"""
        with open(self.test_config_dir / "config.toml", "w") as f:
            f.write(config_content)
        
        # Create a prompts file
        prompts_content = """
[default]
prompt = "You are a test assistant"
"""
        with open(self.test_config_dir / "prompts.toml", "w") as f:
            f.write(prompts_content)
        
        # Mock the config directory detection and avoid sys.exit
        with patch('freechat.Path.home', return_value=Path('.')):
            with patch('freechat.Path.is_dir', return_value=True):
                with patch('sys.exit') as mock_exit:
                    # Mock the _setup_config method to avoid sys.exit
                    with patch.object(FreeChatApp, '_setup_config', return_value=None):
                        self.app = FreeChatApp()
                        # Manually set up some attributes for testing
                self.app.active_prompt_name = "default"
                self.app.current_model = "openrouter/free"
                self.app.MAX_HISTORY_MESSAGES = 50
                self.app.session_messages = []
                from collections import OrderedDict
                self.app._token_cache = OrderedDict()
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary config directory
        if self.test_config_dir.exists():
            for file in self.test_config_dir.glob('*'):
                file.unlink()
            self.test_config_dir.rmdir()
    
    def test_init(self):
        """Test initialization"""
        self.assertIsInstance(self.app, FreeChatApp)
        self.assertEqual(self.app.active_prompt_name, "default")
        self.assertEqual(self.app.current_model, "openrouter/free")
    
    def test_count_tokens(self):
        """Test token counting"""
        test_text = "Hello, world!"
        count = self.app._count_tokens(test_text)
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)
    
    def test_manage_message_history(self):
        """Test message history management"""
        # Add test messages
        for i in range(60):  # More than MAX_HISTORY_MESSAGES
            self.app.session_messages.append({"role": "user", "content": f"Message {i}"})
        
        self.app._manage_message_history()
        self.assertLessEqual(len(self.app.session_messages), self.app.MAX_HISTORY_MESSAGES)
    
    def test_handle_model_command(self):
        """Test model command handling"""
        # Mock the provider factory to return a provider
        with patch.object(self.app.provider_factory, 'get_available_providers', return_value=['openrouter']):
            # Test switching to a valid model
            with patch('freechat.Console.print') as mock_print:
                import asyncio
                asyncio.run(self.app._handle_model_command(['openrouter/test-model']))
                mock_print.assert_called_with('[bold green]✓ Switched model to: openrouter/test-model[/bold green]')
        
        # Test switching to an invalid model
        with patch('freechat.Console.print') as mock_print:
            import asyncio
            asyncio.run(self.app._handle_model_command(['invalid-provider/test-model']))
            # Should print error message and available providers list
            calls = [c.args[0] for c in mock_print.call_args_list]
            self.assertTrue(any('Error' in str(c) for c in calls))
            self.assertTrue(any('Available providers' in str(c) for c in calls))
    
    def test_handle_session_command(self):
        """Test session command handling"""
        # Test session new command
        with patch('freechat.Console.print') as mock_print:
            import asyncio
            asyncio.run(self.app._handle_session_command(['new']))
            mock_print.assert_called_with('[bold green]✓ New session started with default prompt \'default\'.[/bold green]')
    
    def test_token_cache_management(self):
        """Test token cache management"""
        # Add some tokens to the cache
        test_texts = [f"Test text {i}" for i in range(1100)]  # More than the cache limit
        for text in test_texts:
            self.app._count_tokens(text)
        
        # Check that cache size is limited
        self.assertLessEqual(len(self.app._token_cache), 1000)
    
    def test_handle_language_command(self):
        """Test language command handling"""
        # Test switching to Chinese
        with patch('freechat.Console.print') as mock_print:
            import asyncio
            asyncio.run(self.app._handle_language_command(['zh']))
            mock_print.assert_called_with('[bold green]✓ Switched language to 中文 (zh)[/bold green]')
        
        # Test switching back to English
        with patch('freechat.Console.print') as mock_print:
            import asyncio
            asyncio.run(self.app._handle_language_command(['en']))
            mock_print.assert_called_with('[bold green]✓ Switched language to English (en)[/bold green]')
        
        # Test invalid language
        with patch('freechat.Console.print') as mock_print:
            import asyncio
            asyncio.run(self.app._handle_language_command(['invalid']))
            mock_print.assert_called_with('[bold red]Error: Language \'invalid\' not supported.[/bold red]')
    
    def test_apply_prompt(self):
        """Test prompt application"""
        # Test applying a valid prompt
        with patch('freechat.Console.print') as mock_print:
            self.app._apply_prompt('default')
            mock_print.assert_called_with('[bold green]✓ Prompt \'default\' applied. New session started.[/bold green]')
        
        # Test applying an invalid prompt
        with patch('freechat.Console.print') as mock_print:
            self.app._apply_prompt('invalid-prompt')
            mock_print.assert_called_with('[bold red]Error: Prompt \'invalid-prompt\' not found in prompts.toml.[/bold red]')
    
    def test_load_config_with_env_vars(self):
        """Test config loading with environment variables"""
        # Test with environment variables
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'env_openai_key',
            'GEMINI_API_KEY': 'env_gemini_key'
        }):
            # Create a minimal config file without these keys
            config_content = """
[general]
default_model = "openrouter/openrouter/free"
[providers]
openrouter_api_key = "test_key"
"""
            with open(self.test_config_dir / "config.toml", "w") as f:
                f.write(config_content)
            
            # Mock the config directory detection
            with patch('freechat.Path.home', return_value=Path('.')):
                with patch('freechat.Path.is_dir', return_value=True):
                    # Create a temporary app instance to test _load_config
                    from freechat import FreeChatApp
                    app = FreeChatApp()
                    # Mock the _setup_config method to avoid sys.exit
                    app._setup_config = lambda: None
                    # Test the _load_config method
                    config = app._load_config(self.test_config_dir / "config.toml")
                    # Check that environment variables were loaded
                    self.assertEqual(config['providers']['openai_api_key'], 'env_openai_key')
                    self.assertEqual(config['providers']['gemini_api_key'], 'env_gemini_key')
                    self.assertEqual(config['providers']['openrouter_api_key'], 'test_key')
    
    def test_load_config_with_empty_values(self):
        """Test config loading with empty values in config file"""
        # Test with environment variables and empty values in config
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'env_openai_key'
        }):
            # Create a config file with empty openai_api_key
            config_content = """
[general]
default_model = "openrouter/openrouter/free"
[providers]
openai_api_key = ""
openrouter_api_key = "test_key"
"""
            with open(self.test_config_dir / "config.toml", "w") as f:
                f.write(config_content)
            
            # Mock the config directory detection
            with patch('freechat.Path.home', return_value=Path('.')):
                with patch('freechat.Path.is_dir', return_value=True):
                    # Create a temporary app instance to test _load_config
                    from freechat import FreeChatApp
                    app = FreeChatApp()
                    # Mock the _setup_config method to avoid sys.exit
                    app._setup_config = lambda: None
                    # Test the _load_config method
                    config = app._load_config(self.test_config_dir / "config.toml")
                    # Check that environment variable was used for empty value
                    self.assertEqual(config['providers']['openai_api_key'], 'env_openai_key')
                    self.assertEqual(config['providers']['openrouter_api_key'], 'test_key')
    
    def test_load_config_with_env_override_disabled(self):
        """Test config loading with env override disabled"""
        # Test with environment variables but env override disabled
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'env_openai_key'
        }):
            # Create a config file with env override disabled
            config_content = """
[general]
default_model = "openrouter/openrouter/free"
allow_env_override = false
[providers]
openai_api_key = "config_openai_key"
"""
            with open(self.test_config_dir / "config.toml", "w") as f:
                f.write(config_content)
            
            # Mock the config directory detection
            with patch('freechat.Path.home', return_value=Path('.')):
                with patch('freechat.Path.is_dir', return_value=True):
                    # Create a temporary app instance to test _load_config
                    from freechat import FreeChatApp
                    app = FreeChatApp()
                    # Mock the _setup_config method to avoid sys.exit
                    app._setup_config = lambda: None
                    # Test the _load_config method
                    config = app._load_config(self.test_config_dir / "config.toml")
                    # Check that environment variable was not used (override disabled)
                    self.assertEqual(config['providers']['openai_api_key'], 'config_openai_key')
    
    def test_save_config(self):
        """Test config saving"""
        # Mock the config file path
        with patch.object(self.app, 'config_path', self.test_config_dir / "test_save_config.toml"):
            # Mock the config dictionary
            self.app.config = {
                'general': {
                    'default_model': 'test-model',
                    'language': 'en'
                },
                'providers': {
                    'openrouter_api_key': 'test-key'
                }
            }
            # Mock the console print
            with patch('freechat.Console.print') as mock_print:
                # Call save config
                self.app._save_config()
                # Check that the file was created
                self.assertTrue((self.test_config_dir / "test_save_config.toml").exists())
    
    def test_load_translations(self):
        """Test translation loading"""
        # Mock the config directory
        with patch.object(self.app, 'config_dir', self.test_config_dir):
            # Create a test translations file
            translations_content = '''
{
    "en": {
        "hello": "Hello"
    },
    "zh": {
        "hello": "你好"
    }
}
'''
            with open(self.test_config_dir / "translations.json", "w") as f:
                f.write(translations_content)
            # Mock the console print
            with patch('freechat.Console.print') as mock_print:
                # Call load translations
                translations = self.app._load_translations()
                # Check that translations were loaded
                self.assertEqual(translations['en']['hello'], 'Hello')
                self.assertEqual(translations['zh']['hello'], '你好')
    
    def test_get_translation(self):
        """Test translation retrieval"""
        # Set up translations
        self.app.translations = {
            'en': {
                'test_key': 'Test Value'
            },
            'zh': {
                'test_key': '测试值'
            }
        }
        # Set language
        self.app.language = 'en'
        # Test English translation
        self.assertEqual(self.app._translate("test_key"), "Test Value")
        # Test Chinese translation
        self.app.language = 'zh'
        self.assertEqual(self.app._translate("test_key"), "测试值")
        # Test fallback for missing key
        self.assertEqual(self.app._translate("missing_key"), "missing_key")

class TestProviderFactory(unittest.TestCase):
    """Test ProviderFactory class"""
    
    def test_init(self):
        """Test initialization"""
        config = {
            "providers": {
                "openai_api_key": "test_key",
                "openrouter_api_key": "test_key",
                "gemini_api_key": "test_key"
            }
        }
        factory = ProviderFactory(config)
        self.assertIsInstance(factory, ProviderFactory)
        self.assertIn("openai", factory.providers)
        self.assertIn("openrouter", factory.providers)
        self.assertIn("gemini", factory.providers)
    
    def test_get_provider(self):
        """Test get_provider method"""
        config = {
            "providers": {
                "openai_api_key": "test_key"
            }
        }
        factory = ProviderFactory(config)
        provider = factory.get_provider("openai/gpt-4")
        self.assertIsInstance(provider, AIProvider)
        
        # Test non-existent provider
        provider = factory.get_provider("non_existent/model")
        self.assertIsNone(provider)


class TestMemoryEntry(unittest.TestCase):
    """Test MemoryEntry class"""

    def test_memory_entry_creation(self):
        """Test creating a MemoryEntry"""
        from freechat import MemoryEntry
        entry = MemoryEntry(
            id="mem_test_001",
            content="Test memory content",
            category="preferences",
            source="user",
            created_at=1000.0,
            updated_at=1000.0,
            importance=8,
            tags=["test", "preference"],
            branch=None,
            compressed=False,
            original_length=23
        )
        self.assertEqual(entry.id, "mem_test_001")
        self.assertEqual(entry.content, "Test memory content")
        self.assertEqual(entry.category, "preferences")
        self.assertEqual(entry.importance, 8)
        self.assertEqual(len(entry.tags), 2)

    def test_compute_value_score(self):
        """Test value score computation"""
        from freechat import MemoryEntry
        import time
        current_time = time.time()
        entry = MemoryEntry(
            id="mem_test_002",
            content="Recent important memory",
            category="knowledge",
            source="user",
            created_at=current_time - 86400,  # 1 day ago
            updated_at=current_time - 86400,
            access_count=5,
            last_accessed=current_time - 3600,  # 1 hour ago
            importance=9,
            tags=["important", "knowledge", "ai"],
            branch=None,
            compressed=False,
            original_length=25
        )
        score = entry.compute_value_score()
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(entry.value_score, 0.0)


class TestAuctionEngine(unittest.TestCase):
    """Test AuctionEngine class"""

    def test_auction_engine_creation(self):
        """Test creating an AuctionEngine"""
        from freechat import AuctionEngine
        engine = AuctionEngine()
        self.assertIsNotNone(engine.weights)
        self.assertIn('importance', engine.weights)
        self.assertIn('relevance', engine.weights)
        self.assertIn('recency', engine.weights)
        self.assertIn('frequency', engine.weights)

    def test_custom_weights(self):
        """Test AuctionEngine with custom weights"""
        from freechat import AuctionEngine
        custom_weights = {
            'importance': 0.5,
            'relevance': 0.3,
            'recency': 0.1,
            'frequency': 0.1
        }
        engine = AuctionEngine(weights=custom_weights)
        self.assertEqual(engine.weights['importance'], 0.5)

    def test_run_auction(self):
        """Test running an auction"""
        from freechat import AuctionEngine, MemoryEntry
        import time
        engine = AuctionEngine()
        current_time = time.time()
        entries = [
            MemoryEntry(
                id=f"mem_{i}",
                content=f"Memory {i}",
                category="test",
                source="user",
                created_at=current_time - i * 86400,
                updated_at=current_time - i * 86400,
                importance=10 - i,
                tags=["test"],
                branch=None,
                compressed=False,
                original_length=10
            )
            for i in range(5)
        ]
        keep, compress = engine.run_auction(entries, max_keep=3)
        self.assertEqual(len(keep), 3)
        self.assertEqual(len(compress), 2)


class TestMemoryManager(unittest.TestCase):
    """Test MemoryManager class"""

    def setUp(self):
        """Set up test environment"""
        import tempfile
        from freechat import MemoryManager
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_memory.db"
        self.memory_manager = MemoryManager(self.db_path)

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        self.memory_manager.close()
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_remember(self):
        """Test storing a memory"""
        memory_id = self.memory_manager.remember(
            content="Test memory content",
            category="test",
            importance=7,
            tags=["test", "memory"]
        )
        self.assertIsNotNone(memory_id)
        self.assertTrue(len(memory_id) > 0)

    def test_recall(self):
        """Test recalling memories"""
        # Store a memory first
        self.memory_manager.remember(
            content="Python is a great programming language",
            category="knowledge",
            importance=8,
            tags=["python", "programming"]
        )
        # Search for it
        results = self.memory_manager.recall("Python programming", limit=5)
        self.assertIsInstance(results, list)

    def test_forget(self):
        """Test forgetting a memory"""
        # Store and then forget
        memory_id = self.memory_manager.remember(
            content="Temporary memory",
            category="test"
        )
        result = self.memory_manager.forget(memory_id)
        self.assertTrue(result)

    def test_get_stats(self):
        """Test getting memory statistics"""
        # Add some memories
        for i in range(3):
            self.memory_manager.remember(
                content=f"Test memory {i}",
                category="test",
                importance=5
            )
        stats = self.memory_manager.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_memories', stats)


class TestBranchMemoryManager(unittest.TestCase):
    """Test BranchMemoryManager class"""

    def setUp(self):
        """Set up test environment"""
        import tempfile
        from freechat import MemoryManager, BranchMemoryManager
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_branch.db"
        self.memory_manager = MemoryManager(self.db_path)
        self.branch_manager = BranchMemoryManager(self.memory_manager)

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        self.branch_manager = None
        self.memory_manager.close()
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_git_repo(self):
        """Test detecting git repository"""
        result = self.branch_manager._detect_git_repo()
        # Should return None or a Path
        self.assertTrue(result is None or isinstance(result, Path))

    def test_get_current_branch(self):
        """Test getting current git branch"""
        branch = self.branch_manager.get_current_branch()
        # Should return None or a string
        self.assertTrue(branch is None or isinstance(branch, str))

    def test_list_branches_with_memories(self):
        """Test listing branches with memories"""
        # Add a branch-specific memory
        self.memory_manager.remember(
            content="Feature branch memory",
            category="context",
            branch="feature/test"
        )
        branches = self.branch_manager.list_branches_with_memories()
        self.assertIsInstance(branches, list)





class TestSkillSecurityManager(unittest.TestCase):
    """Test SkillSecurityManager class"""

    def test_permission_constants(self):
        """Test permission constants are defined"""
        self.assertEqual(SkillSecurityManager.PERMISSION_FILE_READ, "file_read")
        self.assertEqual(SkillSecurityManager.PERMISSION_FILE_WRITE, "file_write")
        self.assertEqual(SkillSecurityManager.PERMISSION_NETWORK, "network")
        self.assertEqual(SkillSecurityManager.PERMISSION_SHELL, "shell")
        self.assertEqual(SkillSecurityManager.PERMISSION_ENV, "env")

    def test_set_and_get_permissions(self):
        """Test setting and getting permissions"""
        skill_name = "test_skill"
        permissions = ["file_read", "network"]

        SkillSecurityManager.set_permissions(skill_name, permissions)
        result = SkillSecurityManager.get_permissions(skill_name)

        self.assertEqual(result, permissions)

    def test_has_permission(self):
        """Test checking if skill has permission"""
        skill_name = "test_skill_2"
        SkillSecurityManager.set_permissions(skill_name, ["file_read", "file_write"])

        self.assertTrue(SkillSecurityManager.has_permission(skill_name, "file_read"))
        self.assertTrue(SkillSecurityManager.has_permission(skill_name, "file_write"))
        self.assertFalse(SkillSecurityManager.has_permission(skill_name, "network"))
        self.assertFalse(SkillSecurityManager.has_permission(skill_name, "shell"))

    def test_validate_skill_path(self):
        """Test skill path validation"""
        # Valid path in home directory
        valid_path = Path.home() / "test_skill"
        result, msg = SkillSecurityManager.validate_skill_path(valid_path)
        self.assertTrue(result)
        self.assertEqual(msg, "OK")

    def test_generate_install_token(self):
        """Test install token generation"""
        skill_name = "test_skill"
        token = SkillSecurityManager.generate_install_token(skill_name)

        self.assertIsInstance(token, str)
        self.assertTrue(token.startswith(f"{skill_name}:"))
        self.assertGreater(len(token), len(skill_name) + 10)


class TestSkillSandbox(unittest.TestCase):
    """Test SkillSandbox class"""

    def setUp(self):
        """Set up test environment"""
        # Create sandbox with some permissions
        self.sandbox = SkillSandbox("test_skill", ["file_read", "file_write", "network"])

    def test_initialization(self):
        """Test sandbox initialization"""
        self.assertEqual(self.sandbox.skill_name, "test_skill")
        self.assertEqual(self.sandbox.allowed_permissions, {"file_read", "file_write", "network"})

    def test_check_permission(self):
        """Test permission checking"""
        # Allowed permissions
        self.assertTrue(self.sandbox.check_permission("file_read"))
        self.assertTrue(self.sandbox.check_permission("file_write"))
        self.assertTrue(self.sandbox.check_permission("network"))

        # Denied permissions
        self.assertFalse(self.sandbox.check_permission("shell"))
        self.assertFalse(self.sandbox.check_permission("env"))

    def test_validate_file_access(self):
        """Test file access validation"""
        # Valid file path
        test_file = Path.home() / "test.txt"
        allowed, msg = self.sandbox.validate_file_access(test_file, "read")
        self.assertTrue(allowed)
        self.assertEqual(msg, "OK")

    def test_context_manager(self):
        """Test sandbox as context manager"""
        # The context manager modifies environment variables
        import os
        original_env = dict(os.environ)

        with self.sandbox:
            # Inside sandbox, environment is restricted
            self.assertIn("PATH", os.environ)

        # After exiting, environment should be restored
        self.assertEqual(os.environ, original_env)


class TestToolRegistry(unittest.TestCase):
    """Test ToolRegistry class"""

    def setUp(self):
        """Set up test environment"""
        self.registry = ToolRegistry()

    def test_register_get_tool(self):
        """Test tool registration and retrieval using mock"""
        # Create a simple mock ToolDefinition using SimpleNamespace
        from types import SimpleNamespace
        tool_def = SimpleNamespace(
            name="test_tool",
            description="A test tool",
            parameters=[],
            handler=lambda x: x
        )

        self.registry.register(tool_def)

        # Verify tool was registered
        self.assertIn("test_tool", self.registry._tools)

        # Test get
        retrieved = self.registry.get("test_tool")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "test_tool")

    def test_unregister_tool(self):
        """Test tool unregistration"""
        from types import SimpleNamespace
        tool_def = SimpleNamespace(
            name="test_tool",
            description="A test tool",
            parameters=[],
            handler=lambda x: x
        )

        self.registry.register(tool_def)
        self.assertIn("test_tool", self.registry._tools)

        self.registry.unregister("test_tool")
        self.assertNotIn("test_tool", self.registry._tools)

    def test_list_all_tools(self):
        """Test listing all tools"""
        from types import SimpleNamespace
        tool1 = SimpleNamespace(name="tool1", description="Tool 1", parameters=[], handler=lambda: None)
        tool2 = SimpleNamespace(name="tool2", description="Tool 2", parameters=[], handler=lambda: None)

        self.registry.register(tool1)
        self.registry.register(tool2)

        all_tools = self.registry.list_all()
        self.assertEqual(len(all_tools), 2)

    def test_enable_disable_tool(self):
        """Test enabling and disabling tools"""
        from types import SimpleNamespace
        tool_def = SimpleNamespace(
            name="test_tool",
            description="A test tool",
            parameters=[],
            handler=lambda x: x
        )

        self.registry.register(tool_def)

        # Initially not enabled
        self.assertFalse(self.registry.is_enabled("test_tool"))

        # Enable
        result = self.registry.enable("test_tool")
        self.assertTrue(result)
        self.assertTrue(self.registry.is_enabled("test_tool"))

        # Disable
        self.registry.disable("test_tool")
        self.assertFalse(self.registry.is_enabled("test_tool"))


class TestSkillMetadata(unittest.TestCase):
    """Test SkillMetadata class"""

    def test_creation(self):
        """Test skill metadata creation"""
        metadata = SkillMetadata(
            name="test_skill",
            version="1.0.0",
            description="A test skill",
            author="Test Author"
        )

        self.assertEqual(metadata.name, "test_skill")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.description, "A test skill")
        self.assertEqual(metadata.author, "Test Author")
        # Check __slots__ fields exist
        self.assertTrue(hasattr(metadata, 'name'))
        self.assertTrue(hasattr(metadata, 'version'))
        self.assertTrue(hasattr(metadata, 'description'))

    def test_from_toml(self):
        """Test creating metadata from TOML data"""
        toml_data = {
            "skill": {
                "name": "test_skill",
                "version": "1.0.0",
                "description": "A test skill",
                "author": "Test Author"
            }
        }

        metadata = SkillMetadata.from_toml(toml_data)
        self.assertEqual(metadata.name, "test_skill")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.description, "A test skill")


class TestSafeCalculator(unittest.TestCase):
    """Test _safe_calculator function"""

    def test_basic_arithmetic(self):
        from freechat import _safe_calculator
        self.assertEqual(_safe_calculator("2 + 3"), "5")
        self.assertEqual(_safe_calculator("10 * 5"), "50")
        self.assertEqual(_safe_calculator("100 / 4"), "25.0")
        self.assertEqual(_safe_calculator("2 ** 10"), "1024")
        self.assertEqual(_safe_calculator("17 % 5"), "2")

    def test_allowed_functions(self):
        from freechat import _safe_calculator
        self.assertEqual(_safe_calculator("abs(-5)"), "5")
        self.assertEqual(_safe_calculator("round(3.7)"), "4")
        self.assertEqual(_safe_calculator("sqrt(16)"), "4.0")
        self.assertEqual(_safe_calculator("ceil(3.2)"), "4")
        self.assertEqual(_safe_calculator("floor(3.8)"), "3")
        self.assertIn("0.0", _safe_calculator("sin(0)"))
        self.assertEqual(_safe_calculator("log10(100)"), "2.0")

    def test_constants(self):
        from freechat import _safe_calculator
        self.assertIn("3.14", _safe_calculator("pi"))
        self.assertIn("2.71", _safe_calculator("e"))

    def test_nested_calls(self):
        from freechat import _safe_calculator
        self.assertEqual(_safe_calculator("sqrt(abs(-16))"), "4.0")
        self.assertEqual(_safe_calculator("round(abs(-3.7))"), "4")

    def test_security_blocks_unknown_identifier(self):
        from freechat import _safe_calculator
        result = _safe_calculator("os")
        self.assertTrue(result.startswith("Error"))
        self.assertIn("os", result)

    def test_security_blocks_dangerous_function(self):
        from freechat import _safe_calculator
        result = _safe_calculator("os.system('ls')")
        self.assertTrue(result.startswith("Error"))

    def test_security_blocks_import(self):
        from freechat import _safe_calculator
        result = _safe_calculator("__import__('os')")
        self.assertTrue(result.startswith("Error"))

    def test_invalid_expression(self):
        from freechat import _safe_calculator
        result = _safe_calculator("2 +")
        self.assertTrue(result.startswith("Error"))

    def test_empty_expression(self):
        from freechat import _safe_calculator
        result = _safe_calculator("")
        self.assertTrue(result.startswith("Error"))


class TestFileReadTool(unittest.TestCase):
    """Test _file_read_tool function"""

    def setUp(self):
        # Create temp files within home dir so path traversal check passes
        self.test_dir = Path.home() / ".freechat_test_tmp"
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_read_valid_file(self):
        from freechat import _file_read_tool
        test_file = self.test_dir / "read_test.txt"
        test_file.write_text("hello world")
        result = _file_read_tool({"path": str(test_file)})
        self.assertIn("hello world", result)
        self.assertIn("File:", result)

    def test_file_not_found(self):
        from freechat import _file_read_tool
        result = _file_read_tool({"path": str(self.test_dir / "nonexistent.txt")})
        self.assertIn("Error", result)
        self.assertIn("not found", result)

    def test_path_traversal_blocked(self):
        from freechat import _file_read_tool
        result = _file_read_tool({"path": "/etc/passwd"})
        self.assertIn("Error", result)
        self.assertIn("Access denied", result)

    def test_directory_returns_error(self):
        from freechat import _file_read_tool
        result = _file_read_tool({"path": str(self.test_dir)})
        self.assertIn("Error", result)
        self.assertIn("not a file", result)

    def test_size_limit_exceeded(self):
        from freechat import _file_read_tool
        test_file = self.test_dir / "big.txt"
        test_file.write_text("x" * 200)
        result = _file_read_tool({"path": str(test_file), "max_size": 100})
        self.assertIn("Error", result)
        self.assertIn("exceeds", result)


class TestFileWriteTool(unittest.TestCase):
    """Test _file_write_tool function"""

    def setUp(self):
        self.test_dir = Path.home() / ".freechat_test_write_tmp"
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_write_new_file(self):
        from freechat import _file_write_tool
        path = str(self.test_dir / "write_test.txt")
        result = _file_write_tool({"path": path, "content": "hello"})
        self.assertIn("Successfully", result)
        with open(path) as f:
            self.assertEqual(f.read(), "hello")

    def test_append_mode(self):
        from freechat import _file_write_tool
        path = str(self.test_dir / "append_test.txt")
        _file_write_tool({"path": path, "content": "line1"})
        _file_write_tool({"path": path, "content": "line2", "mode": "append"})
        with open(path) as f:
            self.assertEqual(f.read(), "line1line2")

    def test_backup_on_overwrite(self):
        from freechat import _file_write_tool
        path = str(self.test_dir / "backup_test.txt")
        _file_write_tool({"path": path, "content": "original"})
        _file_write_tool({"path": path, "content": "updated"})
        backup = path + ".backup"
        self.assertTrue(os.path.exists(backup))
        with open(backup) as f:
            self.assertEqual(f.read(), "original")

    def test_path_traversal_blocked(self):
        from freechat import _file_write_tool
        result = _file_write_tool({"path": "/etc/test_no_access", "content": "bad"})
        self.assertIn("Error", result)
        self.assertIn("Access denied", result)

    def test_creates_parent_dirs(self):
        from freechat import _file_write_tool
        path = str(self.test_dir / "sub" / "dir" / "nested.txt")
        result = _file_write_tool({"path": path, "content": "nested"})
        self.assertIn("Successfully", result)
        with open(path) as f:
            self.assertEqual(f.read(), "nested")


class TestWebFetchTool(unittest.TestCase):
    """Test _web_fetch_tool function"""

    def test_invalid_url_no_scheme(self):
        from freechat import _web_fetch_tool
        result = _web_fetch_tool({"url": "not-a-url"})
        self.assertIn("Error", result)
        self.assertIn("Invalid URL", result)

    def test_invalid_url_no_host(self):
        from freechat import _web_fetch_tool
        result = _web_fetch_tool({"url": "http://"})
        self.assertIn("Error", result)

    @patch('freechat.httpx.Client')
    def test_successful_fetch(self, mock_client_cls):
        from freechat import _web_fetch_tool
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello World</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        # Make httpx.Client() return a context manager that yields mock_client
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = _web_fetch_tool({"url": "https://example.com"})
        self.assertIn("Hello World", result)

    @patch('freechat.httpx.Client')
    def test_max_length_truncation(self, mock_client_cls):
        from freechat import _web_fetch_tool
        mock_response = MagicMock()
        mock_response.text = "A" * 1000
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = _web_fetch_tool({"url": "https://example.com", "max_length": 50})
        self.assertIn("truncated", result.lower())


class TestSkillSecurityManagerSignature(unittest.TestCase):
    """Test SkillSecurityManager signature methods"""

    def test_compute_signature_consistency(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            skill_path = Path(d) / "test_skill"
            skill_path.mkdir()
            (skill_path / "skill.toml").write_text("name = 'test'")
            sig1 = SkillSecurityManager.compute_signature(skill_path, "secret_key")
            sig2 = SkillSecurityManager.compute_signature(skill_path, "secret_key")
            self.assertEqual(sig1, sig2)
            self.assertIsInstance(sig1, str)
            self.assertTrue(len(sig1) > 0)

    def test_compute_signature_different_keys(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            skill_path = Path(d) / "test_skill"
            skill_path.mkdir()
            (skill_path / "skill.toml").write_text("name = 'test'")
            sig1 = SkillSecurityManager.compute_signature(skill_path, "key1")
            sig2 = SkillSecurityManager.compute_signature(skill_path, "key2")
            self.assertNotEqual(sig1, sig2)

    def test_compute_signature_different_content(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            skill_path = Path(d) / "test_skill"
            skill_path.mkdir()
            (skill_path / "skill.toml").write_text("name = 'test'")
            sig1 = SkillSecurityManager.compute_signature(skill_path, "key")

            (skill_path / "skill.toml").write_text("name = 'modified'")
            sig2 = SkillSecurityManager.compute_signature(skill_path, "key")
            self.assertNotEqual(sig1, sig2)

    def test_compute_signature_nonexistent_path(self):
        result = SkillSecurityManager.compute_signature(Path("/nonexistent/path"), "key")
        self.assertEqual(result, "")

    def test_verify_signature_no_sig_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            skill_path = Path(d) / "test_skill"
            skill_path.mkdir()
            # No .signature file, no trusted key -> should return True (unsigned = OK)
            result = SkillSecurityManager.verify_signature(skill_path)
            self.assertTrue(result)

    def test_verify_signature_with_valid_sig(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            skill_path = Path(d) / "test_skill"
            skill_path.mkdir()
            (skill_path / "skill.toml").write_text("name = 'test'")
            sig = SkillSecurityManager.compute_signature(skill_path, "secret")
            (skill_path / ".signature").write_text(sig)
            result = SkillSecurityManager.verify_signature(skill_path)
            self.assertTrue(result)


class TestToolParameter(unittest.TestCase):
    """Test ToolParameter dataclass"""

    def test_creation_defaults(self):
        from freechat import ToolParameter
        p = ToolParameter(name="arg1", type="string", description="A test arg")
        self.assertEqual(p.name, "arg1")
        self.assertEqual(p.type, "string")
        self.assertTrue(p.required)
        self.assertIsNone(p.enum)

    def test_creation_with_enum(self):
        from freechat import ToolParameter
        p = ToolParameter(name="mode", type="string", description="Mode", enum=["fast", "slow"])
        self.assertEqual(p.enum, ["fast", "slow"])

    def test_to_schema_basic(self):
        from freechat import ToolParameter
        p = ToolParameter(name="path", type="string", description="File path")
        schema = p.to_schema()
        self.assertEqual(schema["type"], "string")
        self.assertEqual(schema["description"], "File path")
        self.assertNotIn("enum", schema)

    def test_to_schema_with_enum(self):
        from freechat import ToolParameter
        p = ToolParameter(name="mode", type="string", description="Mode", enum=["a", "b"])
        schema = p.to_schema()
        self.assertEqual(schema["enum"], ["a", "b"])


class TestToolDefinition(unittest.TestCase):
    """Test ToolDefinition dataclass"""

    def _make_tool(self):
        from freechat import ToolDefinition, ToolParameter
        return ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(name="path", type="string", description="File path"),
                ToolParameter(name="verbose", type="boolean", description="Verbose", required=False),
            ],
            handler=lambda args: "ok"
        )

    def test_to_openai_schema(self):
        tool = self._make_tool()
        schema = tool.to_openai_schema()
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "test_tool")
        self.assertEqual(schema["function"]["description"], "A test tool")
        self.assertIn("path", schema["function"]["parameters"]["properties"])
        self.assertIn("verbose", schema["function"]["parameters"]["properties"])
        self.assertIn("path", schema["function"]["parameters"]["required"])
        self.assertNotIn("verbose", schema["function"]["parameters"]["required"])

    def test_to_gemini_schema(self):
        tool = self._make_tool()
        schema = tool.to_gemini_schema()
        self.assertEqual(schema["name"], "test_tool")
        self.assertEqual(schema["description"], "A test tool")
        self.assertIn("path", schema["parameters"]["properties"])
        self.assertIn("path", schema["parameters"]["required"])

    def test_no_parameters(self):
        from freechat import ToolDefinition
        tool = ToolDefinition(
            name="noop", description="No params", parameters=[], handler=lambda args: "ok"
        )
        schema = tool.to_openai_schema()
        self.assertEqual(schema["function"]["parameters"]["properties"], {})
        self.assertEqual(schema["function"]["parameters"]["required"], [])


class TestToolRegistryExtended(unittest.TestCase):
    """Test extended ToolRegistry methods"""

    def setUp(self):
        self.registry = ToolRegistry()

    def _register_tool(self, name, enabled=False):
        from types import SimpleNamespace
        tool = SimpleNamespace(
            name=name, description=f"Tool {name}", parameters=[],
            handler=lambda x: x, to_openai_schema=lambda: {"name": name},
            to_gemini_schema=lambda: {"name": name}
        )
        self.registry.register(tool)
        if enabled:
            self.registry.enable(name)
        return tool

    def test_list_enabled(self):
        self._register_tool("a", enabled=True)
        self._register_tool("b", enabled=False)
        self._register_tool("c", enabled=True)
        enabled = self.registry.list_enabled()
        names = [t.name for t in enabled]
        self.assertIn("a", names)
        self.assertIn("c", names)
        self.assertNotIn("b", names)

    def test_get_schemas_for_provider_openai(self):
        self._register_tool("t1", enabled=True)
        schemas = self.registry.get_schemas_for_provider("openai")
        self.assertEqual(len(schemas), 1)
        self.assertEqual(schemas[0]["name"], "t1")

    def test_get_schemas_for_provider_gemini(self):
        self._register_tool("t1", enabled=True)
        schemas = self.registry.get_schemas_for_provider("gemini")
        self.assertEqual(len(schemas), 1)

    def test_schema_caching(self):
        self._register_tool("t1", enabled=True)
        schemas1 = self.registry.get_schemas_for_provider("openai")
        schemas2 = self.registry.get_schemas_for_provider("openai")
        self.assertIs(schemas1, schemas2)  # Same cached object

    def test_cache_cleared_on_enable(self):
        self._register_tool("t1", enabled=True)
        schemas1 = self.registry.get_schemas_for_provider("openai")
        self.registry.enable("t1")  # Should clear cache
        schemas2 = self.registry.get_schemas_for_provider("openai")
        self.assertIsNot(schemas1, schemas2)  # New cache entry


class TestSQLiteMemoryStore(unittest.TestCase):
    """Test SQLiteMemoryStore class"""

    def setUp(self):
        import tempfile
        from freechat import SQLiteMemoryStore
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_store.db"
        self.store = SQLiteMemoryStore(self.db_path)

    def tearDown(self):
        import shutil
        self.store.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_entry(self, id="mem_1", content="test content", category="test",
                    importance=5, tags=None, branch=None):
        from freechat import MemoryEntry
        import time
        now = time.time()
        return MemoryEntry(
            id=id, content=content, category=category, source="user",
            created_at=now, updated_at=now, importance=importance,
            tags=tags or [], branch=branch, original_length=len(content)
        )

    def test_init_creates_db(self):
        self.assertTrue(self.db_path.exists())

    def test_insert_and_get(self):
        entry = self._make_entry(tags=["python", "code"])
        self.assertTrue(self.store.insert_memory(entry))
        loaded = self.store.get_memory("mem_1")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.content, "test content")
        self.assertEqual(loaded.category, "test")
        self.assertEqual(sorted(loaded.tags), sorted(["python", "code"]))

    def test_get_nonexistent(self):
        self.assertIsNone(self.store.get_memory("nonexistent"))

    def test_search_by_query(self):
        self.store.insert_memory(self._make_entry(content="Python is great"))
        self.store.insert_memory(self._make_entry(id="mem_2", content="Java is okay"))
        results = self.store.search_memories(query="Python")
        self.assertTrue(any("Python" in r.content for r in results))

    def test_search_by_category(self):
        self.store.insert_memory(self._make_entry(category="knowledge"))
        self.store.insert_memory(self._make_entry(id="mem_2", category="preference"))
        results = self.store.search_memories(category="knowledge")
        self.assertTrue(all(r.category == "knowledge" for r in results))

    def test_search_by_branch(self):
        self.store.insert_memory(self._make_entry(branch="feature/x"))
        self.store.insert_memory(self._make_entry(id="mem_2"))
        results = self.store.search_memories(branch="feature/x")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].branch, "feature/x")

    def test_update_memory(self):
        entry = self._make_entry()
        self.store.insert_memory(entry)
        entry.content = "updated content"
        entry.importance = 9
        entry.tags = ["updated"]
        self.assertTrue(self.store.update_memory(entry))
        loaded = self.store.get_memory("mem_1")
        self.assertEqual(loaded.content, "updated content")
        self.assertEqual(loaded.importance, 9)
        self.assertEqual(loaded.tags, ["updated"])

    def test_delete_memory(self):
        self.store.insert_memory(self._make_entry())
        self.assertTrue(self.store.delete_memory("mem_1"))
        self.assertIsNone(self.store.get_memory("mem_1"))

    def test_delete_nonexistent(self):
        self.assertFalse(self.store.delete_memory("nonexistent"))

    def test_restore_memory(self):
        entry = self._make_entry()
        self.store.insert_memory(entry)
        # Archive it directly
        conn = self.store._get_connection()
        conn.execute("UPDATE memories SET is_archived = 1 WHERE id = 'mem_1'")
        conn.commit()
        self.assertTrue(self.store.restore_memory("mem_1"))
        loaded = self.store.get_memory("mem_1")
        self.assertIsNotNone(loaded)

    def test_clear_all(self):
        self.store.insert_memory(self._make_entry())
        self.store.insert_memory(self._make_entry(id="mem_2"))
        count = self.store.clear_all_memories()
        self.assertEqual(count, 2)
        self.assertIsNone(self.store.get_memory("mem_1"))

    def test_archive_old_memories(self):
        import time
        entry = self._make_entry()
        entry.created_at = time.time() - 100 * 86400  # 100 days ago
        entry.value_score = 0.1
        self.store.insert_memory(entry)
        archived = self.store.archive_old_memories(min_score=0.5, days_old=30)
        self.assertEqual(archived, 1)

    def test_get_all_categories(self):
        self.store.insert_memory(self._make_entry(category="knowledge"))
        self.store.insert_memory(self._make_entry(id="mem_2", category="knowledge"))
        self.store.insert_memory(self._make_entry(id="mem_3", category="preference"))
        cats = self.store.get_all_categories()
        cat_dict = dict(cats)
        self.assertEqual(cat_dict["knowledge"], 2)
        self.assertEqual(cat_dict["preference"], 1)

    def test_escape_fts5_query(self):
        from freechat import SQLiteMemoryStore
        result = SQLiteMemoryStore._escape_fts5_query(["hello", "world"])
        self.assertEqual(result, '"hello" OR "world"')

    def test_escape_fts5_query_special_chars(self):
        from freechat import SQLiteMemoryStore
        result = SQLiteMemoryStore._escape_fts5_query(['test"quote'])
        self.assertIn('""', result)

    def test_batch_update_compression(self):
        import time as time_mod
        entry = self._make_entry()
        self.store.insert_memory(entry)
        entry.content_compressed = "compressed version"
        entry.updated_at = time_mod.time()
        count = self.store.batch_update_compression([entry])
        self.assertEqual(count, 1)
        loaded = self.store.get_memory("mem_1")
        self.assertTrue(loaded.compressed)
        self.assertEqual(loaded.content, "compressed version")

    def test_get_top_memories(self):
        import time
        for i in range(5):
            entry = self._make_entry(id=f"mem_{i}", content=f"memory {i}", importance=10 - i)
            entry.value_score = float(10 - i)
            self.store.insert_memory(entry)
        top = self.store.get_top_memories(limit=3)
        self.assertEqual(len(top), 3)

    def test_get_recent_memories(self):
        import time
        for i in range(3):
            entry = self._make_entry(id=f"mem_{i}", content=f"memory {i}")
            entry.last_accessed = time.time() - i * 60
            self.store.insert_memory(entry)
        recent = self.store.get_recent_memories(limit=2)
        self.assertEqual(len(recent), 2)

    def test_get_stats(self):
        self.store.insert_memory(self._make_entry())
        self.store.insert_memory(self._make_entry(id="mem_2", branch="feature/x"))
        stats = self.store.get_stats()
        self.assertEqual(stats['total_memories'], 2)
        self.assertEqual(stats['global_memories'], 1)
        self.assertIn('average_score', stats)

    def test_find_similar(self):
        self.store.insert_memory(self._make_entry(content="python programming language"))
        self.store.insert_memory(self._make_entry(id="mem_2", content="python coding tutorial"))
        self.store.insert_memory(self._make_entry(id="mem_3", content="java development"))
        similar = self.store.find_similar("python programming", threshold=0.5)
        self.assertTrue(len(similar) > 0)

    def test_get_related_memories(self):
        self.store.insert_memory(self._make_entry(tags=["python", "code"]))
        self.store.insert_memory(self._make_entry(id="mem_2", tags=["python", "tutorial"]))
        self.store.insert_memory(self._make_entry(id="mem_3", tags=["java"]))
        related = self.store.get_related_memories("mem_1")
        # mem_2 shares "python" tag
        self.assertTrue(any(r.id == "mem_2" for r in related))

    def test_advanced_search(self):
        self.store.insert_memory(self._make_entry(
            content="advanced search test", importance=8, tags=["search"]
        ))
        results = self.store.advanced_search(
            query="advanced", min_importance=5, tags=["search"]
        )
        self.assertEqual(len(results), 1)

    def test_close_and_reopen(self):
        self.store.insert_memory(self._make_entry())
        self.store.close()
        from freechat import SQLiteMemoryStore
        store2 = SQLiteMemoryStore(self.db_path)
        loaded = store2.get_memory("mem_1")
        self.assertIsNotNone(loaded)
        store2.close()


class TestMemoryManagerExtended(unittest.TestCase):
    """Test extended MemoryManager methods"""

    def setUp(self):
        import tempfile
        from freechat import MemoryManager
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_mm_ext.db"
        self.mm = MemoryManager(self.db_path)

    def tearDown(self):
        import shutil
        self.mm.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_update_memory_content(self):
        mid = self.mm.remember("original content", category="test")
        result = self.mm.update_memory(mid, content="updated content")
        self.assertTrue(result)
        entry = self.mm._store.get_memory(mid)
        self.assertEqual(entry.content, "updated content")

    def test_update_memory_importance(self):
        mid = self.mm.remember("test", importance=3)
        self.mm.update_memory(mid, importance=9)
        entry = self.mm._store.get_memory(mid)
        self.assertEqual(entry.importance, 9)

    def test_update_memory_tags(self):
        mid = self.mm.remember("test", tags=["old"])
        self.mm.update_memory(mid, tags=["new", "tags"])
        entry = self.mm._store.get_memory(mid)
        self.assertEqual(sorted(entry.tags), sorted(["new", "tags"]))

    def test_update_nonexistent(self):
        result = self.mm.update_memory("nonexistent", content="x")
        self.assertFalse(result)

    def test_update_ignores_disallowed_fields(self):
        mid = self.mm.remember("test")
        self.mm.update_memory(mid, id="hacked", source="hacked")
        entry = self.mm._store.get_memory(mid)
        self.assertEqual(entry.id, mid)  # id unchanged
        self.assertEqual(entry.source, "user")  # source unchanged

    def test_touch_memory(self):
        mid = self.mm.remember("test")
        self.assertTrue(self.mm.touch_memory(mid))
        entry = self.mm._store.get_memory(mid)
        self.assertEqual(entry.access_count, 1)
        self.assertGreater(entry.last_accessed, 0)

    def test_restore(self):
        mid = self.mm.remember("test")
        conn = self.mm._store._get_connection()
        conn.execute("UPDATE memories SET is_archived = 1 WHERE id = ?", (mid,))
        conn.commit()
        self.assertTrue(self.mm.restore(mid))

    def test_clear_all(self):
        self.mm.remember("a")
        self.mm.remember("b")
        count = self.mm.clear_all()
        self.assertEqual(count, 2)

    def test_export_and_import(self):
        self.mm.remember("memory 1", category="test", importance=8, tags=["a"])
        self.mm.remember("memory 2", category="other", tags=["b"])

        export_path = Path(self.temp_dir) / "export.json"
        exported = self.mm.export_memories(export_path)
        self.assertEqual(exported, 2)
        self.assertTrue(export_path.exists())

        # Import into a fresh manager
        from freechat import MemoryManager
        db2 = Path(self.temp_dir) / "import_test.db"
        mm2 = MemoryManager(db2)
        imported = mm2.import_memories(export_path)
        self.assertEqual(imported, 2)
        stats = mm2.get_stats()
        self.assertEqual(stats['total_memories'], 2)
        mm2.close()

    def test_get_categories(self):
        self.mm.remember("a", category="knowledge")
        self.mm.remember("b", category="knowledge")
        self.mm.remember("c", category="preference")
        cats = self.mm.get_categories()
        cat_dict = dict(cats)
        self.assertEqual(cat_dict["knowledge"], 2)

    def test_find_similar(self):
        self.mm.remember("python programming language")
        self.mm.remember("java development framework")
        similar = self.mm.find_similar("python coding")
        self.assertIsInstance(similar, list)

    def test_get_top_memories(self):
        for i in range(5):
            self.mm.remember(f"memory {i}", importance=10 - i)
        top = self.mm.get_top_memories(limit=3)
        self.assertEqual(len(top), 3)

    def test_get_recent_memories(self):
        mid1 = self.mm.remember("old memory")
        mid2 = self.mm.remember("new memory")
        self.mm.touch_memory(mid1)
        self.mm.touch_memory(mid2)
        recent = self.mm.get_recent_memories(limit=1)
        self.assertEqual(len(recent), 1)

    def test_get_related(self):
        self.mm.remember("python code", tags=["python"], category="knowledge")
        self.mm.remember("python tutorial", tags=["python"], category="knowledge")
        self.mm.remember("java code", tags=["java"], category="other")
        mid = self.mm._store.search_memories(query="python code")[0].id
        related = self.mm.get_related(mid)
        self.assertTrue(len(related) > 0)

    def test_advanced_search(self):
        self.mm.remember("test content", importance=8, tags=["search"])
        results = self.mm.advanced_search(query="test", min_importance=5, tags=["search"])
        self.assertEqual(len(results), 1)

    def test_branch_operations(self):
        self.mm.set_current_branch("feature/x")
        self.assertEqual(self.mm.get_current_branch(), "feature/x")
        self.mm.remember("branch memory")
        branches = self.mm.list_branches()
        self.assertIn("feature/x", branches)

    def test_compress_memories(self):
        for i in range(10):
            self.mm.remember(f"memory {i}", importance=i)
        compressed = self.mm.compress_memories()
        # Some memories should be compressed
        self.assertIsInstance(compressed, int)

    def test_summarize_content_short(self):
        result = self.mm._summarize_content("short text")
        self.assertEqual(result, "short text")

    def test_summarize_content_long(self):
        long_text = "x" * 500
        result = self.mm._summarize_content(long_text, max_length=100)
        self.assertTrue(len(result) < len(long_text))
        self.assertIn("compressed", result)


class TestBranchMemoryManagerExtended(unittest.TestCase):
    """Test BranchMemoryManager merge/sync methods"""

    def setUp(self):
        import tempfile
        from freechat import MemoryManager, BranchMemoryManager
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_branch_ext.db"
        self.mm = MemoryManager(self.db_path)
        self.bm = BranchMemoryManager(self.mm)

    def tearDown(self):
        import shutil
        self.mm.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_merge_branch_memories(self):
        self.mm.remember("feature work 1", branch="feature/a", tags=["work"])
        self.mm.remember("feature work 2", branch="feature/a", tags=["code"])
        count = self.bm.merge_branch_memories("feature/a", "main")
        self.assertEqual(count, 2)
        main_memories = self.mm.recall(query="", branch="main")
        self.assertEqual(len(main_memories), 2)

    def test_merge_empty_branch(self):
        count = self.bm.merge_branch_memories("nonexistent", "main")
        self.assertEqual(count, 0)

    def test_sync_branch_memories(self):
        # sync_branch_memories depends on git state, just test it doesn't crash
        self.bm.sync_branch_memories()


class TestSkillDefinition(unittest.TestCase):
    """Test SkillDefinition class"""

    def test_from_directory(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            skill_dir = Path(d) / "test_skill"
            skill_dir.mkdir()
            toml_content = """
[skill]
name = "my_skill"
version = "2.0.0"
description = "A test skill"
author = "Test Author"

[[tools]]
name = "greet"
description = "Say hello"

[[tools.parameters]]
name = "name"
type = "string"
description = "Name to greet"
required = true
"""
            (skill_dir / "skill.toml").write_text(toml_content)
            from freechat import SkillDefinition
            skill = SkillDefinition.from_directory(skill_dir)
            self.assertIsNotNone(skill)
            self.assertEqual(skill.name, "my_skill")
            self.assertEqual(skill.version, "2.0.0")
            self.assertEqual(len(skill.tools), 1)
            self.assertEqual(skill.tools[0].name, "greet")
            self.assertEqual(skill.tools[0].parameters[0].name, "name")

    def test_from_directory_no_toml(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            skill_dir = Path(d) / "empty_skill"
            skill_dir.mkdir()
            from freechat import SkillDefinition
            skill = SkillDefinition.from_directory(skill_dir)
            self.assertIsNone(skill)

    def test_from_directory_invalid_toml(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            skill_dir = Path(d) / "bad_skill"
            skill_dir.mkdir()
            (skill_dir / "skill.toml").write_text("this is not valid toml [[[")
            from freechat import SkillDefinition
            skill = SkillDefinition.from_directory(skill_dir)
            self.assertIsNone(skill)


class TestSkillRegistry(unittest.TestCase):
    """Test SkillRegistry class"""

    def setUp(self):
        # Create skills dir within home so path validation passes
        self.skills_dir = Path.home() / ".freechat_test_skills"
        self.skills_dir.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.skills_dir, ignore_errors=True)

    def _create_skill(self, name="test_skill", version="1.0.0"):
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(exist_ok=True)
        toml = f"""
[skill]
name = "{name}"
version = "{version}"
description = "Test"
"""
        (skill_dir / "skill.toml").write_text(toml)
        return skill_dir

    def test_load_installed_skills(self):
        self._create_skill("skill_a")
        self._create_skill("skill_b")
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        self.assertEqual(len(registry.list_skills()), 2)

    def test_get_skill(self):
        self._create_skill("my_skill")
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        skill = registry.get("my_skill")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "my_skill")

    def test_get_nonexistent(self):
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        self.assertIsNone(registry.get("nonexistent"))

    def test_is_installed(self):
        self._create_skill("installed_skill")
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        self.assertTrue(registry.is_installed("installed_skill"))
        self.assertFalse(registry.is_installed("not_installed"))

    def test_uninstall(self):
        self._create_skill("to_remove")
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        self.assertTrue(registry.is_installed("to_remove"))
        success, msg = registry.uninstall("to_remove")
        self.assertTrue(success)
        self.assertFalse(registry.is_installed("to_remove"))

    def test_uninstall_nonexistent(self):
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        success, msg = registry.uninstall("ghost")
        self.assertFalse(success)

    def test_install_from_local_dir(self):
        source = Path.home() / ".freechat_test_source_skill"
        source.mkdir(exist_ok=True)
        try:
            toml = """
[skill]
name = "imported_skill"
version = "1.0.0"
description = "Imported"
"""
            (source / "skill.toml").write_text(toml)
            from freechat import SkillRegistry
            registry = SkillRegistry(self.skills_dir)
            success, msg = registry.install(source, confirm_permissions=False)
            self.assertTrue(success)
            self.assertTrue(registry.is_installed("imported_skill"))
        finally:
            import shutil
            shutil.rmtree(source, ignore_errors=True)

    def test_parse_git_source_short_form(self):
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        result = registry._parse_git_source("github:user/repo")
        self.assertIsNotNone(result)
        self.assertEqual(result['host'], 'github')
        self.assertEqual(result['user'], 'user')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_git_source_https(self):
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        result = registry._parse_git_source("https://github.com/user/repo.git")
        self.assertIsNotNone(result)
        self.assertEqual(result['host'], 'github')
        self.assertEqual(result['user'], 'user')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_git_source_ssh(self):
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        result = registry._parse_git_source("git@github.com:user/repo.git")
        self.assertIsNotNone(result)
        self.assertEqual(result['host'], 'github')
        self.assertEqual(result['user'], 'user')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_git_source_invalid(self):
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        result = registry._parse_git_source("not a valid source")
        self.assertIsNone(result)

    def test_parse_git_source_with_path(self):
        from freechat import SkillRegistry
        registry = SkillRegistry(self.skills_dir)
        result = registry._parse_git_source("github:user/repo/path/to/skill")
        self.assertIsNotNone(result)
        self.assertEqual(result['path'], 'path/to/skill')


class TestSkillRegistryClient(unittest.TestCase):
    """Test SkillRegistryClient class"""

    def setUp(self):
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_defaults(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        registries = client.list_registries()
        names = [r.name for r in registries]
        self.assertIn("github", names)
        self.assertIn("gitlab", names)

    def test_add_registry(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        success, msg = client.add_registry("custom", "https://custom.example.com")
        self.assertTrue(success)
        reg = client.get_registry("custom")
        self.assertIsNotNone(reg)
        self.assertEqual(reg.url, "https://custom.example.com")

    def test_add_duplicate_registry(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        client.add_registry("custom", "https://custom.example.com")
        success, msg = client.add_registry("custom", "https://other.com")
        self.assertFalse(success)

    def test_remove_registry(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        client.add_registry("removable", "https://removable.example.com")
        success, msg = client.remove_registry("removable")
        self.assertTrue(success)
        self.assertIsNone(client.get_registry("removable"))

    def test_remove_default_registry_fails(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        success, msg = client.remove_registry("github")
        self.assertFalse(success)

    def test_set_default_registry(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        client.add_registry("new_default", "https://new.example.com")
        success, msg = client.set_default_registry("new_default")
        self.assertTrue(success)
        default = client.get_default_registry()
        self.assertEqual(default.name, "new_default")

    def test_set_default_nonexistent(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        success, msg = client.set_default_registry("nonexistent")
        self.assertFalse(success)

    def test_get_default_registry(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        default = client.get_default_registry()
        self.assertEqual(default.name, "github")

    def test_persistence(self):
        from freechat import SkillRegistryClient
        client = SkillRegistryClient(self.config_dir)
        client.add_registry("persistent", "https://persist.example.com")
        # Create a new client to test persistence
        client2 = SkillRegistryClient(self.config_dir)
        reg = client2.get_registry("persistent")
        self.assertIsNotNone(reg)
        self.assertEqual(reg.url, "https://persist.example.com")


class TestTranslateWithKwargs(unittest.TestCase):
    """Test _translate with format kwargs"""

    def setUp(self):
        with patch('freechat.Path.home', return_value=Path('.')):
            with patch('freechat.Path.is_dir', return_value=True):
                with patch.object(FreeChatApp, '_setup_config', return_value=None):
                    self.app = FreeChatApp()
        self.app.language = 'en'

    def test_translate_with_kwargs(self):
        self.app.translations = {'en': {'greeting': 'Hello, {name}!'}}
        result = self.app._translate('greeting', name='World')
        self.assertEqual(result, 'Hello, World!')

    def test_translate_with_multiple_kwargs(self):
        self.app.translations = {'en': {'msg': '{a} and {b}'}}
        result = self.app._translate('msg', a='X', b='Y')
        self.assertEqual(result, 'X and Y')

    def test_translate_missing_key_with_kwargs(self):
        result = self.app._translate('nonexistent', name='test')
        self.assertEqual(result, 'nonexistent')


class TestProviderFactoryExtended(unittest.TestCase):
    """Test ProviderFactory with all providers"""

    def test_all_providers(self):
        config = {"providers": {
            "openai_api_key": "k1",
            "openrouter_api_key": "k2",
            "gemini_api_key": "k3",
            "anthropic_api_key": "k4",
            "mistral_api_key": "k5",
            "nvidia_api_key": "k6"
        }}
        factory = ProviderFactory(config)
        self.assertEqual(len(factory.providers), 6)
        self.assertIn("openai", factory.providers)
        self.assertIn("openrouter", factory.providers)
        self.assertIn("gemini", factory.providers)
        self.assertIn("anthropic", factory.providers)
        self.assertIn("mistral", factory.providers)
        self.assertIn("nvidia", factory.providers)

    def test_get_available_providers(self):
        config = {"providers": {"openai_api_key": "k", "gemini_api_key": "k"}}
        factory = ProviderFactory(config)
        available = factory.get_available_providers()
        self.assertIn("openai", available)
        self.assertIn("gemini", available)
        self.assertEqual(len(available), 2)


class TestOpenAIProvider(unittest.TestCase):
    """Test OpenAIProvider class"""

    def test_name(self):
        from freechat import OpenAIProvider
        p = OpenAIProvider("key", "https://api.openai.com/v1", "openai")
        self.assertEqual(p.name, "openai")

    def test_custom_name(self):
        from freechat import OpenAIProvider
        p = OpenAIProvider("key", "https://openrouter.ai/api/v1", "openrouter")
        self.assertEqual(p.name, "openrouter")

    def test_supports_tools(self):
        from freechat import OpenAIProvider
        p = OpenAIProvider("key", "https://api.openai.com/v1")
        self.assertTrue(p.supports_tools())

    def test_calculate_cost_with_prices(self):
        from freechat import OpenAIProvider
        p = OpenAIProvider("key", "https://api.openai.com/v1")
        p.prices = {"gpt-4": {"input": 0.00003, "output": 0.00006}}
        cost = p.calculate_cost(1000, 500, "gpt-4")
        self.assertIsNotNone(cost)
        self.assertAlmostEqual(cost, 1000 * 0.00003 + 500 * 0.00006)

    def test_calculate_cost_unknown_model(self):
        from freechat import OpenAIProvider
        p = OpenAIProvider("key", "https://api.openai.com/v1")
        cost = p.calculate_cost(1000, 500, "unknown-model")
        self.assertIsNone(cost)


class TestGeminiProvider(unittest.TestCase):
    """Test GeminiProvider class"""

    def test_name(self):
        from freechat import GeminiProvider
        p = GeminiProvider("key")
        self.assertEqual(p.name, "gemini")

    def test_supports_tools(self):
        from freechat import GeminiProvider
        p = GeminiProvider("key")
        self.assertTrue(p.supports_tools())

    def test_calculate_cost(self):
        from freechat import GeminiProvider
        p = GeminiProvider("key")
        cost = p.calculate_cost(1000, 500, "gemini-1.5-pro-latest")
        self.assertIsNone(cost)

    def test_to_gemini_basic(self):
        from freechat import GeminiProvider
        p = GeminiProvider("key")
        msgs = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        result = p._to_gemini(msgs)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertIn("You are helpful", result[0]["parts"][0]["text"])

    def test_to_gemini_multi_turn(self):
        from freechat import GeminiProvider
        p = GeminiProvider("key")
        msgs = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"}
        ]
        result = p._to_gemini(msgs)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(result[1]["role"], "model")
        self.assertEqual(result[2]["role"], "user")

    def test_to_gemini_tool_calls(self):
        from freechat import GeminiProvider
        p = GeminiProvider("key")
        msgs = [
            {"role": "user", "content": "Search for X"},
            {"role": "assistant", "tool_calls": [
                {"function": {"name": "search", "arguments": '{"q":"X"}'}}
            ]}
        ]
        result = p._to_gemini(msgs)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["role"], "model")
        self.assertIn("search", result[1]["parts"][0]["text"])


if __name__ == '__main__':
    unittest.main()
