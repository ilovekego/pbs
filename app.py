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
import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from models import db, User
import services

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'muranga-county-portal-secret-key-2026')

# Fix Heroku Postgres URL prefix compatibility for SQLAlchemy 2.0+
db_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register Blueprints
from routes.auth import auth_bp
from routes.citizen import citizen_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(citizen_bp)
app.register_blueprint(admin_bp)


# Ensure database tables and seed defaults exist on startup (Gunicorn & Local)
with app.app_context():
    services.seed_database_defaults()


@app.route('/')
def index():
    categories = services.get_all_categories()
    _, analytics, _, _ = services.get_admin_dashboard_metrics()
    return render_template('index.html', categories=categories, total=analytics['total'], resolved=analytics['resolved'])


if __name__ == '__main__':
    app.run(debug=True, port=5000)