from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from apps.accounts.decorators import role_required

from .models import Review
from .services import ReviewModerationService


@method_decorator(role_required('admin'), name='dispatch')
class AdminReviewListView(LoginRequiredMixin, TemplateView):
	template_name = 'reviews/admin_review_list.html'
	login_url = 'login'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		rating = self.request.GET.get('rating')
		context['reviews'] = ReviewModerationService.get_reviews(rating=rating)
		context['rating_filter'] = rating or ''
		return context


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('admin'), name='dispatch')
class AdminDeleteReviewView(View):
	def post(self, request, pk, *args, **kwargs):
		review = get_object_or_404(Review, pk=pk)
		ReviewModerationService.delete_review(review)
		messages.success(request, 'Review deleted successfully.')
		return redirect('admin_review_list')
