from django import forms
from core.forms import PublicFormRules
from .models import ServiceInquiry


class ServiceInquiryForm(PublicFormRules, forms.ModelForm):
    class Meta:
        model  = ServiceInquiry
        fields = ['name', 'email', 'phone', 'city', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': 'Your Name', 'class': 'input'}),
            'email':   forms.EmailInput(attrs={'placeholder': 'Your Email', 'class': 'input'}),
            'phone':   forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'input'}),
            'city':    forms.TextInput(attrs={'placeholder': 'Your City', 'class': 'input'}),
            'message': forms.Textarea(attrs={'placeholder': 'Tell us what you need...', 'rows': 4, 'class': 'textarea'}),
        }
