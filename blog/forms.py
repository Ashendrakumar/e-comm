from django import forms
from core.forms import PublicFormRules
from .models import BlogComment


class BlogCommentForm(PublicFormRules, forms.ModelForm):
    class Meta:
        model  = BlogComment
        fields = ['name', 'email', 'content']
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': 'Your Name', 'class': 'input'}),
            'email':   forms.EmailInput(attrs={'placeholder': 'Your Email (not published)', 'class': 'input'}),
            'content': forms.Textarea(attrs={'placeholder': 'Share your thoughts...', 'rows': 4, 'class': 'textarea'}),
        }
