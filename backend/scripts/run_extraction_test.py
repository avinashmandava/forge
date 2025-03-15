import os
import sys
import asyncio

# Add the parent directory to sys.path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_extraction import main

if __name__ == "__main__":
    asyncio.run(main())
