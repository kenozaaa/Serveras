from django.contrib import admin
from .models import GptResult, CalculationResult

def delete_files(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()  

delete_files.short_description = "Delete selected files"

class GptResultAdmin(admin.ModelAdmin):
    list_display = ('filename', 'prefix', 'model_used', 'created_at', 'created_by_display')
    search_fields = ('filename', 'model_used', 'prompt')
    list_filter = ('prefix', 'model_used', 'created_at')  # Add prefix to filter
    actions = [delete_files]

    def created_by_display(self, obj):
        return obj.created_by.username if obj.created_by else 'Unknown'
    created_by_display.short_description = 'Created By'

class CalculationResultAdmin(admin.ModelAdmin):
    list_display = ('filename', 'created_at', 'created_by_display')
    search_fields = ('filename',)
    actions = [delete_files]  

    def created_by_display(self, obj):
        return obj.created_by.username if obj.created_by else 'Unknown'
    created_by_display.short_description = 'Created By'
    
admin.site.register(GptResult, GptResultAdmin)
admin.site.register(CalculationResult, CalculationResultAdmin)
