from __future__ import annotations

import csv
import json
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from core.forms import CSVCommitForm, CSVImportForm
from core.models import Category, Transaction

SUPPORTED_COLUMNS = ["date", "description", "amount", "type", "category", "ignore"]


@dataclass
class CSVPreview:
    headers: list[str]
    rows: list[list[str]]
    delimiter: str


class CSVImportView(LoginRequiredMixin, View):
    template_name = "import/index.html"
    preview_template_name = "import/preview.html"

    def get(self, request):
        return render(request, self.template_name, {"form": CSVImportForm()})

    def post(self, request):
        if "action" in request.POST and request.POST["action"] == "commit":
            return self._handle_commit(request)
        form = CSVImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        try:
            preview = self._build_preview(form.cleaned_data["file"])
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"form": form})
        request.session["import_preview"] = {
            "headers": preview.headers,
            "rows": preview.rows,
            "delimiter": preview.delimiter,
        }
        request.session.modified = True
        suggested = self._suggest_mapping(preview.headers)
        return render(
            request,
            self.preview_template_name,
            {
                "headers": preview.headers,
                "rows": preview.rows[:10],
                "total_rows": len(preview.rows),
                "column_choices": SUPPORTED_COLUMNS,
                "suggested_mapping": suggested,
                "suggested_mapping_json": json.dumps(suggested),
                "action_url": reverse("core:import"),
            },
        )

    def _handle_commit(self, request):
        preview_data = request.session.get("import_preview")
        if not preview_data:
            messages.error(
                request, "No preview data found. Please upload a file again."
            )
            return redirect("core:import")

        commit_form = CSVCommitForm(request.POST)
        if not commit_form.is_valid():
            messages.error(request, "Invalid mapping payload.")
            return redirect("core:import")

        mapping: dict[str, str] = commit_form.cleaned_data["mapping"]
        rows = preview_data["rows"]
        headers = preview_data["headers"]

        created = self._commit_rows(request, headers, mapping, rows)
        messages.success(request, f"Imported {created} transactions")
        request.session.pop("import_preview", None)
        return redirect("core:transactions")

    def _build_preview(self, uploaded_file) -> CSVPreview:
        raw = uploaded_file.read()
        if isinstance(raw, bytes):
            decoded = raw.decode("utf-8-sig")
        else:
            decoded = raw
        sample = decoded[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.get_dialect("excel")
        reader = csv.reader(io.StringIO(decoded), dialect)
        rows = [
            self._normalise_row(row)
            for row in reader
            if any(cell.strip() for cell in row)
        ]
        if not rows:
            raise ValueError("Uploaded file appears to be empty.")
        headers = rows[0]
        data_rows = rows[1:]
        if not headers:
            raise ValueError("Unable to read column headers from the file.")
        return CSVPreview(headers=headers, rows=data_rows, delimiter=dialect.delimiter)

    def _normalise_row(self, row: list[str]) -> list[str]:
        return [cell.strip() for cell in row]

    def _commit_rows(
        self,
        request,
        headers: list[str],
        mapping: dict[str, str],
        rows: list[list[str]],
    ) -> int:
        user = request.user
        created = 0
        with transaction.atomic():
            for row in rows:
                row_data = {
                    header: row[idx] if idx < len(row) else ""
                    for idx, header in enumerate(headers)
                }
                txn_kwargs = self._build_transaction_kwargs(user, row_data, mapping)
                if not txn_kwargs:
                    continue
                transaction_obj = Transaction(**txn_kwargs)
                transaction_obj.full_clean()
                transaction_obj.save()
                created += 1
        return created

    def _build_transaction_kwargs(
        self, user, row_data: dict[str, str], mapping: dict[str, str]
    ) -> dict[str, Any] | None:
        data = {}
        for header, field in mapping.items():
            if field == "ignore":
                continue
            data[field] = row_data.get(header, "")
        if not data:
            return None
        date_value = data.get("date")
        if not date_value:
            return None
        try:
            parsed_date = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            try:
                parsed_date = datetime.strptime(date_value, "%d/%m/%Y").date()
            except Exception:
                return None

        description = data.get("description", "")
        amount_raw = (data.get("amount") or "0").replace(",", "").strip()
        try:
            amount = Decimal(amount_raw)
        except InvalidOperation:
            return None
        raw_type = (data.get("type") or "").strip().upper()
        type_aliases = {
            "DEBIT": Transaction.Type.EXPENSE,
            "DR": Transaction.Type.EXPENSE,
            "CREDIT": Transaction.Type.INCOME,
            "CR": Transaction.Type.INCOME,
            "EXPENSE": Transaction.Type.EXPENSE,
            "INCOME": Transaction.Type.INCOME,
        }
        txn_type = type_aliases.get(raw_type)
        if raw_type in Transaction.Type.values:
            txn_type = raw_type
        amount_negative = amount < 0
        if amount_negative:
            amount = -amount
        if txn_type not in Transaction.Type.values:
            txn_type = (
                Transaction.Type.EXPENSE if amount_negative else Transaction.Type.INCOME
            )
        if amount_negative and txn_type != Transaction.Type.EXPENSE:
            txn_type = Transaction.Type.EXPENSE

        category_name = data.get("category")
        category_instance = None
        if category_name:
            category_kind = (
                Transaction.Type.INCOME
                if txn_type == Transaction.Type.INCOME
                else Transaction.Type.EXPENSE
            )
            category_instance, _ = Category.objects.get_or_create(
                user=user,
                name=category_name.strip(),
                kind=category_kind,
                defaults={"color": "#999999"},
            )

        return {
            "user": user,
            "type": txn_type,
            "amount": amount,
            "currency": "GBP",
            "date": parsed_date,
            "category": category_instance,
            "notes": description,
        }

    def _suggest_mapping(self, headers: list[str]) -> dict[str, str]:
        suggestions: dict[str, str] = {}
        for header in headers:
            key = header.strip().lower()
            if not key:
                continue
            if "date" in key and "updated" not in key:
                suggestions.setdefault(header, "date")
            elif any(word in key for word in ["amount", "value", "total"]):
                suggestions.setdefault(header, "amount")
            elif any(word in key for word in ["desc", "memo", "note"]):
                suggestions.setdefault(header, "description")
            elif "type" in key or "credit" in key or "debit" in key:
                suggestions.setdefault(header, "type")
            elif any(word in key for word in ["category", "group"]):
                suggestions.setdefault(header, "category")
        return suggestions
