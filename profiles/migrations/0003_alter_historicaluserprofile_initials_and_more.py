# Generated by Django 4.2.9 on 2024-01-28 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_userinitials_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaluserprofile',
            name='initials',
            field=models.CharField(db_index=True, max_length=4),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='initials',
            field=models.CharField(max_length=4, unique=True),
        ),
    ]