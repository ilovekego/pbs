import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user, login_user
import services
from models import ServiceRequest, BusinessPermit, BursaryApplication

citizen_bp = Blueprint('citizen', __name__)


@citizen_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def citizen_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == 'POST':
        if not current_user.is_phone_verified:
            flash('Please verify your phone number via SMS OTP before lodging official tickets.', 'warning')
            return redirect(url_for('auth.verify_phone'))

        category_id = request.form.get('category_id')
        constituency = request.form.get('constituency')
        ward = request.form.get('ward')
        specific_location = request.form.get('specific_location')
        priority = request.form.get('priority')
        description = request.form.get('description')
        file_obj = request.files.get('image')

        if not category_id or not specific_location or not description:
            flash('Please fill in all required fields.', 'danger')
        else:
            services.create_service_request(
                user_id=current_user.id,
                category_id=int(category_id),
                constituency=constituency,
                ward=ward,
                specific_location=specific_location,
                priority=priority,
                description=description,
                file_obj=file_obj,
                upload_folder=current_app.config['UPLOAD_FOLDER']
            )
            flash('Your service request ticket has been lodged successfully.', 'success')
            return redirect(url_for('citizen.citizen_dashboard'))

    categories = services.get_all_categories()
    user_requests = services.get_citizen_requests(current_user.id)
    user_permits = BusinessPermit.query.filter_by(user_id=current_user.id).order_by(BusinessPermit.created_at.desc()).all()
    user_bursaries = BursaryApplication.query.filter_by(user_id=current_user.id).order_by(BursaryApplication.created_at.desc()).all()

    return render_template('citizen_dashboard.html', categories=categories, requests=user_requests, permits=user_permits, bursaries=user_bursaries)


@citizen_bp.route('/ticket/<int:request_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(request_id):
    ticket = ServiceRequest.query.get_or_404(request_id)
    if ticket.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized access to ticket.', 'danger')
        return redirect(url_for('citizen.citizen_dashboard'))

    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            is_admin = (current_user.role == 'admin')
            services.add_ticket_comment(ticket.id, current_user.id, message, is_admin=is_admin)
            flash('Your response message has been posted to the ticket thread.', 'success')
            return redirect(url_for('citizen.ticket_detail', request_id=ticket.id))

    return render_template('ticket_detail.html', ticket=ticket)


@citizen_bp.route('/api/mwananchi-ai', methods=['POST'])
def mwananchi_ai_chat():
    data = request.get_json() or {}
    user_prompt = data.get('prompt', '').strip()
    chat_history = data.get('history', [])

    if not user_prompt:
        return jsonify({'response': 'Please enter a valid message or question.'}), 400

    user_context = None
    if current_user.is_authenticated:
        recent_requests = services.get_citizen_requests(current_user.id)
        recent_permits = BusinessPermit.query.filter_by(user_id=current_user.id).all()
        
        tickets_summary = [f"#{r.ticket_id} ({r.category_rel.name}: {r.status})" for r in recent_requests[:3]]
        permits_summary = [f"#{p.permit_number} ({p.business_name}: {p.status})" for p in recent_permits[:2]]

        user_context = {
            'is_logged_in': True,
            'name': current_user.full_name,
            'email': current_user.email,
            'phone': current_user.phone,
            'constituency': current_user.constituency or 'Kiharu',
            'ward': current_user.ward or 'Township',
            'is_phone_verified': current_user.is_phone_verified,
            'recent_tickets': tickets_summary,
            'permits': permits_summary
        }

    ai_response = services.ask_mwananchi_groq_ai(user_prompt, chat_history=chat_history, user_context=user_context)

    # 1. ACTION: REGISTER GUEST ACCOUNT
    reg_match = re.search(r'\[ACTION:REGISTER_USER\Vert{}(.*?)\Vert{}(.*?)\Vert{}(.*?)\Vert{}(.*?)\Vert{}(.*?)\Vert{}(.*?)\Vert{}(.*?)\]', ai_response)
    if reg_match:
        fn, em, nid, ph, pw, con, wd = [g.strip() for g in reg_match.groups()]
        new_u, err, otp = services.register_user(fn, em, nid, ph, pw, con, wd)
        if new_u:
            login_user(new_u)
            services.send_talksasa_otp(new_u.phone, otp)
            completion_msg = (
                f"\n\n**Account Registration Complete!**\n"
                f"Welcome, **{fn}**! Your account has been created and you are now logged in. "
                f"An SMS verification OTP code has been sent to `{ph}`."
            )
            ai_response = re.sub(r'\[ACTION:REGISTER_USER\Vert{}.*?\]', completion_msg, ai_response)
        else:
            ai_response = re.sub(r'\[ACTION:REGISTER_USER\Vert{}.*?\]', f"\n\n**Registration Notice:** {err}", ai_response)

    # 2. ACTION: CREATE SERVICE TICKET
    ticket_match = re.search(r'\[ACTION:CREATE_TICKET\Vert{}(.*?)\Vert{}(.*?)\Vert{}(.*?)\]', ai_response)
    if ticket_match:
        cat_code, location, desc = [g.strip() for g in ticket_match.groups()]
        if not current_user.is_authenticated:
            msg = "\n\nI can lodge this ticket for you! Let us set up your account first. What is your full name?"
        elif not current_user.is_phone_verified:
            msg = "\n\nI prepared your ticket, but you must verify your phone number via SMS OTP first before I can submit it."
        else:
            categories = services.get_all_categories()
            matched_cat = next((c for c in categories if c.code.upper() == cat_code.upper()), categories[0] if categories else None)
            if matched_cat:
                new_req = services.create_service_request(
                    user_id=current_user.id,
                    category_id=matched_cat.id,
                    constituency=current_user.constituency or 'Kiharu',
                    ward=current_user.ward or 'Township',
                    specific_location=location,
                    priority='Medium',
                    description=desc,
                    file_obj=None,
                    upload_folder=current_app.config['UPLOAD_FOLDER']
                )
                msg = f"\n\n**Action Executed:** Service request ticket lodged! **Ticket ID: {new_req.ticket_id}**."
            else:
                msg = "\n\nUnable to match department category."
        ai_response = re.sub(r'\[ACTION:CREATE_TICKET\Vert{}.*?\]', msg, ai_response)

    # 3. ACTION: APPLY BUSINESS PERMIT
    permit_match = re.search(r'\[ACTION:APPLY_PERMIT\Vert{}(.*?)\Vert{}(.*?)\Vert{}(.*?)\]', ai_response)
    if permit_match:
        b_name, b_type, b_loc = [g.strip() for g in permit_match.groups()]
        if current_user.is_authenticated:
            p = services.create_business_permit(current_user.id, b_name, b_type, b_loc)
            msg = f"\n\n**Action Executed:** Single Business Permit application submitted! **Permit No: {p.permit_number}**."
        else:
            msg = "\n\nI can submit your Single Business Permit application! Let us create your account first. What is your full name?"
        ai_response = re.sub(r'\[ACTION:APPLY_PERMIT\Vert{}.*?\]', msg, ai_response)

    # 4. ACTION: APPLY BURSARY
    bursary_match = re.search(r'\[ACTION:APPLY_BURSARY\Vert{}(.*?)\Vert{}(.*?)\Vert{}(.*?)\]', ai_response)
    if bursary_match:
        s_name, inst, amt = [g.strip() for g in bursary_match.groups()]
        if current_user.is_authenticated:
            try:
                b = services.create_bursary_application(current_user.id, s_name, inst, float(amt))
                msg = f"\n\n**Action Executed:** County Bursary application submitted! **Application ID: {b.application_id}**."
            except ValueError:
                msg = "\n\nInvalid amount specified."
        else:
            msg = "\n\nI can submit your bursary application! Let us create your account first. What is your full name?"
        ai_response = re.sub(r'\[ACTION:APPLY_BURSARY\Vert{}.*?\]', msg, ai_response)

    return jsonify({'response': ai_response})
