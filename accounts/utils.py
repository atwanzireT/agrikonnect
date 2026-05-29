import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def normalize_ugandan_phone(phone: str) -> str:
    phone = (phone or "").strip().replace(" ", "")

    if phone.startswith("+256"):
        return phone
    if phone.startswith("256"):
        return f"+{phone}"
    if phone.startswith("0") and len(phone) == 10:
        return f"+256{phone[1:]}"
    return phone


def is_valid_ugandan_phone(phone: str) -> bool:
    normalized = normalize_ugandan_phone(phone)
    if not normalized.startswith("+256"):
        return False

    digits = normalized.replace("+", "")
    return digits.isdigit() and len(digits) == 12


def send_sms(phone: str, message: str):
    api_key = getattr(settings, "YOOLA_SMS_API_KEY", "")
    url = getattr(settings, "YOOLA_SMS_URL", "https://yoolasms.com/api/v1/send")

    if not api_key:
        logger.error("YOOLA_SMS_API_KEY is missing.")
        return False, "Missing SMS API key."

    normalized_phone = normalize_ugandan_phone(phone)

    payload = {
        "phone": normalized_phone,
        "message": message,
        "api_key": api_key,
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_text = response.text

        logger.info("SMS API status: %s | response: %s", response.status_code, response_text)

        if response.status_code >= 400:
            return False, f"SMS API returned {response.status_code}: {response_text}"

        return True, response_text

    except requests.RequestException as exc:
        logger.exception("SMS sending failed")
        return False, str(exc)
    except Exception as exc:
        logger.exception("Unexpected SMS error")
        return False, str(exc)