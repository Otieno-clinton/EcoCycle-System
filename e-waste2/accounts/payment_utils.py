import base64
import re
import requests
from datetime import datetime
from django.conf import settings

def calculate_charges(waste_type, quantity):
    # Pricing per kg for different waste types
    PRICES = {
        'electronics': 50,   # KES per kg
        'batteries': 75,     # KES per kg
        'appliances': 40,    # KES per kg
        'other': 30          # KES per kg
    }
    return PRICES.get(waste_type, 30) * quantity

def format_phone_number(phone_number):
    phone_number = re.sub(r'\D', '', phone_number)
    if phone_number.startswith('0'):
        return '254' + phone_number[1:]
    elif phone_number.startswith('7'):
        return '254' + phone_number
    return phone_number

def generate_mpesa_token(consumer_key, consumer_secret):
    password = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
    response = requests.get(
        'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
        headers={'Authorization': f'Basic {password}'}
    )
    return response.json().get('access_token') if response.status_code == 200 else None

def initiate_stk_push(phone, amount, order_id, callback_url):
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    passkey = settings.MPESA_PASSKEY
    shortcode = settings.MPESA_SHORTCODE
    
    token = generate_mpesa_token(consumer_key, consumer_secret)
    if not token:
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()
    
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": f"EWASTE-{order_id}",
        "TransactionDesc": "E-Waste Collection Payment"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
        json=payload,
        headers=headers
    )
    
    return response.json() if response.status_code == 200 else None