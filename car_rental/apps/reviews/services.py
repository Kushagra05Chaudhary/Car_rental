from apps.reviews.models import Review


class ReviewModerationService:
    """Admin review moderation services."""

    @staticmethod
    def get_reviews(rating=None):
        reviews = Review.objects.select_related('user', 'car', 'car__owner').all().order_by('-created_at')
        if rating:
            reviews = reviews.filter(rating=rating)
        return reviews

    @staticmethod
    def delete_review(review):
        review.delete()
