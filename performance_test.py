#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance test script for FreeChat
"""

import time
import subprocess
import sys
import asyncio
import os
import tempfile
from pathlib import Path

# Ensure dependencies are available before importing freechat
import importlib.util
required_specs = ["rich", "httpx", "tiktoken", "prompt_toolkit"]
missing = [name for name in required_specs if not importlib.util.find_spec(name)]
if missing:
    print(f"Missing dependencies for micro-benchmarks: {missing}")
    print("Skipping micro-benchmarks. Install dependencies to run full suite.")
    HAS_DEPS = False
else:
    HAS_DEPS = True
    import freechat


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


# --- Micro-benchmarks ---

async def benchmark_streaming_latency():
    """Benchmark streaming loop latency by measuring concurrent counter progress."""
    print("\n[Micro-benchmark] Streaming latency...")
    app = freechat.FreeChatApp()

    counter = [0]
    stop = [False]

    async def ticker():
        while not stop[0]:
            counter[0] += 1
            await asyncio.sleep(0)

    async def mock_stream():
        for i in range(1000):
            yield f"chunk {i} "

    ticker_task = asyncio.create_task(ticker())
    start = time.time()
    buffer_len = 0
    async for chunk in mock_stream():
        app._stream_buffer.append(chunk)
        buffer_len += len(chunk)
        if buffer_len >= app._STREAM_BUFFER_THRESHOLD:
            await app._flush_stream_buffer_async()
            buffer_len = 0
    if app._stream_buffer:
        await app._flush_stream_buffer_async()
    elapsed = time.time() - start
    stop[0] = True
    await ticker_task

    print(f"  Time for 1000 chunks: {elapsed:.4f}s")
    print(f"  Concurrent ticker increments: {counter[0]}")
    return elapsed, counter[0]


def benchmark_find_similar():
    """Benchmark find_similar with many memories."""
    print("\n[Micro-benchmark] find_similar with 2000 memories...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "memories.db"
        store = freechat.SQLiteMemoryStore(db_path)

        # Insert 2000 synthetic memories
        start = time.time()
        for i in range(2000):
            entry = freechat.MemoryEntry(
                id=f"mem_{i}",
                content=f"This is a synthetic memory about topic {i % 50} with some common words like python code async await",
                category="test",
                source="benchmark",
                created_at=time.time(),
                updated_at=time.time(),
                importance=5,
                tags=["benchmark", f"topic{i % 50}"],
            )
            store.insert_memory(entry)
        insert_time = time.time() - start

        start = time.time()
        results = store.find_similar("python async await code", threshold=0.1)
        query_time = time.time() - start
        store.close()

    print(f"  Insert 2000 memories: {insert_time:.4f}s")
    print(f"  find_similar query: {query_time:.4f}s (results: {len(results)})")
    return query_time


def benchmark_token_cache_memory():
    """Benchmark token cache respects byte limit."""
    print("\n[Micro-benchmark] Token cache memory limit...")
    app = freechat.FreeChatApp()
    # Force tokenizer to exist for test
    if not app.tokenizer:
        print("  Skipped: tiktoken not available")
        return None

    start = time.time()
    for i in range(1000):
        size = (i % 20 + 1) * 100  # 100 to 2000 bytes
        text = "x" * size
        app._count_tokens(text)
    elapsed = time.time() - start

    print(f"  1000 inserts time: {elapsed:.4f}s")
    print(f"  Cache entries: {len(app._token_cache)}")
    print(f"  Cache bytes: {app._token_cache_bytes} (limit: {app.MAX_TOKEN_CACHE_BYTES})")
    assert app._token_cache_bytes <= app.MAX_TOKEN_CACHE_BYTES, "Cache exceeded byte limit!"
    assert len(app._token_cache) <= 1000, "Cache exceeded entry limit!"
    return elapsed, app._token_cache_bytes


def benchmark_compression_batch():
    """Benchmark batch compression update vs old per-entry approach."""
    print("\n[Micro-benchmark] Memory compression batch update...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "memories.db"
        manager = freechat.MemoryManager(db_path, max_global=50, max_branch=25)

        # Insert 500 memories
        for i in range(500):
            manager.remember(
                content=f"Memory content number {i} with enough text to be meaningful for compression testing",
                category="benchmark",
                importance=5,
                tags=["test", f"item{i}"]
            )

        start = time.time()
        compressed = manager.compress_memories()
        elapsed = time.time() - start
        manager.close()

    print(f"  Compressed {compressed} memories in {elapsed:.4f}s")
    return elapsed, compressed


def main():
    print("FreeChat Performance Test")
    print("=" * 50)

    startup_time = test_startup_time()
    memory_usage = test_memory_usage()

    if HAS_DEPS:
        print("\n" + "=" * 50)
        print("Running micro-benchmarks...")
        print("=" * 50)

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(benchmark_streaming_latency())
        except Exception as e:
            print(f"  Streaming benchmark failed: {e}")

        try:
            benchmark_find_similar()
        except Exception as e:
            print(f"  find_similar benchmark failed: {e}")

        try:
            benchmark_token_cache_memory()
        except Exception as e:
            print(f"  Token cache benchmark failed: {e}")

        try:
            benchmark_compression_batch()
        except Exception as e:
            print(f"  Compression benchmark failed: {e}")
    else:
        print("\nMicro-benchmarks skipped due to missing dependencies.")

    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Startup time: {startup_time:.2f}s" if startup_time else "Startup test failed")
    print(f"Memory usage: {memory_usage:.2f}MB" if memory_usage else "Memory test failed")
    print("=" * 50)


if __name__ == "__main__":
    main()
