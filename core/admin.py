from django.contrib import admin
from .models import Company, FormLink, Complaint, Feedback


# =========================
# FEEDBACK INLINE
# =========================
class FeedbackInline(admin.StackedInline):
    model = Feedback
    extra = 0
    readonly_fields = ('submitted_at',)


# =========================
# COMPLAINT ADMIN
# =========================
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'submitted_at')
    list_filter = ('is_resolved', 'submitted_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('submitted_at', 'feedback_token')

    inlines = [FeedbackInline]


# =========================
# FORM LINK ADMIN
# =========================
@admin.register(FormLink)
class FormLinkAdmin(admin.ModelAdmin):
    list_display = ('company', 'form_type', 'form_link', 'created_at')
    list_filter = ('form_type', 'created_at')
    search_fields = ('company__company_name', 'form_link')


# =========================
# COMPANY ADMIN
# =========================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'phone', 'city', 'state', 'business_type', 'created_at')
    list_filter = ('business_type', 'city', 'state', 'created_at')
    search_fields = ('company_name', 'email', 'gst_number', 'city')
    prepopulated_fields = {'slug': ('company_name',)}

    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'company_name', 'slug', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'pincode')
        }),
        ('Business Info', {
            'fields': ('business_type', 'gst_number', 'description', 'logo')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


# =========================
# FEEDBACK ADMIN
# =========================
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'rating', 'submitted_at')
    list_filter = ('rating', 'submitted_at')
    search_fields = ('complaint__name', 'complaint__email', 'message')
    readonly_fields = ('submitted_at',)