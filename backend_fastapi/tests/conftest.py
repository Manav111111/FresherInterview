import os
import sys

# Ensure backend_fastapi directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure fresher_ai_kb directory is in sys.path
root_dir = os.path.dirname(backend_dir)
kb_dir = os.path.join(root_dir, "fresher_ai_kb")
if kb_dir not in sys.path:
    sys.path.insert(0, kb_dir)

import pytest

@pytest.fixture
def anyio_backend():
    return "asyncio"
