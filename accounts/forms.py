from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe


class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join(
            [f'<div class="alert alert-danger" role="alert">{e}</div>'
             for e in self]
        ))


class SignUpForm(UserCreationForm):
    ROLE_CHOICES = [
        ('seeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    company_name = forms.CharField(required=False, max_length=255)

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2',
                          'role', 'company_name']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update(
                {'class': 'form-control'}
            )

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company_name = cleaned_data.get('company_name', '').strip()
        if role == 'recruiter' and not company_name:
            self.add_error('company_name',
                           'Company name is required for recruiters.')
        return cleaned_data
