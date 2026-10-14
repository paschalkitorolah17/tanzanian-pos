"""
Base interface for mobile money providers.
"""

from abc import ABC, abstractmethod


class BaseMobileMoneyProvider(ABC):

    @abstractmethod
    def initiate_payment(self, amount, phone, reference, callback_url):
        """
        Start a payment request (e.g. STK Push).
        Returns a dict with provider response.
        """
        pass

    @abstractmethod
    def verify_callback(self, payload, headers):
        """
        Verify and parse an incoming callback/webhook.
        Returns normalized data or raises ValidationError.
        """
        pass
