from django.contrib import admin

from calculator.models import CalculationRecord, Message_After_Transaction, Users


@admin.register(CalculationRecord)
class CalculationRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'calculator_type', 'created_at')
    list_filter = ('calculator_type', 'created_at')
    search_fields = ('user__username', 'result')
    readonly_fields = ('created_at',)


admin.site.register(Users)
admin.site.register(Message_After_Transaction)
