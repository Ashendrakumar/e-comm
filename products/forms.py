from django import forms
from .models import Review, ProductInquiry


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1, max_value=5,
        widget=forms.HiddenInput(attrs={'id': 'rating-input'})
    )

    class Meta:
        model  = Review
        fields = ['name', 'email', 'rating', 'title', 'content', 'pros', 'cons']
        widgets = {
            'name':    forms.TextInput(attrs={
                'placeholder': 'Your full name', 'class': 'form-input'}),
            'email':   forms.EmailInput(attrs={
                'placeholder': 'your@email.com', 'class': 'form-input'}),
            'title':   forms.TextInput(attrs={
                'placeholder': 'Summarise your experience', 'class': 'form-input'}),
            'content': forms.Textarea(attrs={
                'placeholder': 'Tell others what you think about this product…',
                'rows': 4, 'class': 'form-textarea'}),
            'pros':    forms.Textarea(attrs={
                'placeholder': 'What did you love about it?',
                'rows': 2, 'class': 'form-textarea'}),
            'cons':    forms.Textarea(attrs={
                'placeholder': 'Anything you disliked?',
                'rows': 2, 'class': 'form-textarea'}),
        }

    def clean_rating(self):
        r = self.cleaned_data.get('rating')
        if r not in range(1, 6):
            raise forms.ValidationError('Please select a rating between 1 and 5.')
        return r


class ProductInquiryForm(forms.ModelForm):
    class Meta:
        model  = ProductInquiry
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={
                'placeholder': 'Your name', 'class': 'form-input'}),
            'email':   forms.EmailInput(attrs={
                'placeholder': 'your@email.com', 'class': 'form-input'}),
            'phone':   forms.TextInput(attrs={
                'placeholder': '+91 98765 43210', 'class': 'form-input'}),
            'message': forms.Textarea(attrs={
                'placeholder': 'Ask anything about this product — price, availability, bulk orders…',
                'rows': 4, 'class': 'form-textarea'}),
        }
