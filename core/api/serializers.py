from __future__ import annotations

from rest_framework import serializers

from core.models import Budget, Category, Tag, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "kind", "color", "archived", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "archived", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.none(), allow_null=True, required=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=False
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "amount",
            "currency",
            "date",
            "category",
            "tags",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request:
            user = request.user
            self.fields["category"].queryset = Category.objects.filter(user=user)
            self.fields["tags"].queryset = Tag.objects.filter(user=user)

    def validate_category(self, value):
        request = self.context.get("request")
        if value is None or request is None:
            return value
        if value.user_id != request.user.id:
            raise serializers.ValidationError(
                "Category must belong to the current user."
            )
        txn_type = self.initial_data.get("type")
        if txn_type is None and self.instance is not None:
            txn_type = self.instance.type
        if txn_type and value.kind != txn_type:
            raise serializers.ValidationError(
                "Category kind must match transaction type."
            )
        return value

    def validate_tags(self, value):
        request = self.context.get("request")
        if not request:
            return value
        user_id = request.user.id
        invalid = [tag for tag in value if tag.user_id != user_id]
        if invalid:
            raise serializers.ValidationError("Tags must belong to the current user.")
        return value

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        validated_data["user"] = self.context["request"].user
        transaction = super().create(validated_data)
        if tags:
            transaction.tags.set(tags)
        return transaction

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        validated_data.pop("user", None)
        transaction = super().update(instance, validated_data)
        if tags is not None:
            transaction.tags.set(tags)
        return transaction


class BudgetSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.none())

    class Meta:
        model = Budget
        fields = [
            "id",
            "category",
            "amount",
            "start_month",
            "rollover",
            "period",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "period"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request:
            user = request.user
            self.fields["category"].queryset = Category.objects.filter(
                user=user, kind=Category.Kind.EXPENSE
            )

    def validate_category(self, value):
        request = self.context.get("request")
        if request and value.user_id != request.user.id:
            raise serializers.ValidationError(
                "Category must belong to the current user."
            )
        if value.kind != Category.Kind.EXPENSE:
            raise serializers.ValidationError(
                "Only expense categories can be budgeted."
            )
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        validated_data.setdefault("period", Budget.Period.MONTH)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        validated_data.pop("period", None)
        return super().update(instance, validated_data)
