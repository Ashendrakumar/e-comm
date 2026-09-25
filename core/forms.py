from django import forms
from .models import ContactInquiry, NewsletterSubscription


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'subject', 'message', 'inquiry_type']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name', 'class': 'input'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email', 'class': 'input'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'input'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Subject', 'class': 'input'}),
            'message': forms.Textarea(attrs={'placeholder': 'Your Message', 'rows': 5, 'class': 'textarea'}),
            'inquiry_type': forms.Select(attrs={'class': 'select'}),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscription
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email address', 'class': 'form-input'}),
        }
