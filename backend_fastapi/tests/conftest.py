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

import inspect
import asyncio
import pytest

@pytest.fixture
def anyio_backend():
    return "asyncio"

def pytest_pyfunc_call(pyfuncitem):
    """Natively executes async def test functions with asyncio.run if pytest-asyncio plugin is not loaded."""
    if pyfuncitem.config.pluginmanager.has_plugin("asyncio"):
        return None
    if inspect.iscoroutinefunction(pyfuncitem.obj):
        argnames = pyfuncitem._fixtureinfo.argnames
        args = [pyfuncitem.funcargs[arg] for arg in argnames if arg in pyfuncitem.funcargs]
        asyncio.run(pyfuncitem.obj(*args))
        return True

