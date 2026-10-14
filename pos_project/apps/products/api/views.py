from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from apps.products.models import Product


class ProductSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({'success': True, 'results': []})

        business = request.user.business
        if not business:
            return Response({'success': False, 'message': 'No business assigned'}, status=400)

        products = Product.objects.filter(
            business=business,
            is_active=True
        ).filter(
            Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q)
        )[:15]

        results = [{
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'barcode': p.barcode,
            'selling_price': str(p.selling_price),
            'tax_rate': str(p.tax_rate),
            'tax_status': p.tax_status,
        } for p in products]

        return Response({'success': True, 'results': results})
