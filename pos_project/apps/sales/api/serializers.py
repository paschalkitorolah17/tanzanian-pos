from rest_framework import serializers
from decimal import Decimal


class SaleItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal('0.001'))
    discount = serializers.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), min_value=Decimal('0'))


class PaymentSerializer(serializers.Serializer):
    payment_method_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')


class CreateSaleSerializer(serializers.Serializer):
    branch_id = serializers.IntegerField()
    items = SaleItemSerializer(many=True)
    payments = PaymentSerializer(many=True)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_null=True)
