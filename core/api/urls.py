from __future__ import annotations

from rest_framework.routers import DefaultRouter

from core.api.views import (
    BudgetViewSet,
    CategoryViewSet,
    TagViewSet,
    TransactionViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("tags", TagViewSet, basename="tag")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("budgets", BudgetViewSet, basename="budget")

urlpatterns = router.urls
