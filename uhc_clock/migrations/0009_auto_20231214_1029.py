# Generated by Django 3.0.14 on 2023-12-14 07:29

from django.db import migrations, models
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('regions', '__first__'),
        ('uhc_clock', '0008_auto_20231210_1723'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='facts_uhc_databaseview',
            options={'managed': False, 'ordering': ('indicator',), 'verbose_name': 'UHC Fact', 'verbose_name_plural': '   UHC-Clock Facts'},
        ),
        migrations.AlterModelOptions(
            name='stguhcindicatortheme',
            options={'managed': True, 'ordering': ('level',), 'verbose_name': 'UHC Theme', 'verbose_name_plural': '  UHC Clock Themes'},
        ),
        migrations.AlterModelOptions(
            name='stguhclockindicators',
            options={'managed': True, 'ordering': ('indicator',), 'verbose_name': 'UHC Indicator', 'verbose_name_plural': '   UHC Indicators'},
        ),
        migrations.AlterModelOptions(
            name='stguhclockindicatorsgroup',
            options={'managed': True, 'ordering': ('translations__name',), 'verbose_name': 'Group', 'verbose_name_plural': '  Indicator Groups'},
        ),
        migrations.AlterField(
            model_name='stguhcindicatortheme',
            name='indicators',
            field=smart_selects.db_fields.ChainedManyToManyField(blank=True, chained_field='group', chained_model_field='group', horizontal=True, limit_choices_to={'indicator__translations__language_code': 'en'}, to='uhc_clock.StgUHClockIndicators', verbose_name='indicators'),
        ),
        migrations.AlterField(
            model_name='stguhcindicatortheme',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='uhc_clock.StgUHCIndicatorTheme', verbose_name='Parent Theme'),
        ),
        migrations.AlterField(
            model_name='stguhclockindicators',
            name='Indicator_type',
            field=models.CharField(choices=[('1', 'Input'), ('2', 'Process'), ('3', 'Output'), ('4', 'Outcomes'), ('5', 'Impact')], default='1', max_length=5, verbose_name='Indicator Type'),
        ),
        migrations.CreateModel(
            name='CountrySelectionUHCIndicators',
            fields=[
                ('countrychoice_id', models.AutoField(primary_key=True, serialize=False)),
                ('domain', models.ManyToManyField(default=None, to='uhc_clock.StgUHCIndicatorTheme', verbose_name='UHC Clock Theme')),
                ('indicators', smart_selects.db_fields.ChainedManyToManyField(blank=True, chained_field='domain', chained_model_field='group', horizontal=True, limit_choices_to={'indicator__translations__language_code': 'en'}, to='uhc_clock.StgUHClockIndicators')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='regions.StgLocation', verbose_name='Country/Location')),
            ],
            options={
                'verbose_name': 'Country Selection',
                'verbose_name_plural': 'Country Selections',
                'db_table': 'stg_uhclock_country_indicators_selection',
                'ordering': ('location',),
                'managed': True,
            },
        ),
    ]