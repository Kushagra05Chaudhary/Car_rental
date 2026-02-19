from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import OwnerRequest, CustomUser


class OwnerModerationService:
	"""Service layer for admin owner verification workflow."""

	@staticmethod
	def get_pending_requests():
		return OwnerRequest.objects.select_related('user').filter(status='pending').order_by('-created_at')

	@staticmethod
	@transaction.atomic
	def approve_request(request_id):
		owner_request = get_object_or_404(OwnerRequest.objects.select_related('user'), pk=request_id, status='pending')
		owner_request.status = 'approved'
		owner_request.rejection_reason = ''
		owner_request.save(update_fields=['status', 'rejection_reason'])

		user = owner_request.user
		user.role = 'owner'
		user.save(update_fields=['role'])
		return owner_request

	@staticmethod
	@transaction.atomic
	def reject_request(request_id, reason=''):
		owner_request = get_object_or_404(OwnerRequest.objects.select_related('user'), pk=request_id, status='pending')
		owner_request.status = 'rejected'
		owner_request.rejection_reason = reason.strip()
		owner_request.save(update_fields=['status', 'rejection_reason'])
		return owner_request


class UserManagementService:
	"""Service layer for admin user management."""

	@staticmethod
	def get_users(search=None, role=None, status=None):
		users = CustomUser.objects.all().order_by('-date_joined')

		if search:
			users = users.filter(
				Q(username__icontains=search)
				| Q(email__icontains=search)
				| Q(phone__icontains=search)
			)

		if role:
			users = users.filter(role=role)

		if status == 'active':
			users = users.filter(is_active=True)
		elif status == 'inactive':
			users = users.filter(is_active=False)

		return users

	@staticmethod
	def get_stats():
		return {
			'total_users': CustomUser.objects.count(),
			'total_admins': CustomUser.objects.filter(role='admin').count(),
			'total_owners': CustomUser.objects.filter(role='owner').count(),
			'total_customers': CustomUser.objects.filter(role='user').count(),
			'active_users': CustomUser.objects.filter(is_active=True).count(),
			'inactive_users': CustomUser.objects.filter(is_active=False).count(),
		}

	@staticmethod
	@transaction.atomic
	def toggle_user_status(user_id, acting_user):
		user = get_object_or_404(CustomUser, pk=user_id)

		if user.id == acting_user.id:
			raise ValueError('You cannot change your own account status.')

		if user.is_superuser:
			raise ValueError('Superuser account status cannot be changed from this panel.')

		user.is_active = not user.is_active
		user.save(update_fields=['is_active'])
		return user
