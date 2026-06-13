import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add bot_runner directory to python path
runner_path = Path(__file__).resolve().parent.parent.parent / "bot_runner"
sys.path.insert(0, str(runner_path))

# Set dummy environment variables before importing telegram_bot
os.environ["BOT_API_KEY"] = "mock-key"

import telegram_bot
from telegram_bot import (
    start,
    help_command,
    register_chat,
    handle_token,
    WELCOME_TEXT,
    HELP_TEXT,
    HOW_TO_REGISTER_TEXT
)

# Reuse the run_async runner helper
import asyncio
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

@pytest.fixture
def mock_update_context():
    # Setup mock update
    update = MagicMock()
    update.effective_chat.id = 123456
    update.effective_chat.type = "private"
    update.effective_user.id = 123456
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.delete = AsyncMock()
    update.message.text = "test_text"
    
    # Setup mock context
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    return update, context

@patch("telegram_bot.is_user_linked")
def test_start_handler_linked_user(mock_linked, mock_update_context):
    """Verify start handler behaves correctly when the user is already linked."""
    update, context = mock_update_context
    mock_linked.return_value = AsyncMock()
    mock_linked.return_value = True

    run_async(start(update, context))

    update.message.reply_text.assert_called_once()
    # Should reply with welcome text and keyboard
    args, kwargs = update.message.reply_text.call_args
    assert args[0] == WELCOME_TEXT

@patch("telegram_bot.is_user_linked")
def test_start_handler_unlinked_user(mock_linked, mock_update_context):
    """Verify start handler prompts to share phone/token when the user is not linked."""
    update, context = mock_update_context
    mock_linked.return_value = AsyncMock()
    mock_linked.return_value = False

    run_async(start(update, context))

    update.message.reply_text.assert_called_once()
    args, kwargs = update.message.reply_text.call_args
    assert "به ربات تفکر خوش آمدید!" in args[0]
    assert "شماره موبایل خود را به اشتراک بگذارید" in args[0]

@patch("telegram_bot.is_user_linked")
def test_help_command(mock_linked, mock_update_context):
    """Verify help command displays instructions."""
    update, context = mock_update_context
    mock_linked.return_value = AsyncMock()
    mock_linked.return_value = True

    run_async(help_command(update, context))

    update.message.reply_text.assert_called_once()
    args, kwargs = update.message.reply_text.call_args
    assert args[0] == HELP_TEXT

def test_register_chat_in_private_chat(mock_update_context):
    """Verify register_chat fails with warning if run in a private chat."""
    update, context = mock_update_context
    update.effective_chat.type = "private"

    run_async(register_chat(update, context))

    update.message.reply_text.assert_called_once_with(
        "⚠️ این دستور فقط در گروه‌ها و کانال‌ها قابل استفاده است."
    )

@patch("telegram_bot.api_client")
def test_register_chat_success(mock_api_client, mock_update_context):
    """Verify register_chat succeeds and registers target for group/channel chats."""
    update, context = mock_update_context
    update.effective_chat.type = "group"
    update.effective_chat.id = -987654
    update.effective_chat.title = "گروه تستی تفکر"
    update.effective_user.id = 555
    
    mock_api_client.get_user_id_by_chat = AsyncMock(return_value=12)
    mock_api_client.register_destination = AsyncMock()

    run_async(register_chat(update, context))

    # Should register destination with label and user_id
    mock_api_client.get_user_id_by_chat.assert_called_once_with("telegram", 555)
    mock_api_client.register_destination.assert_called_once_with(
        12, "telegram", "-987654", "گروه تستی تفکر"
    )
    # Should send private success message to the registering user
    context.bot.send_message.assert_called_once()
    kwargs = context.bot.send_message.call_args[1]
    assert kwargs["chat_id"] == 555
    assert "✅ *مقصد با موفقیت ثبت شد!*" in kwargs["text"]

@patch("telegram_bot.is_user_linked")
@patch("telegram_bot.api_client")
def test_handle_token_success(mock_api_client, mock_linked, mock_update_context):
    """Verify token validation links account successfully."""
    update, context = mock_update_context
    update.message.text = "  my-secret-token  "
    update.effective_chat.id = 123456
    update.effective_user.id = 123456
    
    mock_api_client.verify_link = AsyncMock()
    mock_linked.return_value = AsyncMock()
    mock_linked.return_value = True

    run_async(handle_token(update, context))

    # Verify link should be called with stripped token
    mock_api_client.verify_link.assert_called_once_with("my-secret-token", "telegram", 123456)
    
    # Success message should be sent to the user
    context.bot.send_message.assert_called_once()
    args, kwargs = context.bot.send_message.call_args
    assert args[0] == 123456
    assert "✅ *حساب شما با موفقیت به ربات متصل شد!*" in args[1]
