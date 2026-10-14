"""
Mobile money callback / webhook endpoints.

These must be CSRF-exempt and publicly reachable (HTTPS in production).
Always verify provider signatures before trusting the data.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError

logger = logging.getLogger('apps.payments')


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """
    Receive M-Pesa payment result callbacks.

    Flow (when fully implemented):
    1. Parse JSON body
    2. Verify authenticity (signature / result codes)
    3. Find matching pending payment / sale by reference
    4. Mark payment confirmed (idempotent)
    5. Return 200 so provider stops retrying
    """
    try:
        import json
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        logger.warning('M-Pesa callback: invalid JSON')
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid payload'}, status=400)

    logger.info('M-Pesa callback received: %s', payload)

    # Scaffold only – do not process money yet
    # from apps.payments.providers.mpesa import MpesaProvider
    # provider = MpesaProvider()
    # try:
    #     result = provider.verify_callback(payload, request.headers)
    #     # update Payment / Sale status here
    # except ValidationError as e:
    #     logger.warning('M-Pesa callback rejected: %s', e)
    #     return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)}, status=400)

    # Always acknowledge so the provider does not flood retries during development
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted (scaffold)'})
