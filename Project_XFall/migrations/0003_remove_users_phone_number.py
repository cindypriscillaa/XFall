# Generated by Django 3.2 on 2022-04-04 16:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Project_XFall', '0002_alter_users_username'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='users',
            name='phone_number',
        ),
    ]