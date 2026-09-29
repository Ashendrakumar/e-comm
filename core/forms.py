from django import forms
from django.core.validators import MaxLengthValidator, MinLengthValidator

from .models import ContactInquiry, NewsletterSubscription
from .validators import validate_phone


class PublicFormRules:
    """Length and phone rules shared by every public form.

    Applied to whichever of these fields a form has. The limits are also rendered
    as minlength / maxlength attributes, which static/js/form-validate.js checks
    before submit; hand-written forms in templates repeat the same numbers.
    """
    LENGTHS = {                     # field name: (min, max)
        'name':    (2, 100),
        'subject': (2, 200),
        'city':    (2, 100),
        'title':   (None, 200),
        'message': (10, 2000),
        'content': (10, 2000),
        'pros':    (None, 1000),
        'cons':    (None, 1000),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            lo, hi = self.LENGTHS.get(name, (None, None))
            if lo:
                field.min_length = lo
                field.validators.append(MinLengthValidator(lo))
                field.widget.attrs['minlength'] = lo
            if hi:
                field.max_length = hi
                field.validators.append(MaxLengthValidator(hi))
                field.widget.attrs['maxlength'] = hi
            if name == 'phone':
                field.validators.append(validate_phone)
                field.widget.input_type = 'tel'
                field.widget.attrs.update(maxlength=20, autocomplete='tel', inputmode='tel')
            elif name == 'email':
                field.widget.attrs.setdefault('autocomplete', 'email')
            elif name == 'name':
                field.widget.attrs.setdefault('autocomplete', 'name')


class ContactForm(PublicFormRules, forms.ModelForm):
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


class NewsletterForm(forms.Form):
    # A plain Form, not a ModelForm: the model's unique=True would reject an
    # address that is already subscribed, and the view handles that case itself.
    email = forms.EmailField(max_length=NewsletterSubscription._meta.get_field('email').max_length,
                             widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address',
                                                            'class': 'form-input'}))
