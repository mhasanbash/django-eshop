import hashlib, random
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from kavenegar import *
import hmac
import hashlib


def hash_code(code: str) -> str:
    key = settings.SECRET_KEY.encode()
    return hmac.new(key, code.encode(), hashlib.sha256).hexdigest()

def generate_otp(length: int = 6) -> str:
    start = 10**(length-1)
    end = (10**length) - 1
    return str(random.randint(start, end))

def otp_expiry(minutes: int = 2):
    return timezone.now() + timedelta(minutes=minutes)

def send_sms_kavenegar(phone: str) -> bool:
    
    try:
        data = {
            "to": phone,
        }
        response = requests.post(
            "https://console.melipayamak.com/api/send/otp/",
            json=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=10,
        )
        result = response.json()
        
        return result

    except (APIException, HTTPException, requests.RequestException) as e:
        print("SMS send error:", e)
        return False
