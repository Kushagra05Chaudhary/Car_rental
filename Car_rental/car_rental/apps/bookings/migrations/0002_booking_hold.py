from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cars', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingHold',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_holds', to='cars.car')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_holds', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
