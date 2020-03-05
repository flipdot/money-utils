# Generated by Django 2.2.5 on 2020-03-05 23:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TanRequest',
            fields=[
                ('date', models.DateTimeField(auto_now_add=True, primary_key=True, serialize=False)),
                ('expired', models.BooleanField(default=False)),
                ('challenge', models.TextField()),
                ('hhduc', models.TextField(null=True)),
                ('answer', models.TextField(null=True)),
            ],
        ),
    ]
