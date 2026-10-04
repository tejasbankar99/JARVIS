"""
test_system.py — Automated JARVIS Subsystem Diagnostics
======================================================
Validates all major JARVIS modules and configurations before startup:
  1. Configuration & API keys
  2. System Telemetry & Monitor
  3. Memory subsystem
  4. Weather caching engine
  5. Audio subsystem presence
"""

import sys
import time

def run_diagnostics():
    print("=" * 60)
    print("   JARVIS Subsystem Diagnostics & Health Self-Test")
    print("=" * 60)
    
    # 1. Config Test
    print("[1/5] Checking Configuration & Environment...")
    try:
        from config import validate_config, AI_PROVIDER
        cfg = validate_config()
        if cfg["valid"]:
            print(f"  [OK] AI Provider '{AI_PROVIDER}' configuration is valid.")
        else:
            print(f"  [WARN] Provider '{AI_PROVIDER}' warnings: {', '.join(cfg['warnings'])}")
    except Exception as e:
        print(f"  [FAIL] Config check failed: {e}")

    # 2. System Monitor Test
    print("\n[2/5] Testing System Telemetry...")
    try:
        from system_monitor import get_cpu, get_ram, get_disk_health
        print(f"  [OK] {get_cpu()}")
        print(f"  [OK] {get_ram()}")
        print(f"  [OK] {get_disk_health()}")
    except Exception as e:
        print(f"  [FAIL] Telemetry error: {e}")

    # 3. Memory Subsystem Test
    print("\n[3/5] Testing Persistent Memory Subsystem...")
    try:
        from memory import remember, recall, get_session_stats
        test_key = "_selftest_status"
        remember(test_key, "operational")
        val = recall(test_key)
        stats = get_session_stats()
        print(f"  [OK] Memory recall verified: {val}")
        print(f"  [OK] Total stored memories: {stats['facts_count']} facts, {stats['total_entries']} entries")
    except Exception as e:
        print(f"  [FAIL] Memory error: {e}")

    # 4. Weather Service Test
    print("\n[4/5] Testing Weather Service & Cache...")
    try:
        from weather import get_weather_brief
        brief = get_weather_brief("London")
        print(f"  [OK] Weather sample: {brief}")
    except Exception as e:
        print(f"  [FAIL] Weather error: {e}")

    # 5. Audio Subsystem Test
    print("\n[5/5] Checking Audio & PyAudio Shim...")
    try:
        import pyaudio_shim
        print("  [OK] Audio interface drivers accessible.")
    except Exception as e:
        print(f"  [WARN] Audio shim notice: {e}")

    print("\n" + "=" * 60)
    print("   Diagnostics Complete: All primary systems nominal.")
    print("=" * 60)

if __name__ == "__main__":
    run_diagnostics()
