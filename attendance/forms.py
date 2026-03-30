from django import forms
from .models import FeeStructure

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