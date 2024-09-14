from models import db, Users, Blogs, Follow, Comments, Likes, Dislikes, Role
from flask_security import (
    SQLAlchemyUserDatastore,
    auth_required,
    current_user,
    hash_password,
    utils,
)
from flask_restful import Resource, reqparse, fields, marshal_with
from flask import jsonify, request
from datetime import datetime
import werkzeug
import os
from os import path
import matplotlib.pyplot as plt
import tasks
from cache import cache
import cachingdata

cd = os.getcwd()

UPLOAD_BLOG = "../frontend/src/assets/blogs"
UPLOAD_PROFILE = "../frontend/src/assets/profile"

# Initialize user datastore
user_datastore = SQLAlchemyUserDatastore(db, Users, Role)

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
        # Fetch current user details
        chk = Users.query.filter_by(id=current_user.id).first()
        
        # Get followers and following
        following = Follow.query.filter_by(follower_id=current_user.id).all()
        follower = Follow.query.filter_by(followed_id=current_user.id).all()
        flr = []
        flng = []
        for fl in following:
            u = Users.query.filter_by(id=fl.followed_id).first()
            flng.append({"username": u.username, "uid": u.id})
        for fl in follower:
            u = Users.query.filter_by(id=fl.follower_id).first()
            flr.append({"username": u.username, "uid": u.id})
        print(following)

        # Get blogs from followed users
        blogs = []
        if following:
            followed_ids = [c.followed_id for c in following]
            blgs = (
                Blogs.query.filter(Blogs.user_id.in_(followed_ids))
                .order_by(Blogs.blog_time.desc())
                .all()
            )
            print(blgs)
            for blg in blgs:
                l = Likes.query.filter_by(blog_id=blg.id).count()
                dl = Dislikes.query.filter_by(blog_id=blg.id).count()
                cmnt = Comments.query.filter_by(blog_id=blg.id).count()
                blogs.append(
                    {
                        "id": blg.id,
                        "title": blg.blog_title,
                        "preview": blg.blog_preview,
                        "content": blg.blog_content,
                        "date": blg.blog_time.strftime("%d %b"),
                        "time": blg.blog_time.strftime("%I:%M %p"),
                        "user": blg.user.username,
                        "image": blg.blog_img,
                        "likes": l,
                        "dislikes": dl,
                        "comments": cmnt,
                    }
                )
        print(blogs)
        return {
            "blogs": blogs,
            "email": current_user.email,
            "fullname": current_user.fullname,
            "about": current_user.about,
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

        # Check if user already exists
        check_email = Users.query.filter_by(email=email).first()
        check_username = Users.query.filter_by(username=user_name).first()
        if check_email:
            print(check_email)
            return (
                jsonify({"error": "User already exists! Try with another email."}),
                400,
            )
        elif check_username:
            print(check_username)
            return (
                jsonify({"error": "User already exists! Try with another username."}),
                400,
            )
        else:
            # Create new user with hashed password
            user_datastore.create_user(
                email=email, username=user_name, password=hash_password(passw)
            )
            db.session.commit()
            data = Users.query.filter_by(email=email).first()
            return data, 201

    @auth_required("token")
    def put(self):
        """
        Update user profile information.
        """
        try:
            fullname = request.form.get("fullname")
            about = request.form.get("about")
            profile_pic = request.files.get("profile_pic")
            imgname = "no-profile-pic.jpeg"
            if profile_pic:
                imgname = f"{current_user.username}{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
                profile_pic.save(path.join(UPLOAD_PROFILE, imgname))
            Users.query.filter_by(id=current_user.id).update(
                {"fullname": fullname, "about": about, "profile_img": imgname}
            )
            db.session.commit()
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
            user_id = current_user.id
            Likes.query.filter_by(user_id=user_id).delete()
            Dislikes.query.filter_by(user_id=user_id).delete()
            Comments.query.filter_by(user_id=user_id).delete()
            Blogs.query.filter_by(user_id=user_id).delete()
            Users.query.filter_by(id=user_id).delete()
            Follow.query.filter_by(followed_id=user_id).delete()
            Follow.query.filter_by(follower_id=user_id).delete()
            db.session.commit()
            return {"message": "Account deleted successfully"}, 200
        except Exception as e:
            print(e)
            return {"error": "Failed to delete account"}, 500

# Request parsers for blog data
blog_req_args = reqparse.RequestParser()
blog_req_args.add_argument(
    "blogTitle",
    required=True,
    help="Blog title is required",
    location="form",
)
blog_req_args.add_argument(
    "blogContent",
    required=True,
    help="Blog content is required",
    location="form",
)
blog_req_args.add_argument(
    "blogPrev",
    required=True,
    help="Blog preview is required",
    location="form",
)
blog_req_args.add_argument(
    "blogImage",
    required=False,
    type=werkzeug.datastructures.FileStorage,
    location="files",
)

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
        blg = cachingdata.get_blogs_by_blogId(blog_id=id)
        if not blg:
            return {"error": "Blog not found"}, 404

        # Get engagement data
        l = Likes.query.filter_by(blog_id=id).count()
        dl = Dislikes.query.filter_by(blog_id=id).count()
        cmnt = Comments.query.filter_by(blog_id=id).count()
        x = ["Likes", "Dislikes", "Comments"]
        y = [l, dl, cmnt]

        # Plot engagement graph
        plt.clf()
        plt.bar(x, y, color="green")
        plt.ylabel("Frequency", fontsize=15, color="r")
        plt.xlabel("Post-Engagement", color="b")
        plt.grid(axis="both", alpha=0.65)
        plt.title("Post-engagement graph", fontsize=15, color="r")
        plt.yticks(range(int(max(y)) + 4))
        plt.legend(["count"])
        dic = os.getcwd()
        print(dic)
        plt.savefig("../frontend/src/assets/test.png")

        return {
            "title": blg.blog_title,
            "preview": blg.blog_preview,
            "content": blg.blog_content,
        }

    @auth_required("token")
    def post(self):
        """
        Create a new blog post.
        """
        try:
            blog_title = request.form.get("blogTitle")
            blog_prev = request.form.get("blogPrev")
            blog_content = request.form.get("blogContent")
            blog_img = request.files.get("blogImage")
            imgname = "no-img.jpeg"
            if blog_img:
                imgname = f"{current_user.username}{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
                blog_img.save(path.join(UPLOAD_BLOG, imgname))
            new_blog = Blogs(
                blog_title=blog_title,
                blog_preview=blog_prev,
                blog_content=blog_content,
                blog_img=imgname,
                user_id=current_user.id,
                blog_time=datetime.now(),
            )
            db.session.add(new_blog)
            db.session.commit()
            cache.delete_memoized(cachingdata.get_blogs_by_blogId)
            return {"message": "Blog posted successfully"}, 201
        except Exception as e:
            print(e)
            return {"error": "Failed to post blog"}, 500

    @auth_required("token")
    def put(self, id):
        """
        Update an existing blog post.
        """
        try:
            title = request.form.get("blogTitle")
            prev = request.form.get("blogPrev")
            content = request.form.get("blogContent")
            blog_img = request.files.get("blogImage")
            imgname = "no-img.jpeg"
            if blog_img:
                imgname = f"{current_user.username}{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
                blog_img.save(path.join(UPLOAD_BLOG, imgname))
            update_data = {
                "blog_title": title,
                "blog_preview": prev,
                "blog_content": content,
                "blog_img": imgname,
                "blog_time": datetime.now(),
            }
            Blogs.query.filter_by(id=id).update(update_data)
            db.session.commit()
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
        try:
            Likes.query.filter_by(blog_id=id).delete()
            Dislikes.query.filter_by(blog_id=id).delete()
            Comments.query.filter_by(blog_id=id).delete()
            Blogs.query.filter_by(id=id).delete()
            db.session.commit()
            cache.delete_memoized(cachingdata.get_blogs_by_blogId)
            return {"message": "Blog deleted successfully"}, 200
        except Exception as e:
            print(e)
            return {"error": "Failed to delete blog"}, 500

class ProfileAPI(Resource):
    def get(self, username):
        """
        Get user profile information along with their blogs.
        """
        print(username)
        chk = cachingdata.get_user_by_username(username)
        if not chk:
            return {"error": "User not found"}, 404
        print(chk)
        following = Follow.query.filter_by(follower_id=chk.id).count()
        followers = Follow.query.filter_by(followed_id=chk.id).count()
        blgs = (
            Blogs.query.filter_by(user_id=chk.id)
            .order_by(Blogs.blog_time.desc())
            .all()
        )
        blogs = []
        for blg in blgs:
            l = Likes.query.filter_by(blog_id=blg.id).count()
            dl = Dislikes.query.filter_by(blog_id=blg.id).count()
            cmnt = Comments.query.filter_by(blog_id=blg.id).count()
            blogs.append(
                {
                    "id": blg.id,
                    "title": blg.blog_title,
                    "preview": blg.blog_preview,
                    "content": blg.blog_content,
                    "date": blg.blog_time.strftime("%d %b"),
                    "time": blg.blog_time.strftime("%I:%M %p"),
                    "user": blg.user.username,
                    "image": blg.blog_img,
                    "likes": l,
                    "dislikes": dl,
                    "comments": cmnt,
                }
            )
        totalpost = Blogs.query.filter_by(user_id=chk.id).count()
        return {
            "username": chk.username,
            "totalpost": totalpost,
            "followers": followers,
            "following": following,
            "fullname": chk.fullname,
            "about": chk.about,
            "profile_pic": chk.profile_img,
            "blogs": blogs,
        }

search_req = reqparse.RequestParser()
search_req.add_argument("username", help="Username")

class SearchAPI(Resource):
    def post(self):
        """
        Search for users by username.
        """
        args = search_req.parse_args()
        username = args.get("username")
        data = []
        if username:
            q = f"%{username}%"
            users = Users.query.filter(Users.username.like(q)).all()
            print(users)
            for user in users:
                data.append({"username": user.username})
        print(data)
        return {"users": data}

follow_req = reqparse.RequestParser()
follow_req.add_argument("follower", help="Follower username")
follow_req.add_argument("following", help="User to follow")

class FollowAPI(Resource):
    @auth_required("token")
    def post(self):
        """
        Follow a user.
        """
        args = follow_req.parse_args()
        follower_username = args.get("follower")
        following_username = args.get("following")
        flwr = Users.query.filter_by(username=follower_username).first()
        fl = Users.query.filter_by(username=following_username).first()
        print(follower_username, following_username)
        if not flwr or not fl:
            return {"error": "User not found"}, 404
        fc = Follow.query.filter_by(followed_id=fl.id, follower_id=flwr.id).first()
        if fc:
            return {"response": "You already follow this user"}, 400
        else:
            f = Follow(followed_id=fl.id, follower_id=flwr.id)
            db.session.add(f)
            db.session.commit()
            return {"response": "Followed successfully"}, 200

unfollow_req = reqparse.RequestParser()
unfollow_req.add_argument("follower", help="Follower username")
unfollow_req.add_argument("unfollowing", help="User to unfollow")

class UnfollowAPI(Resource):
    @auth_required("token")
    def post(self):
        """
        Unfollow a user.
        """
        args = unfollow_req.parse_args()
        follower_username = args.get("follower")
        unfollowing_username = args.get("unfollowing")
        flwr = Users.query.filter_by(username=follower_username).first()
        unfl = Users.query.filter_by(username=unfollowing_username).first()
        print(follower_username, unfollowing_username)
        if not flwr or not unfl:
            return {"error": "User not found"}, 404
        fc = Follow.query.filter_by(followed_id=unfl.id, follower_id=flwr.id).first()
        if fc:
            Follow.query.filter_by(followed_id=unfl.id, follower_id=flwr.id).delete()
            db.session.commit()
            return {"response": "Unfollowed successfully"}, 200
        else:
            return {"response": "You are not following this user"}, 400

luk_req = reqparse.RequestParser()
luk_req.add_argument("like", help="True for like, False for dislike")
luk_req.add_argument("blog", help="Blog ID")
luk_req.add_argument("username", help="Username")

class LikeUnlikeAPI(Resource):
    @auth_required("token")
    def post(self):
        """
        Like or dislike a blog post.
        """
        args = luk_req.parse_args()
        like = args.get("like")
        blog_id = args.get("blog")
        print(like, blog_id)
        if like == "True":
            l = Likes.query.filter_by(blog_id=blog_id, user_id=current_user.id).first()
            dl = Dislikes.query.filter_by(blog_id=blog_id, user_id=current_user.id).first()
            if l:
                return {"like": "Already liked"}, 200
            if dl:
                Dislikes.query.filter_by(blog_id=blog_id, user_id=current_user.id).delete()
            new_like = Likes(blog_id=blog_id, user_id=current_user.id)
            db.session.add(new_like)
            db.session.commit()
            return {"like": "Liked successfully"}, 200
        elif like == "False":
            dl = Dislikes.query.filter_by(blog_id=blog_id, user_id=current_user.id).first()
            l = Likes.query.filter_by(blog_id=blog_id, user_id=current_user.id).first()
            if dl:
                return {"dislike": "Already disliked"}, 200
            if l:
                Likes.query.filter_by(blog_id=blog_id, user_id=current_user.id).delete()
            new_dislike = Dislikes(blog_id=blog_id, user_id=current_user.id)
            db.session.add(new_dislike)
            db.session.commit()
            return {"dislike": "Disliked successfully"}, 200
        else:
            return {"error": "Invalid like parameter"}, 400

cmnt_req = reqparse.RequestParser()
cmnt_req.add_argument("cmnt", help="Comment text")
cmnt_req.add_argument("user", help="Username")

class CommentAPI(Resource):
    @cache.memoize(timeout=10)
    @auth_required("token")
    def get(self, id):
        """
        Get comments for a blog post.
        """
        comments = []
        cmnts = (
            Comments.query.filter_by(blog_id=id)
            .order_by(Comments.comment_time.desc())
            .all()
        )
        for cmnt in cmnts:
            usr = Users.query.filter_by(id=cmnt.user_id).first()
            comments.append(
                {
                    "comment": cmnt.comment,
                    "username": usr.username,
                    "id": cmnt.id,
                    "date": cmnt.comment_time.strftime("%d %b"),
                    "time": cmnt.comment_time.strftime("%I:%M %p"),
                }
            )
        return {"comments": comments}

    @auth_required("token")
    def post(self, id):
        """
        Post a comment on a blog post.
        """
        args = cmnt_req.parse_args()
        cmnt_text = args.get("cmnt")
        if not cmnt_text:
            return {"error": "Comment text is required"}, 400
        new_comment = Comments(
            blog_id=id,
            user_id=current_user.id,
            comment=cmnt_text,
            comment_time=datetime.now(),
        )
        db.session.add(new_comment)
        db.session.commit()
        return {"cmnt": "Comment added successfully"}, 201

    @auth_required("token")
    def delete(self, id):
        """
        Delete a comment.
        """
        comment = Comments.query.filter_by(id=id, user_id=current_user.id).first()
        if not comment:
            return {"error": "Comment not found or unauthorized"}, 404
        db.session.delete(comment)
        db.session.commit()
        return {"message": "Comment deleted successfully"}, 200

class ExportblogAPI(Resource):
    @auth_required("token")
    def get(self):
        """
        Export all blogs of the current user.
        """
        blgs = Blogs.query.filter_by(user_id=current_user.id).all()
        if blgs:
            cnt = 0
            bl = []
            for blg in blgs:
                cnt += 1
                bl.append(
                    {
                        "SNo": cnt,
                        "Blog_title": blg.blog_title,
                        "Blog_preview": blg.blog_preview,
                        "Blog_content": blg.blog_content,
                        "Last_modified": str(blg.blog_time),
                    }
                )
            # Trigger Celery task to export blogs
            tasks.export_blog.delay(bl, current_user.username, current_user.email)
            return jsonify("Blogs exported successfully"), 200
        else:
            return jsonify("No blogs to export"), 400
