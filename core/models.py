from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
import uuid


# =========================
# COMPANY MODEL
# =========================
class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')

    company_name = models.CharField(max_length=250)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)

    # Address Fields
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    gst_number = models.CharField(
        max_length=15, 
        unique=True,
        validators=[RegexValidator(r'^[0-9A-Z]{15}$', 'Enter a valid 15-character GST number')]
    )

    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description = models.TextField()

    BUSINESS_TYPE = [
        ('retail', 'Retail'),
        ('service', 'Service'),
        ('manufacturing', 'Manufacturing'),
        ('technology', 'Technology'),
        ('other', 'Other'),
    ]
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE)

    slug = models.SlugField(unique=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.company_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.company_name


# =========================
# FORM LINK MODEL
# =========================
class FormLink(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='form_links')

    FORM_TYPE = [
        ('contact', 'Contact / General Inquiry'),
        ('support', 'Support Request'),
        ('bug', 'Bug / Technical Issue'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ]

    form_type = models.CharField(max_length=20, choices=FORM_TYPE)
    form_link = models.URLField(unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.company_name} - {self.get_form_type_display()}"


# =========================
# COMPLAINT MODEL
# =========================
class Complaint(models.Model):
    form_link = models.ForeignKey(FormLink, on_delete=models.CASCADE, related_name='complaints')

    name = models.CharField(max_length=250)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    subject = models.CharField(max_length=250)
    message = models.TextField()

    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    feedback_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    feedback_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Complaint from {self.name}"


# =========================
# FEEDBACK MODEL
# =========================
class Feedback(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='feedback')

    rating = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ]
    )  # 0–10
    message = models.TextField(blank=True, null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}/10 - {self.complaint.name}"