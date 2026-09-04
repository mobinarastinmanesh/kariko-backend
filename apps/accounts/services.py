import logging
import random
import string

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

OTP_CACHE_PREFIX = "otp:"


def _cache_key(phone: str) -> str:
    return f"{OTP_CACHE_PREFIX}{phone}"


def generate_otp(phone: str) -> str:
    code = "".join(random.choices(string.digits, k=settings.OTP_LENGTH))
    cache.set(_cache_key(phone), code, timeout=settings.OTP_EXPIRY_SECONDS)
    if settings.OTP_DEBUG:
        logger.warning("OTP for %s: %s", phone, code)
    else:
        _send_sms(phone, code)
    return code


def verify_otp(phone: str, code: str) -> bool:
    stored = cache.get(_cache_key(phone))
    if stored and stored == code:
        cache.delete(_cache_key(phone))
        return True
    return False


def _send_sms(phone: str, code: str) -> None:
    # Plug in your SMS provider (Kavenegar, Twilio, etc.) here.
    logger.info("SMS to %s: your code is %s", phone, code)
