# Copyright 2026 Jane Gathuo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import uuid
import random
import requests
import resend
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from models import db, User, ServiceCategory, ServiceRequest, TicketComment, BusinessPermit, BursaryApplication

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def format_kenyan_phone(phone_number):
    clean_phone = str(phone_number).strip().replace(' ', '').replace('+', '').replace('-', '')
    if clean_phone.startswith('0'):
        clean_phone = '254' + clean_phone[1:]
    elif clean_phone.startswith('7') or clean_phone.startswith('1'):
        clean_phone = '254' + clean_phone
    return clean_phone


def generate_otp_code():
    return str(random.randint(100000, 999999))


# Autonomous Mwananchi AI Agent Dispatcher with Conversational Memory & Up-To-Date Murang'a Leadership Knowledge

def ask_mwananchi_groq_ai(user_prompt, chat_history=None, user_context=None):
    api_endpoint = "https://api.vinniedigitalhub.co.ke/ai/gpt"

    # Comprehensive Murang'a County Leadership & Governance Knowledge Base
    system_context = (
        "You are Mwananchi AI, the official Autonomous Digital Assistant for the Murang'a County Government Public Service Board in Kenya.\n\n"
        "OFFICIAL MURANG'A COUNTY LEADERSHIP KNOWLEDGE BASE (Always use these current facts):\n"
        "- Governor: H.E. Dr. Irungu Kang'ata\n"
        "- Deputy Governor: H.E. Stephen Munania\n"
        "- Senator: Hon. Joe Nyutu (Joseph Nyutu Ngugi)\n"
        "- Woman Representative: Hon. Betty Maina (Beatrice Njeri Maina)\n"
        "- County Assembly Speaker: Hon. Johnson Mukuha\n"
        "- Deputy Speaker: Hon. Moses Gachui Mungai (Kihumbu-ini Ward)\n"
        "- Majority Leader: Hon. Francis Kibe Kamau (Ithiru Ward)\n"
        "- 7 Constituencies & Members of Parliament (MPs):\n"
        "  1. Kiharu Constituency: Hon. Samson Ndindi Nyoro\n"
        "  2. Kangema Constituency: Hon. Peter Irungu Kihungi\n"
        "  3. Mathioya Constituency: Hon. Edwin Mugo Gichuki\n"
        "  4. Maragua Constituency: Hon. Mary Wamaua Waithira\n"
        "  5. Kandara Constituency: Hon. Chege Njuguna\n"
        "  6. Gatanga Constituency: Hon. Edward Muriu\n"
        "  7. Kigumo Constituency: Hon. Joseph Kamau Munyoro\n"
        "- 35 Electoral Wards & Elected MCAs:\n"
        "  * Kiharu: Township (Hon. Karina Machigo), Mbiri (Hon. Benard Ruiru), Gaturi (Hon. Njeri Gathee), Mugoiri (Hon. John Kamwaga), Murarandia (Hon. Peter Munga), Wangu (Hon. Margaret Gichia)\n"
        "  * Kangema: Muguru (Hon. Moses Muchiri), Kanyenyaini (Hon. Grace Nduta), Rwathia (Hon. Kenneth Kamau)\n"
        "  * Mathioya: Gitugi (Hon. Edwin Mwangi), Kiru (Hon. Morris Thuku), Kamacharia (Hon. Gerald Wambugu)\n"
        "  * Maragua: Nginda (Hon. John Mwangi), Ichagaki (Hon. Hilary Muchoki), Makuyu (Hon. Thomas Muteti), Kambiti (Hon. Laban Chomba), Kamahuha (Hon. James Karanja), Muthithi (Hon. Boniface Mbau)\n"
        "  * Kandara: Muruka (Hon. Peter Murigi), Ng'araria (Hon. Simon Wamwea), Ruchu (Hon. Naomi Maina), Gaichanjiru (Hon. John Munyua), Kagundi-ini (Hon. Samson Mukora), Ithiru (Hon. Francis Kibe)\n"
        "  * Gatanga: Gatanga (Hon. John Kibaiya), Kihumbu-ini (Hon. Moses Gachui), Mugumo-ini (Hon. Alex Wainaina), Kariara (Hon. Clement Mbatia), Ithanga (Hon. Alex Makau), Kakuzi Mitumburi (Hon. Steven Kimani)\n"
        "  * Kigumo: Kigumo (Hon. Caroline Njoroge), Kangari (Hon. Moses Mirara), Kinyona (Hon. Liz Mbugua), Kahumbu (Hon. Chefman Isaac), Kimorori Wempa (Hon. Elizabeth Mwangi)\n"
        "- Department Categories & Codes: ROADS (Roads & Agri-Access), LIGHTS (Streetlights), WATER (Water & Sewage), WASTE (Market Sanitation).\n"
        "- Portal Services: Service Requests, Single Business Permits (SBP), County Bursaries, Smart Parking, Land Rates, Public Service Recruitment.\n"
        "- STRICT PERSONA RULE: NEVER mention third-party AI vendors, OpenAI, ChatGPT, Groq, or LLMs. Speak strictly as Murang'a County's official Digital Assistant.\n\n"
        "INTERACTIVE ONE-BY-ONE CONVERSATIONAL FLOW:\n"
        "1. Do NOT request all user information at once! Ask questions ONE BY ONE in a friendly, conversational tone.\n"
        "2. For Account Registration: First ask for Full Name. Once answered, ask for Email. Next National ID, then Phone Number, Password, Constituency, and Ward.\n"
        "3. For Service Tickets / Permits / Bursaries: Ask for missing details step by step.\n"
        "4. Once ALL necessary fields have been collected across the conversation history, output the corresponding action tag at the very end of your response:\n"
        "   - Account Registration: [ACTION:REGISTER_USER|FULL_NAME|EMAIL|NATIONAL_ID|PHONE|PASSWORD|CONSTITUENCY|WARD]\n"
        "   - Service Ticket: [ACTION:CREATE_TICKET|CATEGORY_CODE|SPECIFIC_LOCATION|PROBLEM_DESCRIPTION]\n"
        "   - Business Permit: [ACTION:APPLY_PERMIT|BUSINESS_NAME|BUSINESS_TYPE|LOCATION]\n"
        "   - County Bursary: [ACTION:APPLY_BURSARY|STUDENT_NAME|INSTITUTION|AMOUNT]\n"
        "   - Ticket Comment: [ACTION:ADD_COMMENT|TICKET_ID|MESSAGE]\n"
    )

    if user_context and user_context.get('is_logged_in'):
        context_str = (
            f"Active Logged-In Citizen Context:\n"
            f"- Name: {user_context.get('name')}\n"
            f"- Email: {user_context.get('email')}\n"
            f"- Phone: {user_context.get('phone')}\n"
            f"- Residence: {user_context.get('ward')} Ward, {user_context.get('constituency')} Constituency\n"
            f"- Phone Verified: {user_context.get('is_phone_verified')}\n"
            f"- Active Tickets: {', '.join(user_context.get('recent_tickets')) if user_context.get('recent_tickets') else 'None'}\n"
            f"- Business Permits: {', '.join(user_context.get('permits')) if user_context.get('permits') else 'None'}\n"
        )
        system_context += context_str
    else:
        system_context += "Current User Context: Guest Visitor (Not logged in).\n"

    # Assemble Conversational History Context
    history_text = ""
    if chat_history and isinstance(chat_history, list):
        history_text = "\nRecent Conversation History:\n"
        for msg in chat_history[-8:]:  # Include last 8 turns of conversation
            role_label = "Citizen" if msg.get('role') == 'user' else "Mwananchi AI"
            history_text += f"{role_label}: {msg.get('text', '')}\n"

    full_prompt = f"{system_context}\n{history_text}\nCitizen Current Input: {user_prompt}"

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
        return "Mwananchi AI Agent is currently updating county service pipelines. Please try again shortly."
    except requests.RequestException as exc:
        print(f"Mwananchi AI connection error: {exc}")
        return "Unable to establish connection with Mwananchi AI Agent server. Please check your network."


# SMS & Email Services

def send_talksasa_otp(phone_number, otp_code, custom_message=None):
    api_endpoint = os.environ.get('TALKSASA_API_ENDPOINT', 'https://bulksms.talksasa.com/api/v3/sms/send')
    api_token = os.environ.get('TALKSASA_API_TOKEN', '')
    sender_id = os.environ.get('TALKSASA_SENDER_ID', 'TALK-SASA')

    formatted_phone = format_kenyan_phone(phone_number)
    
    if custom_message:
        message_text = custom_message
    else:
        message_text = f"Your Murang'a County Portal verification code is: {otp_code}. Valid for 10 minutes."

    if not api_token:
        print(f"[SMS MOCK] Token not configured | To: {formatted_phone} | Message: {message_text}")
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
        return response.status_code in [200, 201, 202]
    except requests.RequestException as exc:
        print(f"TalkSasa connection failure: {exc}")
        return False


def send_verification_email_smtp(to_email, verification_link):
    api_key = os.environ.get('RESEND_API_KEY', '')
    sender_email = os.environ.get('MAIL_DEFAULT_SENDER', 'Murang\'a County Portal <otp@vinniedigitalhub.co.ke>')

    if not api_key:
        print(f"[EMAIL MOCK] API key missing | Link for {to_email}: {verification_link}")
        return True

    resend.api_key = api_key

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>Verify Account</title></head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 10px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h2 style="color: #002B49;">Murang'a County Government</h2>
            <p>Hello,</p>
            <p>Please verify your email address to complete registration on the Murang'a County Public Service Portal.</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #002B49; color: #fff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: bold;">Verify Email Address</a>
            </p>
            <p style="font-size: 12px; color: #888;">Valid for 24 hours.</p>
        </div>
    </body>
    </html>
    """

    params = {
        "from": sender_email,
        "to": [to_email],
        "subject": "Account Verification - Murang'a County Portal",
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
        print(f"[RESET EMAIL MOCK] API key missing | To: {to_email} | OTP: {otp_code}")
        return True

    resend.api_key = api_key

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>Password Reset</title></head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 10px; padding: 30px;">
            <h2 style="color: #002B49;">Murang'a County Government</h2>
            <p>Your Password Reset OTP Code is:</p>
            <h1 style="color: #002B49; letter-spacing: 5px;">{otp_code}</h1>
            <p style="font-size: 12px; color: #888;">Expires in 10 minutes.</p>
        </div>
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


# User & Account Services

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
        return False, "The OTP code has expired."

    if user.phone_otp == submitted_otp:
        user.is_phone_verified = True
        user.phone_otp = None
        user.otp_expiry = None
        db.session.commit()
        return True, "Phone number verified successfully."

    return False, "Invalid OTP code."


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

    sms_msg = f"Your Murang'a County Portal password reset OTP is: {otp_code}. Valid for 10 minutes."
    send_talksasa_otp(user.phone, otp_code, custom_message=sms_msg)
    send_password_reset_email(user.email, otp_code)

    return user, otp_code


def complete_password_reset(user_id, submitted_otp, new_password):
    user = User.query.get(user_id)
    if not user:
        return False, "User account not found."

    if not user.phone_otp or not user.otp_expiry:
        return False, "No active reset request found."

    if datetime.utcnow() > user.otp_expiry:
        return False, "The reset code has expired."

    if user.phone_otp == submitted_otp:
        user.set_password(new_password)
        user.phone_otp = None
        user.otp_expiry = None
        db.session.commit()
        return True, "Password reset successfully."

    return False, "Invalid OTP code entered."


# Expanded County Services Operations

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


def add_ticket_comment(ticket_id, user_id, message, is_admin=False):
    req = ServiceRequest.query.get(ticket_id)
    if not req:
        return None, "Ticket not found."

    comment = TicketComment(
        ticket_id=ticket_id,
        user_id=user_id,
        message=message,
        is_admin_reply=is_admin
    )
    req.updated_at = datetime.utcnow()
    db.session.add(comment)
    db.session.commit()
    return comment, None


def create_business_permit(user_id, business_name, business_type, location, fee=5000.0):
    p_num = f"SBP-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:5].upper()}"
    permit = BusinessPermit(
        permit_number=p_num,
        user_id=user_id,
        business_name=business_name,
        business_type=business_type,
        location=location,
        fee_amount=fee
    )
    db.session.add(permit)
    db.session.commit()
    return permit


def create_bursary_application(user_id, student_name, institution, amount):
    app_id = f"BUR-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:5].upper()}"
    bursary = BursaryApplication(
        application_id=app_id,
        user_id=user_id,
        student_name=student_name,
        institution=institution,
        requested_amount=amount
    )
    db.session.add(bursary)
    db.session.commit()
    return bursary


def get_citizen_requests(user_id):
    return ServiceRequest.query.filter_by(user_id=user_id).order_by(ServiceRequest.created_at.desc()).all()


def update_request_status(request_id, new_status, admin_notes):
    req = ServiceRequest.query.get(request_id)
    if not req:
        return False, "Request ticket not found."

    if new_status in ['Pending', 'In Progress', 'Resolved', 'Closed']:
        req.status = new_status
        if admin_notes:
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


def get_admin_dashboard_metrics():
    all_requests = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).all()
    categories = ServiceCategory.query.all()
    all_permits = BusinessPermit.query.order_by(BusinessPermit.created_at.desc()).all()
    all_bursaries = BursaryApplication.query.order_by(BursaryApplication.created_at.desc()).all()

    total_cases = len(all_requests)
    pending_cases = sum(1 for r in all_requests if r.status == 'Pending')
    in_progress_cases = sum(1 for r in all_requests if r.status == 'In Progress')
    resolved_cases = sum(1 for r in all_requests if r.status == 'Resolved')
    overdue_cases = sum(1 for r in all_requests if r.is_overdue)

    category_counts = {cat.name: sum(1 for r in all_requests if r.category_id == cat.id) for cat in categories}

    analytics = {
        'total': total_cases,
        'pending': pending_cases,
        'in_progress': in_progress_cases,
        'resolved': resolved_cases,
        'overdue': overdue_cases,
        'category_counts': category_counts,
        'total_permits': len(all_permits),
        'total_bursaries': len(all_bursaries)
    }

    return all_requests, analytics, all_permits, all_bursaries


def seed_database_defaults():
    db.create_all()

    try:
        if ServiceCategory.query.count() == 0:
            default_categories = [
                ServiceCategory(name='Agri-Access & Roads', code='ROADS', description='Potholes, feeder roads, culverts.', icon_class='fa-solid fa-road'),
                ServiceCategory(name='Streetlight Repairs', code='LIGHTS', description='Floodlights, solar lights.', icon_class='fa-solid fa-lightbulb'),
                ServiceCategory(name='Water Infrastructure', code='WATER', description='Main pipe bursts, sewer lines.', icon_class='fa-solid fa-droplet'),
                ServiceCategory(name='Market Sanitation', code='WASTE', description='Uncollected waste, dumping sites.', icon_class='fa-solid fa-trash-can')
            ]
            db.session.add_all(default_categories)
            db.session.commit()

        existing_admin = User.query.filter((User.email == 'admin@muranga.go.ke') | (User.phone == '254700000000')).first()
        if not existing_admin:
            admin = User(full_name='County Director', email='admin@muranga.go.ke', national_id='10000000', phone='254700000000', is_phone_verified=True, is_email_verified=True, constituency='Kiharu', ward='Township', role='admin')
            admin.set_password('AdminPass123!')

            citizen = User(full_name='Jane Citizen', email='jane@citizen.go.ke', national_id='28394012', phone='254712345678', is_phone_verified=True, is_email_verified=True, constituency='Kiharu', ward='Township', role='citizen')
            citizen.set_password('CitizenPass123!')

            db.session.add_all([admin, citizen])
            db.session.commit()
    except (IntegrityError, Exception) as exc:
        db.session.rollback()
        print(f"[SEED HANDLED] Database seeding skipped: {exc}")