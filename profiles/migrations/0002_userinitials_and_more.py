# Generated by Django 4.2.9 on 2024-01-28 21:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserInitials',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('initials', models.CharField(max_length=4, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='historicaluserprofile',
            name='other_associated_initials',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='other_associated_initials',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='all_associated_initials',
            field=models.ManyToManyField(related_name='user_profile_all_associated', to='profiles.userinitials'),
        ),
        migrations.AlterField(
            model_name='historicaluserprofile',
            name='initials',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='profiles.userinitials'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='initials',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_profile', to='profiles.userinitials'),
        ),
    ]