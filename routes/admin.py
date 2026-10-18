from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import services
from models import ServiceRequest, BusinessPermit, BursaryApplication

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access restricted to County Administrative Officers.', 'danger')
        return redirect(url_for('citizen.citizen_dashboard'))

    all_requests, analytics, all_permits, all_bursaries = services.get_admin_dashboard_metrics()
    return render_template(
        'admin_dashboard.html',
        requests=all_requests,
        analytics=analytics,
        permits=all_permits,
        bursaries=all_bursaries
    )


@admin_bp.route('/admin/update-status/<int:request_id>', methods=['POST'])
@login_required
def update_status(request_id):
    if current_user.role != 'admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('citizen.citizen_dashboard'))

    new_status = request.form.get('status')
    admin_notes = request.form.get('admin_notes')

    success, message = services.update_request_status(request_id, new_status, admin_notes)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/ticket/<int:request_id>/reply', methods=['POST'])
@login_required
def admin_ticket_reply(request_id):
    if current_user.role != 'admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('citizen.citizen_dashboard'))

    message = request.form.get('message', '').strip()
    if message:
        services.add_ticket_comment(request_id, current_user.id, message, is_admin=True)
        flash('Official admin reply posted to ticket thread.', 'success')

    return redirect(url_for('citizen.ticket_detail', request_id=request_id))


@admin_bp.route('/admin/permit/<int:permit_id>/update', methods=['POST'])
@login_required
def update_permit_status(permit_id):
    if current_user.role != 'admin':
        return redirect(url_for('citizen.citizen_dashboard'))

    permit = BusinessPermit.query.get_or_404(permit_id)
    new_status = request.form.get('status')
    if new_status in ['Under Review', 'Approved', 'Issued', 'Rejected']:
        permit.status = new_status
        services.db.session.commit()
        flash(f'Business Permit #{permit.permit_number} status updated to {new_status}.', 'success')

    return redirect(url_for('admin.admin_dashboard'))