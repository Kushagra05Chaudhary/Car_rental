from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_customuser_created_at_customuser_driving_license_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownerrequest',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
