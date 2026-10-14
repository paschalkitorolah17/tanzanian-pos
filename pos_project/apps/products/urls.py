from django.urls import path
from .views import (
    product_list, product_create, product_edit,
    category_list, category_create, category_edit,
)
from .label_views import label_list, print_labels, barcode_image

urlpatterns = [
    path('products/', product_list, name='product-list'),
    path('products/add/', product_create, name='product-create'),
    path('products/<int:pk>/edit/', product_edit, name='product-edit'),

    path('categories/', category_list, name='category-list'),
    path('categories/add/', category_create, name='category-create'),
    path('categories/<int:pk>/edit/', category_edit, name='category-edit'),

    path('labels/', label_list, name='label-list'),
    path('labels/print/', print_labels, name='print-labels'),
    path('labels/barcode/<int:product_id>/', barcode_image, name='barcode-image'),
]
