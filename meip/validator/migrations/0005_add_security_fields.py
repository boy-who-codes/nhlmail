from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('validator', '0004_add_check_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailresult',
            name='has_spf',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='emailresult',
            name='has_dmarc',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='emailresult',
            name='spam_filter',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
