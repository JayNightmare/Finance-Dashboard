from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Optional

from django import forms
from django.db.models import Q

from .models import Budget, Category, Tag, Transaction


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "kind", "color", "archived"]


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name", "archived"]


class TransactionForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Transaction
        fields = ["type", "amount", "currency", "date", "category", "tags", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(
                user=user, archived=False
            )
            self.fields["tags"].queryset = Tag.objects.filter(user=user, archived=False)
        self.fields["amount"].min_value = Decimal("0.01")

    def clean_category(self) -> Optional[Category]:
        category = self.cleaned_data.get("category")
        txn_type = self.cleaned_data.get("type")
        if category and txn_type and category.kind != txn_type:
            raise forms.ValidationError("Category kind must match transaction type")
        return category


class TransactionFilterForm(forms.Form):
    start = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    end = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    category = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)
    tag = forms.ModelChoiceField(queryset=Tag.objects.none(), required=False)
    type = forms.ChoiceField(
        choices=[("", "All"), *Transaction.Type.choices], required=False
    )
    min_amount = forms.DecimalField(required=False, min_value=Decimal("0.00"))
    max_amount = forms.DecimalField(required=False, min_value=Decimal("0.01"))
    q = forms.CharField(required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(
                user=user, archived=False
            )
            self.fields["tag"].queryset = Tag.objects.filter(user=user, archived=False)
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            base_class = (
                "form-select" if isinstance(widget, forms.Select) else "form-control"
            )
            widget.attrs["class"] = f"{existing} {base_class}".strip()

    def build_filters(self) -> Q:
        data = self.cleaned_data
        filters = Q()
        if data.get("start"):
            filters &= Q(date__gte=data["start"])
        if data.get("end"):
            filters &= Q(date__lte=data["end"])
        if data.get("category"):
            filters &= Q(category=data["category"])
        if data.get("tag"):
            filters &= Q(tags=data["tag"])
        if data.get("type"):
            filters &= Q(type=data["type"])
        if data.get("min_amount"):
            filters &= Q(amount__gte=data["min_amount"])
        if data.get("max_amount"):
            filters &= Q(amount__lte=data["max_amount"])
        if data.get("q"):
            filters &= Q(notes__icontains=data["q"])
        return filters


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["category", "amount", "start_month", "rollover"]
        widgets = {
            "start_month": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(
                user=user, archived=False, kind=Category.Kind.EXPENSE
            )


class CSVImportForm(forms.Form):
    file = forms.FileField()


class CSVMappingForm(forms.Form):
    column_type = forms.ChoiceField(
        choices=[
            ("date", "Date"),
            ("description", "Description"),
            ("amount", "Amount"),
            ("type", "Type"),
            ("category", "Category"),
            ("ignore", "Ignore"),
        ]
    )


class CSVCommitForm(forms.Form):
    mapping = forms.JSONField()

    required_fields = {"date", "amount"}

    def clean_mapping(self) -> dict[str, str]:
        mapping = self.cleaned_data["mapping"]
        if not isinstance(mapping, dict):
            raise forms.ValidationError("Invalid mapping payload")
        values = {value for value in mapping.values() if value != "ignore"}
        missing = self.required_fields.difference(values)
        if missing:
            raise forms.ValidationError("Mapping must include date and amount columns.")
        return mapping
