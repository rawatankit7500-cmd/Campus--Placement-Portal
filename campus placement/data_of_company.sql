CREATE DATABASE placement_db;
USE placement_db;

CREATE TABLE student_users (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),

    phone VARCHAR(15),
    erp_id VARCHAR(50),
    roll_no VARCHAR(50),

    father_name VARCHAR(100),
    mother_name VARCHAR(100),
    dob DATE,
    

    college VARCHAR(150),
    course VARCHAR(50),
    year VARCHAR(20),
    section VARCHAR(10),

    high_school FLOAT,
    intermediate FLOAT,
    cgpa FLOAT,
    profile_pic VARCHAR(255),
    resume VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100),
    job_role VARCHAR(100),
    package VARCHAR(50),
    eligibility_cgpa FLOAT,
    required_skills TEXT,
    visit_date DATE
);

CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT,
    company_id INT,
    status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES student_users(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);