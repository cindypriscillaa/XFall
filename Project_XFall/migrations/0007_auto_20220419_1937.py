# Generated by Django 3.2 on 2022-04-19 12:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Project_XFall', '0006_cameras_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationhistories',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Project_XFall.users'),
        ),
        migrations.AlterField(
            model_name='notificationhistories',
            name='created_date',
            field=models.DateTimeField(blank=True),
        ),
        migrations.AlterField(
            model_name='notificationhistories',
            name='updated_date',
            field=models.DateTimeField(blank=True),
        ),
        migrations.AlterField(
            model_name='notifications',
            name='created_date',
            field=models.DateTimeField(blank=True),
        ),
        migrations.AlterField(
            model_name='notifications',
            name='updated_date',
            field=models.DateTimeField(blank=True),
        ),
        migrations.AlterField(
            model_name='users',
            name='phone_number',
            field=models.PositiveIntegerField(blank=True, default='64'),
        ),
    ]
