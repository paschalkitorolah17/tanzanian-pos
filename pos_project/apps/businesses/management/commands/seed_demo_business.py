"""
Management command: python manage.py seed_demo_business

Creates a realistic Tanzanian demo business with one main branch
and default settings. Safe to run multiple times (it checks first).
"""

from django.core.management.base import BaseCommand
from apps.businesses.models import Business, Branch, BusinessSettings


class Command(BaseCommand):
    help = 'Creates a demo Tanzanian business with default branch and settings'

    def handle(self, *args, **options):
        business, created = Business.objects.get_or_create(
            name='Kittoh Retail Store',
            defaults={
                'tin': '123-456-789',
                'phone': '+255712345678',
                'email': 'info@kittoh.co.tz',
                'address': 'Samora Avenue, Dar es Salaam',
                'currency_code': 'TZS',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created business: {business.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Business already exists: {business.name}'))

        # Default settings
        settings, _ = BusinessSettings.objects.get_or_create(
            business=business,
            defaults={
                'allow_negative_stock': False,
                'max_discount_percent': 15.00,
                'default_tax_rate': 18.00,
                'receipt_footer': 'Asante kwa kununua kwa Kittoh Retail Store! Karibu tena.',
            }
        )

        # Main branch
        branch, branch_created = Branch.objects.get_or_create(
            business=business,
            code='HQ',
            defaults={
                'name': 'Main Branch - Dar es Salaam',
                'address': 'Samora Avenue, Dar es Salaam',
                'phone': '+255712345678',
                'is_main': True,
            }
        )

        if branch_created:
            self.stdout.write(self.style.SUCCESS(f'Created branch: {branch.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Branch already exists: {branch.name}'))

        self.stdout.write(self.style.SUCCESS('Demo business is ready.'))
