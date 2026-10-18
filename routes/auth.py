import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from models import User
import services

auth_bp = Blueprint('auth', __name__)

serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'muranga-county-portal-secret-key-2026'))


def send_verification_email(email, user_id):
    token = serializer.dumps(user_id, salt='email-verification-salt')
    verification_link = url_for('auth.verify_email', token=token, _external=True)
    services.send_verification_email_smtp(email, verification_link)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()

        user, err, otp_code = services.register_user(
            full_name=request.form.get('full_name', '').strip(),
            email=email,
            national_id=request.form.get('national_id', '').strip(),
            phone=phone,
            password=request.form.get('password', ''),
            constituency=request.form.get('constituency'),
            ward=request.form.get('ward'),
            role=request.form.get('role', 'citizen')
        )

        if err:
            flash(err, 'danger')
            return redirect(url_for('auth.register'))

        services.send_talksasa_otp(phone, otp_code)
        send_verification_email(email, user.id)

        session['pending_user_id'] = user.id
        session['otp_sent_timestamp'] = datetime.utcnow().timestamp()

        flash('Registration initiated. Check your phone for SMS OTP and email for verification link.', 'info')
        return redirect(url_for('auth.verify_phone'))

    return render_template('register.html')


@auth_bp.route('/verify-phone', methods=['GET', 'POST'])
def verify_phone():
    user_id = session.get('pending_user_id')
    if not user_id:
        flash('Verification session expired. Please log in or register.', 'warning')
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        submitted_otp = request.form.get('otp_code', '').strip()
        success, msg = services.verify_user_phone_otp(user.id, submitted_otp)

        if success:
            flash('Phone number verified successfully.', 'success')
            if user.is_email_verified:
                session.pop('pending_user_id', None)
                login_user(user)
                return redirect(url_for('auth.dashboard'))
            else:
                flash('Phone verified. Please check your inbox to verify your email before logging in.', 'info')
                return redirect(url_for('auth.login'))
        else:
            flash(msg, 'danger')

    return render_template('verify_phone.html', phone=user.phone)


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    user_id = session.get('pending_user_id') or session.get('reset_user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Session expired.'}), 400

    last_sent = session.get('otp_sent_timestamp', 0)
    now = datetime.utcnow().timestamp()

    if now - last_sent < 60:
        remaining = int(60 - (now - last_sent))
        return jsonify({'success': False, 'message': f'Please wait {remaining} seconds.'}), 429

    user, new_otp = services.generate_fresh_otp(user_id)
    if user:
        services.send_talksasa_otp(user.phone, new_otp)
        session['otp_sent_timestamp'] = now
        return jsonify({'success': True, 'message': 'A new OTP code has been dispatched.'})

    return jsonify({'success': False, 'message': 'User record not found.'}), 404


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    try:
        user_id = serializer.loads(token, salt='email-verification-salt', max_age=86400)
    except Exception:
        flash('The email verification link is invalid or expired.', 'danger')
        return redirect(url_for('auth.login'))

    success, msg = services.mark_email_verified(user_id)
    flash(msg, 'success' if success else 'warning')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = services.authenticate_user(identifier, password)
        if user:
            if not user.is_phone_verified:
                session['pending_user_id'] = user.id
                flash('Please complete phone verification.', 'warning')
                return redirect(url_for('auth.verify_phone'))

            if not user.is_email_verified:
                flash('Please verify your email address before logging in.', 'warning')
                return redirect(url_for('auth.login'))

            login_user(user)
            flash(f'Welcome back, {user.full_name}.', 'info')
            return redirect(url_for('auth.dashboard'))

        flash('Invalid credentials. Please check your email, phone, or ID and password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        user, otp_code = services.initiate_password_reset(identifier)

        if user:
            session['reset_user_id'] = user.id
            session['otp_sent_timestamp'] = datetime.utcnow().timestamp()
            flash('Password reset OTP sent to your registered phone and email.', 'info')
            return redirect(url_for('auth.reset_password_otp'))
        else:
            flash('If an account exists with those details, a reset OTP has been sent.', 'info')
            return redirect(url_for('auth.forgot_password'))

    return render_template('forgot_password.html')


@auth_bp.route('/reset-password-otp', methods=['GET', 'POST'])
def reset_password_otp():
    user_id = session.get('reset_user_id')
    if not user_id:
        flash('Password reset session expired.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        submitted_otp = request.form.get('otp_code', '').strip()
        new_password = request.form.get('new_password', '')

        success, msg = services.complete_password_reset(user_id, submitted_otp, new_password)
        if success:
            session.pop('reset_user_id', None)
            flash('Password updated successfully. Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(msg, 'danger')

    return render_template('reset_password_otp.html')


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    return redirect(url_for('citizen.citizen_dashboard'))