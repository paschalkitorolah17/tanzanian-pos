"""
Management command: python manage.py seed_products

Creates realistic Tanzanian demo categories and products
for the first business found in the database (Kittoh Retail Store).
Safe to run multiple times.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.businesses.models import Business
from apps.products.models import Category, Product


class Command(BaseCommand):
    help = 'Seed demo categories and products for Tanzanian POS'

    def handle(self, *args, **options):
        business = Business.objects.filter(is_active=True).first()
        if not business:
            self.stdout.write(self.style.ERROR('No business found. Run seed_demo_business first.'))
            return

        self.stdout.write(f'Seeding data for business: {business.name}')

        # --------------------------------------------------
        # Categories
        # --------------------------------------------------
        categories_data = [
            'Soft Drinks',
            'Water & Juices',
            'Food Staples',
            'Household',
            'Personal Care',
            'Electronics',
            'Snacks',
        ]

        categories = {}
        for name in categories_data:
            cat, created = Category.objects.get_or_create(
                business=business,
                name=name,
                defaults={'is_active': True}
            )
            categories[name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'  + Category: {name}'))

        # --------------------------------------------------
        # Products
        # --------------------------------------------------
        products_data = [
            # Soft Drinks
            {'name': 'Coca Cola 500ml', 'sku': 'CC-500', 'barcode': '5449000000996', 'category': 'Soft Drinks', 'cost': 800, 'sell': 1200, 'unit': 'pcs'},
            {'name': 'Coca Cola 1L', 'sku': 'CC-1L', 'barcode': '5449000005431', 'category': 'Soft Drinks', 'cost': 1400, 'sell': 2000, 'unit': 'pcs'},
            {'name': 'Coca Cola 2L', 'sku': 'CC-2L', 'barcode': '5449000000997', 'category': 'Soft Drinks', 'cost': 2200, 'sell': 3000, 'unit': 'pcs'},
            {'name': 'Fanta Orange 500ml', 'sku': 'FT-500', 'barcode': '5449000012345', 'category': 'Soft Drinks', 'cost': 800, 'sell': 1200, 'unit': 'pcs'},
            {'name': 'Sprite 500ml', 'sku': 'SP-500', 'barcode': '5449000012346', 'category': 'Soft Drinks', 'cost': 800, 'sell': 1200, 'unit': 'pcs'},

            # Water
            {'name': 'Azam Water 500ml', 'sku': 'AZ-500', 'barcode': '6001234567890', 'category': 'Water & Juices', 'cost': 400, 'sell': 700, 'unit': 'pcs'},
            {'name': 'Azam Water 1.5L', 'sku': 'AZ-1.5', 'barcode': '6001234567891', 'category': 'Water & Juices', 'cost': 700, 'sell': 1200, 'unit': 'pcs'},
            {'name': 'Kilimanjaro Water 500ml', 'sku': 'KL-500', 'barcode': '6001234567892', 'category': 'Water & Juices', 'cost': 450, 'sell': 800, 'unit': 'pcs'},

            # Food Staples
            {'name': 'Sugar 1kg', 'sku': 'SG-1KG', 'barcode': '6009876543210', 'category': 'Food Staples', 'cost': 2800, 'sell': 3500, 'unit': 'kg'},
            {'name': 'Rice 5kg', 'sku': 'RC-5KG', 'barcode': '6009876543211', 'category': 'Food Staples', 'cost': 12000, 'sell': 15000, 'unit': 'bag'},
            {'name': 'Cooking Oil 1L', 'sku': 'OIL-1L', 'barcode': '6009876543212', 'category': 'Food Staples', 'cost': 4500, 'sell': 5500, 'unit': 'pcs'},
            {'name': 'Blue Band 500g', 'sku': 'BB-500', 'barcode': '6009876543213', 'category': 'Food Staples', 'cost': 3200, 'sell': 4000, 'unit': 'pcs'},

            # Household
            {'name': 'OMO 1kg', 'sku': 'OMO-1KG', 'barcode': '6005556667771', 'category': 'Household', 'cost': 4500, 'sell': 5800, 'unit': 'pcs'},
            {'name': 'OMO 500g', 'sku': 'OMO-500', 'barcode': '6005556667772', 'category': 'Household', 'cost': 2500, 'sell': 3200, 'unit': 'pcs'},
            {'name': 'Toilet Paper 4 rolls', 'sku': 'TP-4', 'barcode': '6005556667773', 'category': 'Household', 'cost': 2800, 'sell': 3800, 'unit': 'pack'},

            # Electronics
            {'name': 'USB Cable Type-C', 'sku': 'USB-TC', 'barcode': '6901234567890', 'category': 'Electronics', 'cost': 3500, 'sell': 7000, 'unit': 'pcs'},
            {'name': 'Phone Charger 2A', 'sku': 'CHG-2A', 'barcode': '6901234567891', 'category': 'Electronics', 'cost': 5000, 'sell': 10000, 'unit': 'pcs'},
            {'name': 'Earphones', 'sku': 'EAR-01', 'barcode': '6901234567892', 'category': 'Electronics', 'cost': 4000, 'sell': 8000, 'unit': 'pcs'},
        ]

        created_count = 0
        for p in products_data:
            product, created = Product.objects.get_or_create(
                business=business,
                sku=p['sku'],
                defaults={
                    'name': p['name'],
                    'barcode': p.get('barcode', ''),
                    'category': categories.get(p['category']),
                    'unit': p['unit'],
                    'cost_price': Decimal(str(p['cost'])),
                    'selling_price': Decimal(str(p['sell'])),
                    'tax_status': 'taxable',
                    'tax_rate': Decimal('18.00'),
                    'reorder_level': Decimal('10'),
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  + Product: {p["name"]}'))

        self.stdout.write(self.style.SUCCESS(f'\nDone! Created {created_count} new products.'))
        self.stdout.write(self.style.SUCCESS(f'Total products now: {Product.objects.filter(business=business).count()}'))
