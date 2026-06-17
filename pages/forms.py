from django import forms
from .models import ServiceInquiry


class ServiceInquiryForm(forms.ModelForm):
    class Meta:
        model  = ServiceInquiry
        fields = ['name', 'email', 'phone', 'city', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': 'Your Name', 'class': 'form-input'}),
            'email':   forms.EmailInput(attrs={'placeholder': 'Your Email', 'class': 'form-input'}),
            'phone':   forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-input'}),
            'city':    forms.TextInput(attrs={'placeholder': 'Your City', 'class': 'form-input'}),
            'message': forms.Textarea(attrs={'placeholder': 'Tell us what you need...', 'rows': 4, 'class': 'form-textarea'}),
        }
