from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, CollectionRequest, Payment

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role', {'fields': ('role',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'first_name', 'last_name', 'phone', 'address'),
        }),
    )

# Payment Inline for CollectionRequest Admin
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('created_at', 'mpesa_receipt_number', 'transaction_date')
    fields = ('amount', 'phone_number', 'status', 'mpesa_receipt_number', 'verified', 'admin_approved', 'created_at', 'transaction_date')
    can_delete = False

# Collection Request Admin
class CollectionRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'producer_info', 'waste_type', 'quantity', 'status', 'request_date', 'collection_date', 'collector_info', 'final_disposition')
    list_filter = ('status', 'waste_type', 'request_date', 'final_disposition')
    search_fields = ('producer__username', 'producer__email', 'description', 'admin_notes', 'recycling_notes')
    readonly_fields = ('request_date',)
    date_hierarchy = 'request_date'
    inlines = [PaymentInline]
    
    fieldsets = (
        ('Request Information', {
            'fields': ('producer', 'waste_type', 'quantity', 'description', 'request_date', 'status')
        }),
        ('Collection Details', {
            'fields': ('collector', 'collection_date', 'admin_notes')
        }),
        ('Recycling Information', {
            'fields': ('final_disposition', 'recycling_notes', 'recycling_date', 'actual_quantity')
        }),
    )
    
    def producer_info(self, obj):
        return format_html('<a href="/admin/app_name/user/{}/">{}</a>', 
                          obj.producer.id, obj.producer)
    
    def collector_info(self, obj):
        if obj.collector:
            return format_html('<a href="/admin/app_name/user/{}/">{}</a>', 
                              obj.collector.id, obj.collector)
        return "-"
    
    producer_info.short_description = 'Producer'
    collector_info.short_description = 'Collector'

# Payment Admin
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_link', 'amount', 'phone_number', 'status', 'verified', 'admin_approved', 'created_at')
    list_filter = ('status', 'verified', 'admin_approved', 'created_at')
    search_fields = ('mpesa_receipt_number', 'phone_number', 'request__producer__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('request', 'amount', 'phone_number', 'status', 'created_at')
        }),
        ('Transaction Details', {
            'fields': ('mpesa_receipt_number', 'transaction_date', 'verified', 'admin_approved')
        }),
    )
    
    def request_link(self, obj):
        return format_html('<a href="/admin/app_name/collectionrequest/{}/">Request #{}</a>', 
                          obj.request.id, obj.request.id)
    
    request_link.short_description = 'Collection Request'

# Register models with the admin site
admin.site.register(User, CustomUserAdmin)
admin.site.register(CollectionRequest, CollectionRequestAdmin)
admin.site.register(Payment, PaymentAdmin)