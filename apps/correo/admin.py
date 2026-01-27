from django.contrib import admin
from .models import EmailCampaign, EmailRecipient, EmailDailyLimit

class EmailRecipientInline(admin.TabularInline):
    model = EmailRecipient
    extra = 0
    readonly_fields = ('sent_at', 'status', 'error_message')
    can_delete = False
    ordering = ('status',)

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'course', 'status', 'progress', 'created_at', 'sent_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'subject', 'course__nombre')
    readonly_fields = (
        'total_recipients', 'sent_count', 'failed_count', 
        'celery_task_id', 'progress', 'current_batch',
        'sent_at', 'created_at'
    )
    inlines = [EmailRecipientInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course')

@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'campaign', 'status', 'sent_at')
    list_filter = ('status', 'campaign', 'sent_at')
    search_fields = ('full_name', 'email', 'campaign__name')
    readonly_fields = ('sent_at', 'error_message')

@admin.register(EmailDailyLimit)
class EmailDailyLimitAdmin(admin.ModelAdmin):
    list_display = ('date', 'count', 'get_remaining')
    list_filter = ('date',)
    readonly_fields = ('date', 'count', 'get_remaining')
    
    def get_remaining(self, obj):
        """Muestra cuántos correos quedan disponibles para ese día."""
        from django.conf import settings
        daily_limit = getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
        remaining = daily_limit - obj.count
        return max(0, remaining)
    get_remaining.short_description = 'Restantes'
