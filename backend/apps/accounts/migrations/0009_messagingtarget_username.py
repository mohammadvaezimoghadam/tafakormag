from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_user_bale_bot_disconnect_reason_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagingtarget',
            name='username',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
