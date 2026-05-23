from core.smartapi_client import get_smartapi_session

try:
    smart_api = get_smartapi_session()
    print("SmartAPI Connected Successfully!")

except Exception as e:
    print("Connection Failed:")
    print(e)