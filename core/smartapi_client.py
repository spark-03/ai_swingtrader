from SmartApi import SmartConnect
from dotenv import load_dotenv
import pyotp
import os

load_dotenv()

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP")


def get_smartapi_session():

    smart_api = SmartConnect(api_key=API_KEY)

    totp = pyotp.TOTP(TOTP_SECRET).now()

    session = smart_api.generateSession(
        CLIENT_CODE,
        PASSWORD,
        totp
    )

    return smart_api