---
name: bot-task-queue
description: >-
  Guides the safe scheduling, processing, and management of asynchronous bot tasks
  (BotTask model) for Telegram and Bale in Tafakor. Use whenever sending messages, editing posts,
  or deleting content on external messaging platforms.
---

# BotTask Queue & External Platform Synchronization

In Tafakor, interactions with Telegram and Bale (channels, groups, bots) are decoupled from the web request cycle through the `BotTask` model (`backend/apps/notes/models.py`).

## 1. Why BotTask?
- External APIs may experience network timeouts, latency, or proxy/VPN issues.
- Web requests must respond within milliseconds (< 200ms) without waiting for Telegram or Bale network round-trips.
- Provides automatic retry and logging for failed deliveries.

## 2. Standard Pattern: Creating a BotTask

Always create a `BotTask` instance through services rather than invoking Telegram/Bale libraries directly:

```python
from backend.apps.notes.models import BotTask

def schedule_post_broadcast(post, connection, action='send'):
    """
    Schedules an asynchronous broadcast task for Telegram or Bale.
    """
    return BotTask.objects.create(
        post=post,
        platform=connection.platform,       # 'telegram' or 'bale'
        chat_id=connection.chat_id,
        bot_token=connection.bot_token,
        task_type=action,                   # 'send', 'edit', 'delete'
        status=BotTask.Status.PENDING,
        content=post.content,
        meta_data={
            'topic_id': post.topic_id,
            'author_id': post.author_id,
        }
    )
```

## 3. Best Practices
1. **Never Call External API in Views:**  
   Do not import `telebot`, `telegram`, or `bale` client SDKs inside `views.py`.
2. **Handle Duplicate Messages:**  
   Before queueing a new `BotTask` for a post, check if an identical pending or completed task already exists using `content_hash` and `post_id`.
3. **Idempotency:**  
   Ensure worker scripts mark tasks as `PROCESSING` before executing and `DONE` or `FAILED` with error messages upon completion.

