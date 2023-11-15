# Generated by Django 3.0.14 on 2023-11-15 07:34

from django.db import migrations, models
import django.db.models.deletion
import parler.fields
import parler.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('indicators', '0007_auto_20230124_1019'),
    ]

    operations = [
        migrations.CreateModel(
            name='Facts_UHC_DatabaseView',
            fields=[
                ('fact_id', models.AutoField(primary_key=True, serialize=False)),
                ('uhc_theme', models.CharField(blank=True, max_length=500, null=True, verbose_name='UHC Theme')),
                ('indicator_code', models.CharField(blank=True, max_length=10, null=True, verbose_name='Indicator Code')),
                ('indicator_name', models.CharField(blank=True, max_length=200, null=True, verbose_name='Indicator Name')),
                ('location', models.CharField(max_length=500, verbose_name='Location Name')),
                ('categoryoption', models.CharField(max_length=500, verbose_name='Disaggregation Options')),
                ('datasource', models.CharField(max_length=500, verbose_name='Data Source')),
                ('measure_type', models.CharField(max_length=500, verbose_name='Measure Type')),
                ('value_received', models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True, verbose_name='Numeric Value')),
                ('start_period', models.PositiveIntegerField(blank=True, verbose_name='Start Year')),
                ('end_period', models.PositiveIntegerField(blank=True, verbose_name='End Year')),
                ('period', models.CharField(blank=True, max_length=25, verbose_name='Period')),
                ('comment', models.CharField(blank=True, max_length=25, verbose_name='Status')),
            ],
            options={
                'verbose_name': 'UHC Fact',
                'verbose_name_plural': ' UHC Facts',
                'db_table': 'vw_uhc_clock_fact_indicators',
                'ordering': ('indicator_name',),
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='StgUHCIndicatorGroup',
            fields=[
                ('domain_id', models.AutoField(primary_key=True, serialize=False)),
                ('uuid', models.CharField(default=uuid.uuid4, editable=False, max_length=36, unique=True, verbose_name='Unique ID')),
                ('code', models.CharField(blank=True, max_length=45, null=True, unique=True, verbose_name='Code')),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Date Created')),
                ('date_lastupdated', models.DateTimeField(auto_now=True, null=True, verbose_name='Date Modified')),
                ('indicators', models.ManyToManyField(blank=True, db_table='stg_uhc_clock_domain_members', to='indicators.StgIndicator', verbose_name='Indicators')),
            ],
            options={
                'verbose_name': 'UHC Theme',
                'verbose_name_plural': ' UHC Themes',
                'db_table': 'stg_uhc_indicator_themes',
                'ordering': ('translations__name',),
                'managed': True,
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='StgUHCIndicatorGroupTranslation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                ('name', models.CharField(max_length=150, verbose_name='UHC Clock Theme')),
                ('shortname', models.CharField(max_length=45, verbose_name='Short Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Brief Description')),
                ('master', parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='uhc_clock.StgUHCIndicatorGroup')),
            ],
            options={
                'verbose_name': 'UHC Theme Translation',
                'db_table': 'stg_uhc_indicator_themes_translation',
                'db_tablespace': '',
                'managed': True,
                'default_permissions': (),
                'unique_together': {('language_code', 'master')},
            },
            bases=(parler.models.TranslatedFieldsModelMixin, models.Model),
        ),
    ]
