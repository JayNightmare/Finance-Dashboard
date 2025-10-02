from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Category, Tag, Transaction


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="user",
        email="user@example.com",
        password="SuperSecret123",
    )


@pytest.fixture
def other_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="other",
        email="other@example.com",
        password="SuperSecret123",
    )


@pytest.mark.django_db
def test_transactions_list_is_scoped_to_user(api_client, user, other_user):
    income_category = Category.objects.create(
        user=user, name="Salary", kind=Category.Kind.INCOME
    )
    expense_category = Category.objects.create(
        user=other_user, name="Bills", kind=Category.Kind.EXPENSE
    )
    Transaction.objects.create(
        user=user,
        type=Transaction.Type.INCOME,
        amount="1500.00",
        currency="GBP",
        date=date(2024, 1, 1),
        category=income_category,
        notes="January salary",
    )
    Transaction.objects.create(
        user=other_user,
        type=Transaction.Type.EXPENSE,
        amount="75.00",
        currency="GBP",
        date=date(2024, 1, 2),
        category=expense_category,
        notes="Utilities",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/transactions/")

    assert response.status_code == 200
    payload = response.data
    assert payload["count"] == 1
    assert payload["results"][0]["notes"] == "January salary"


@pytest.mark.django_db
def test_transaction_create_assigns_user_and_tags(api_client, user):
    category = Category.objects.create(
        user=user, name="Dining", kind=Category.Kind.EXPENSE
    )
    tag = Tag.objects.create(user=user, name="Food")

    api_client.force_authenticate(user=user)
    response = api_client.post(
        "/api/transactions/",
        {
            "type": Transaction.Type.EXPENSE,
            "amount": "42.50",
            "currency": "GBP",
            "date": "2024-02-12",
            "category": category.id,
            "tags": [tag.id],
            "notes": "Dinner",
        },
        format="json",
    )

    assert response.status_code == 201, response.content
    transaction_id = response.data["id"]
    transaction = Transaction.objects.get(id=transaction_id)
    assert transaction.user == user
    assert transaction.tags.filter(name="Food").exists()
