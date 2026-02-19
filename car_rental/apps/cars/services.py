from django.db.models import Q

from .models import Car


class AdminCarModerationService:
    """Admin moderation services for cars."""

    @staticmethod
    def get_cars(owner_id=None, availability=None, query=None):
        cars = Car.objects.select_related('owner').all().order_by('-created_at')

        if owner_id:
            cars = cars.filter(owner_id=owner_id)

        if availability == 'available':
            cars = cars.filter(is_available=True)
        elif availability == 'unavailable':
            cars = cars.filter(is_available=False)

        if query:
            cars = cars.filter(
                Q(name__icontains=query)
                | Q(brand__icontains=query)
                | Q(location__icontains=query)
                | Q(owner__username__icontains=query)
            )

        return cars

    @staticmethod
    def toggle_availability(car):
        car.is_available = not car.is_available
        car.save(update_fields=['is_available'])
        return car

    @staticmethod
    def toggle_featured(car):
        car.is_featured = not car.is_featured
        car.save(update_fields=['is_featured'])
        return car

    @staticmethod
    def bulk_update(cars, action):
        if action == 'enable':
            return cars.update(is_available=True)
        if action == 'disable':
            return cars.update(is_available=False)
        if action == 'feature':
            return cars.update(is_featured=True)
        if action == 'unfeature':
            return cars.update(is_featured=False)
        return 0
