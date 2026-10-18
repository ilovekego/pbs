from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='citizen')

    # Phone & Email Verification Fields
    phone_otp = db.Column(db.String(10), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    is_phone_verified = db.Column(db.Boolean, default=False)
    is_email_verified = db.Column(db.Boolean, default=False)

    # Location Fields
    constituency = db.Column(db.String(50), nullable=True)
    ward = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship('ServiceRequest', backref='citizen', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon_class = db.Column(db.String(50), nullable=False)

    requests = db.relationship('ServiceRequest', backref='category_rel', lazy=True)


class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(30), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'), nullable=False)

    constituency = db.Column(db.String(50), nullable=False)
    ward = db.Column(db.String(50), nullable=False)
    specific_location = db.Column(db.String(150), nullable=False)

    priority = db.Column(db.String(20), default='Medium')
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='Pending')
    admin_notes = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @property
    def is_overdue(self):
        if self.status == 'Pending':
            delta = datetime.utcnow() - self.created_at
            return delta.total_seconds() > (48 * 3600)
        return False