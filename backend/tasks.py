from celery import Celery
from jinja2 import Template
from weasyprint import HTML
import csv
import os
from emailgenr import send_email
from models import Users, Blogs
from bson import ObjectId

# Initialize Celery instance
celery = Celery()

# Paths to static and template directories
wrkng_dir = os.path.abspath(os.path.dirname(__file__))
path_s = os.path.join(wrkng_dir, "static/")
path_t = os.path.join(wrkng_dir, "templates/")

def format_report(template_path, data, user="User"):
    """
    Function to format the report with the provided data.
    """
    with open(template_path) as file:
        temp = Template(file.read())
        return temp.render(blgs=data, user=user)

def pdf_report(data, user):
    """
    Generate a PDF report for blogs.
    """
    msg = format_report(os.path.join(path_t, "monthly_report.html"), data=data, user=user)
    html = HTML(string=msg)
    file_name = f"{user}_BlogLite.pdf"
    print(file_name)
    html.write_pdf(target=file_name)

@celery.task()
def export_blog(blog_list, username, email):
    """
    Celery task to export blog information to CSV and send it via email.
    """
    csv_file_path = os.path.join(path_s, f'blogs_info_{username}.csv')
    
    # Write blogs to CSV
    with open(csv_file_path, 'w', encoding='utf8', newline='') as f:
        file_writer = csv.DictWriter(f, fieldnames=blog_list[0].keys(), restval='')
        file_writer.writeheader()
        file_writer.writerows(blog_list)
    
    # Load email template and send email with CSV
    with open(os.path.join(path_t, 'blogs_csv.html'), 'r') as f:
        template = Template(f.read())
    send_email(
        to_address=email,
        subject='Exported Blog List',
        message=template.render(user=username, data=blog_list),
        content="html",
        attachment=csv_file_path
    )
    return "CSV created."

@celery.task()
def daily_reminder():
    """
    Celery task to send daily reminders to all users about their blogs.
    """
    users_collection = Users().collection
    blogs_collection = Blogs().collection
    
    users = users_collection.find({})
    
    for user in users:
        email = user['email']
        username = user['username']
        
        # Fetch the user's blogs
        blogs = blogs_collection.find({'user_id': ObjectId(user['_id'])})
        blog_list = [{"blog_id": str(blog['_id']), "blog_title": blog['blog_title'], "blog_preview": blog['blog_preview'], "blog_content": blog['blog_content'], "last_modified": str(blog['blog_time'])} for blog in blogs]
        
        # Load daily reminder email template and send the email
        with open(os.path.join(path_t, 'daily_reminder.html'), 'r') as f:
            template = Template(f.read())
        send_email(
            to_address=email,
            subject='Daily Reminder',
            message=template.render(user=username, blgs=blog_list),
            content="html"
        )

@celery.task()
def monthly_reminder():
    """
    Celery task to send monthly blog reports to all users.
    """
    users_collection = Users().collection
    blogs_collection = Blogs().collection
    
    users = users_collection.find({})
    
    for user in users:
        email = user['email']
        username = user['username']
        
        # Fetch the user's blogs
        blogs = blogs_collection.find({'user_id': ObjectId(user['_id'])})
        blog_list = [{"SNo": idx + 1, "blog_title": blog['blog_title'], "blog_preview": blog['blog_preview'], "blog_content": blog['blog_content'], "last_modified": str(blog['blog_time'])} for idx, blog in enumerate(blogs)]
        
        # Generate a PDF report for the user
        pdf_report(blog_list, username)
        
        # Load monthly report email template and send the email with the PDF report attached
        with open(os.path.join(path_t, 'monthly_report.html'), 'r') as f:
            template = Template(f.read())
        send_email(
            to_address=email,
            subject='Monthly Blog Report',
            message=template.render(user=username, blgs=blog_list),
            content="html",
            attachment=os.path.join(wrkng_dir, f"{username}_BlogLite.pdf")
        )
