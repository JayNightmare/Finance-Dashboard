from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.forms import CategoryForm
from core.models import Category


class CategoryListView(LoginRequiredMixin, ListView):
    template_name = "categories/list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_form"] = CategoryForm()
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    template_name = "categories/form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("core:categories")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Category created")
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "categories/form.html"
    form_class = CategoryForm
    model = Category
    success_url = reverse_lazy("core:categories")

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Category updated")
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "categories/confirm_delete.html"
    model = Category
    success_url = reverse_lazy("core:categories")

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Category deleted")
        return super().delete(request, *args, **kwargs)
