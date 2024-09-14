from flask_security import auth_required, current_user, hash_password
from flask_restful import Resource, reqparse, fields, marshal_with
from flask import jsonify, request, current_app
from datetime import datetime
import os
import matplotlib.pyplot as plt
import tasks
from cache import cache
import cachingdata
from werkzeug.datastructures import FileStorage
from bson import ObjectId
from itsdangerous import URLSafeTimedSerializer

# Directories for uploads
UPLOAD_BLOG = "../frontend/src/assets/blogs"
UPLOAD_PROFILE = "../frontend/src/assets/profile"

# Request parsers for user data
user_req = reqparse.RequestParser()
user_req.add_argument("email", required=True, help="Email is required")
user_req.add_argument("username", required=True, help="Username is required")
user_req.add_argument("password1", required=True, help="Password is required")

user_fields = {
    "username": fields.String,
    "email": fields.String,
}

class UsersAPI(Resource):
    @cache.memoize(timeout=10)
    @auth_required("token")
    def get(self):
        """
        Get user information along with blogs from followed users.
        """
        user_collection = current_app.mongo.db.users
        follow_collection = current_app.mongo.db.follows
        blog_collection = current_app.mongo.db.blogs
        like_collection = current_app.mongo.db.likes
        dislike_collection = current_app.mongo.db.dislikes
        comment_collection = current_app.mongo.db.comments

        # Fetch current user details
        chk = user_collection.find_one({'_id': ObjectId(current_user.id)})

        # Get followers and following
        following = follow_collection.find({'follower_id': ObjectId(current_user.id)})
        follower = follow_collection.find({'followed_id': ObjectId(current_user.id)})
        flr = []
        flng = []

        for fl in following:
            u = user_collection.find_one({'_id': ObjectId(fl['followed_id'])})
            flng.append({"username": u["username"], "uid": str(u["_id"])})
        for fl in follower:
            u = user_collection.find_one({'_id': ObjectId(fl['follower_id'])})
            flr.append({"username": u["username"], "uid": str(u["_id"])})

        # Get blogs from followed users
        blogs = []
        if following:
            followed_ids = [fl['followed_id'] for fl in following]
            blgs = blog_collection.find({'user_id': {'$in': followed_ids}}).sort("blog_time", -1)

            for blg in blgs:
                l = like_collection.count_documents({'blog_id': blg['_id']})
                dl = dislike_collection.count_documents({'blog_id': blg['_id']})
                cmnt = comment_collection.count_documents({'blog_id': blg['_id']})
                user = user_collection.find_one({'_id': ObjectId(blg['user_id'])})
                blogs.append({
                    "id": str(blg['_id']),
                    "title": blg['blog_title'],
                    "preview": blg['blog_preview'],
                    "content": blg['blog_content'],
                    "date": blg['blog_time'].strftime("%d %b"),
                    "time": blg['blog_time'].strftime("%I:%M %p"),
                    "user": user['username'],
                    "image": blg['blog_img'],
                    "likes": l,
                    "dislikes": dl,
                    "comments": cmnt,
                })

        return {
            "blogs": blogs,
            "email": chk['email'],
            "fullname": chk.get('fullname', ''),
            "about": chk.get('about', ''),
            "follower": flr,
            "following": flng,
        }

    @marshal_with(user_fields)
    def post(self):
        """
        Register a new user.
        """
        args = user_req.parse_args()
        email = args.get("email")
        user_name = args.get("username")
        passw = args.get("password1")

        user_collection = current_app.mongo.db.users

        # Check if user already exists
        check_email = user_collection.find_one({'email': email})
        check_username = user_collection.find_one({'username': user_name})
        if check_email:
            return jsonify({"error": "User already exists! Try with another email."}), 400
        elif check_username:
            return jsonify({"error": "User already exists! Try with another username."}), 400
        else:
            # Create new user with hashed password
            hashed_password = hash_password(passw)
            user_id = user_collection.insert_one({
                'email': email,
                'username': user_name,
                'password': hashed_password,
                'profile_img': 'no-profile-pic.jpeg',
                'fullname': '',
                'about': '',
                'fs_uniquifier': str(ObjectId()),
                'active': True,
                'blogs': [],
                'comments': [],
                'likes': [],
                'dislikes': [],
                'followers': [],
                'followed': []
            }).inserted_id

            return user_collection.find_one({'_id': ObjectId(user_id)}), 201

    @auth_required("token")
    def put(self):
        """
        Update user profile information.
        """
        try:
            fullname = request.form.get("fullname")
            about = request.form.get("about")
            profile_pic = request.files.get("profile_pic")

            user_collection = current_app.mongo.db.users

            imgname = "no-profile-pic.jpeg"
            if profile_pic:
                imgname = f"{current_user.username}{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
                profile_pic.save(os.path.join(UPLOAD_PROFILE, imgname))

            user_collection.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$set': {
                    "fullname": fullname,
                    "about": about,
                    "profile_img": imgname
                }}
            )
            return {"message": "Profile updated successfully"}, 200
        except Exception as e:
            print(e)
            return {"error": "Failed to update profile"}, 500

    @auth_required("token")
    def delete(self):
        """
        Delete the current user's account and related data.
        """
        try:
            user_collection = current_app.mongo.db.users
            blog_collection = current_app.mongo.db.blogs
            comment_collection = current_app.mongo.db.comments
            like_collection = current_app.mongo.db.likes
            dislike_collection = current_app.mongo.db.dislikes
            follow_collection = current_app.mongo.db.follows

            user_id = ObjectId(current_user.id)

            # Delete user-related data
            like_collection.delete_many({'user_id': user_id})
            dislike_collection.delete_many({'user_id': user_id})
            comment_collection.delete_many({'user_id': user_id})
            blog_collection.delete_many({'user_id': user_id})
            follow_collection.delete_many({'follower_id': user_id})
            follow_collection.delete_many({'followed_id': user_id})

            # Delete user account
            user_collection.delete_one({'_id': user_id})

            return {"message": "Account deleted successfully"}, 200
        except Exception as e:
            print(e)
            return {"error": "Failed to delete account"}, 500


# Blog Request Parsers and Fields
blog_req_args = reqparse.RequestParser()
blog_req_args.add_argument("blogTitle", required=True, help="Blog title is required", location="form")
blog_req_args.add_argument("blogContent", required=True, help="Blog content is required", location="form")
blog_req_args.add_argument("blogPrev", required=True, help="Blog preview is required", location="form")
blog_req_args.add_argument("blogImage", required=False, type=FileStorage, location="files")

Blog_fields = {
    "blogTitle": fields.String,
    "blogPrev": fields.String,
    "blogImage": fields.String,
    "blogContent": fields.String,
}

class BlogAPI(Resource):
    @auth_required("token")
    def get(self, id):
        """
        Retrieve a specific blog post along with engagement statistics.
        """
        blog_collection = current_app.mongo.db.blogs
        like_collection = current_app.mongo.db.likes
        dislike_collection = current_app.mongo.db.dislikes
        comment_collection = current_app.mongo.db.comments

        # Fetch the blog
        blg = blog_collection.find_one({'_id': ObjectId(id)})
        if not blg:
            return {"error": "Blog not found"}, 404

        # Get engagement data
        l = like_collection.count_documents({'blog_id': ObjectId(id)})
        dl = dislike_collection.count_documents({'blog_id': ObjectId(id)})
        cmnt = comment_collection.count_documents({'blog_id': ObjectId(id)})

        # Plot engagement graph
        plt.clf()
        plt.bar(["Likes", "Dislikes", "Comments"], [l, dl, cmnt], color="green")
        plt.ylabel("Frequency", fontsize=15, color="r")
        plt.xlabel("Post-Engagement", color="b")
        plt.grid(axis="both", alpha=0.65)
        plt.title("Post-engagement graph", fontsize=15, color="r")
        plt.savefig("../frontend/src/assets/test.png")

        return {
            "title": blg['blog_title'],
            "preview": blg['blog_preview'],
            "content": blg['blog_content'],
        }

    @auth_required("token")
    def post(self):
        """
        Create a new blog post.
        """
        blog_collection = current_app.mongo.db.blogs
        args = blog_req_args.parse_args()
        try:
            blog_title = args["blogTitle"]
            blog_prev = args["blogPrev"]
            blog_content = args["blogContent"]
            blog_img = args["blogImage"]
            imgname = "no-img.jpeg"
            if blog_img:
                imgname = f"{current_user.username}{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
                blog_img.save(os.path.join(UPLOAD_BLOG, imgname))

            blog_id = blog_collection.insert_one({
                'blog_title': blog_title,
                'blog_preview': blog_prev,
                'blog_content': blog_content,
                'blog_img': imgname,
                'user_id': ObjectId(current_user.id),
                'blog_time': datetime.utcnow()
            }).inserted_id

            cache.delete_memoized(cachingdata.get_blogs_by_blogId)

            return {"message": "Blog posted successfully", "blog_id": str(blog_id)}, 201
        except Exception as e:
            print(e)
            return {"error": "Failed to post blog"}, 500

    @auth_required("token")
    def put(self, id):
        """
        Update an existing blog post.
        """
        blog_collection = current_app.mongo.db.blogs
        args = blog_req_args.parse_args()
        try:
            title = args["blogTitle"]
            prev = args["blogPrev"]
            content = args["blogContent"]
            blog_img = args["blogImage"]
            imgname = "no-img.jpeg"
            if blog_img:
                imgname = f"{current_user.username}{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
                blog_img.save(os.path.join(UPLOAD_BLOG, imgname))

            blog_collection.update_one(
                {'_id': ObjectId(id)},
                {'$set': {
                    'blog_title': title,
                    'blog_preview': prev,
                    'blog_content': content,
                    'blog_img': imgname,
                    'blog_time': datetime.utcnow()
                }}
            )

            cache.delete_memoized(cachingdata.get_blogs_by_blogId)
            return {"message": "Blog updated successfully"}, 200
        except Exception as e:
            print(e)
            return {"error": "Failed to update blog"}, 500

    @auth_required("token")
    def delete(self, id):
        """
        Delete a blog post along with related likes, dislikes, and comments.
        """
        blog_collection = current_app.mongo.db.blogs
        like_collection = current_app.mongo.db.likes
        dislike_collection = current_app.mongo.db.dislikes
        comment_collection = current_app.mongo.db.comments

        try:
            blog_id = ObjectId(id)

            # Delete blog-related data
            like_collection.delete_many({'blog_id': blog_id})
            dislike_collection.delete_many({'blog_id': blog_id})
            comment_collection.delete_many({'blog_id': blog_id})
            blog_collection.delete_one({'_id': blog_id})

            cache.delete_memoized(cachingdata.get_blogs_by_blogId)

            return {"message": "Blog deleted successfully"}, 200
        except Exception as e:
            print(e)
            return {"error": "Failed to delete blog"}, 500

# Token Verification Route for the Frontend to call
class VerifyTokenAPI(Resource):
    def get(self):
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header is missing."}), 401
        token = auth_header.split(" ")[1]  # Remove 'Bearer' prefix

        try:
            # Decode the token
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            data = s.loads(token, max_age=current_app.config.get('SECURITY_TOKEN_MAX_AGE', 3600))
            return jsonify({"valid": True}), 200
        except Exception:
            return jsonify({"valid": False, "error": "Invalid or expired token."}), 401

# Add all routes in `app.py`
# Do not add `api.add_resource` in `api.py` to avoid circular imports

# Add all routes
api.add_resource(UsersAPI, "/api/user")
api.add_resource(BlogAPI, "/api/blog", "/api/blog/<string:id>")
api.add_resource(VerifyTokenAPI, "/api/verify-token")
