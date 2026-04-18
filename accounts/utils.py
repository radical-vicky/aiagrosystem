# accounts/utils.py

import random
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class OTPService:
    """Handle OTP generation and sending"""
    
    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return f"{random.randint(100000, 999999)}"
    
    @staticmethod
    def send_otp_via_sms(phone_number, otp_code):
        """Send OTP via SMS (console fallback for development)"""
        # For development without SMS provider
        print(f"\n{'='*50}")
        print(f"📱 SMS VERIFICATION")
        print(f"To: {phone_number}")
        print(f"OTP Code: {otp_code}")
        print(f"Valid for: 10 minutes")
        print(f"{'='*50}\n")
        
        # In production, you can uncomment and configure one of these:
        
        # Option 1: Twilio
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=f"Your verification code for AI AgroSystem is: {otp_code}",
        #     from_=settings.TWILIO_PHONE_NUMBER,
        #     to=phone_number
        # )
        
        # Option 2: Africa's Talking
        # import africastalking
        # africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
        # sms = africastalking.SMS
        # response = sms.send(f"Your verification code is: {otp_code}", [phone_number])
        
        return True

class IDVerificationService:
    """Handle Government ID verification"""
    
    @staticmethod
    def validate_id_format(id_number, id_type):
        """Basic format validation for IDs"""
        if id_type == 'national_id':
            # Nigerian National ID: 11 digits
            return len(id_number) >= 10 and id_number.isdigit()
        elif id_type == 'drivers_license':
            # Basic validation for driver's license
            return len(id_number) >= 8
        elif id_type == 'passport':
            # Passport number validation
            return len(id_number) >= 6
        elif id_type == 'voter_id':
            # Voter's card validation
            return len(id_number) >= 10
        return True