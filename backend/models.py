from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from datetime import datetime
from flask_security.utils import verify_password
from flask import current_app
from itsdangerous import URLSafeTimedSerializer

db = SQLAlchemy()

# Association table for roles and users
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Likes(db.Model):
    __tablename__ = 'likes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'), primary_key=True)

    # Relationships
    user = db.relationship('Users', back_populates='likes')
    blog = db.relationship('Blogs', back_populates='likes')

class Dislikes(db.Model):
    __tablename__ = 'dislikes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'), primary_key=True)

    # Relationships
    user = db.relationship('Users', back_populates='dislikes')
    blog = db.relationship('Blogs', back_populates='dislikes')

class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'))
    comment_time = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.String)

    # Relationships
    author = db.relationship('Users', back_populates='comments')
    blog = db.relationship('Blogs', back_populates='comments')

class Blogs(db.Model):
    __tablename__ = 'blogs'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    blog_title = db.Column(db.String(255), nullable=False)
    blog_img = db.Column(db.String(255), default="no-img.jpeg")
    blog_preview = db.Column(db.String)
    blog_content = db.Column(db.Text)
    blog_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    author = db.relationship('Users', back_populates='blogs')
    comments = db.relationship('Comments', back_populates='blog', lazy='dynamic')
    likes = db.relationship('Likes', back_populates='blog', lazy='dynamic')
    dislikes = db.relationship('Dislikes', back_populates='blog', lazy='dynamic')

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=True)
    profile_img = db.Column(db.String(255), default="no-profile-pic.jpeg")
    fullname = db.Column(db.String(255), default='')
    about = db.Column(db.String(255), default='')
    active = db.Column(db.Boolean())
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)

    # Relationships
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    blogs = db.relationship('Blogs', back_populates='author', lazy='dynamic')
    comments = db.relationship('Comments', back_populates='author', lazy='dynamic')
    likes = db.relationship('Likes', back_populates='user', lazy='dynamic')
    dislikes = db.relationship('Dislikes', back_populates='user', lazy='dynamic')
    followed = db.relationship(
        'Follow',
        foreign_keys='Follow.follower_id',
        backref=db.backref('followers', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    followers = db.relationship(
        'Follow',
        foreign_keys='Follow.followed_id',
        backref=db.backref('followed', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Methods
    def verify_password(self, password):
        """
        Verify the user's password.
        """
        return verify_password(password, self.password)

    def get_auth_token(self):
        """
        Generate an authentication token.
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': str(self.id)})

    @staticmethod
    def verify_auth_token(token):
        """
        Verify an authentication token.
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=current_app.config.get('SECURITY_TOKEN_MAX_AGE', 3600))
        except Exception:
            return None
        return Users.query.get(data['id'])

# Ensure relationships are properly set up
Comments.author = db.relationship('Users', back_populates='comments')
Comments.blog = db.relationship('Blogs', back_populates='comments')
Likes.user = db.relationship('Users', back_populates='likes')
Likes.blog = db.relationship('Blogs', back_populates='likes')
Dislikes.user = db.relationship('Users', back_populates='dislikes')
Dislikes.blog = db.relationship('Blogs', back_populates='dislikes')
#jnjnjnjnjnjnjnjnjn