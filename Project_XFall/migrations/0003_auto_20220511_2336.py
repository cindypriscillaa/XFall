# Generated by Django 3.2 on 2022-05-11 23:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Project_XFall', '0002_userverificationlogs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userverificationlogs',
            name='username',
        ),
        migrations.AddField(
            model_name='userverificationlogs',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Project_XFall.users'),
            preserve_default=False,
        ),
    ]
