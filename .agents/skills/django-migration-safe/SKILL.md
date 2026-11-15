---
name: django-migration-safe
description: >-
  Provides safe schema migration guidelines for PostgreSQL in Tafakor, avoiding table locks,
  downtime, and data corruption on high-volume tables like Post, Topic, and UserSubscription.
  Use when adding fields, modifying constraints, or renaming columns.
---

# Safe Django Database Migrations Guide

The Tafakor platform handles active user notes, real-time bot broadcasts, and subscription transactions. Migrations must be designed to avoid exclusive table locks (`ACCESS EXCLUSIVE`) that freeze the database.

## 1. Safe Patterns by Operation

### Adding a New Column
- **Safe:** Add with `null=True, blank=True` or a constant `default=...` (in Django 3.1+ / Postgres 11+, adding columns with non-volatile defaults is fast and does not rewrite the table).
- **Dangerous:** Adding a field with `null=False` and a dynamic callable default like `default=timezone.now` without batching.

### Adding an Index
- For large tables (e.g. `Post`, `BotTask`), avoid blocking indexes during peak hours.
- Prefer `AddIndexConcurrently` from `django.contrib.postgres.operations` when adding indexes to production tables.

### Renaming a Column or Table
- **Never rename directly:** Renaming in a single migration causes immediate downtime because running backend code will query the old column name while the database has the new one.
- **Use the Expand/Contract Pattern:**
  1. Add the new column (nullable).
  2. Write to both old and new columns in code (dual writing).
  3. Backfill data from old column to new column via data migration.
  4. Switch reading to new column.
  5. Remove old column in a subsequent release.

## 2. Pre-Migration Checklist
- [ ] Has a database backup been created before running `migrate` on production?
- [ ] Does the migration contain any data-loss operations (`RemoveField`, `DeleteModel`)? Confirm with the team first.
- [ ] Have you tested the migration locally with `python manage.py migrate` and `python manage.py migrate <app> <previous_migration_number>` to ensure reversibility?

