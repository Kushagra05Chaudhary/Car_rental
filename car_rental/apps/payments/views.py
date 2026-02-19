from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from apps.accounts.decorators import role_required

from .models import Payment
from .services import PaymentAnalyticsService


@method_decorator(role_required('admin'), name='dispatch')
class AdminPaymentListView(LoginRequiredMixin, TemplateView):
	template_name = 'payments/admin_payments.html'
	login_url = 'login'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		status = self.request.GET.get('status')
		period = self.request.GET.get('period', 'monthly')

		payments = Payment.objects.select_related('user', 'booking').all().order_by('-created_at')
		if status:
			payments = payments.filter(status=status)

		context['payments'] = payments
		context['summary'] = PaymentAnalyticsService.get_summary(period=period)
		context['revenue_chart'] = PaymentAnalyticsService.get_revenue_chart_data()
		context['status_chart'] = PaymentAnalyticsService.get_status_breakdown()
		context['filters'] = {'status': status or '', 'period': period}
		return context
