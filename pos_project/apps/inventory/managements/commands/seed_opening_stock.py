
"""
python manage.py seed_opening_stock

Sets a realistic opening stock for all products of the first business.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.businesses.models import Business, Branch
from apps.products.models import Product
from apps.inventory.services import StockService
from apps.inventory.models import Warehouse

User = get_user_model()


class Command(BaseCommand):
    help = 'Set opening stock for demo products'

    def handle(self, *args, **options):
        business = Business.objects.filter(is_active=True).first()
        if not business:
            self.stdout.write(self.style.ERROR('No business found.'))
            return

        branch = business.branches.filter(is_active=True).first()
        if not branch:
            self.stdout.write(self.style.ERROR('No branch found.'))
            return

        # Create default warehouse if needed
        warehouse, _ = Warehouse.objects.get_or_create(
            branch=branch,
            name='Main Store',
            defaults={'is_default': True}
        )

        user = User.objects.filter(is_superuser=True).first()
        if not user:
            self.stdout.write(self.style.ERROR('No superuser found.'))
            return

        products = Product.objects.filter(business=business, is_active=True)
        count = 0

        for product in products:
            # Give different realistic quantities
            if 'Coca Cola' in product.name or 'Fanta' in product.name or 'Sprite' in product.name:
                qty = Decimal('50')
            elif 'Water' in product.name:
                qty = Decimal('80')
            elif 'Sugar' in product.name or 'Rice' in product.name:
                qty = Decimal('30')
            else:
                qty = Decimal('20')

            StockService.set_opening_stock(
                product=product,
                branch=branch,
                quantity=qty,
                user=user,
                warehouse=warehouse,
                notes='Demo opening stock'
            )
            count += 1
            self.stdout.write(self.style.SUCCESS(f'  {product.name}: {qty}'))

        self.stdout.write(self.style.SUCCESS(f'\nOpening stock set for {count} products.'))
