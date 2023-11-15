# Generated by Django 3.0.14 on 2023-11-15 20:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uhc_clock', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stguhcindicatorgroup',
            name='level',
            field=models.SmallIntegerField(choices=[(1, 'level 1'), (2, 'level 2')], default=1, verbose_name='Theme Level'),
        ),
        migrations.AddField(
            model_name='stguhcindicatorgroup',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='uhc_clock.StgUHCIndicatorGroup', verbose_name='Parent UHC Theme'),
        ),
    ]