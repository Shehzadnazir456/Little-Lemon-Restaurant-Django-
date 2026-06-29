from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='prep_time_minutes',
            field=models.PositiveSmallIntegerField(
                default=20,
                help_text='Estimated preparation time in minutes shown to the customer',
            ),
        ),
    ]
