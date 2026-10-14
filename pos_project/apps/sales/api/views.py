from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from apps.businesses.models import Branch
from apps.customers.models import Customer
from apps.sales.services import SaleService
from .serializers import CreateSaleSerializer


class CreateSaleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateSaleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            branch = Branch.objects.get(
                id=data['branch_id'],
                business=request.user.business,
                is_active=True
            )
        except Branch.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid branch'
            }, status=status.HTTP_400_BAD_REQUEST)

        customer = None
        if data.get('customer_id'):
            try:
                customer = Customer.objects.get(
                    id=data['customer_id'],
                    business=request.user.business,
                    is_active=True
                )
            except Customer.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Invalid customer'
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            sale = SaleService.create_sale(
                branch=branch,
                cashier=request.user,
                items=data['items'],
                payments=data['payments'],
                customer=customer,
                notes=data.get('notes', ''),
                idempotency_key=data.get('idempotency_key'),
            )
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e.message) if hasattr(e, 'message') else str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Unable to complete sale.',
                'detail': str(e) if request.user.is_superuser else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': True,
            'message': 'Sale completed successfully',
            'data': {
                'id': sale.id,
                'transaction_number': sale.transaction_number,
                'grand_total': str(sale.grand_total),
                'created_at': sale.created_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)
