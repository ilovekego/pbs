import os
import uuid
import random
import requests
import resend
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from models import db, User, ServiceCategory, ServiceRequest

# Permitted file upload extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def format_kenyan_phone(phone_number):
    # Formats local phone numbers to standard 254 international format for TalkSasa API
    clean_phone = str(phone_number).strip().replace(' ', '').replace('+', '').replace('-', '')
    if clean_phone.startswith('0'):
        clean_phone = '254' + clean_phone[1:]
    elif clean_phone.startswith('7') or clean_phone.startswith('1'):
        clean_phone = '254' + clean_phone
    return clean_phone


def generate_otp_code():
    # Generates a 6-digit numeric OTP code
    return str(random.randint(100000, 999999))


# Mwananchi AI Agent Service Integration

def ask_mwananchi_groq_ai(user_prompt, user_context=None):
    api_endpoint = "https://api.vinniedigitalhub.co.ke/ai/gpt"

    # Base System Persona Context
    system_context = (
        "You are Mwananchi AI, the official intelligent AI Agent for Murang'a County Government Public Service Board in Kenya. "
        "You assist citizens with information and can execute actions like lodging service request tickets or checking status. "
        "Murang'a County Department Categories & Codes:\n"
        "1. Agri-Access & Roads (Code: ROADS) - Potholes, damaged feeder roads, culverts.\n"
        "2. Streetlight Repairs (Code: LIGHTS) - High-mast lights, solar lights, dark streets.\n"
        "3. Water Infrastructure (Code: WATER) - Burst pipes, low water pressure, sewer blockages.\n"
        "4. Market Sanitation (Code: WASTE) - Market garbage, uncollected refuse, illegal dumps.\n"
        "County Details: 7 Constituencies (Kiharu, Kangema, Mathioya, Maragua, Kandara, Gatanga, Kigumo) across 35 Wards.\n"
    )

    if user_context and user_context.get('is_logged_in'):
        context_str = (
            f"Active User Info:\n"
            f"- Name: {user_context.get('name')}\n"
            f"- Electoral Residence: {user_context.get('ward')} Ward, {user_context.get('constituency')} Constituency\n"
            f"- Phone Verified: {user_context.get('is_phone_verified')}\n"
            f"- Recent Tickets: {', '.join(user_context.get('recent_tickets')) if user_context.get('recent_tickets') else 'None'}\n"
            "Action Execution Rule: If the user explicitly asks you to lodge or submit a ticket and provides an issue description and location, "
            "include this action tag at the end of your response: [ACTION:CREATE_TICKET|CATEGORY_CODE|SPECIFIC_LOCATION|PROBLEM_DESCRIPTION]\n"
        )
        system_context += context_str

    full_prompt = f"{system_context}\nCitizen Query: {user_prompt}"

    try:
        response = requests.get(
            api_endpoint,
            params={"prompt": full_prompt},
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") and "response" in data:
                return data["response"].strip()

        print(f"Mwananchi AI API Error ({response.status_code}): {response.text}")
        return "Mwananchi AI is currently processing requests. Please try again shortly."
    except requests.RequestException as exc:
        print(f"Mwananchi AI connection error: {exc}")
        return "Unable to connect to Mwananchi AI server at the moment. Please check your network connection."


# TalkSasa Bulk SMS v3 API Integration

def send_talksasa_otp(phone_number, otp_code, custom_message=None):
    api_endpoint = os.environ.get('TALKSASA_API_ENDPOINT', 'https://bulksms.talksasa.com/api/v3/sms/send')
    api_token = os.environ.get('TALKSASA_API_TOKEN', '')
    sender_id = os.environ.get('TALKSASA_SENDER_ID', 'TALK-SASA')

    formatted_phone = format_kenyan_phone(phone_number)
    
    if custom_message:
        message_text = custom_message
    else:
        message_text = f"Your Murang'a County Portal verification code is: {otp_code}. Valid for 10 minutes."

    # Safe fallback logging if environment variable is not set locally
    if not api_token:
        print(f"[SMS MOCK] Token not configured in .env | To: {formatted_phone} | Message: {message_text}")
        return True

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    payload = {
        'sender_id': sender_id,
        'recipient': formatted_phone,
        'phone': formatted_phone,
        'message': message_text
    }

    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=8)
        
        # HTTP 200 (OK), 201 (Created), and 202 (Accepted/Queued) are valid success codes for TalkSasa
        if response.status_code in [200, 201, 202]:
            return True
            
        print(f"TalkSasa API response error ({response.status_code}): {response.text}")
        return False
    except requests.RequestException as exc:
        print(f"TalkSasa connection failure: {exc}")
        return False


# Resend API Email Dispatchers

def send_verification_email_smtp(to_email, verification_link):
    api_key = os.environ.get('RESEND_API_KEY', '')
    sender_email = os.environ.get('MAIL_DEFAULT_SENDER', 'Murang\'a County Portal <otp@vinniedigitalhub.co.ke>')

    # Safe fallback if RESEND_API_KEY is omitted in development
    if not api_key:
        print(f"[EMAIL MOCK] API key missing in .env | Link for {to_email}: {verification_link}")
        return True

    resend.api_key = api_key

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Account</title>
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <tr>
                <td style="background-color: #002B49; padding: 24px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: bold;">Murang'a County Government</h1>
                    <p style="color: #D4AF37; margin: 5px 0 0 0; font-size: 13px; font-weight: 600; letter-spacing: 1px;">PUBLIC SERVICE REQUEST PORTAL</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 32px 28px; color: #1E293B;">
                    <h2 style="color: #002B49; font-size: 18px; margin-top: 0;">Account Email Verification</h2>
                    <p style="font-size: 15px; line-height: 1.6; color: #334155;">Hello,</p>
                    <p style="font-size: 15px; line-height: 1.6; color: #334155;">Thank you for registering on the Murang'a County Public Service Request Portal. Please confirm your email address to activate your account and access county services.</p>
                    
                    <div style="text-align: center; margin: 32px 0;">
                        <a href="{verification_link}" style="background-color: #002B49; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 2px 6px rgba(0,43,73,0.3);">
                            Verify Email Address
                        </a>
                    </div>

                    <p style="font-size: 13px; line-height: 1.5; color: #64748B;">If the button above does not work, copy and paste this link into your browser address bar:</p>
                    <p style="font-size: 13px; word-break: break-all; color: #2558E5; background-color: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; margin: 0;">
                        <a href="{verification_link}" style="color: #2558E5; text-decoration: underline;">{verification_link}</a>
                    </p>
                    
                    <p style="font-size: 13px; color: #64748B; margin-top: 24px; margin-bottom: 0;">This verification link is valid for 24 hours.</p>
                </td>
            </tr>
            <tr>
                <td style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="font-size: 12px; color: #94A3B8; margin: 0;">&copy; 2026 Murang'a County Public Service Board | Official Governance Portal</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    params = {
        "from": sender_email,
        "to": [to_email],
        "subject": "Verify Your Account - Murang'a County Portal",
        "html": html_body
    }

    try:
        response = resend.Emails.send(params)
        return bool(response.get("id"))
    except Exception as exc:
        print(f"Resend email dispatch error: {exc}")
        return False


def send_password_reset_email(to_email, otp_code):
    api_key = os.environ.get('RESEND_API_KEY', '')
    sender_email = os.environ.get('MAIL_RESET_SENDER', 'Murang\'a County Portal <reset@vinniedigitalhub.co.ke>')

    if not api_key:
        print(f"[RESET EMAIL MOCK] API key missing in .env | To: {to_email} | OTP: {otp_code}")
        return True

    resend.api_key = api_key

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset OTP</title>
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <tr>
                <td style="background-color: #002B49; padding: 24px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: bold;">Murang'a County Government</h1>
                    <p style="color: #D4AF37; margin: 5px 0 0 0; font-size: 13px; font-weight: 600; letter-spacing: 1px;">PUBLIC SERVICE REQUEST PORTAL</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 32px 28px; color: #1E293B;">
                    <h2 style="color: #002B49; font-size: 18px; margin-top: 0;">Password Reset Request</h2>
                    <p style="font-size: 15px; line-height: 1.6; color: #334155;">Hello,</p>
                    <p style="font-size: 15px; line-height: 1.6; color: #334155;">We are sorry to hear that you cannot log in to your portal. We hope that you are the one who triggered the button. If that is the case, use the OTP below and follow the steps on screen to reset your password.</p>
                    
                    <div style="text-align: center; margin: 32px 0;">
                        <div style="display: inline-block; background-color: #f8fafc; border: 2px dashed #002B49; padding: 16px 36px; border-radius: 10px;">
                            <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #002B49;">{otp_code}</span>
                        </div>
                    </div>

                    <p style="font-size: 13px; color: #64748B; margin-top: 24px; margin-bottom: 0;">This OTP code will expire in 10 minutes. If you did not request this password reset, please ignore this email or contact support.</p>
                </td>
            </tr>
            <tr>
                <td style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="font-size: 12px; color: #94A3B8; margin: 0;">&copy; 2026 Murang'a County Public Service Board | Official Governance Portal</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    params = {
        "from": sender_email,
        "to": [to_email],
        "subject": "Password Reset OTP - Murang'a County Portal",
        "html": html_body
    }

    try:
        response = resend.Emails.send(params)
        return bool(response.get("id"))
    except Exception as exc:
        print(f"Resend reset email dispatch error: {exc}")
        return False


# Identity & Account Management Services

def register_user(full_name, email, national_id, phone, password, constituency=None, ward=None, role='citizen'):
    if User.query.filter_by(email=email).first():
        return None, "This email address is already registered.", None

    if User.query.filter_by(national_id=national_id).first():
        return None, "This National ID is already registered.", None

    otp_code = generate_otp_code()
    otp_expiry = datetime.utcnow() + timedelta(minutes=10)

    user = User(
        full_name=full_name,
        email=email,
        national_id=national_id,
        phone=phone,
        phone_otp=otp_code,
        otp_expiry=otp_expiry,
        is_phone_verified=False,
        is_email_verified=False,
        constituency=constituency,
        ward=ward,
        role=role
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return user, None, otp_code


def authenticate_user(identifier, password):
    clean_id = str(identifier).strip().lower()
    formatted_phone = format_kenyan_phone(clean_id)

    # Multi-identifier login: Allows logging in via Email, National ID, or Phone Number
    user = User.query.filter(
        (User.email == clean_id) | 
        (User.national_id == clean_id) | 
        (User.phone == clean_id) |
        (User.phone == formatted_phone)
    ).first()

    if user and user.check_password(password):
        return user
    return None


def verify_user_phone_otp(user_id, submitted_otp):
    user = User.query.get(user_id)
    if not user:
        return False, "User account not found."

    if not user.phone_otp or not user.otp_expiry:
        return False, "No active OTP request found."

    if datetime.utcnow() > user.otp_expiry:
        return False, "The OTP code has expired. Please request a new code."

    if user.phone_otp == submitted_otp:
        user.is_phone_verified = True
        user.phone_otp = None
        user.otp_expiry = None
        db.session.commit()
        return True, "Phone number verified successfully."

    return False, "Invalid OTP code entered."


def generate_fresh_otp(user_id):
    user = User.query.get(user_id)
    if not user:
        return None, None

    new_otp = generate_otp_code()
    user.phone_otp = new_otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    return user, new_otp


def mark_email_verified(user_id):
    user = User.query.get(user_id)
    if not user:
        return False, "User account not found."

    user.is_email_verified = True
    db.session.commit()
    return True, "Email address verified successfully."


def initiate_password_reset(identifier):
    clean_id = str(identifier).strip().lower()
    formatted_phone = format_kenyan_phone(clean_id)

    user = User.query.filter(
        (User.email == clean_id) | 
        (User.national_id == clean_id) | 
        (User.phone == clean_id) |
        (User.phone == formatted_phone)
    ).first()

    if not user:
        return None, None

    otp_code = generate_otp_code()
    user.phone_otp = otp_code
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()

    # Dispatch SMS OTP via TalkSasa
    sms_msg = f"We are sorry to hear that you cannot log in to your portal. Your password reset OTP is: {otp_code}. Valid for 10 minutes."
    send_talksasa_otp(user.phone, otp_code, custom_message=sms_msg)

    # Dispatch Email OTP via Resend from reset@vinniedigitalhub.co.ke
    send_password_reset_email(user.email, otp_code)

    return user, otp_code


def complete_password_reset(user_id, submitted_otp, new_password):
    user = User.query.get(user_id)
    if not user:
        return False, "User account not found."

    if not user.phone_otp or not user.otp_expiry:
        return False, "No active reset request found."

    if datetime.utcnow() > user.otp_expiry:
        return False, "The reset code has expired. Please request a new code."

    if user.phone_otp == submitted_otp:
        user.set_password(new_password)
        user.phone_otp = None
        user.otp_expiry = None
        db.session.commit()
        return True, "Password reset successfully."

    return False, "Invalid OTP code entered."


# Service Categories & Request Operations

def get_all_categories():
    return ServiceCategory.query.all()


def create_service_request(user_id, category_id, constituency, ward, specific_location, priority, description, file_obj, upload_folder):
    filename = None
    if file_obj and file_obj.filename != '' and is_allowed_file(file_obj.filename):
        ext = file_obj.filename.rsplit('.', 1)[1].lower()
        filename = f"req_{uuid.uuid4().hex[:10]}_{int(datetime.utcnow().timestamp())}.{ext}"
        file_obj.save(os.path.join(upload_folder, filename))

    ticket_number = f"MUR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    new_request = ServiceRequest(
        ticket_id=ticket_number,
        category_id=category_id,
        constituency=constituency,
        ward=ward,
        specific_location=specific_location,
        priority=priority,
        description=description,
        image_filename=filename,
        user_id=user_id
    )
    db.session.add(new_request)
    db.session.commit()
    return new_request


def get_citizen_requests(user_id):
    return ServiceRequest.query.filter_by(user_id=user_id).order_by(ServiceRequest.created_at.desc()).all()


def update_request_status(request_id, new_status, admin_notes):
    req = ServiceRequest.query.get(request_id)
    if not req:
        return False, "Request ticket not found."

    if new_status in ['Pending', 'In Progress', 'Resolved']:
        req.status = new_status
        req.admin_notes = admin_notes
        db.session.commit()
        return True, f"Ticket #{req.ticket_id} updated to '{new_status}'."

    return False, "Invalid status choice."


def record_citizen_rating(request_id, user_id, rating_val):
    req = ServiceRequest.query.get(request_id)
    if req and req.user_id == user_id and rating_val and 1 <= rating_val <= 5:
        req.rating = rating_val
        db.session.commit()
        return True
    return False


# Analytics Data Engine

def get_admin_dashboard_metrics():
    all_requests = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).all()
    categories = ServiceCategory.query.all()

    total_cases = len(all_requests)
    pending_cases = sum(1 for r in all_requests if r.status == 'Pending')
    in_progress_cases = sum(1 for r in all_requests if r.status == 'In Progress')
    resolved_cases = sum(1 for r in all_requests if r.status == 'Resolved')
    overdue_cases = sum(1 for r in all_requests if r.is_overdue)

    category_counts = {}
    for cat in categories:
        category_counts[cat.name] = sum(1 for r in all_requests if r.category_id == cat.id)

    analytics = {
        'total': total_cases,
        'pending': pending_cases,
        'in_progress': in_progress_cases,
        'resolved': resolved_cases,
        'overdue': overdue_cases,
        'category_counts': category_counts
    }

    return all_requests, analytics


# Database Initialization & Seeding Defaults

def seed_database_defaults():
    db.create_all()

    try:
        if ServiceCategory.query.count() == 0:
            default_categories = [
                ServiceCategory(
                    name='Agri-Access & Roads',
                    code='ROADS',
                    description='Potholes, feeder road damage, broken culverts, and mudslides.',
                    icon_class='fa-solid fa-road'
                ),
                ServiceCategory(
                    name='Streetlight Repairs',
                    code='LIGHTS',
                    description='High-mast floodlights, market lighting, and solar light faults.',
                    icon_class='fa-solid fa-lightbulb'
                ),
                ServiceCategory(
                    name='Water Infrastructure',
                    code='WATER',
                    description='Main pipe bursts, low pressure, and sewer line blockages.',
                    icon_class='fa-solid fa-droplet'
                ),
                ServiceCategory(
                    name='Market Sanitation',
                    code='WASTE',
                    description='Uncollected waste at market centers and illegal dumping sites.',
                    icon_class='fa-solid fa-trash-can'
                )
            ]
            db.session.add_all(default_categories)
            db.session.commit()

        # Check for existing admin or citizen by email or phone before attempting insert
        existing_admin = User.query.filter(
            (User.email == 'admin@muranga.go.ke') | (User.phone == '254700000000')
        ).first()

        if not existing_admin:
            admin = User(
                full_name='County Director',
                email='admin@muranga.go.ke',
                national_id='10000000',
                phone='254700000000',
                is_phone_verified=True,
                is_email_verified=True,
                constituency='Kiharu',
                ward='Township',
                role='admin'
            )
            admin.set_password('AdminPass123!')

            citizen = User(
                full_name='Jane Citizen',
                email='jane@citizen.go.ke',
                national_id='28394012',
                phone='254712345678',
                is_phone_verified=True,
                is_email_verified=True,
                constituency='Kiharu',
                ward='Township',
                role='citizen'
            )
            citizen.set_password('CitizenPass123!')

            db.session.add_all([admin, citizen])
            db.session.commit()
    except (IntegrityError, Exception) as exc:
        db.session.rollback()
        print(f"[SEED HANDLED] Database seeding skipped by concurrent worker: {exc}")