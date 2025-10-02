from __future__ import annotations

import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from core.forms import TransactionFilterForm
from core.models import Transaction


class CSVExportView(LoginRequiredMixin, View):
    template_name = "export/index.html"

    def get(self, request):
        filter_form = TransactionFilterForm(request.GET or None, user=request.user)
        preview = None
        if filter_form.is_valid():
            queryset = (
                Transaction.objects.for_user(request.user)
                .with_related()
                .order_by("-date", "-created_at")
            )
            filters = filter_form.build_filters()
            if filters:
                queryset = queryset.filter(filters).distinct()
            if request.GET.get("download") == "1":
                return self._build_csv_response(queryset)
            preview = list(queryset[:25])
        return render(
            request,
            self.template_name,
            {
                "form": filter_form,
                "preview": preview,
            },
        )

    def _build_csv_response(self, queryset) -> HttpResponse:
        timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f"attachment; filename=transactions-{timestamp}.csv"
        )
        writer = csv.writer(response)
        writer.writerow(
            ["date", "type", "amount", "currency", "category", "tags", "notes"]
        )
        for txn in queryset.iterator():
            tag_names = ";".join(txn.tags.values_list("name", flat=True))
            writer.writerow(
                [
                    txn.date,
                    txn.get_type_display(),
                    txn.amount,
                    txn.currency,
                    txn.category.name if txn.category else "",
                    tag_names,
                    txn.notes,
                ]
            )
        return response
