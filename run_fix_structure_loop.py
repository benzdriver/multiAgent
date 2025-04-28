#!/usr/bin/env python3
from fixer.structure_loop import run_fix_loop
import asyncio

if __name__ == "__main__":
    print("🔄 Starting architecture validation and fix loop...")
    asyncio.run(run_fix_loop()) 