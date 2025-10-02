from __future__ import annotations

from django.urls import path

from core.views import (
    CategoryCreateView,
    CategoryDeleteView,
    CategoryListView,
    CategoryReportView,
    CategoryUpdateView,
    BudgetCreateView,
    BudgetDeleteView,
    BudgetListView,
    BudgetUpdateView,
    CSVExportView,
    CSVImportView,
    DashboardView,
    MonthlyReportView,
    TransactionCreateView,
    TransactionDeleteView,
    TransactionListView,
    TransactionUpdateView,
    TagCreateView,
    TagDeleteView,
    TagListView,
    TagUpdateView,
)

app_name = "core"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/new/", CategoryCreateView.as_view(), name="category-create"),
    path(
        "categories/<int:pk>/edit/",
        CategoryUpdateView.as_view(),
        name="category-update",
    ),
    path(
        "categories/<int:pk>/delete/",
        CategoryDeleteView.as_view(),
        name="category-delete",
    ),
    path("budgets/", BudgetListView.as_view(), name="budgets"),
    path("budgets/new/", BudgetCreateView.as_view(), name="budget-create"),
    path("budgets/<int:pk>/edit/", BudgetUpdateView.as_view(), name="budget-update"),
    path("budgets/<int:pk>/delete/", BudgetDeleteView.as_view(), name="budget-delete"),
    path("tags/", TagListView.as_view(), name="tags"),
    path("tags/new/", TagCreateView.as_view(), name="tag-create"),
    path("tags/<int:pk>/edit/", TagUpdateView.as_view(), name="tag-update"),
    path("tags/<int:pk>/delete/", TagDeleteView.as_view(), name="tag-delete"),
    path("transactions/", TransactionListView.as_view(), name="transactions"),
    path(
        "transactions/new/", TransactionCreateView.as_view(), name="transaction-create"
    ),
    path(
        "transactions/<int:pk>/edit/",
        TransactionUpdateView.as_view(),
        name="transaction-update",
    ),
    path(
        "transactions/<int:pk>/delete/",
        TransactionDeleteView.as_view(),
        name="transaction-delete",
    ),
    path("import/", CSVImportView.as_view(), name="import"),
    path("export/", CSVExportView.as_view(), name="export"),
    path("reports/monthly/", MonthlyReportView.as_view(), name="reports-monthly"),
    path(
        "reports/categories/",
        CategoryReportView.as_view(),
        name="reports-categories",
    ),
]
