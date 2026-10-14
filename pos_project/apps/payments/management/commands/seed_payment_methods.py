from django.core.management.base import BaseCommand
from apps.businesses.models import Business
from apps.payments.models import PaymentMethod

class Command(BaseCommand):
    help = 'Seed default Tanzanian payment methods'

    def handle(self, *args, **options):
        business = Business.objects.filter(is_active=True).first()
        if not business:
            self.stdout.write(self.style.ERROR('No business found'))
            return

        methods = [
            {'name': 'Cash', 'code': 'cash', 'is_cash': True, 'requires_reference': False, 'sort_order': 1},
            {'name': 'M-Pesa', 'code': 'mpesa', 'is_cash': False, 'requires_reference': True, 'sort_order': 2},
            {'name': 'Airtel Money', 'code': 'airtel', 'is_cash': False, 'requires_reference': True, 'sort_order': 3},
            {'name': 'Mixx by Yas', 'code': 'mixx', 'is_cash': False, 'requires_reference': True, 'sort_order': 4},
            {'name': 'HaloPesa', 'code': 'halopesa', 'is_cash': False, 'requires_reference': True, 'sort_order': 5},
            {'name': 'Bank Transfer', 'code': 'bank', 'is_cash': False, 'requires_reference': True, 'sort_order': 6},
            {'name': 'Card', 'code': 'card', 'is_cash': False, 'requires_reference': True, 'sort_order': 7},
        ]

        for m in methods:
            obj, created = PaymentMethod.objects.get_or_create(
                business=business,
                code=m['code'],
                defaults=m
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  + {m["name"]}'))

        self.stdout.write(self.style.SUCCESS('Payment methods ready.'))
