"""
M-Pesa (Vodacom Tanzania) provider scaffold.

IMPORTANT:
- Replace credentials with real values from Vodacom OpenAPI / merchant portal.
- Test only in sandbox until credentials are verified.
- Never commit real secrets to git.
"""

import os
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from .base import BaseMobileMoneyProvider


class MpesaProvider(BaseMobileMoneyProvider):
    """
    Scaffold for M-Pesa STK Push / C2B.

    Expected env vars (add to .env when ready):
        MPESA_CONSUMER_KEY=
        MPESA_CONSUMER_SECRET=
        MPESA_SHORTCODE=          # Till or Paybill
        MPESA_PASSKEY=
        MPESA_ENV=sandbox         # or production
        MPESA_CALLBACK_URL=https://yourdomain.com/api/v1/payments/mpesa/callback/
    """

    def __init__(self):
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY', '')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET', '')
        self.shortcode = os.getenv('MPESA_SHORTCODE', '')
        self.passkey = os.getenv('MPESA_PASSKEY', '')
        self.env = os.getenv('MPESA_ENV', 'sandbox')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL', '')

        if self.env == 'production':
            self.base_url = 'https://api.safaricom.co.ke'   # confirm exact TZ endpoint with Vodacom
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'

    def _get_access_token(self):
        """OAuth token – implement with real endpoint when credentials are ready."""
        if not self.consumer_key or not self.consumer_secret:
            raise ValidationError('M-Pesa credentials not configured')

        # Placeholder – replace with real OAuth call
        # url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        # response = requests.get(url, auth=(self.consumer_key, self.consumer_secret), timeout=30)
        # return response.json().get('access_token')
        raise ValidationError(
            'M-Pesa live integration not configured yet. '
            'Use manual reference entry for now.'
        )

    def initiate_payment(self, amount, phone, reference, callback_url=None):
        """
        Initiate STK Push (Lipa na M-Pesa Online style).

        phone: 2557XXXXXXXX (no +)
        amount: Decimal or float
        reference: unique string (e.g. sale idempotency key)
        """
        # Normalize phone
        phone = str(phone).replace('+', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '255' + phone[1:]

        # TODO: real STK Push request when credentials are available
        raise ValidationError(
            'STK Push is scaffolded but not live. '
            'Configure MPESA_* env vars and implement the API call.'
        )

    def verify_callback(self, payload, headers):
        """
        Parse and verify an incoming M-Pesa callback.

        Expected to return something like:
        {
            'success': True/False,
            'amount': Decimal,
            'phone': '...',
            'reference': '...',
            'provider_ref': '...',  # M-Pesa receipt number
            'raw': payload,
        }
        """
        # TODO: verify signature / result code from Vodacom payload
        # For now, reject until implemented
        raise ValidationError('M-Pesa callback verification not implemented yet')
