
from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"



UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

#---------------------Database--------------------------->

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="prernarawat@896914",
    database="placement_db"
)


@app.route("/")
def home():
    return render_template("index.html")


#------------------------Student Resgisteration-------------------->

@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        data = request.form
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM student_users WHERE email=%s", (data["email"],))
        if cur.fetchone():
            return render_template("register.html", error="Email exists")

        password = generate_password_hash(data["password"])

        resume = request.files.get("resume")

        if not resume or not resume.filename.endswith(".pdf"):
            return render_template("register.html", error="Only PDF resume allowed")

        resume_name = str(uuid.uuid4()) + "_" + secure_filename(resume.filename)
        resume.save(os.path.join(app.config["UPLOAD_FOLDER"], resume_name))

        cur = db.cursor()
        cur.execute("""
            INSERT INTO student_users (name,email,password,course,cgpa,resume)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (data["name"], data["email"], password, data["course"], data["cgpa"], resume_name))

        db.commit()
        return redirect("/login/student")

    return render_template("register.html")


#-----------------------student login----------------------->

@app.route("/login/student", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM student_users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/student/dashboard")

    return render_template("student_login.html")


#----------------------------Student Dashboard-------------------->

@app.route("/student/dashboard")
def student_dashboard():
    if "user_id" not in session:
        return redirect("/login/student")

    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM student_users WHERE id=%s", (session["user_id"],))
    student = cur.fetchone()

    return render_template("student_dashboard.html", student=student)


#-----------------------Student Dashboard // placement ---------------------->

@app.route("/placement")
def placement():
    if "user_id" not in session:
        return redirect("/login/student")

    cur = db.cursor(dictionary=True)

    # student fetch
    cur.execute("SELECT * FROM student_users WHERE id=%s", (session["user_id"],))
    student = cur.fetchone()

    # companies fetch
    cur.execute("SELECT * FROM companies ORDER BY visit_date DESC")
    companies = cur.fetchall()

    return render_template("placement.html", companies=companies, student=student)

#-----------------------Student Dashboard // Apply ---------------------->

@app.route("/apply/<int:company_id>")
def apply(company_id):
    if "user_id" not in session:
        return redirect("/login/student")

    student_id = session["user_id"]
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM applications WHERE student_id=%s AND company_id=%s",
                (student_id, company_id))
    if cur.fetchone():
        return render_template("apply_success.html", message="Already applied!")

    cur.execute("SELECT cgpa FROM student_users WHERE id=%s", (student_id,))
    student = cur.fetchone()

    cur.execute("SELECT eligibility_cgpa FROM companies WHERE id=%s", (company_id,))
    company = cur.fetchone()

    if student["cgpa"] < company["eligibility_cgpa"]:
        return render_template("apply_success.html", message="Not Eligible ❌")

    cur = db.cursor()
    cur.execute("INSERT INTO applications (student_id, company_id) VALUES (%s,%s)",
                (student_id, company_id))
    db.commit()

    return render_template("apply_success.html", message="Applied Successfully 🎉")


#-----------------------Student Dashboard // exam page ---------------------->
@app.route("/applied_companies")
def applied_companies():
    if "user_id" not in session:
        return redirect("/login/student")

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM student_users WHERE id=%s", (session["user_id"],))
    student = cur.fetchone()

    cur.execute("""
        SELECT c.company_name, a.status
        FROM applications a
        JOIN companies c ON a.company_id = c.id
        WHERE a.student_id=%s
    """, (session["user_id"],))

    companies = cur.fetchall()

    return render_template("applied_companies.html", companies=companies, student=student)


#-----------------------Student Dashboard // upcoming compaines ---------------------->
@app.route("/upcoming_companies")
def upcoming_companies():
    if "user_id" not in session:
        return redirect("/login/student")
    
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM upcoming_companies ORDER BY visit_date ASC")
    companies = cur.fetchall()

    return render_template("upcoming_companies.html", companies=companies)

@app.route("/upgrade", methods=["GET", "POST"])
def upgrade():
    if "user_id" not in session:
        return redirect("/login/student")

    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        data = request.form

        cur.execute("""
            UPDATE student_users 
            SET name=%s, phone=%s, course=%s, cgpa=%s
            WHERE id=%s
        """, (
            data["name"], data["phone"], data["course"], data["cgpa"], session["user_id"]
        ))
        db.commit()

        return redirect("/student/dashboard")

    # GET
    cur.execute("SELECT * FROM student_users WHERE id=%s", (session["user_id"],))
    student = cur.fetchone()

    return render_template("upgrade_info.html", student=student)

#-----------------------Student Dashboard // Preparation ---------------------->

@app.route("/preparation")
def preparation():
    if "user_id" not in session:
        return redirect("/login/student")

    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM student_users WHERE id=%s", (session["user_id"],))
    student = cur.fetchone()

    return render_template("preparation_plan.html", student=student)

#-----------------------Student Dashboard // Notices ---------------------->

@app.route("/notices")
def student_notices():
    if "user_id" not in session:
        return redirect("/login/student")

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM student_users WHERE id=%s", (session["user_id"],))
    student = cur.fetchone()

    cur.execute("SELECT * FROM notices ORDER BY date DESC")
    notices = cur.fetchall()

    return render_template("notices.html", notices=notices, student=student)

#-----------------------Student Dashboard // Exams ---------------------->

@app.route("/exams")
def student_exams():
    if "user_id" not in session:
        return redirect("/login/student")

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM student_users WHERE id=%s", (session["user_id"],))
    student = cur.fetchone()

    cur.execute("SELECT * FROM exams ORDER BY date ASC")
    exams = cur.fetchall()

    return render_template("exams.html", exams=exams, student=student)


#-----------------------Admin login ---------------------->

@app.route("/login/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect("/admin/dashboard")

    if request.method == "POST":
        if request.form["email"] == "admin@gmail.com" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin/dashboard")

    return render_template("admin_login.html")


#-----------------------Admin dashboard ---------------------->

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/login/admin")

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) as total FROM student_users")
    total_students = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM companies")
    total_companies = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM applications")
    total_applications = cur.fetchone()["total"]

    return render_template("admin_dashboard.html",
                           total_students=total_students,
                           total_companies=total_companies,
                           total_applications=total_applications)



#-----------------------Admin Dashboard // Resumes ---------------------->

@app.route("/admin/resumes")
def admin_resumes():
    if "admin" not in session:
        return redirect("/login/admin")

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT name, email, course, cgpa, resume FROM student_users")
    students = cur.fetchall()

    return render_template("admin_resumes.html", students=students)

#-----------------------admin Dashboard // students---------------------->
@app.route("/admin/students")
def admin_students():
    if "admin" not in session:
        return redirect("/login/admin")

    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, name, email, course, cgpa, resume FROM student_users")
    students = cur.fetchall()

    return render_template("admin_students.html", students=students)

@app.route("/admin/delete_student/<int:id>")
def delete_student(id):
    if "admin" not in session:
        return redirect("/login/admin")

    cur = db.cursor()
    cur.execute("DELETE FROM student_users WHERE id=%s", (id,))
    db.commit()

    return redirect("/admin/students")

@app.route("/admin/companies")
def admin_companies():
    if "admin" not in session:
        return redirect("/login/admin")

    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM companies ORDER BY id DESC")
    companies = cur.fetchall()

    return render_template("admin_companies.html", companies=companies)

@app.route("/admin/delete_company/<int:id>")
def delete_company(id):
    if "admin" not in session:
        return redirect("/login/admin")

    cur = db.cursor()
    cur.execute("DELETE FROM companies WHERE id=%s", (id,))
    db.commit()

    return redirect("/admin/companies")

#------------------------ Admin Dahboard // Application ------------------------->

@app.route("/admin/applications")
def admin_applications():
    if "admin" not in session:
        return redirect("/login/admin")

    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.id, s.name, c.company_name, a.status
        FROM applications a
        JOIN student_users s ON a.student_id = s.id
        JOIN companies c ON a.company_id = c.id
    """)
    applications = cur.fetchall()

    return render_template("admin_applications.html", applications=applications)

#------------------------ Admin Dahboard // updates ------------------------->

@app.route("/admin/update_status/<int:id>/<status>")
def update_status(id, status):
    cur = db.cursor()
    cur.execute("UPDATE applications SET status=%s WHERE id=%s", (status, id))
    db.commit()
    return redirect("/admin/applications")


#------------------------ Admin Dahboard // Notices ------------------------->
@app.route("/admin/notices", methods=["GET"])
def admin_notices():
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM notices ORDER BY id DESC")
    notices = cur.fetchall()
    return render_template("admin_notices.html", notices=notices)


#------------------------ Admin Dahboard // Add notification ------------------------->

@app.route("/admin/add_notice", methods=["POST"])
def add_notice():
    data = request.form
    cur = db.cursor()
    cur.execute("INSERT INTO notices (title, description, date) VALUES (%s,%s,NOW())",
                (data["title"], data["description"]))
    db.commit()
    return redirect("/admin/notices")

#------------------------ Admin Dahboard // delete notices ------------------------->
@app.route("/admin/delete_notice/<int:id>")
def delete_notice(id):
    cur = db.cursor()
    cur.execute("DELETE FROM notices WHERE id=%s", (id,))
    db.commit()
    return redirect("/admin/notices")


#------------------------ Admin Dahboard // Exams ------------------------->

@app.route("/admin/exams")
def admin_exams():
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM exams ORDER BY id DESC")
    exams = cur.fetchall()
    return render_template("admin_exams.html", exams=exams)

#------------------------ Admin Dahboard // Add exams ------------------------->

@app.route("/admin/add_exam", methods=["POST"])
def add_exam():
    data = request.form
    cur = db.cursor()
    cur.execute("""
        INSERT INTO exams (subject, date, time, type)
        VALUES (%s,%s,%s,%s)
    """, (data["subject"], data["date"], data["time"], data["type"]))
    db.commit()
    return redirect("/admin/exams")

#------------------------ Admin Dahboard // Delete exam ------------------------->

@app.route("/admin/delete_exam/<int:id>")
def delete_exam(id):
    cur = db.cursor()
    cur.execute("DELETE FROM exams WHERE id=%s", (id,))
    db.commit()
    return redirect("/admin/exams")

#------------------------ Admin Dahboard // Add company ------------------------->

@app.route("/admin/add_company", methods=["GET", "POST"])
def add_company():
    if "admin" not in session:
        return redirect("/login/admin")

    if request.method == "POST":
        data = request.form

        cur = db.cursor()
        cur.execute("""
            INSERT INTO companies 
            (company_name, job_role, package, eligibility_cgpa, required_skills, location, visit_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            data["company_name"],
            data["job_role"],
            data["package"],
            data["eligibility_cgpa"],
            data["required_skills"],
            data["location"],
            data["visit_date"]
        ))

        db.commit()
        return redirect("/admin/companies")

    return render_template("admin_add_company.html")

#------------------------ Logout for all ------------------------->
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)