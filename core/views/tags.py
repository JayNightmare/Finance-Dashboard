from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.forms import TagForm
from core.models import Tag


class TagListView(LoginRequiredMixin, ListView):
    template_name = "tags/list.html"
    context_object_name = "tags"

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user).order_by("name")


class TagCreateView(LoginRequiredMixin, CreateView):
    template_name = "tags/form.html"
    form_class = TagForm
    success_url = reverse_lazy("core:tags")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Tag created")
        return super().form_valid(form)


class TagUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "tags/form.html"
    form_class = TagForm
    model = Tag
    success_url = reverse_lazy("core:tags")

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Tag updated")
        return super().form_valid(form)


class TagDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "tags/confirm_delete.html"
    model = Tag
    success_url = reverse_lazy("core:tags")

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Tag deleted")
        return super().delete(request, *args, **kwargs)
