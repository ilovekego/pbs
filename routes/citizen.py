import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
import services

citizen_bp = Blueprint('citizen', __name__)


@citizen_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def citizen_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == 'POST':
        # Soft-gate ticket creation: Require phone verification before lodging
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
    return render_template('citizen_dashboard.html', categories=categories, requests=user_requests)


@citizen_bp.route('/rate-service/<int:request_id>', methods=['POST'])
@login_required
def rate_service(request_id):
    rating_val = request.form.get('rating', type=int)
    if services.record_citizen_rating(request_id, current_user.id, rating_val):
        flash('Thank you for rating our service resolution.', 'success')
    else:
        flash('Unable to record rating.', 'danger')
    return redirect(url_for('citizen.citizen_dashboard'))


@citizen_bp.route('/api/mwananchi-ai', methods=['POST'])
def mwananchi_ai_chat():
    data = request.get_json() or {}
    user_prompt = data.get('prompt', '').strip()

    if not user_prompt:
        return jsonify({'response': 'Please enter a valid message or question.'}), 400

    # Build User Context for AI Agent capabilities
    user_context = None
    if current_user.is_authenticated:
        recent_requests = services.get_citizen_requests(current_user.id)
        tickets_summary = []
        for req in recent_requests[:3]:
            tickets_summary.append(f"#{req.ticket_id} ({req.category_rel.name}: {req.status})")

        user_context = {
            'is_logged_in': True,
            'name': current_user.full_name,
            'constituency': current_user.constituency or 'Kiharu',
            'ward': current_user.ward or 'Township',
            'is_phone_verified': current_user.is_phone_verified,
            'is_email_verified': current_user.is_email_verified,
            'recent_tickets': tickets_summary
        }

    ai_response = services.ask_mwananchi_groq_ai(user_prompt, user_context=user_context)

    # ACTION AGENT ENGINE: Parse structured command tag [ACTION:CREATE_TICKET|CODE|LOCATION|DESCRIPTION]
    action_match = re.search(r'\[ACTION:CREATE_TICKET\|(.*?)\|(.*?)\|(.*?)\]', ai_response)
    if action_match:
        cat_code = action_match.group(1).strip().upper()
        location = action_match.group(2).strip()
        description = action_match.group(3).strip()

        if not current_user.is_authenticated:
            action_result_msg = "\n\nI can submit this ticket for you! Please log in or register a citizen account first."
        elif not current_user.is_phone_verified:
            action_result_msg = "\n\nI prepared your ticket, but you must verify your phone number via SMS OTP first before I can submit it on your behalf."
        else:
            categories = services.get_all_categories()
            matched_cat = next((c for c in categories if c.code == cat_code), categories[0] if categories else None)
            
            if matched_cat:
                new_req = services.create_service_request(
                    user_id=current_user.id,
                    category_id=matched_cat.id,
                    constituency=current_user.constituency or 'Kiharu',
                    ward=current_user.ward or 'Township',
                    specific_location=location,
                    priority='Medium',
                    description=description,
                    file_obj=None,
                    upload_folder=current_app.config['UPLOAD_FOLDER']
                )
                action_result_msg = f"\n\n**Action Executed:** I have successfully lodged your service request ticket! **Ticket ID: {new_req.ticket_id}**. You can track its progress on your dashboard."
            else:
                action_result_msg = "\n\nCould not match category department."

        # Strip action tag and append human-friendly action outcome
        ai_response = re.sub(r'\[ACTION:CREATE_TICKET\|.*?\]', action_result_msg, ai_response)

    return jsonify({'response': ai_response})