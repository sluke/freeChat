#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance test script for FreeChat
"""

import time
import subprocess
import sys

def test_startup_time():
    """Test application startup time"""
    print("Testing startup time...")
    start_time = time.time()
    
    # Run the application and send Ctrl+C to exit immediately
    try:
        process = subprocess.Popen(
            [sys.executable, "freechat.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it time to initialize
        time.sleep(3)
        
        # Send Ctrl+C to exit
        process.terminate()
        process.wait(timeout=5)
        
    except subprocess.TimeoutExpired:
        print("Startup test timed out")
        return None
    except Exception as e:
        print(f"Error during startup test: {e}")
        return None
    
    end_time = time.time()
    startup_time = end_time - start_time
    print(f"Startup time: {startup_time:.2f} seconds")
    return startup_time

def test_memory_usage():
    """Test memory usage (simplified)"""
    print("\nTesting memory usage...")
    try:
        # Use psutil if available
        import psutil
        import os
        
        # Start a subprocess
        process = subprocess.Popen(
            [sys.executable, "freechat.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it time to initialize
        time.sleep(2)
        
        # Check memory usage
        p = psutil.Process(process.pid)
        memory_info = p.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        print(f"Memory usage: {memory_mb:.2f} MB")
        
        # Terminate the process
        process.terminate()
        process.wait(timeout=5)
        
        return memory_mb
    except ImportError:
        print("psutil not available, skipping memory test")
        return None
    except Exception as e:
        print(f"Error during memory test: {e}")
        return None

def main():
    print("FreeChat Performance Test")
    print("=" * 50)
    
    startup_time = test_startup_time()
    memory_usage = test_memory_usage()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Startup time: {startup_time:.2f}s" if startup_time else "Startup test failed")
    print(f"Memory usage: {memory_usage:.2f}MB" if memory_usage else "Memory test failed")
    print("=" * 50)

if __name__ == "__main__":
    main()
