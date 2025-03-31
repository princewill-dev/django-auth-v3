from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, BlacklistedToken

# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'account_id', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'last_activity')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'account_id')
    ordering = ('-date_joined',)
    readonly_fields = ('account_id', 'date_joined', 'last_activity')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'account_id')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Verification'), {'fields': ('email_verification_code', 'email_verification_code_created_at')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_activity')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'blacklisted_at', 'expires_at')
    list_filter = ('blacklisted_at', 'expires_at')
    search_fields = ('user__email', 'token')
    date_hierarchy = 'blacklisted_at'
    readonly_fields = ('blacklisted_at',)
    
    def has_add_permission(self, request):
        # Tokens should only be blacklisted via the logout view
        return False
