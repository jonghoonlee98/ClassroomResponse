# Generated by Django 2.0.1 on 2020-03-02 18:12

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0007_auto_20200302_1611'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='data',
            field=jsonfield.fields.JSONField(null=True),
        ),
        migrations.AddField(
            model_name='studentanswer',
            name='submission',
            field=jsonfield.fields.JSONField(null=True),
        ),
    ]