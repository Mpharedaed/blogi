from flask import current_app
from flask_security import UserMixin, RoleMixin
from datetime import datetime
from flask_security.utils import verify_password
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

# Role model for managing user roles
class Role:
    def __init__(self, mongo):
        self.collection = mongo.db.roles

    def create_role(self, name, description=""):
        """
        Create a new role in the roles collection.
        """
        return self.collection.insert_one({
            'name': name,
            'description': description
        })

    def find_role(self, name):
        """
        Find a role by name.
        """
        return self.collection.find_one({'name': name})

# Users model for managing user accounts
class Users(UserMixin):
    def __init__(self, mongo):
        self.collection = mongo.db.users

    def create_user(self, username, email, password, roles=[]):
        """
        Create a new user in the users collection.
        """
        hashed_password = generate_password_hash(password)
        user = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'roles': roles,
            'active': True,
            'profile_img': "no-profile-pic.jpeg",
            'fullname': '',
            'about': '',
            'fs_uniquifier': str(ObjectId()),
            'followed': [],
            'followers': [],
            'blogs': [],
            'comments': [],
            'likes': [],
            'dislikes': [],
        }
        return self.collection.insert_one(user)

    def find_user(self, username):
        """
        Find a user by their username.
        """
        return self.collection.find_one({'username': username})

    def find_user_by_email(self, email):
        """
        Find a user by their email.
        """
        return self.collection.find_one({'email': email})

    def verify_password(self, password, stored_password):
        """
        Verify the password by comparing the hashed password.
        """
        return check_password_hash(stored_password, password)

    def get_auth_token(self, user_id):
        """
        Generate an authentication token for the user.
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': str(user_id)})

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
        return data['id']

# Blog model for managing blog posts
class Blogs:
    def __init__(self, mongo):
        self.collection = mongo.db.blogs

    def create_blog(self, title, content, author_id, blog_img="no-img.jpeg"):
        """
        Create a new blog post.
        """
        blog = {
            'title': title,
            'content': content,
            'blog_img': blog_img,
            'author_id': author_id,
            'timestamp': datetime.utcnow(),
            'comments': [],
            'likes': [],
            'dislikes': []
        }
        return self.collection.insert_one(blog)

    def find_blog(self, blog_id):
        """
        Find a blog by its ObjectId.
        """
        return self.collection.find_one({'_id': ObjectId(blog_id)})

    def find_blogs_by_user(self, user_id):
        """
        Retrieve all blogs written by a specific user.
        """
        return self.collection.find({'author_id': user_id})

# Comments model for managing blog comments
class Comments:
    def __init__(self, mongo):
        self.collection = mongo.db.comments

    def add_comment(self, user_id, blog_id, comment):
        """
        Add a comment to a blog post.
        """
        comment_data = {
            'user_id': user_id,
            'blog_id': blog_id,
            'comment': comment,
            'timestamp': datetime.utcnow()
        }
        return self.collection.insert_one(comment_data)

    def find_comments_by_blog(self, blog_id):
        """
        Retrieve all comments for a specific blog post.
        """
        return self.collection.find({'blog_id': blog_id})

# Likes model for managing likes on blog posts
class Likes:
    def __init__(self, mongo):
        self.collection = mongo.db.likes

    def like_blog(self, user_id, blog_id):
        """
        Add a like to a blog post.
        """
        return self.collection.insert_one({'user_id': user_id, 'blog_id': blog_id})

    def unlike_blog(self, user_id, blog_id):
        """
        Remove a like from a blog post.
        """
        return self.collection.delete_one({'user_id': user_id, 'blog_id': blog_id})

    def count_likes(self, blog_id):
        """
        Count the number of likes on a blog post.
        """
        return self.collection.count_documents({'blog_id': blog_id})

# Dislikes model for managing dislikes on blog posts
class Dislikes:
    def __init__(self, mongo):
        self.collection = mongo.db.dislikes

    def dislike_blog(self, user_id, blog_id):
        """
        Add a dislike to a blog post.
        """
        return self.collection.insert_one({'user_id': user_id, 'blog_id': blog_id})

    def remove_dislike(self, user_id, blog_id):
        """
        Remove a dislike from a blog post.
        """
        return self.collection.delete_one({'user_id': user_id, 'blog_id': blog_id})

    def count_dislikes(self, blog_id):
        """
        Count the number of dislikes on a blog post.
        """
        return self.collection.count_documents({'blog_id': blog_id})

# Follow model for managing following/followers relationships
class Follow:
    def __init__(self, mongo):
        self.collection = mongo.db.follows

    def follow_user(self, follower_id, followed_id):
        """
        Follow another user.
        """
        return self.collection.insert_one({'follower_id': follower_id, 'followed_id': followed_id})

    def unfollow_user(self, follower_id, followed_id):
        """
        Unfollow a user.
        """
        return self.collection.delete_one({'follower_id': follower_id, 'followed_id': followed_id})

    def find_followers(self, user_id):
        """
        Find all followers of a user.
        """
        return self.collection.find({'followed_id': user_id})

    def find_following(self, user_id):
        """
        Find all users a user is following.
        """
        return self.collection.find({'follower_id': user_id})
