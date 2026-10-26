from django.db import models


class CronJobLog(models.Model):
    """
    Keeps track of the cron jobs that ran etc. and any error
    messages if they failed.
    """

    code = models.CharField(max_length=64, db_index=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    is_success = models.BooleanField(default=False)
    message = models.TextField(default='', blank=True)  # TODO: db_index=True

    # This field is used to mark jobs executed in exact time.
    # Jobs that run every X minutes, have this field empty.
    ran_at_time = models.TimeField(null=True, blank=True, db_index=True, editable=False)

    def __unicode__(self):
        return '%s (%s)' % (self.code, 'Success' if self.is_success else 'Fail')

    def __str__(self):
        return "%s (%s)" % (self.code, "Success" if self.is_success else "Fail")

    class Meta:
        # index_together was removed in Django 5.1; these are the equivalent
        # indexes. Explicit index names are limited to 30 characters, so the
        # long index_together-generated names could not be kept;
        # 0004_rename_indexes migrates existing databases to these names.
        indexes = [
            models.Index(
                fields=['code', 'is_success', 'ran_at_time'],
                name='cronjoblog_code_is_succ_ran',
            ),
            models.Index(
                fields=['code', 'start_time', 'ran_at_time'],
                name='cronjoblog_code_start_ran',
            ),
            # useful when finding latest run (order by start_time) of cron
            models.Index(
                fields=['code', 'start_time'],
                name='cronjoblog_code_start',
            ),
        ]
        app_label = 'django_cron'


class CronJobLock(models.Model):
    job_name = models.CharField(max_length=200, unique=True)
    locked = models.BooleanField(default=False)
