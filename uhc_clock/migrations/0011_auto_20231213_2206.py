# Generated by Django 3.0.14 on 2023-12-13 19:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uhc_clock', '0010_auto_20231213_2106'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='countryselectionuhcindicators',
            name='id',
        ),
        migrations.AddField(
            model_name='countryselectionuhcindicators',
            name='country_id',
            field=models.AutoField(default=1, primary_key=True, serialize=False),
            preserve_default=False,
        ),
    ]
