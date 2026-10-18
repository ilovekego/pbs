from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import services

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('citizen.citizen_dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        national_id = request.form.get('national_id')
        phone = request.form.get('phone')
        password = request.form.get('password')
        constituency = request.form.get('constituency')
        ward = request.form.get('ward')
        role = request.form.get('role', 'citizen')

        user, error, otp_code = services.register_user(
            full_name=full_name,
            email=email,
            national_id=national_id,
            phone=phone,
            password=password,
            constituency=constituency,
            ward=ward,
            role=role
        )

        if error:
            flash(error, 'danger')
            return render_template('register.html')

        login_user(user)

        services.send_talksasa_otp(user.phone, otp_code)
        verify_link = url_for('auth.verify_email_token', token=user.id, _external=True)
        services.send_verification_email_smtp(user.email, verify_link)

        flash('Welcome to Murang\'a Portal! Please verify your phone number and email to lodge service requests.', 'info')
        return redirect(url_for('citizen.citizen_dashboard'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('citizen.citizen_dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('email')
        password = request.form.get('password')

        user = services.authenticate_user(identifier, password)
        if user:
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('citizen.citizen_dashboard'))

        flash('Invalid login credentials. Please check your identifier and password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/verify-phone', methods=['GET', 'POST'])
@login_required
def verify_phone():
    if current_user.is_phone_verified:
        flash('Your phone number is already verified.', 'info')
        return redirect(url_for('citizen.citizen_dashboard'))

    if request.method == 'POST':
        otp_code = request.form.get('otp_code')
        success, message = services.verify_user_phone_otp(current_user.id, otp_code)
        if success:
            flash(message, 'success')
            return redirect(url_for('citizen.citizen_dashboard'))
        flash(message, 'danger')

    return render_template('verify_phone.html', phone=current_user.phone)


@auth_bp.route('/resend-otp', methods=['POST'])
@login_required
def resend_otp():
    user, new_otp = services.generate_fresh_otp(current_user.id)
    if user and new_otp:
        services.send_talksasa_otp(user.phone, new_otp)
        return jsonify({'success': True, 'message': 'A new SMS OTP has been sent to your phone.'})
    return jsonify({'success': False, 'message': 'Failed to resend OTP.'}), 400


@auth_bp.route('/resend-email-verification', methods=['POST'])
@login_required
def resend_email_verification():
    verify_link = url_for('auth.verify_email_token', token=current_user.id, _external=True)
    if services.send_verification_email_smtp(current_user.email, verify_link):
        flash(f'Verification email dispatched to {current_user.email}. Check your inbox or spam folder.', 'success')
    else:
        flash('Failed to dispatch verification email. Please try again.', 'danger')
    return redirect(url_for('citizen.citizen_dashboard'))


@auth_bp.route('/verify-email/<int:token>')
def verify_email_token(token):
    success, message = services.mark_email_verified(token)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        user, otp_code = services.initiate_password_reset(identifier)
        if user:
            flash('Password reset OTP sent to your registered phone and email.', 'info')
            return redirect(url_for('auth.reset_password_otp'))
        flash('No account found with that identifier.', 'danger')

    return render_template('forgot_password.html')


@auth_bp.route('/reset-password-otp', methods=['GET', 'POST'])
def reset_password_otp():
    if request.method == 'POST':
        otp_code = request.form.get('otp_code')
        new_password = request.form.get('new_password')
        
        user = services.User.query.filter_by(phone_otp=otp_code).first()
        if user:
            success, message = services.complete_password_reset(user.id, otp_code, new_password)
            if success:
                flash(message, 'success')
                return redirect(url_for('auth.login'))
            flash(message, 'danger')
        else:
            flash('Invalid or expired OTP code.', 'danger')

    return render_template('reset_password_otp.html')
