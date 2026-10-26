# -*- coding: utf-8 -*-
from django.db import migrations, models

# Meta.unique_together was removed in Django 5.1. This migration records
# the equivalent constraint in the migration state and creates the index
# on databases that are missing it (fresh installs, because the
# unique_together option in 0001_initial no longer creates an index).
#
# The index name matches the one unique_together used to generate, so on
# existing databases the index already exists and IF NOT EXISTS is a no-op.


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0008_alter_transaction_original_amount'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterUniqueTogether(
                    name='feeentry',
                    unique_together=set(),
                ),
                migrations.AddConstraint(
                    model_name='feeentry',
                    constraint=models.UniqueConstraint(
                        fields=['member', 'month'],
                        name='fee_entry_member_id_month_966eb854_uniq',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        'CREATE UNIQUE INDEX IF NOT EXISTS "fee_entry_member_id_month_966eb854_uniq" '
                        'ON "fee_entry" ("member_id", "month");',
                    ],
                    reverse_sql=[
                        'DROP INDEX IF EXISTS "fee_entry_member_id_month_966eb854_uniq";',
                    ],
                ),
            ],
        ),
    ]
