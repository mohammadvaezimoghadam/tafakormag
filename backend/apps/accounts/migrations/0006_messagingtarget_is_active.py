from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_messagingtarget"),
    ]

    operations = [
        migrations.AddField(
            model_name="messagingtarget",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
