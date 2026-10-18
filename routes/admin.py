from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import services

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access restricted to County Administrators.', 'danger')
        return redirect(url_for('citizen.citizen_dashboard'))

    all_requests, analytics = services.get_admin_dashboard_metrics()
    return render_template('admin_dashboard.html', requests=all_requests, analytics=analytics)


@admin_bp.route('/admin/update_status/<int:request_id>', methods=['POST'])
@login_required
def update_status(request_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    success, msg = services.update_request_status(
        request_id=request_id,
        new_status=request.form.get('status'),
        admin_notes=request.form.get('admin_notes', '').strip()
    )
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('admin.admin_dashboard'))