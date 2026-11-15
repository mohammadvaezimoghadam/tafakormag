---
name: django-n1-audit
description: >-
  Audits and optimizes Django ORM querysets to eliminate N+1 query problems in DRF ViewSets,
  list endpoints, and nested serializers across the Tafakor backend. Use when modifying models,
  adding relations to serializers, or optimizing slow API responses.
---

# Django N+1 Query Audit & Optimization Guide

In Tafakor, models like `Topic`, `Post`, and `Subscription` have multiple one-to-many and many-to-many relations. Without explicit pre-loading, DRF serializers will trigger a separate SQL query for every single row returned.

## 1. Golden Decision Matrix

| Relationship Type | ORM Method to Use | Example in Tafakor |
| :--- | :--- | :--- |
| **ForeignKey (1-N direct)** | `.select_related(...)` | `Post.objects.select_related('topic', 'author')` |
| **OneToOne (1-1)** | `.select_related(...)` | `User.objects.select_related('profile')` |
| **Reverse ForeignKey (N-1 inverse)** | `.prefetch_related(...)` | `Topic.objects.prefetch_related('telegram_connections')` |
| **ManyToMany (M-N)** | `.prefetch_related(...)` | `Post.objects.prefetch_related('tags', 'reactions')` |
| **Filtered Reverse Relation** | `Prefetch(..., queryset=...)` | Custom filtered prefetch for active subscriptions |

## 2. Standard ViewSet Queryset Optimization Pattern

```python
# backend/apps/notes/views.py
from django.db.models import Prefetch

class PostViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Post.objects.filter(is_deleted=False)\
            .select_related('topic', 'author')\
            .prefetch_related(
                'tags',
                'reactions',
                'comments__author',
                Prefetch(
                    'topic__telegram_connections',
                    queryset=TelegramConnection.objects.filter(is_active=True)
                )
            )\
            .order_by('-created_at')
```

## 3. Serializer N+1 Pitfalls to Avoid

- **Property Methods accessing DB:** Avoid adding `@property` on a model that executes `.count()` or `.filter()` without caching or annotations (use `annotate()` in queryset instead).
- **SerializerMethodField:** If a `SerializerMethodField` accesses a related model, ensure that related model is in `select_related` or `prefetch_related`.

## 4. Verification Step

To verify query count during testing or development:
```python
from django.db import connection, reset_queries

reset_queries()
# Execute view or service call
response = client.get('/api/notes/posts/')
print(f"Total queries: {len(connection.queries)}")
# Should be a constant number (e.g., 2 to 4 queries), NOT proportional to row count!
```

