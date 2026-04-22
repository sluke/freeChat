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
            category="context",
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


if __name__ == '__main__':
    unittest.main()
