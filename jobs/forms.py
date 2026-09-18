from django import forms
from .models import JobPosting


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            'title',
            'description',
            'skills_required',
            'location',
            'salary_min',
            'salary_max',
            'remote_onsite',
            'visa_sponsorship',
            'status',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        if salary_min is not None and salary_max is not None:
            if salary_min > salary_max:
                self.add_error(
                    'salary_max',
                    'Maximum salary must be greater than or equal to minimum salary.'
                )
        return cleaned_data
