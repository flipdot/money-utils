from _sha256 import sha256

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.datetime_safe import datetime

from schema.fee_util import PayInterval
from schema.transaction import TxType


# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


def choice_from_enum(enum):
    return [(v.name, v.name.lower().capitalize()) for v in enum]


class FeeEntry(models.Model):
    id = models.CharField(max_length=255, primary_key=True)

    member = models.ForeignKey('Member', models.DO_NOTHING)
    month = models.DateField()

    tx = models.ForeignKey('Transaction', models.DO_NOTHING)
    fee = models.TextField()
    pay_interval = models.CharField(max_length=9)

    class Meta:
        managed = False
        db_table = 'fee_entry'
        unique_together = (('member', 'month'),)

    def save(self, *args, **kwargs):
        self.id = "{}|{}".format(self.member.id, self.month)
        super().save(*args, **kwargs)


class Member(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    nick = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    email = models.TextField(blank=True, null=True)

    entry_date = models.DateField(blank=True, null=True)
    exit_date = models.DateField(blank=True, null=True)
    pay_interval = models.TextField(choices=choice_from_enum(PayInterval))

    last_fee = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    fee = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)

    class Meta:
        managed = False
        db_table = 'member'


class Status(models.Model):
    key = models.CharField(primary_key=True, max_length=255)
    value_str = models.TextField(blank=True, null=True)
    value_dt = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'status'


class Transaction(models.Model):
    tx_id = models.CharField(primary_key=True, max_length=255)

    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING, blank=True, null=True)
    type = models.TextField(blank=True, null=True, choices=choice_from_enum(TxType))

    import_date = models.DateTimeField(auto_now_add=True)

    amount = models.DecimalField(decimal_places=2, max_digits=10)

    status = models.TextField(blank=True, null=True)
    funds_code = models.TextField(blank=True, null=True)
    id = models.TextField(blank=True, null=True)
    customer_reference = models.TextField(blank=True, null=True)
    bank_reference = models.TextField(blank=True, null=True)
    extra_details = models.TextField(blank=True, null=True)
    currency = models.TextField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    entry_date = models.DateField(blank=True, null=True)
    transaction_code = models.TextField(blank=True, null=True)
    posting_text = models.TextField(blank=True, null=True)
    prima_nota = models.TextField(blank=True, null=True)
    purpose = models.TextField()
    applicant_bin = models.TextField(blank=True, null=True)
    applicant_iban = models.TextField(blank=True, null=True)
    applicant_name = models.TextField(blank=True, null=True)
    return_debit_notes = models.TextField(blank=True, null=True)
    recipient_name = models.TextField(blank=True, null=True)
    additional_purpose = models.TextField(blank=True, null=True)
    gvc_applicant_iban = models.TextField(blank=True, null=True)
    gvc_applicant_bin = models.TextField(blank=True, null=True)
    end_to_end_reference = models.TextField(blank=True, null=True)
    additional_position_reference = models.TextField(blank=True, null=True)
    applicant_creditor_id = models.TextField(blank=True, null=True)
    purpose_code = models.TextField(blank=True, null=True)
    additional_position_date = models.TextField(blank=True, null=True)
    deviate_applicant = models.TextField(blank=True, null=True)
    deviate_recipient = models.TextField(blank=True, null=True)
    frst_one_off_recc = models.TextField(db_column='FRST_ONE_OFF_RECC', blank=True, null=True)  # Field name made lowercase.
    old_sepa_ci = models.TextField(db_column='old_SEPA_CI', blank=True, null=True)  # Field name made lowercase.
    old_sepa_additional_position_reference = models.TextField(db_column='old_SEPA_additional_position_reference', blank=True, null=True)  # Field name made lowercase.
    settlement_tag = models.TextField(blank=True, null=True)
    debitor_identifier = models.TextField(blank=True, null=True)
    compensation_amount = models.TextField(blank=True, null=True)
    original_amount = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        managed = False
        db_table = 'transaction'

    def save(self, *args, **kwargs):
        self.tx_id = self.gen_id(self)
        super().save(*args, **kwargs)

    def gen_id(self):
        # hash together as much as possible
        # there are NO unique transaction IDs in hbci...
        raw = "|".join([
            str(self.date),
            str(self.entry_date),
            str(self.applicant_bin),
            str(self.applicant_iban),
            str(self.amount),
            str(self.transaction_code),
            str(self.id),
            str(self.status),
            str(self.prima_nota),
            str(self.purpose),
        ])
        sha = sha256(raw.encode("UTF8"))
        return sha.hexdigest()

    def __str__(self) -> str:
        return "Tx[from: '{sender}', purpose: '{purpose}', amount: {amount:.2f}, date: {date}]" \
            .format(sender=self.applicant_name, purpose=self.purpose, amount=self.amount, date=self.date)
