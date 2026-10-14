from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.customers.models import Customer


class QuickCustomerCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        business = request.user.business
        if not business:
            return Response({'success': False, 'message': 'No business assigned'}, status=400)

        name = request.data.get('name', '').strip()
        phone = request.data.get('phone', '').strip()

        if not name:
            return Response({'success': False, 'message': 'Name is required'}, status=400)

        if phone and Customer.objects.filter(business=business, phone=phone).exists():
            # Return existing customer instead of error
            customer = Customer.objects.get(business=business, phone=phone)
            return Response({
                'success': True,
                'message': 'Customer already exists',
                'data': {
                    'id': customer.id,
                    'name': customer.name,
                    'phone': customer.phone,
                }
            })

        customer = Customer.objects.create(
            business=business,
            name=name,
            phone=phone,
        )

        return Response({
            'success': True,
            'message': 'Customer created',
            'data': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
            }
        }, status=201)
