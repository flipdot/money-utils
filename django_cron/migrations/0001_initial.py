# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CronJobLog',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ('code', models.CharField(max_length=64, db_index=True)),
                ('start_time', models.DateTimeField(db_index=True)),
                ('end_time', models.DateTimeField(db_index=True)),
                ('is_success', models.BooleanField(default=False)),
                ('message', models.TextField(max_length=1000, blank=True)),
                (
                    'ran_at_time',
                    models.TimeField(
                        db_index=True, null=True, editable=False, blank=True
                    ),
                ),
            ],
        ),
        # Vendored from django-cron 0.6.0: the original AlterIndexTogether
        # operation was replaced by explicit AddIndex operations because
        # Meta.index_together was removed in Django 5.1. The names still
        # match what index_together generated (0004 renames them, because
        # they are longer than the 30 characters allowed for an explicit
        # models.Index).
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(
                fields=['code', 'is_success', 'ran_at_time'],
                name='django_cron_cronjoblog_code_is_success_ran_at_time_84da9606_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(
                fields=['code', 'start_time', 'ran_at_time'],
                name='django_cron_cronjoblog_code_start_time_ran_at_time_8b50b8fa_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(
                fields=['code', 'start_time'],
                name='django_cron_cronjoblog_code_start_time_4fc78f9d_idx',
            ),
        ),
    ]
