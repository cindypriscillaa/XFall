# Generated by Django 3.2 on 2022-05-13 23:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Project_XFall', '0003_auto_20220511_2336'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='profile_image',
            field=models.TextField(blank=True),
        ),
    ]
