# Generated manually for pending_review status choice and default update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0006_donationtransaction_payment_transaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donationcampaign',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending_review', 'در انتظار تأیید'),
                    ('active', 'در حال جمع\u200cآوری'),
                    ('completed', 'تکمیل\u200cشده'),
                    ('expired', 'منقضی\u200cشده'),
                    ('paused', 'متوقف/در حال بررسی'),
                    ('inactive', 'متوقف و غیرفعال\u200cشده'),
                ],
                default='active',
                max_length=20,
            ),
        ),
    ]

