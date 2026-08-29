from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0011_post_content_hash_post_published_platforms_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='post_badge',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
