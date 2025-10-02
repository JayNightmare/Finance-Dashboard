from __future__ import annotations

import calendar
from dataclasses import dataclass
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from core.forms import BudgetForm
from core.models import Budget, Transaction


@dataclass(frozen=True)
class BudgetProgress:
    budget: Budget
    spent: Decimal
    remaining: Decimal
    percentage: float


class BudgetListView(LoginRequiredMixin, TemplateView):
    template_name = "budgets/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        budgets = Budget.objects.filter(user=user).select_related("category")
        progress_rows: list[BudgetProgress] = []
        for budget in budgets:
            start = budget.start_month
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = start.replace(day=last_day)
            spent = Transaction.objects.filter(
                user=user,
                category=budget.category,
                type=Transaction.Type.EXPENSE,
                date__gte=start,
                date__lte=end,
            ).aggregate(total=Sum("amount")).get("total") or Decimal("0")
            remaining = max(Decimal("0"), budget.amount - spent)
            percentage = float(
                (spent / budget.amount * Decimal("100")) if budget.amount else 0
            )
            progress_rows.append(
                BudgetProgress(
                    budget=budget,
                    spent=spent,
                    remaining=remaining,
                    percentage=min(100.0, round(percentage, 2)),
                )
            )
        context.update(
            {
                "budget_progress": progress_rows,
                "create_form": BudgetForm(user=user),
            }
        )
        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    template_name = "budgets/form.html"
    form_class = BudgetForm
    success_url = reverse_lazy("core:budgets")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Budget created")
        return super().form_valid(form)


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "budgets/form.html"
    form_class = BudgetForm
    model = Budget
    success_url = reverse_lazy("core:budgets")

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related("category")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Budget updated")
        return super().form_valid(form)


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "budgets/confirm_delete.html"
    model = Budget
    success_url = reverse_lazy("core:budgets")

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Budget deleted")
        return super().delete(request, *args, **kwargs)
