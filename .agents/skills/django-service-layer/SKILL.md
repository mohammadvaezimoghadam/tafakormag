---
name: django-service-layer
description: >-
  Guides the creation and refactoring of Django business logic into dedicated service layers
  in Tafakor (backend/apps/*/services.py). Use whenever adding new business features,
  refactoring fat ViewSets, or orchestrating multi-model mutations and background side-effects.
---

# Django Service Layer Pattern for Tafakor

This skill enforces the Service Layer pattern across all apps in the Tafakor Django platform.

## Architecture Guidelines

1. **Separation of Concerns:**
   - **Views / ViewSets:** Parse HTTP request, validate serializer, check permissions, call service function, return `Response(data, status=...)`.
   - **Services (`services.py`):** Contain domain logic, transactional mutations, external API calls, task queueing, and business rules.
   - **Models (`models.py`):** Define fields, database constraints, property helpers, and model-instance-specific calculations.

2. **Standard Service Function Structure:**
   ```python
   # backend/apps/<app_name>/services.py
   import logging
   from django.db import transaction
   from rest_framework.exceptions import ValidationError

   logger = logging.getLogger(__name__)

   class SomeDomainService:
       @staticmethod
       @transaction.atomic
       def execute_action(user, validated_data):
           # 1. Validation of domain invariants
           if not user.is_active:
               raise ValidationError("حساب کاربری غیرفعال است.")

           # 2. Database mutations
           instance = Model.objects.create(...)

           # 3. Enqueue side effects (e.g. BotTask)
           BotTask.objects.create(...)

           logger.info("Successfully executed action for user %s", user.id)
           return instance
   ```

3. **Thin ViewSet Example:**
   ```python
   # backend/apps/<app_name>/views.py
   class PostViewSet(viewsets.ModelViewSet):
       ...
       @action(detail=True, methods=['post'], url_path='publish-to-bot')
       def publish_to_bot(self, request, pk=None):
           post = self.get_object()
           serializer = PublishSerializer(data=request.data)
           serializer.is_valid(raise_exception=True)

           # Delegate entirely to service:
           result = PostPublishService.publish(post=post, user=request.user, data=serializer.validated_data)
           return Response({'status': 'queued', 'task_id': result.id})
   ```

4. **Rules Checklist:**
   - [ ] No `Model.objects.create()` or `.update()` inside `@action` views if it involves more than 1 model or external side-effect.
   - [ ] Use `@transaction.atomic` in services when mutating multiple tables to guarantee consistency.
   - [ ] Return domain models or explicit dictionaries, not raw HTTP `Response` objects from services.

