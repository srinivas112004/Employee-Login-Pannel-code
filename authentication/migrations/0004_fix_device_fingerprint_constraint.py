# Generated manually to fix device_fingerprint unique constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_day3_device_session_management'),
    ]

    operations = [
        # Remove unique constraint from device_fingerprint field
        migrations.AlterField(
            model_name='device',
            name='device_fingerprint',
            field=models.CharField(max_length=64),
        ),
    ]
