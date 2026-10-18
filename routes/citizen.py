import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import services

citizen_bp = Blueprint('citizen', __name__)


@citizen_bp.route('/citizen/dashboard', methods=['GET', 'POST'])
@login_required
def citizen_dashboard():
    if current_user.role != 'citizen':
        return redirect(url_for('admin.admin_dashboard'))

    categories = services.get_all_categories()

    if request.method == 'POST':
        upload_folder = os.path.join('static', 'uploads')
        req_obj = services.create_service_request(
            user_id=current_user.id,
            category_id=request.form.get('category_id'),
            constituency=request.form.get('constituency', current_user.constituency),
            ward=request.form.get('ward', current_user.ward),
            specific_location=request.form.get('specific_location', '').strip(),
            priority=request.form.get('priority', 'Medium'),
            description=request.form.get('description', '').strip(),
            file_obj=request.files.get('image'),
            upload_folder=upload_folder
        )
        flash(f'Service Request #{req_obj.ticket_id} submitted successfully.', 'success')
        return redirect(url_for('citizen.citizen_dashboard'))

    requests_list = services.get_citizen_requests(current_user.id)
    return render_template('citizen_dashboard.html', categories=categories, requests=requests_list)


@citizen_bp.route('/citizen/rate_service/<int:request_id>', methods=['POST'])
@login_required
def rate_service(request_id):
    success = services.record_citizen_rating(
        request_id=request_id,
        user_id=current_user.id,
        rating_val=request.form.get('rating', type=int)
    )
    if success:
        flash('Thank you for rating our response team.', 'success')
    return redirect(url_for('citizen.citizen_dashboard'))