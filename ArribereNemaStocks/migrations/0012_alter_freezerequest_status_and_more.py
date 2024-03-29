# Generated by Django 4.2.9 on 2024-01-29 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ArribereNemaStocks', '0011_alter_historicaltube_date_thawed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='freezerequest',
            name='status',
            field=models.CharField(choices=[('R', 'Requested'), ('A', 'Advanced/Testing'), ('C', 'Completed'), ('F', 'Failed'), ('X', 'Cancelled')], default='R', max_length=1),
        ),
        migrations.AlterField(
            model_name='historicalfreezerequest',
            name='status',
            field=models.CharField(choices=[('R', 'Requested'), ('A', 'Advanced/Testing'), ('C', 'Completed'), ('F', 'Failed'), ('X', 'Cancelled')], default='R', max_length=1),
        ),
    ]
