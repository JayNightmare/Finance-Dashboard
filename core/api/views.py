from __future__ import annotations

from rest_framework import filters, permissions, viewsets

from core.api.serializers import (
    BudgetSerializer,
    CategorySerializer,
    TagSerializer,
    TransactionSerializer,
)
from core.models import Budget, Category, Tag, Transaction


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["notes"]
    ordering_fields = ["date", "amount", "created_at"]
    ordering = ["-date", "-created_at"]

    def get_queryset(self):
        queryset = Transaction.objects.for_user(self.request.user).with_related()
        params = self.request.query_params
        if "type" in params:
            queryset = queryset.filter(type=params["type"])
        if "category" in params:
            queryset = queryset.filter(category_id=params["category"])
        if "tag" in params:
            queryset = queryset.filter(tags__id=params["tag"]).distinct()
        if "date__gte" in params:
            queryset = queryset.filter(date__gte=params["date__gte"])
        if "date__lte" in params:
            queryset = queryset.filter(date__lte=params["date__lte"])
        if "amount__gte" in params:
            queryset = queryset.filter(amount__gte=params["amount__gte"])
        if "amount__lte" in params:
            queryset = queryset.filter(amount__lte=params["amount__lte"])
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ["-start_month"]
    ordering_fields = ["start_month", "amount", "created_at"]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related("category")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
