from django.contrib import admin
from .models import EmailCampaign, EmailRecipient

class EmailRecipientInline(admin.TabularInline):
    model = EmailRecipient
    extra = 0
    readonly_fields = ('sent_at', 'status', 'error_message')
    can_delete = False
    ordering = ('status',)

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'course', 'status', 'created_at', 'sent_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'subject', 'course__nombre')
    readonly_fields = ('total_recipients', 'sent_count', 'failed_count', 'sent_at', 'created_at')
    inlines = [EmailRecipientInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course')

@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'campaign', 'status', 'sent_at')
    list_filter = ('status', 'campaign', 'sent_at')
    search_fields = ('full_name', 'email', 'campaign__name')
    readonly_fields = ('sent_at', 'error_message')
