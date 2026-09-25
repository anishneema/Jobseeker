from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from .models import JobSeekerProfile


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
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    company_name = forms.CharField(required=False, max_length=255)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'email', 'password1', 'password2',
                          'role', 'company_name']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update(
                {'class': 'form-control'}
            )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'An account with this email already exists.'
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company_name = cleaned_data.get('company_name', '').strip()
        if role == 'recruiter' and not company_name:
            self.add_error('company_name',
                           'Company name is required for recruiters.')
        return cleaned_data

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            'headline',
            'skills',
            'location',
            'projects',
            'education',
            'work_experience',
            'links',
            'show_skills',
            'show_education',
            'show_work_experience',
            'show_links',
        ]
        widgets = {
            'projects': forms.Textarea(attrs={'rows':4}),
            'education': forms.Textarea(attrs={'rows': 4}),
            'work_experience': forms.Textarea(attrs={'rows': 4}),
            'links': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-check-input'})