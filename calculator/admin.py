from django.contrib import admin, messages

from calculator.models import CalculationRecord, Message_After_Transaction, PaymentVerificationRequest, Users
from calculator.payment import approve_payment_request


@admin.register(CalculationRecord)
class CalculationRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'calculator_type', 'created_at')
    list_filter = ('calculator_type', 'created_at')
    search_fields = ('user__username', 'result')
    readonly_fields = ('created_at',)


@admin.register(PaymentVerificationRequest)
class PaymentVerificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'parsed_reference',
        'parsed_amount',
        'status',
        'failure_reason',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'parsed_reference', 'receipt_text', 'failure_reason')
    readonly_fields = (
        'user',
        'receipt_text',
        'parsed_reference',
        'parsed_amount',
        'parsed_recipient',
        'api_response',
        'verification_checks',
        'failure_reason',
        'created_at',
        'reviewed_at',
    )
    actions = ('approve_selected', 'reject_selected')

    @admin.action(description='Approve selected — grant premium access')
    def approve_selected(self, request, queryset):
        approved = 0
        for item in queryset:
            if approve_payment_request(item):
                approved += 1
        self.message_user(request, f'{approved} payment(s) approved.', messages.SUCCESS)

    @admin.action(description='Reject selected')
    def reject_selected(self, request, queryset):
        updated = queryset.exclude(
            status__in=(
                PaymentVerificationRequest.STATUS_AUTO_APPROVED,
                PaymentVerificationRequest.STATUS_MANUAL_APPROVED,
            )
        ).update(
            status=PaymentVerificationRequest.STATUS_REJECTED,
        )
        self.message_user(request, f'{updated} request(s) rejected.', messages.WARNING)


admin.site.register(Users)
admin.site.register(Message_After_Transaction)
