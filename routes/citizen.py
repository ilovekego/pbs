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

    ai_response = services.ask_mwananchi_groq_ai(user_prompt)
    return jsonify({'response': ai_response})