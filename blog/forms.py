from django import forms
from .models import BlogComment


class BlogCommentForm(forms.ModelForm):
    class Meta:
        model  = BlogComment
        fields = ['name', 'email', 'content']
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': 'Your Name', 'class': 'form-input'}),
            'email':   forms.EmailInput(attrs={'placeholder': 'Your Email (not published)', 'class': 'form-input'}),
            'content': forms.Textarea(attrs={'placeholder': 'Share your thoughts...', 'rows': 4, 'class': 'form-textarea'}),
        }
