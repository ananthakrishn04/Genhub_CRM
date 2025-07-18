# Generated by Django 5.2.1 on 2025-06-27 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_alter_report_created_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='columns',
            field=models.JSONField(blank=True, default=list, help_text='Columns to include in the report', null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='email_recipients',
            field=models.JSONField(blank=True, default=list, help_text='Email addresses to send scheduled reports', null=True),
        ),
    ]
