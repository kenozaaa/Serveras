# Generated by Django 5.1 on 2024-08-16 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0003_rename_uploaded_at_calculationresult_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calculationresult',
            name='file_path',
            field=models.CharField(max_length=1024),
        ),
    ]
