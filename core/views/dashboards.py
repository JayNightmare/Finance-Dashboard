from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from core.models import Transaction


@dataclass(frozen=True)
class CategorySummary:
    name: str
    total: Decimal
    type: str


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        month_txns = (
            Transaction.objects.for_user(user)
            .filter(date__year=today.year, date__month=today.month)
            .with_related()
        )

        totals = month_txns.aggregate(
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
        income_total = totals.get("income") or Decimal("0")
        expense_total = totals.get("expense") or Decimal("0")
        net_total = income_total - expense_total

        category_rows = (
            month_txns.exclude(category__isnull=True)
            .values("category__name", "category__kind")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:5]
        )
        top_categories = [
            CategorySummary(row["category__name"], row["total"], row["category__kind"])
            for row in category_rows
        ]

        recent_transactions = (
            Transaction.objects.for_user(user)
            .with_related()
            .order_by("-date", "-created_at")[:10]
        )

        currencies = Counter(month_txns.values_list("currency", flat=True))
        currency_warning = None
        if len(currencies) > 1:
            currency_warning = "Multiple currencies detected this month. Totals are displayed without FX conversion."

        context.update(
            {
                "income_total": income_total,
                "expense_total": expense_total,
                "net_total": net_total,
                "top_categories": top_categories,
                "recent_transactions": recent_transactions,
                "currency_warning": currency_warning,
            }
        )
        return context
