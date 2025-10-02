from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core.models import Category, Transaction
from core.views.imports import CSVImportView


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="csv-user", email="csv@example.com", password="TestPass123"
    )


@pytest.mark.django_db
def test_build_transaction_kwargs_creates_category(user):
    view = CSVImportView()
    mapping = {
        "Date": "date",
        "Details": "description",
        "Amount": "amount",
        "Category": "category",
    }
    row_data = {
        "Date": "2024-04-05",
        "Details": "Coffee Shop",
        "Amount": "-3.50",
        "Category": "Cafe",
    }

    kwargs = view._build_transaction_kwargs(user, row_data, mapping)

    assert kwargs is not None
    assert kwargs["type"] == Transaction.Type.EXPENSE
    assert kwargs["amount"] == Decimal("3.50")
    assert kwargs["category"].name == "Cafe"
    assert kwargs["category"].kind == Category.Kind.EXPENSE


@pytest.mark.django_db
def test_build_transaction_kwargs_skips_invalid_amount(user):
    view = CSVImportView()
    mapping = {
        "Date": "date",
        "Amount": "amount",
        "Memo": "description",
    }
    row_data = {
        "Date": "2024-04-05",
        "Amount": "not-a-number",
        "Memo": "Bad data",
    }

    kwargs = view._build_transaction_kwargs(user, row_data, mapping)

    assert kwargs is None
