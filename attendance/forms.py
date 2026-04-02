from django import forms
from .models import FeeStructure, StudentProfile


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ["student", "semester", "total_fee", "due_date"]

        widgets = {
            "student": forms.Select(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),
            "semester": forms.NumberInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),
            "total_fee": forms.NumberInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),
            "due_date": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),
        }


class BulkFeeStructureForm(forms.Form):
    students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.all().order_by("full_name"),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    semester = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
        })
    )
    total_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
        })
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
        })
    )
    only_without_fee = forms.BooleanField(required=False)
    overwrite_existing = forms.BooleanField(required=False)


class BulkNotificationForm(forms.Form):
    students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.all().order_by("full_name"),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    title = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
            "rows": 5
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
        })
    )
    only_students_with_fee = forms.BooleanField(required=False)