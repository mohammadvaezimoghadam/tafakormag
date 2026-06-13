import os
import sys
import base64
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add telegram_proxy directory to python path
proxy_path = Path(__file__).resolve().parent.parent.parent / "telegram_proxy"
sys.path.insert(0, str(proxy_path))

# Set dummy environment variables before importing local_proxy
os.environ["USE_PROXY_RELAY"] = "true"
os.environ["GAS_URL"] = "https://mock-gas-url.com/exec"
os.environ["RELAY_TOKEN"] = "mock-token"

import local_proxy
from aiohttp import web
from aiohttp.test_utils import TestServer, TestClient

class MockResponseContextManager:
    """Mock context manager for aiohttp ClientSession.post."""
    def __init__(self, response):
        self.response = response
    async def __aenter__(self):
        return self.response
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

import threading
import asyncio

def run_async(coro):
    result = []
    exception = []
    
    def target():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            val = loop.run_until_complete(coro)
            result.append(val)
        except BaseException as e:
            exception.append(e)
        finally:
            loop.close()
            
    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    
    if exception:
        raise exception[0]
    return result[0] if result else None

@patch("local_proxy.ClientSession.post")
def test_proxy_relay_success(mock_post):
    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", local_proxy.handle_relay)
    
    async def run_test():
        async with TestServer(app) as server:
            async with TestClient(server) as client:
                # 1. Setup mock response from Google Apps Script
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    "status": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body_base64": base64.b64encode(b'{"ok": true, "result": "mocked"}').decode("utf-8")
                })
                mock_post.return_value = MockResponseContextManager(mock_response)

                # 2. Make request to our proxy test client
                headers = {"X-Test-Header": "yes"}
                resp = await client.request("GET", "/bot12345/getMe", headers=headers)

                # 3. Assert proxy returned correct response
                assert resp.status == 200
                json_data = await resp.json()
                assert json_data["ok"] is True
                assert json_data["result"] == "mocked"

                # 4. Verify that ClientSession.post was called with correct payload
                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                assert args[0] == "https://mock-gas-url.com/exec"
                payload = kwargs["json"]
                assert payload["token"] == "mock-token"
                assert payload["targetUrl"] == "https://api.telegram.org/bot12345/getMe"
                assert payload["method"] == "GET"
                assert payload["headers"]["X-Test-Header"] == "yes"

    run_async(run_test())

@patch("local_proxy.ClientSession.post")
def test_proxy_relay_gas_error(mock_post):
    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", local_proxy.handle_relay)
    
    async def run_test():
        async with TestServer(app) as server:
            async with TestClient(server) as client:
                # 1. Setup mock response representing a GAS failure (e.g. 502)
                mock_response = MagicMock()
                mock_response.status = 502
                mock_response.text = AsyncMock(return_value="GAS Server Error")
                mock_post.return_value = MockResponseContextManager(mock_response)

                # 2. Make request to our proxy
                resp = await client.request("POST", "/bot12345/sendMessage", data="hello")

                # 3. Assert proxy returns 502
                assert resp.status == 502
                json_data = await resp.json()
                assert "error" in json_data
                assert json_data["details"] == "GAS Server Error"

    run_async(run_test())
