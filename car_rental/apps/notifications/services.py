from .models import Notification


def create_notification(user, title, message):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message
    )
