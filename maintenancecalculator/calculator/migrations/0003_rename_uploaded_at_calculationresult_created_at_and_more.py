# Generated by Django 5.1 on 2024-08-16 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0002_calculationresult'),
    ]

    operations = [
        migrations.RenameField(
            model_name='calculationresult',
            old_name='uploaded_at',
            new_name='created_at',
        ),
        migrations.AlterField(
            model_name='calculationresult',
            name='file_path',
            field=models.CharField(max_length=255),
        ),
    ]