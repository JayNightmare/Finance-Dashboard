from __future__ import annotations

import json
from calendar import month_name
from datetime import date
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from core.forms import TransactionFilterForm
from core.models import Transaction


class MonthlyReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/monthly.html"
    months_to_show = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate().replace(day=1)
        start = self._subtract_months(today, self.months_to_show - 1)
        rows = (
            Transaction.objects.for_user(user)
            .filter(date__gte=start)
            .values("date__year", "date__month")
            .annotate(
                income=Sum(
                    "amount",
                    filter=models.Q(type=Transaction.Type.INCOME),
                    default=Decimal("0"),
                ),
                expense=Sum(
                    "amount",
                    filter=models.Q(type=Transaction.Type.EXPENSE),
                    default=Decimal("0"),
                ),
            )
        )
        row_map = {(row["date__year"], row["date__month"]): row for row in rows}

        labels: list[str] = []
        income_series: list[Decimal] = []
        expense_series: list[Decimal] = []
        net_series: list[Decimal] = []

        current = start
        for _ in range(self.months_to_show):
            key = (current.year, current.month)
            row = row_map.get(key, {"income": Decimal("0"), "expense": Decimal("0")})
            income = row.get("income") or Decimal("0")
            expense = row.get("expense") or Decimal("0")
            labels.append(f"{month_name[current.month][:3]} {current.year}")
            income_series.append(income)
            expense_series.append(expense)
            net_series.append(income - expense)
            current = self._add_month(current)

        rows_for_table = [
            {
                "label": labels[idx],
                "income": income_series[idx],
                "expense": expense_series[idx],
                "net": net_series[idx],
            }
            for idx in range(len(labels))
        ]

        chart_payload = json.dumps(
            {
                "labels": labels,
                "income": [float(value) for value in income_series],
                "expense": [float(value) for value in expense_series],
                "net": [float(value) for value in net_series],
            }
        )

        context.update(
            {
                "monthly_rows": rows_for_table,
                "chart_data_json": chart_payload,
            }
        )
        return context

    def _subtract_months(self, date_value: date, months: int) -> date:
        year = date_value.year
        month = date_value.month - months
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, 1)

    def _add_month(self, date_value: date) -> date:
        if date_value.month == 12:
            return date(date_value.year + 1, 1, 1)
        return date(date_value.year, date_value.month + 1, 1)


class CategoryReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/categories.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        form = TransactionFilterForm(self.request.GET or None, user=user)
        queryset = Transaction.objects.for_user(user).with_related()
        if form.is_valid():
            filters = form.build_filters()
            if filters:
                queryset = queryset.filter(filters).distinct()
        raw_categories = list(
            queryset.exclude(category__isnull=True)
            .values("category__name", "category__kind")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        categories = [
            {
                "name": row["category__name"],
                "kind": row["category__kind"],
                "total": row["total"] or Decimal("0"),
            }
            for row in raw_categories
        ]

        income_total = sum(
            row["total"] for row in categories if row["kind"] == Transaction.Type.INCOME
        )
        expense_total = sum(
            row["total"]
            for row in categories
            if row["kind"] == Transaction.Type.EXPENSE
        )

        chart_payload = json.dumps(
            {
                "labels": [row["name"] for row in categories],
                "totals": [float(row["total"]) for row in categories],
            }
        )

        context.update(
            {
                "form": form,
                "categories": categories,
                "income_total": income_total,
                "expense_total": expense_total,
                "net_total": income_total - expense_total,
                "chart_data_json": chart_payload,
            }
        )
        return context
