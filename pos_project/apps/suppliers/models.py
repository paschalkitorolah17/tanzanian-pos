from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel, BusinessScopedModel


class Supplier(TimeStampedModel, SoftDeleteModel, BusinessScopedModel):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        unique_together = [('business', 'name')]

    def __str__(self):
        return self.name
