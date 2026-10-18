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
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='citizen')
    
    phone_otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    is_phone_verified = db.Column(db.Boolean, default=False)
    is_email_verified = db.Column(db.Boolean, default=False)
    
    constituency = db.Column(db.String(80), nullable=True)
    ward = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    service_requests = db.relationship('ServiceRequest', backref='author', lazy=True, cascade="all, delete-orphan")
    business_permits = db.relationship('BusinessPermit', backref='applicant', lazy=True, cascade="all, delete-orphan")
    bursaries = db.relationship('BursaryApplication', backref='applicant', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('TicketComment', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon_class = db.Column(db.String(50), default='fa-solid fa-gears')

    requests = db.relationship('ServiceRequest', backref='category_rel', lazy=True)


class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(30), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    constituency = db.Column(db.String(80), nullable=False)
    ward = db.Column(db.String(80), nullable=False)
    specific_location = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20), default='Medium')
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(20), default='Pending')
    admin_notes = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    thread_comments = db.relationship('TicketComment', backref='ticket', lazy=True, cascade="all, delete-orphan", order_by="TicketComment.created_at.asc()")

    @property
    def is_overdue(self):
        if self.status in ['Pending', 'In Progress']:
            return (datetime.utcnow() - self.created_at) > timedelta(hours=48)
        return False


class TicketComment(db.Model):
    __tablename__ = 'ticket_comments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_admin_reply = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BusinessPermit(db.Model):
    __tablename__ = 'business_permits'

    id = db.Column(db.Integer, primary_key=True)
    permit_number = db.Column(db.String(30), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    business_name = db.Column(db.String(150), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    fee_amount = db.Column(db.Float, default=5000.0)
    status = db.Column(db.String(20), default='Under Review')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BursaryApplication(db.Model):
    __tablename__ = 'bursary_applications'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(30), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_name = db.Column(db.String(120), nullable=False)
    institution = db.Column(db.String(150), nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending Review')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
