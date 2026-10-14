from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.payments.models import PaymentMethod


class PaymentMethodListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        if not business:
            return Response({'success': False, 'message': 'No business assigned'}, status=400)

        methods = PaymentMethod.objects.filter(
            business=business,
            is_active=True
        ).order_by('sort_order', 'name')

        results = [{
            'id': m.id,
            'name': m.name,
            'code': m.code,
            'is_cash': m.is_cash,
            'requires_reference': m.requires_reference,
        } for m in methods]

        return Response({'success': True, 'results': results})
