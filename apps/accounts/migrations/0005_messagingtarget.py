# Generated manually for MessagingTarget

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_alter_botconnectiontoken_platform"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessagingTarget",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "platform",
                    models.CharField(
                        choices=[("telegram", "Telegram"), ("bale", "Bale")],
                        max_length=10,
                    ),
                ),
                ("chat_id", models.CharField(max_length=100)),
                ("label", models.CharField(max_length=255)),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messaging_targets",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="messagingtarget",
            constraint=models.UniqueConstraint(
                fields=("user", "platform", "chat_id"),
                name="unique_user_platform_chat",
            ),
        ),
    ]
