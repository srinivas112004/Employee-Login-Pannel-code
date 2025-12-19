# Generated manually for Day 3

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_user_is_email_verified_user_two_factor_enabled_and_more'),
    ]

    operations = [
        # Drop old table
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS user_devices;',
            reverse_sql='',  # Can't reverse this easily
        ),
        
        # Create new Device model
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_fingerprint', models.CharField(max_length=64, unique=True)),
                ('device_name', models.CharField(max_length=255)),
                ('device_type', models.CharField(max_length=50)),
                ('browser', models.CharField(blank=True, max_length=100, null=True)),
                ('browser_version', models.CharField(blank=True, max_length=50, null=True)),
                ('os', models.CharField(blank=True, max_length=100, null=True)),
                ('os_version', models.CharField(blank=True, max_length=50, null=True)),
                ('is_trusted', models.BooleanField(default=False)),
                ('last_used_at', models.DateTimeField(auto_now=True)),
                ('last_ip', models.GenericIPAddressField()),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_devices', to='authentication.user')),
            ],
            options={
                'verbose_name': 'User Device',
                'verbose_name_plural': 'User Devices',
                'db_table': 'user_devices',
                'ordering': ['-last_used_at'],
            },
        ),
        
        # Create UserSession model
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_token', models.TextField()),
                ('ip_address', models.GenericIPAddressField()),
                ('location', models.CharField(blank=True, max_length=255)),
                ('user_agent', models.TextField()),
                ('login_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('logout_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_suspicious', models.BooleanField(default=False)),
                ('flagged_reason', models.TextField(blank=True)),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='authentication.device')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='authentication.user')),
            ],
            options={
                'verbose_name': 'User Session',
                'verbose_name_plural': 'User Sessions',
                'db_table': 'user_sessions',
                'ordering': ['-login_at'],
            },
        ),
        
        # Add unique constraint
        migrations.AddConstraint(
            model_name='device',
            constraint=models.UniqueConstraint(fields=('user', 'device_fingerprint'), name='unique_user_device'),
        ),
    ]
