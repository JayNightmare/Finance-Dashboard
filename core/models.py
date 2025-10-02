from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class BaseUserModel(models.Model):
    """Abstract base model that ensures per-user scoping."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s"
    )

    class Meta:
        abstract = True


class Category(BaseUserModel):
    class Kind(models.TextChoices):
        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"

    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    color = models.CharField(max_length=7, blank=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("user", "name", "kind")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.get_kind_display()})"


class Tag(BaseUserModel):
    name = models.CharField(max_length=120)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("user", "name")

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class TransactionQuerySet(models.QuerySet):
    def for_user(self, user: models.Model) -> "TransactionQuerySet":
        return self.filter(user=user)

    def with_related(self) -> "TransactionQuerySet":
        return self.select_related("category").prefetch_related("tags")


class TransactionManager(models.Manager):
    def get_queryset(self) -> TransactionQuerySet:  # type: ignore[override]
        return TransactionQuerySet(self.model, using=self._db)

    def for_user(self, user: models.Model) -> TransactionQuerySet:
        return self.get_queryset().for_user(user)


class Transaction(BaseUserModel):
    class Type(models.TextChoices):
        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"

    type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(max_length=3, default="GBP")
    date = models.DateField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="transactions")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TransactionManager()

    class Meta:
        ordering = ("-date", "-created_at")
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "category", "date"]),
            GinIndex(
                name="transaction_notes_trgm",
                fields=["notes"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_type_display()} {self.amount} {self.currency} on {self.date}"

    @property
    def signed_amount(self) -> Decimal:
        multiplier = Decimal("1") if self.type == self.Type.INCOME else Decimal("-1")
        return self.amount * multiplier

    def clean(self) -> None:
        super().clean()
        if self.category and self.category.user_id != self.user_id:
            raise ValidationError(
                {"category": "Category must belong to the transaction user."}
            )
        if self.category and self.category.kind != self.type:
            raise ValidationError(
                {"category": "Category kind must match transaction type."}
            )
        if self.amount <= 0:
            raise ValidationError({"amount": "Amount must be greater than zero."})

    def set_tags(self, tag_ids: Iterable[int]) -> None:
        tags = Tag.objects.filter(id__in=tag_ids, user_id=self.user_id)
        self.tags.set(tags)


class Budget(BaseUserModel):
    class Period(models.TextChoices):
        MONTH = "MONTH", "Month"

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="budgets"
    )
    period = models.CharField(
        max_length=10, choices=Period.choices, default=Period.MONTH
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    start_month = models.DateField(
        help_text="Represents the first day of the month this budget applies to."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    rollover = models.BooleanField(default=False)

    class Meta:
        ordering = ("-start_month", "category__name")
        unique_together = ("user", "category", "start_month")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.category} budget for {self.start_month:%B %Y}"

    def clean(self) -> None:
        super().clean()
        if self.category.user_id != self.user_id:
            raise ValidationError(
                {"category": "Category must belong to the budget user."}
            )
        if self.category.kind != Category.Kind.EXPENSE:
            raise ValidationError(
                {"category": "Only expense categories can be budgeted."}
            )
        if self.start_month.day != 1:
            raise ValidationError(
                {"start_month": "Start month must be the first day of the month."}
            )


@dataclass(frozen=True)
class ReportRow:
    month: int
    year: int
    income: Decimal
    expense: Decimal

    @property
    def net(self) -> Decimal:
        return self.income - self.expense


def get_month_bounds(
    date_value: timezone.datetime,
) -> tuple[timezone.datetime, timezone.datetime]:
    start = date_value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (start + timezone.timedelta(days=32)).replace(day=1)
    end = next_month - timezone.timedelta(seconds=1)
    return start, end
