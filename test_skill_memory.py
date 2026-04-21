#!/usr/bin/env python3
"""
Test suite for Skill and Memory system functionality.
"""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
import freechat


class TestSkillSystem(unittest.TestCase):
    """Test cases for Skill system."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.skills_dir = Path(self.temp_dir) / "skills"
        self.skills_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_skill_metadata_creation(self):
        """Test SkillMetadata creation."""
        metadata = freechat.SkillMetadata(
            name="test-skill",
            version="1.0.0",
            description="A test skill",
            author="Test Author"
        )
        self.assertEqual(metadata.name, "test-skill")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.description, "A test skill")

    def test_skill_metadata_from_toml(self):
        """Test SkillMetadata from TOML data."""
        toml_data = {
            "skill": {
                "name": "test-skill",
                "version": "1.0.0",
                "description": "A test skill",
                "author": "Test Author",
                "entry_point": "main:initialize"
            }
        }
        metadata = freechat.SkillMetadata.from_toml(toml_data)
        self.assertEqual(metadata.name, "test-skill")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.entry_point, "main:initialize")

    def test_skill_registry_initialization(self):
        """Test SkillRegistry initialization."""
        # Create a mock tool registry
        mock_tool_registry = MagicMock()

        registry = freechat.SkillRegistry(self.skills_dir, mock_tool_registry)

        self.assertIsInstance(registry, freechat.SkillRegistry)
        self.assertEqual(len(registry.list_skills()), 0)


class TestMemorySystem(unittest.TestCase):
    """Test cases for Memory system."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_db = Path(self.temp_dir) / "memories.db"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_memory_entry_creation(self):
        """Test MemoryEntry creation."""
        entry = freechat.MemoryEntry()
        self.assertIsInstance(entry, freechat.MemoryEntry)
        self.assertEqual(entry.id, "")
        self.assertEqual(entry.content, "")
        self.assertEqual(entry.category, "general")

    def test_memory_entry_with_values(self):
        """Test MemoryEntry with custom values."""
        entry = freechat.MemoryEntry(
            id="test-id",
            content="Test memory content",
            category="test",
            importance=8
        )
        self.assertEqual(entry.id, "test-id")
        self.assertEqual(entry.content, "Test memory content")
        self.assertEqual(entry.category, "test")
        self.assertEqual(entry.importance, 8)

    def test_sqlite_memory_store_initialization(self):
        """Test SQLiteMemoryStore initialization with string path."""
        store = freechat.SQLiteMemoryStore(str(self.memory_db))
        self.assertIsInstance(store, freechat.SQLiteMemoryStore)

        # Verify tables were created
        import sqlite3
        conn = sqlite3.connect(str(self.memory_db))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn("memories", tables)

    def test_sqlite_memory_store_with_path_object(self):
        """Test SQLiteMemoryStore initialization with Path object."""
        store = freechat.SQLiteMemoryStore(self.memory_db)
        self.assertIsInstance(store, freechat.SQLiteMemoryStore)

    def test_memory_manager_initialization(self):
        """Test MemoryManager initialization with string path."""
        manager = freechat.MemoryManager(str(self.memory_db))
        self.assertIsInstance(manager, freechat.MemoryManager)

    def test_memory_manager_remember_and_recall(self):
        """Test MemoryManager remember and recall."""
        manager = freechat.MemoryManager(str(self.memory_db))

        # Store a memory
        memory_id = manager.remember("Python is a great programming language", importance=8)
        self.assertIsNotNone(memory_id)
        self.assertTrue(memory_id.startswith("mem_"))


class TestCommandHandlers(unittest.TestCase):
    """Test cases for command handlers."""

    def test_skill_command_exists(self):
        """Test that _handle_skill_command method exists."""
        self.assertTrue(hasattr(freechat.FreeChatApp, '_handle_skill_command'))

    def test_memory_command_exists(self):
        """Test that _handle_memory_command method exists."""
        self.assertTrue(hasattr(freechat.FreeChatApp, '_handle_memory_command'))


async def run_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSkillSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestMemorySystem))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandHandlers))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
