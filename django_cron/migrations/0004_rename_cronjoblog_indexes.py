# -*- coding: utf-8 -*-
from django.db import migrations, models

# The original index_together-based index names are longer than 30
# characters, which is not allowed for explicit models.Index. This
# migration renames them on existing databases.
#
# (old name, columns, new name)
OLD_TO_NEW = [
    (
        "django_cron_cronjoblog_code_is_success_ran_at_time_84da9606_idx",
        ["code", "is_success", "ran_at_time"],
        "cronjoblog_code_is_succ_ran",
    ),
    (
        "django_cron_cronjoblog_code_start_time_ran_at_time_8b50b8fa_idx",
        ["code", "start_time", "ran_at_time"],
        "cronjoblog_code_start_ran",
    ),
    (
        "django_cron_cronjoblog_code_start_time_4fc78f9d_idx",
        ["code", "start_time"],
        "cronjoblog_code_start",
    ),
]

TABLE = "django_cron_cronjoblog"


def _create(old, cols):
    return 'CREATE INDEX IF NOT EXISTS "%s" ON "%s" (%s);' % (
        old, TABLE, ", ".join('"%s"' % c for c in cols),
    )


sql = [
    'DROP INDEX IF EXISTS "%s";' % old for old, _, _ in OLD_TO_NEW
] + [_create(new, cols) for _, cols, new in OLD_TO_NEW]

reverse_sql = [
    'DROP INDEX IF EXISTS "%s";' % new for _, _, new in OLD_TO_NEW
] + [_create(old, cols) for old, cols, _ in OLD_TO_NEW]


class Migration(migrations.Migration):

    dependencies = [
        ('django_cron', '0003_cronjoblock'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveIndex(model_name='cronjoblog', name=old)
                for old, _, _ in OLD_TO_NEW
            ] + [
                migrations.AddIndex(
                    model_name='cronjoblog',
                    index=models.Index(fields=cols, name=new),
                )
                for _, cols, new in OLD_TO_NEW
            ],
            database_operations=[
                # IF EXISTS / IF NOT EXISTS make this idempotent, so it is
                # a no-op on databases where 0001 already created the new
                # names.
                migrations.RunSQL(sql=sql, reverse_sql=reverse_sql),
            ],
        ),
    ]
