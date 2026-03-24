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

from freechat import FreeChatApp, ProviderFactory, AIProvider

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
default_model = "openrouter/stepfun/step-3.5-flash:free"
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
                self.app.current_model = "openrouter/stepfun/step-3.5-flash:free"
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
        self.assertEqual(self.app.current_model, "openrouter/stepfun/step-3.5-flash:free")
    
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
            mock_print.assert_called_with('[bold red]Error: Provider for \'invalid-provider/test-model\' not found.[/bold red]')
    
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
default_model = "openrouter/stepfun/step-3.5-flash:free"
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
default_model = "openrouter/stepfun/step-3.5-flash:free"
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
default_model = "openrouter/stepfun/step-3.5-flash:free"
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

if __name__ == '__main__':
    unittest.main()
