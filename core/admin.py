from __future__ import annotations

from django.contrib import admin

from .models import Budget, Category, Tag, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "user", "archived")
    list_filter = ("kind", "archived")
    search_fields = ("name",)
    autocomplete_fields = ("user",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "archived")
    list_filter = ("archived",)
    search_fields = ("name",)
    autocomplete_fields = ("user",)


class TagInline(admin.TabularInline):
    model = Transaction.tags.through
    extra = 1


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "type", "amount", "currency", "category", "user")
    list_filter = ("type", "currency", "date", "category")
    search_fields = ("notes",)
    autocomplete_fields = ("user", "category", "tags")
    inlines = [TagInline]
    date_hierarchy = "date"
    ordering = ("-date",)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("category", "amount", "period", "start_month", "user", "rollover")
    list_filter = ("period", "start_month", "rollover")
    search_fields = ("category__name",)
    autocomplete_fields = ("user", "category")
