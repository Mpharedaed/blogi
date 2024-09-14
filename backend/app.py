import os
from os import path
from flask import Flask, send_from_directory, request, jsonify
from flask_pymongo import PyMongo
from flask_security import Security
from flask_restful import Api, Resource
from flask_login import LoginManager, login_user
from flask_cors import CORS
from celery import Celery
from celery.schedules import crontab
from werkzeug.security import generate_password_hash, check_password_hash

# Import API resources
from api import (
    UsersAPI,
    BlogAPI,
    ProfileAPI,
    SearchAPI,
    FollowAPI,
    UnfollowAPI,
    LikeUnlikeAPI,
    CommentAPI,
    ExportblogAPI,
)

# Import cache and tasks
from cache import cache
from tasks import daily_reminder, monthly_reminder

# Flask app setup
app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")

# Initialize the LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# CORS Setup
CORS(app, origins=[
    "https://blogi-1-frontend.onrender.com",
    "https://dawlatemad.com",
    "https://www.dawlatemad.com"
])

# MongoDB configuration
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb+srv://mohamedredaed:<red88luck>@cluster.mongodb.net/?retryWrites=true&w=majority")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["SECURITY_PASSWORD_SALT"] = os.environ.get("SECURITY_PASSWORD_SALT")
app.config["SECURITY_USERNAME_ENABLE"] = True
app.config["WTF_CSRF_ENABLED"] = False
app.config["SECURITY_TOKEN_AUTHENTICATION_HEADER"] = "Authentication-Token"
app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"

# Redis, Celery, Cache setup
app.config["CELERY_BROKER_URL"] = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
app.config["CELERY_RESULT_BACKEND"] = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
app.config["CELERY_ENABLE_UTC"] = False
app.config["CELERY_TIMEZONE"] = "Asia/Kolkata"
app.config["CACHE_REDIS_URL"] = os.environ.get("CACHE_REDIS_URL", "redis://localhost:6379/3")
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 100

# Initialize Flask extensions
api = Api(app)
cache.init_app(app)

# Initialize MongoDB with PyMongo
mongo = PyMongo(app)

# Initialize Celery
celery_app = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery_app.conf.update(app.config)

# Custom user datastore using PyMongo
class UserDatastore:
    def __init__(self, mongo):
        self.users = mongo.db.users
        self.roles = mongo.db.roles

    def create_user(self, **kwargs):
        return self.users.insert_one(kwargs)

    def find_user(self, **kwargs):
        return self.users.find_one(kwargs)

    def find_role(self, **kwargs):
        return self.roles.find_one(kwargs)

# Initialize user datastore with PyMongo
user_datastore = UserDatastore(mongo)
security = Security(app, user_datastore)

# Define the LoginAPI resource
class LoginAPI(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        # Query MongoDB to find the user by username
        user = mongo.db.users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):  # Use hashed passwords
            login_user(user)  # This function remains the same from Flask-Login
            token = user.get('auth_token', 'some_generated_token')  # Generate or retrieve token
            return {"message": "Login successful", "token": token}, 200
        else:
            return {"message": "Invalid username or password"}, 401

# API resource setup
api.add_resource(UsersAPI, "/api/user")
api.add_resource(LoginAPI, "/api/login")
api.add_resource(BlogAPI, "/api/blog", "/api/blog/<int:id>")
api.add_resource(ProfileAPI, "/api/profile/<string:username>")
api.add_resource(SearchAPI, "/api/search")
api.add_resource(FollowAPI, "/api/follow")
api.add_resource(UnfollowAPI, "/api/unfollow")
api.add_resource(LikeUnlikeAPI, "/api/likeunlike")
api.add_resource(CommentAPI, "/api/comment/<int:id>")
api.add_resource(ExportblogAPI, "/api/exportblogs")

# Serve Vue.js frontend
@app.route("/")
@app.route("/<path:filename>")
def serve_frontend(filename=""):
    if filename != "" and os.path.exists(f"../frontend/dist/{filename}"):
        return send_from_directory("../frontend/dist", filename) 
    else:
        return send_from_directory("../frontend/dist", "index.html")

# Celery periodic tasks
@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Daily reminder
    sender.add_periodic_task(
        crontab(hour=23, minute=14, day_of_week="*"),
        daily_reminder.s(),
    )
    # Monthly report
    sender.add_periodic_task(
        crontab(hour=23, minute=14, day_of_month="22"),
        monthly_reminder.s(),
    )

celery_app.conf.timezone = "Asia/Kolkata"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
