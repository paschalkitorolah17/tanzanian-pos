from django.core.management.base import BaseCommand
from apps.businesses.models import Business
from apps.expenses.models import ExpenseCategory

class Command(BaseCommand):
    help = 'Seed default expense categories'

    def handle(self, *args, **options):
        business = Business.objects.filter(is_active=True).first()
        if not business:
            self.stdout.write(self.style.ERROR('No business found'))
            return

        categories = [
            'Rent',
            'Electricity',
            'Water',
            'Internet / Airtime',
            'Transport',
            'Salaries & Wages',
            'Packaging',
            'Maintenance & Repairs',
            'Marketing',
            'Office Supplies',
            'Other',
        ]

        for name in categories:
            obj, created = ExpenseCategory.objects.get_or_create(
                business=business,
                name=name,
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  + {name}'))

        self.stdout.write(self.style.SUCCESS('Expense categories ready.'))
