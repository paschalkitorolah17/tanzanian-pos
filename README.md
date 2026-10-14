# Tanzanian POS

Production-oriented Point of Sale and business management system for Tanzanian retail shops.

## Features

- POS with mixed payments (Cash, M-Pesa, Airtel Money, etc.)
- Inventory, stock receiving, suppliers
- Sales returns
- Expenses and Profit & Loss reports
- Multi-branch support
- Role-based access (Owner, Manager, Cashier, Operator)
- PDF receipts
- Barcode label printing
- Offline Bootstrap UI with neon-green accents

## Stack

- Django 5 + Django REST Framework
- MySQL
- Vanilla JS + Bootstrap 5 (offline)

## Setup (development)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt
cp .env.example .env   # edit DB and SECRET_KEY
python manage.py migrate
python manage.py runserver