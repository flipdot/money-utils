# Vendored: django-cron 0.6.0

This directory is a copy of the [`django-cron`](https://pypi.org/project/django-cron/)
package (version 0.6.0, MIT license, see [LICENSE](LICENSE)), vendored because:

- the package is unmaintained (last release 2022) and declares itself deprecated,
- it is incompatible with Django >= 5.1: `CronJobLog.Meta` used `index_together`,
  which was removed and now raises `TypeError` at app startup,
- it imports `django_common` (`django_common.helper.send_mail`) without declaring
  it as a dependency, which crashes `runcrons` the moment
  `django_cron.cron.FailedRunsNotificationCronJob` is imported.

## Local changes vs. upstream 0.6.0

- `models.py`: `Meta.index_together` replaced by `Meta.indexes` with
  `models.Index`. The `index_together`-generated index names are longer than
  the 30 characters allowed for an explicit `models.Index`, so the indexes
  are renamed.
- `migrations/0001_initial.py`: `AlterIndexTogether` replaced by three
  `AddIndex` operations keeping the original index names, so the migration
  state matches existing databases.
- `migrations/0004_rename_cronjoblog_indexes.py` (new): renames the
  over-long indexes to ≤30-character names. The `RunSQL` uses
  `IF EXISTS` / `IF NOT EXISTS`, so it is a no-op on databases where 0001
  already created the new names.
- `cron.py`: `from django_common.helper import send_mail` replaced by
  `from django.core.mail import send_mail` (django-common is an abandoned
  2013 package that was never declared as a dependency).
- `tests.py`: removed (it is the package's own test suite, not part of this
  project's tests).

The app label (`django_cron`), model names, table names and management
commands (`runcrons`, `cronloop`) are unchanged, so existing deployments keep
working without schema changes.
