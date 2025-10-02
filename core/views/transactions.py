from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.forms import TransactionFilterForm, TransactionForm
from core.models import Transaction


class TransactionListView(LoginRequiredMixin, ListView):
    template_name = "transactions/list.html"
    context_object_name = "transactions"
    paginate_by = 25

    def get_queryset(self):
        qs = Transaction.objects.for_user(self.request.user).with_related()
        self.filter_form = TransactionFilterForm(
            self.request.GET or None, user=self.request.user
        )
        if self.filter_form.is_valid():
            qs = qs.filter(self.filter_form.build_filters()).distinct()
        return qs.order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = getattr(
            self, "filter_form", TransactionFilterForm(user=self.request.user)
        )
        context["create_form"] = TransactionForm(user=self.request.user)
        return context


class TransactionCreateView(LoginRequiredMixin, CreateView):
    template_name = "transactions/form.html"
    form_class = TransactionForm
    success_url = reverse_lazy("core:transactions")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        form.instance.set_tags(form.cleaned_data.get("tags", []))
        messages.success(self.request, "Transaction created")
        return response


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "transactions/form.html"
    form_class = TransactionForm
    model = Transaction
    success_url = reverse_lazy("core:transactions")

    def get_queryset(self):
        return Transaction.objects.for_user(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.set_tags(form.cleaned_data.get("tags", []))
        messages.success(self.request, "Transaction updated")
        return response


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "transactions/confirm_delete.html"
    model = Transaction
    success_url = reverse_lazy("core:transactions")

    def get_queryset(self):
        return Transaction.objects.for_user(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Transaction deleted")
        return super().delete(request, *args, **kwargs)
