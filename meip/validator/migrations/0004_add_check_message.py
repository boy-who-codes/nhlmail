from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('validator', '0003_validationbatch_current_processing_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailresult',
            name='check_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
