from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.core.validators import validate_email  # ✅ ADD THIS
from django.core.exceptions import ValidationError  
from django.conf import settings
from django.utils.text import slugify
import uuid
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Company, FormLink, Complaint, Feedback
from .forms import CustomUserCreationForm, CompanyForm, FeedbackForm
from django.db.models import Avg, Count


def send_feedback_email(complaint):
    """Send feedback request email to customer after complaint is resolved."""
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings
    
    # Generate feedback link
    feedback_link = f"{settings.SITE_URL}/feedback/{complaint.feedback_token}/"
    
    # Email context
    context = {
        'customer_name': complaint.name,
        'complaint_subject': complaint.subject,
        'company_name': complaint.form_link.company.company_name,
        'feedback_link': feedback_link,
        'resolved_date': complaint.submitted_at.strftime("%B %d, %Y"),
    }
    
    # Render email templates
    html_message = render_to_string('emails/feedback_request.html', context)
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject=f"✅ Your issue is resolved! How did we do, {complaint.name}? ⭐",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[complaint.email],
        html_message=html_message,
        fail_silently=False,
    )
# =========================
# HOME PAGE
# =========================

def home(request):
    if request.user.is_authenticated:
        return redirect('user_dashboard')
    return render(request, 'home.html')


# =========================
# AUTHENTICATION
# =========================

# views.py
 # Import forms

def user_register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            request.session['pending_user_id'] = user.id
            messages.success(request, 'Account created! Now register your company.')
            return redirect('create_company')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'user_register.html', {'form': form})

@login_required
def register_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            messages.success(request, "Company created successfully!")
            return redirect('company_dashboard', slug=company.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CompanyForm()
    
    return render(request, 'create_company.html', {'form': form})

def login_view(request):
    """Single login function (removed duplicate)"""
    if request.user.is_authenticated:
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# =========================
# USER DASHBOARD
# =========================

@login_required
def user_dashboard(request):
    companies = request.user.companies.all()
    
    # Calculate stats
    total_companies = companies.count()
    
    context = {
        'companies': companies,
        'total_companies': total_companies,
    }
    
    return render(request, 'user_dashboard.html', context)

@login_required
def create_company(request):
    """For existing users to add more companies"""
    if request.method == 'POST':
        try:
            company = Company.objects.create(
                user=request.user,
                company_name=request.POST.get('company_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address_line1=request.POST.get('address_line1'),
                address_line2=request.POST.get('address_line2'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                country=request.POST.get('country'),
                pincode=request.POST.get('pincode'),
                gst_number=request.POST.get('gst_number'),
                logo=request.FILES.get('logo'),
                description=request.POST.get('description'),
                business_type=request.POST.get('business_type'),
            )
            
            # Generate slug
            company.slug = slugify(company.company_name)
            company.save()
            
            messages.success(request, "Company created successfully!")
            return redirect('company_dashboard', slug=company.slug)
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'create_company.html')






# =========================
# COMPANY DASHBOARD
# =========================
@login_required
def company_dashboard(request, slug):
    """SECURE: Only access companies owned by logged-in user"""
    company = get_object_or_404(Company, slug=slug, user=request.user)
    form_links = FormLink.objects.filter(company=company)
    complaints = Complaint.objects.filter(form_link__company=company).order_by('-submitted_at')
    
      # Stats
    total_complaints = complaints.count()
    resolved_complaints = complaints.filter(is_resolved=True).count()
    pending_complaints = total_complaints - resolved_complaints
    
    # ✅ ADD THIS: Calculate total feedback for this company
    total_feedback = Feedback.objects.filter(
        complaint__form_link__company=company
    ).count()
    
    if request.method == 'POST':
        # ✅ GENERATE FORM LINK
        if 'form_type' in request.POST:
            form_type = request.POST.get('form_type')
            
            if not form_type:
                messages.error(request, "Please select a form type")
                return redirect('company_dashboard', slug=slug)
            
            # Validate form_type is valid
            valid_types = [choice[0] for choice in FormLink.FORM_TYPE]
            if form_type not in valid_types:
                messages.error(request, "Invalid form type selected")
                return redirect('company_dashboard', slug=slug)
            
            # Generate unique ID for form link
            unique_id = uuid.uuid4().hex[:16]
            form_url = request.build_absolute_uri(f"/form/{unique_id}/")
            
            # Create FormLink
            try:
                FormLink.objects.create(
                    company=company,
                    form_type=form_type,
                    form_link=form_url
                )
                messages.success(request, "✅ Form link generated successfully!")
            except Exception as e:
                messages.error(request, f"Error creating form link: {str(e)}")
            
            return redirect('company_dashboard', slug=slug)
            
        # ✅ RESOLVE COMPLAINT
        elif 'complaint_id' in request.POST:
            complaint_id = request.POST.get('complaint_id')
            complaint = get_object_or_404(
                Complaint, 
                id=complaint_id, 
                form_link__company=company
            )
            
            if not complaint.is_resolved and not hasattr(complaint, 'feedback'):
                complaint.is_resolved = True
                complaint.save()
                
                try:
                    send_feedback_email(complaint)
                    messages.success(request, "Complaint resolved! Feedback email sent.")
                except Exception as e:
                    messages.warning(request, f"Complaint resolved, but email failed: {str(e)}")
            else:
                complaint.is_resolved = True
                complaint.save()
                messages.info(request, "Complaint marked as resolved.")
            
            return redirect('company_dashboard', slug=slug)
    
    context = {
        'company': company,
        'form_links': form_links,
        'form_types': FormLink.FORM_TYPE,
        'complaints': complaints,
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints': pending_complaints,
        'total_feedback': total_feedback,
    }
    
    return render(request, 'company_dashboard.html', context)


# =========================
# COMPANY PROFILE
# =========================

@login_required
def company_profile(request, slug):
    """View company profile"""
    company = get_object_or_404(Company, slug=slug, user=request.user)
    return render(request, 'company_profile.html', {'company': company})


@login_required
def edit_company(request, slug):
    """Edit company details"""
    company = get_object_or_404(Company, slug=slug, user=request.user)
    
    if request.method == 'POST':
        company.company_name = request.POST.get('company_name')
        company.email = request.POST.get('email')
        company.phone = request.POST.get('phone')
        company.address_line1 = request.POST.get('address_line1')
        company.address_line2 = request.POST.get('address_line2')
        company.city = request.POST.get('city')
        company.state = request.POST.get('state')
        company.country = request.POST.get('country')
        company.pincode = request.POST.get('pincode')
        company.gst_number = request.POST.get('gst_number')
        company.description = request.POST.get('description')
        company.business_type = request.POST.get('business_type')
        
        if 'logo' in request.FILES:
            company.logo = request.FILES['logo']
        
        # Update slug if name changed
        company.slug = slugify(company.company_name)
        company.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('company_profile', slug=slug)
    
    return render(request, 'edit_company.html', {'company': company})


# =========================
# CUSTOMER FORM (Public)
# =========================

def customer_form(request, unique_id):
    """Public form for customers to submit complaints"""
    
    # ✅ SECURE: Match exact form link
    form_link = get_object_or_404(FormLink, form_link__endswith=f"/form/{unique_id}/")
    
    if request.method == 'POST':
        # ✅ Get and clean data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # ✅ Validate required fields
        if not name:
            messages.error(request, "Name is required.")
            return render(request, 'customer_form.html', {'form_link': form_link})
        
        if not email:
            messages.error(request, "Email is required.")
            return render(request, 'customer_form.html', {'form_link': form_link})
        
        if not subject:
            messages.error(request, "Subject is required.")
            return render(request, 'customer_form.html', {'form_link': form_link})
        
        if not message:
            messages.error(request, "Message is required.")
            return render(request, 'customer_form.html', {'form_link': form_link})
        
        # ✅ Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, 'customer_form.html', {'form_link': form_link})
        
        # ✅ Create complaint (feedback_token auto-generated by model)
        try:
            complaint = Complaint.objects.create(
                form_link=form_link,
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            
            # ✅ Send email notification to company
            try:
                send_mail(
                    subject=f"🔔 New Complaint: {subject}",
                    message=f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[form_link.company.email],
                    fail_silently=False,
                )
            except Exception as e:
                # Log error but don't block complaint submission
                messages.warning(request, "Complaint submitted, but notification email failed.")
            
            # ✅ Success - Show thank you page
            messages.success(request, 'Your complaint has been submitted successfully.')
            
            # ✅✅✅ FIX: ADD form_link TO CONTEXT ✅✅✅
            return render(request, 'thank_you.html', {
                'customer_name': name,
                'complaint': complaint,
                'form_link': form_link  # ← ADD THIS LINE!
            })
            
        except Exception as e:
            messages.error(request, f"Error submitting complaint: {str(e)}")
            return render(request, 'customer_form.html', {'form_link': form_link})
    
    # GET request - Show form
    return render(request, 'customer_form.html', {'form_link': form_link})

# =========================
# FEEDBACK WITH STAR RATING
# =========================

# ✅ This is your final, correct submit_feedback view:
def submit_feedback(request, token):
    """Customer submits star rating feedback"""
    complaint = get_object_or_404(Complaint, feedback_token=token)
    
    # Check if feedback already exists
    if hasattr(complaint, 'feedback'):
        messages.info(request, "You have already submitted feedback for this complaint.")
        return redirect('home')
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.complaint = complaint
            feedback.save()
            
            complaint.feedback_sent = True
            complaint.save()
            
            messages.success(request, "Thank you for your feedback!")
            return redirect('home')
        else:
            messages.error(request, "Please provide a valid rating.")
    else:
        form = FeedbackForm()
    
    return render(request, 'submit_feedback.html', {
        'form': form,
        'complaint': complaint
    })

# views.py - Add this new function

# views.py - company_feedback_list function

@login_required
def company_feedback_list(request, slug):
    """Display all feedback for a specific company"""
    company = get_object_or_404(Company, slug=slug, user=request.user)
    
    # Get all feedback for this company's complaints
    feedback_items = Feedback.objects.filter(
        complaint__form_link__company=company
    ).select_related(
        'complaint', 
        'complaint__form_link'
    ).order_by('-submitted_at')
    
    # Stats
    total_feedback = feedback_items.count()
    avg_rating = feedback_items.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # ✅ Calculate rating breakdown WITH percentages (NO widthratio needed)
    rating_breakdown = {}
    for stars in [5, 4, 3, 2, 1]:
        count = feedback_items.filter(rating=stars).count()
        # Calculate percentage safely (avoid division by zero)
        percentage = (count / total_feedback * 100) if total_feedback > 0 else 0
        rating_breakdown[stars] = {
            'count': count,
            'percentage': round(percentage, 1)  # e.g., 45.5
        }
    
    context = {
        'company': company,
        'feedback_items': feedback_items,
        'total_feedback': total_feedback,
        'avg_rating': round(avg_rating, 1),
        'rating_breakdown': rating_breakdown,  # Now includes 'percentage' key
    }
    
    return render(request, 'company_feedback.html', context)