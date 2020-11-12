from flask import Flask, render_template, redirect, request, url_for, flash, session, logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime
from forms import ContactForm

app = Flask(__name__)
app.secret_key = "ozyalhan-web-dev-project"  # required for flashing

# Setup for the ORM SQAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/ozgur/Desktop/ozyalhan/ozy_blog.db'
db = SQLAlchemy(app)


# User login decorator, we will control pages with it.
# use @login_function before unwanted enterance for the pages without loggin
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:  # user logged in
            return f(*args, **kwargs)
        else:
            flash("Please login for see this page.", "warning")
            return redirect(url_for("login"))
    return decorated_function


class Users(db.Model):
    """ create the initial users table"""
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(40), nullable=False)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)


class RegisterForm(Form):
    """User Registiration is making here"""

    fullname = StringField("Fullname", validators=[validators.length(4, 40,)])
    username = StringField("Username", validators=[validators.length(4, 40)])
    email = StringField("Email", validators=[validators.Email(
        message="Please write valid email address."), validators.length(16, 40)])
    password = PasswordField("Password", validators=[validators.length(6, 40, message="Password should contains between 6-40 characters."), validators.DataRequired(
        message="Please set a password."), validators.equal_to(fieldname="confirm", message='Passwords must match')])
    confirm = PasswordField("Verify Password")


@app.route("/register", methods=["POST", "GET"])
def register():
    """Register Operations"""

    form = RegisterForm(request.form)

    # Register Process
    if request.method == "POST" and form.validate():

        fullname = form.username.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(
            form.password.data)  # Security Modified

        user = Users(fullname=fullname, username=username,
                     email=email, password=password)

        # Control that email or username used before
        cu = control_username_exist(username)
        cm = control_email_exist(email)
        if (cm and cu):
            flash(
                "Your email and username used before. Please try another ones.", 'warning')
            return redirect(url_for("register"))
        elif (cu):
            flash(
                "Your username used before. Please try another one.", 'warning')
            return redirect(url_for("register"))
        elif (cm):
            flash(
                "Your email used before. Please try another one.", 'warning')
            return redirect(url_for("register"))
        else:
            try:
                db.session.add(user)
                db.session.commit()
            except exc.SQLAlchemyError as e:
                flash(
                    "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
                return redirect(url_for("register"))
            else:
                flash("You registred succesfuly", "success")
                return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)


def control_username_exist(username):
    """Controls the email is signed before or not. Returns boolean. True is desired one"""

    checked_username = Users.query.filter_by(username=username)
    if username == checked_username:
        return True
    else:
        return False


def control_email_exist(email):
    """Controls the email is signed before or not. Returns boolean. True is desired one"""

    checked_email = Users.query.filter_by(email=email).first()
    if checked_email is None:
        return False
    else:
        return True


def return_password_hashed(email):
    """Controls the password in login page for match. Returns boolean. True is desired one"""

    # check that email is wrong, if wrong it will return empty string, if it is true it will return hashed_password value
    user_data = Users.query.filter_by(email=email).first()
    if user_data is None:
        return ""
    else:
        hashed_password = user_data.password
        return hashed_password


@ app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        useremail = request.form["useremail"]
        ce = control_email_exist(useremail)  # true or false

        # if useremail is correct, then check the password.
        if(ce):
            userpassword = request.form["userpassword"]
            # in any case of situation userpassword musnt be empty so this control is required.
            if userpassword != "":
                checked_userpassword = return_password_hashed(useremail)
                if sha256_crypt.verify(userpassword, checked_userpassword):
                    flash("Logined succesfully.", "success")

                    # Session Starts Here
                    session["logged_in"] = True

                    # Reach username from db
                    user_info = Users.query.filter_by(email=useremail).first()
                    username = user_info.username

                    session["username"] = username

                    return redirect(url_for("index"))
                else:
                    flash("Your password is incorrect.", "danger")
                    return redirect(url_for("login"))
        else:
            flash("There is no user with this email.", "danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html")


@ app.route("/logout")
def logout():
    session.clear()
    flash("You logout successfuly.", "success")
    return redirect(url_for("index"))


class Blogs(db.Model):
    """ create the initial blog table"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False)
    author = db.Column(db.String(40), nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_date = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)


# Blog Form
class BlogForm(Form):
    title = StringField("Blog Title", validators=[
                        validators.length(max=40, message="Maksimum 40 Character"), validators.data_required()])
    content = TextAreaField("Content", validators=[
                            validators.data_required(message="Write something please😃")])


# Add Blog Post
@app.route("/addblog", methods=["POST", "GET"])
@login_required
def addblog():
    form = BlogForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        blog_post = Blogs(
            title=title, author=session["username"], content=content)

        try:
            db.session.add(blog_post)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            flash(
                "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
            return redirect(url_for("dashboard"))
        else:
            flash("Blog Post has been added successfuly.", "success")
            return redirect(url_for("dashboard"))
    else:
        return render_template("addblog.html", form=form)


@ app.route("/dashboard")
@login_required
def dashboard(): < br > <br > <br > <br > <br >


<div class = "container" >
   <div class = "jumbotron text-center" >
        <h3 class = "p-2 mb-2 bg-info text-white" > <strong > Welcome < /strong > !</h3 >
        <hr >
        <h4 class = "text-dark" > Ozgur Yasar Alhan is an Electronics and Communication Engineer. < /h4 >
        <br >
        <h5 class = "text-dark" > He loves coding, cleaning, fixing home stuffs, making keep alive old computers &
        electronics,
           and creating automated systems. < /h5 >
        <br >
        <h5 class = "text-primary" > You can find about him < strong > everything < /strong > in here.😊< /h5 >
    </div >
</div >
</div >



{ % endblock  % }

# get db values ... it can be empty string if not author only will be ours

# blog_posts = Blogs.query.all()

# blog_posts = Blogs.query.filter_by(author=session["username"]).first()

blog_posts = Blogs.query.filter_by(author=session["username"]).all()
 diary_posts = Diaries.query.filter_by(author=session["username"]).all()
  project_posts = Projects.query.filter_by(author=session["username"]).all()

   # blog_posts = Blogs.querry.all()

   if blog_posts != "" or diary_posts != "" or project_posts != "":

        # For Debugging only
        # flash("{}".format(blog_posts), "success")
        # return render_template("index.html")

        return render_template("dashboard.html", blogs=blog_posts, diaries=diary_posts, projects=project_posts)

    return render_template("dashboard.html")


# BUG-1
"""
Edit FUnction with Post method doesnt work well, after the post get data from form but sysyem doesnt care about validators.
I checked all attempts to find solution but no good solution,
For start it seems okay but after,  I need solve it.

"""


@app.route("/edit-blog/<string:id>", methods=["POST", "GET"])
@login_required
def edit_blog(id):
    form = BlogForm(request.form)
    if request.method == "GET":
        blog_edit = Blogs.query.filter_by(id=id).first()

        if blog_edit == "":
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok", "danger")
            return redirect(url_for("index"))
        else:
            form = BlogForm(request.form)
            form.title.data = blog_edit.title
            form.content.data = blog_edit.content

            return render_template("editblog.html", form=form)

    form = BlogForm(request.form)
    if request.method == "POST" and form.validate():

        # form = BlogForm(request.form)  # ilk olarak fom bilgileri alındı.
        # form = BlogForm(request.form)
        new_title = form.title.data
        new_content = form.content.data  # veriler değiştirildi.

        # get old  db info
        blog_edit = Blogs.query.filter_by(id=id).first()

        # update
        blog_edit.title = new_title
        blog_edit.content = new_content

        # blog_edit = Blogs.query.filter_by(id=id).update(dict(title=new_title, content=new_content))

        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            flash(
                "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
            return redirect(url_for("dashboard"))
        else:
            # flash("{}".format(blog_edit.title), "success")
            flash("Your Blog Post has been updated successfuly.", "success")
            return redirect(url_for("dashboard"))

    flash("Title size can be maximum 40 character and content should not be empty.", "warning")
    return redirect(url_for("dashboard"))


@app.route("/delete-blog/<string:id>")
@login_required
def delete_blog(id):
    """Delete Blog PostOperation"""

    blog_delete = Blogs.query.filter_by(
        id=id, author=session["username"]).first()

    try:
        db.session.delete(blog_delete)
        db.session.commit()
    except exc.SQLAlchemyError as e:
        flash(
            "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
        return redirect(url_for("dashboard"))
    else:
        # flash("{}".format(blog_edit.title), "success")
        flash("Your Blog Post been deleted successfuly.", "success")
        return redirect(url_for("dashboard"))


@ app.route("/blogs")
def blogs():
    """Shows all blogs with title and author username to public"""

    blogs = Blogs.query.all()

    if blogs != "":  # veritabanında makale var
        # tek makale için fect one tümü için fetch all liste içinde sözlükler

        return render_template("blogs.html", blogs=blogs)

    else:
        return render_template("blogs.html")

    return render_template("blogs.html")


@app.route("/blog/<string:id>")
def blog(id):
    """Blog Detail Function"""

    blog = Blogs.query.filter_by(id=id).first()

    if blog != "":
        return render_template("blog.html", blog=blog)
    else:
        return render_template("blog.html")


@ app.route("/")
def index():
    """Main Page/Index Page Function"""
    return render_template("index.html")


@ app.route("/about")
def about():
    return render_template("/about.html")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()

    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('contact.html', form=form)
        else:
            #         msg = Message(form.subject.data, sender='contact@example.com',
            #                       recipients=['your_email@example.com'])
            #         msg.body = """
            #   From: %s <%s>
            #   %s
            #   """ % (form.name.data, form.email.data, form.message.data)
            #         mail.send(msg)

            return render_template('contact.html', success=True)

    elif request.method == 'GET':
        return render_template('contact.html', form=form)


# Search Blog
@app.route("/search-blog", methods=["GET", "POST"])
def search_blog():
    # /search olarak get ile sayfaya ulaşılmaya çalışıldığında index e yönlenir.
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        search = "%{}%".format(keyword)

        blogs = Blogs.query.filter(Blogs.title.like(search)).all()

        if blogs == "":
            flash("No result", "warning")
            return redirect(url_for("blogs"))
        else:
            return render_template("blogs.html", blogs=blogs)


########
class Diaries(db.Model):
    """ create the initial diary table"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False)
    author = db.Column(db.String(40), nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_date = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)


# Diary Form
class DiaryForm(Form):
    title = StringField("Diary Title", validators=[
                        validators.length(max=40, message="Maksimum 40 Character"), validators.data_required()])
    content = TextAreaField("Content", validators=[
                            validators.data_required(message="Write something please😃")])


# Add Diary Post
@app.route("/adddiary", methods=["POST", "GET"])
@login_required
def adddiary():
    form = DiaryForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        diary_post = Diaries(
            title=title, author=session["username"], content=content)

        try:
            db.session.add(diary_post)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            flash(
                "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
            return redirect(url_for("dashboard"))
        else:
            flash("Diary Post has been added successfuly.", "success")
            return redirect(url_for("dashboard"))
    else:
        return render_template("adddiary.html", form=form)


@app.route("/edit-diary/<string:id>", methods=["POST", "GET"])
@login_required
def edit_diary(id):
    form = DiaryForm(request.form)
    if request.method == "GET":
        diary_edit = Diaries.query.filter_by(id=id).first()

        if diary_edit == "":
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok", "danger")
            return redirect(url_for("index"))
        else:
            form = DiaryForm(request.form)
            form.title.data = diary_edit.title
            form.content.data = diary_edit.content

            return render_template("editdiary.html", form=form)

    form = DiaryForm(request.form)
    if request.method == "POST" and form.validate():

        # form = DiaryForm(request.form)  # ilk olarak fom bilgileri alındı.
        # form = DiaryForm(request.form)
        new_title = form.title.data
        new_content = form.content.data  # veriler değiştirildi.

        # get old  db info
        diary_edit = Diaries.query.filter_by(id=id).first()

        # update
        diary_edit.title = new_title
        diary_edit.content = new_content

        # diary_edit = Diaries.query.filter_by(id=id).update(dict(title=new_title, content=new_content))

        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            flash(
                "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
            return redirect(url_for("dashboard"))
        else:
            # flash("{}".format(diary_edit.title), "success")
            flash("Your Diary Post has been updated successfuly.", "success")
            return redirect(url_for("dashboard"))

    flash("Title size can be maximum 40 character and content should not be empty.", "warning")
    return redirect(url_for("dashboard"))


@app.route("/delete-diary/<string:id>")
@login_required
def delete_diary(id):
    """Delete Diary PostOperation"""

    diary_delete = Diaries.query.filter_by(
        id=id, author=session["username"]).first()

    try:
        db.session.delete(diary_delete)
        db.session.commit()
    except exc.SQLAlchemyError as e:
        flash(
            "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
        return redirect(url_for("dashboard"))
    else:
        # flash("{}".format(diary_edit.title), "success")
        flash("Your Diary Post been deleted successfuly.", "success")
        return redirect(url_for("dashboard"))


@ app.route("/diaries")
def diaries():
    """Shows all diaries with title and author username to public"""

    diaries = Diaries.query.all()

    if diaries != "":  # veritabanında makale var
        # tek makale için fect one tümü için fetch all liste içinde sözlükler

        return render_template("diaries.html", diaries=diaries)

    else:
        return render_template("diaries.html")

    return render_template("diaries.html")


@app.route("/diary/<string:id>")
def diary(id):
    """Diary Detail Function"""

    diary = Diaries.query.filter_by(id=id).first()

    if diary != "":
        return render_template("diary.html", diary=diary)
    else:
        return render_template("diary.html")

# Search Diary


@app.route("/search-diary", methods=["GET", "POST"])
def search_diary():
    # /search olarak get ile sayfaya ulaşılmaya çalışıldığında index e yönlenir.
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        search = "%{}%".format(keyword)

        diaries = Diaries.query.filter(Diaries.title.like(search)).all()

        if diaries == "":
            flash("No result", "warning")
            return redirect(url_for("diaries"))
        else:
            return render_template("diaries.html", diaries=diaries)

########


class Projects(db.Model):
    """ create the initial project table"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False)
    author = db.Column(db.String(40), nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_date = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)


# Project Form
class ProjectForm(Form):
    title = StringField("Project Title", validators=[
                        validators.length(max=40, message="Maksimum 40 Character"), validators.data_required()])
    content = TextAreaField("Content", validators=[
                            validators.data_required(message="Write something please😃")])


# Add Project Post
@app.route("/addproject", methods=["POST", "GET"])
@login_required
def addproject():
    form = ProjectForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        project_post = Projects(
            title=title, author=session["username"], content=content)

        try:
            db.session.add(project_post)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            flash(
                "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
            return redirect(url_for("dashboard"))
        else:
            flash("Project Post has been added successfuly.", "success")
            return redirect(url_for("dashboard"))
    else:
        return render_template("addproject.html", form=form)


@app.route("/edit-project/<string:id>", methods=["POST", "GET"])
@login_required
def edit_project(id):
    form = ProjectForm(request.form)
    if request.method == "GET":
        project_edit = Projects.query.filter_by(id=id).first()

        if project_edit == "":
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok", "danger")
            return redirect(url_for("index"))
        else:
            form = ProjectForm(request.form)
            form.title.data = project_edit.title
            form.content.data = project_edit.content

            return render_template("editproject.html", form=form)

    form = ProjectForm(request.form)
    if request.method == "POST" and form.validate():

        # form = ProjectForm(request.form)  # ilk olarak fom bilgileri alındı.
        # form = ProjectForm(request.form)
        new_title = form.title.data
        new_content = form.content.data  # veriler değiştirildi.

        # get old  db info
        project_edit = Projects.query.filter_by(id=id).first()

        # update
        project_edit.title = new_title
        project_edit.content = new_content

        # project_edit = Projects.query.filter_by(id=id).update(dict(title=new_title, content=new_content))

        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            flash(
                "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
            return redirect(url_for("dashboard"))
        else:
            # flash("{}".format(project_edit.title), "success")
            flash("Your Project Post has been updated successfuly.", "success")
            return redirect(url_for("dashboard"))

    flash("Title size can be maximum 40 character and content should not be empty.", "warning")
    return redirect(url_for("dashboard"))


@app.route("/delete-project/<string:id>")
@login_required
def delete_project(id):
    """Delete Project PostOperation"""

    project_delete = Projects.query.filter_by(
        id=id, author=session["username"]).first()

    try:
        db.session.delete(project_delete)
        db.session.commit()
    except exc.SQLAlchemyError as e:
        flash(
            "Please send error message bellow to ozguryasaralhan@gmail.com\n{}".format(e), "warning")
        return redirect(url_for("dashboard"))
    else:
        # flash("{}".format(project_edit.title), "success")
        flash("Your Project Post been deleted successfuly.", "success")
        return redirect(url_for("dashboard"))


@ app.route("/projects")
def projects():
    """Shows all projects with title and author username to public"""

    projects = Projects.query.all()

    if projects != "":  # veritabanında makale var
        # tek makale için fect one tümü için fetch all liste içinde sözlükler

        return render_template("projects.html", projects=projects)

    else:
        return render_template("projects.html")

    return render_template("projects.html")


@app.route("/project/<string:id>")
def project(id):
    """Project Detail Function"""

    project = Projects.query.filter_by(id=id).first()

    if project != "":
        return render_template("project.html", project=project)
    else:
        return render_template("project.html")

# Search Project


@app.route("/search-project", methods=["GET", "POST"])
def search_project():
    # /search olarak get ile sayfaya ulaşılmaya çalışıldığında index e yönlenir.
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        search = "%{}%".format(keyword)

        projects = Projects.query.filter(Projects.title.like(search)).all()

        if projects == "":
            flash("No result", "warning")
            return redirect(url_for("projects"))
        else:
            return render_template("projects.html", projects=projects)

########


if __name__ == "__main__":
    # db.drop_all()  # sometimes I need destroy all DATA
    db.create_all()  # firstly create db,other times doesnt create again.
    app.run(debug=True)

    # class Contact_info(db.Model):
    #     """ create the initial contact_info table"""
    #     pass

    # class Projects(db.Model):
    #     """ create the initial projects table"""
    #     pass

    # class Articles(db.Model):
    #     """ create the initial articles table"""
    #     pass

    # class Diaries(db.Model):
    #     """ create the initial diaries table"""
    #     pass
