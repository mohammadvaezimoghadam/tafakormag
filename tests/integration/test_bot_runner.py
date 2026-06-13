import os
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add bot_runner directory to python path
runner_path = Path(__file__).resolve().parent.parent.parent / "bot_runner"
sys.path.insert(0, str(runner_path))

# Set dummy environment variables before importing main to prevent loading active logs/configs
os.environ["BOT_API_KEY"] = "mock-key"

from main import format_text_for_telegram, task_processor, dynamic_bot_manager

def test_format_text_for_telegram():
    """Verify Markdown-to-HTML formatting helper function."""
    # Bold conversion
    assert format_text_for_telegram("hello **bold**") == "hello <b>bold</b>"
    # Italic conversion
    assert format_text_for_telegram("hello *italic*") == "hello <i>italic</i>"
    # Inline code conversion
    assert format_text_for_telegram("hello `code`") == "hello <code>code</code>"
    # Escaping HTML characters
    assert format_text_for_telegram("hello <world>") == "hello &lt;world&gt;"

class StopTestLoop(BaseException):
    """Exception raised to safely break out of the infinite task_processor/bot_manager loop."""
    pass

import threading

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

@patch("main.api_client")
@patch("main.post_with_retry")
def test_task_processor_success(mock_post_retry, mock_api_client):
    """Verify task processor fetches tasks, posts them, and marks them complete."""
    # Setup mock tasks
    mock_api_client.fetch_tasks = AsyncMock(return_value=[{
        "id": 1,
        "action": "send",
        "platform": "telegram",
        "chat_id": "12345",
        "text": "hello",
        "bot_token": "token",
        "media_type": "text",
        "media_url": None
    }])
    mock_api_client.complete_task = AsyncMock(return_value=True)

    # Mock post_with_retry returning status_code 200
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": {"message_id": "999"}}
    mock_post_retry.return_value = mock_resp

    # Patch asyncio.sleep to break the loop after first iteration
    async def mock_sleep(seconds):
        raise StopTestLoop()

    async def run_test():
        with patch("asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(StopTestLoop):
                await task_processor()

    run_async(run_test())

    # Assert fetch_tasks and complete_task were called
    mock_api_client.fetch_tasks.assert_called_once()
    mock_api_client.complete_task.assert_called_once_with(1, "999")
    mock_post_retry.assert_called_once()

@patch("main.api_client")
def test_dynamic_bot_manager_runs_bots(mock_api_client):
    """Verify dynamic bot manager launches tasks for active bots."""
    # Setup mock active custom bots
    mock_api_client.get_active_custom_bots = AsyncMock(return_value=[{
        "user_id": 42,
        "platform": "telegram",
        "token": "token42",
        "phone": "09123456789"
    }])

    # Patch run_single_bot and asyncio.sleep to break loop
    async def mock_sleep(seconds):
        raise StopTestLoop()

    async def run_test():
        with patch("main.run_single_bot") as mock_run_bot, patch("asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(StopTestLoop):
                await dynamic_bot_manager()

    run_async(run_test())

    mock_api_client.get_active_custom_bots.assert_called_once()
    # Check that a task was created in running_bots dict
    from main import running_bots
    assert "telegram_42" in running_bots
    # Cancel the running mock task to clean up
    running_bots["telegram_42"].cancel()
    running_bots.clear()

@patch("main.api_client")
@patch("main.post_with_retry")
def test_task_processor_rate_limit_429(mock_post_retry, mock_api_client):
    """Verify that HTTP 429 rate limit responses delay tasks instead of completing them."""
    # Setup mock tasks
    mock_api_client.fetch_tasks = AsyncMock(return_value=[{
        "id": 99,
        "action": "send",
        "platform": "telegram",
        "chat_id": "12345",
        "text": "rate limit test",
        "bot_token": "token",
        "media_type": "text",
        "media_url": None
    }])
    mock_api_client.complete_task = AsyncMock(return_value=True)

    # Mock post_with_retry returning status_code 429 with Retry-After header
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "15"}
    mock_post_retry.return_value = mock_resp

    # Patch asyncio.sleep to break the loop after first iteration
    async def mock_sleep(seconds):
        raise StopTestLoop()

    async def run_test():
        with patch("asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(StopTestLoop):
                await task_processor()

    run_async(run_test())

    # Assert fetch_tasks was called, but complete_task was NOT called
    mock_api_client.fetch_tasks.assert_called_once()
    mock_api_client.complete_task.assert_not_called()
    mock_post_retry.assert_called_once()

    # Verify that the task is stored in rate_limit_delays with delay
    from main import rate_limit_delays
    assert 99 in rate_limit_delays

    # Now let's test that the task is skipped when in rate_limit_delays
    import time
    rate_limit_delays[99] = time.time() + 10  # Delay for 10 seconds

    mock_api_client.fetch_tasks.reset_mock()
    mock_post_retry.reset_mock()
    mock_api_client.complete_task.reset_mock()

    run_async(run_test())

    # Fetch tasks should be called, but post_with_retry and complete_task should not!
    mock_api_client.fetch_tasks.assert_called_once()
    mock_post_retry.assert_not_called()
    mock_api_client.complete_task.assert_not_called()

    # Clean up
    rate_limit_delays.clear()
