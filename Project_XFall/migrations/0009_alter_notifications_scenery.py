# Generated by Django 3.2 on 2022-05-14 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Project_XFall', '0008_alter_notifications_scenery'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifications',
            name='scenery',
            field=models.ImageField(blank=True, upload_to=''),
        ),
    ]
