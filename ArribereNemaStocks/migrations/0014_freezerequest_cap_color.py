# Generated by Django 4.2.7 on 2023-12-22 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ArribereNemaStocks', '0013_alter_freezerequest_requester_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='freezerequest',
            name='cap_color',
            field=models.CharField(default='N/A', max_length=50),
        ),
    ]