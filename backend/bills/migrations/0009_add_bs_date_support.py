# Generated migration for adding BS date support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bills', '0008_rename_is_recurring_to_is_reimbursable'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='bill_date_bs',
            field=models.CharField(
                max_length=10, 
                blank=True, 
                null=True,
                help_text='Bill date in Bikram Sambat (BS) format YYYY-MM-DD'
            ),
        ),
        migrations.AddField(
            model_name='bill',
            name='use_bs_date',
            field=models.BooleanField(
                default=False,
                help_text='Whether to use BS date for display'
            ),
        ),
    ]
