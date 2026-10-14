from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel, BusinessScopedModel


class Customer(TimeStampedModel, SoftDeleteModel, BusinessScopedModel):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        unique_together = [('business', 'phone')]  # phone unique per business when provided

    def __str__(self):
        return f"{self.name} ({self.phone})" if self.phone else self.name
