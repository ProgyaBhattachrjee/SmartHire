import os
import re
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for
from backend.database import insert_candidate, get_all_candidates
import PyPDF2

app = Flask(__name__, template_folder='frontend/templates')

# Configure file upload settings
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Folder where resumes will be uploaded
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Function to check if the file is a valid PDF
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to extract candidate information from resume
def extract_candidate_info_from_resume(filepath):
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        
        # Extract text from all pages
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    
    # Debug: Check extracted text
    print("Extracted Text from Resume:", text)

    name = extract_name_from_text(text)
    email = extract_email_from_text(text)
    skills = extract_skills_from_text(text)
    experience = extract_experience_from_text(text)

    # Debug: Check extracted fields
    print(f"Extracted Name: {name}")
    print(f"Extracted Email: {email}")
    print(f"Extracted Skills: {skills}")
    print(f"Extracted Experience: {experience}")

    if name and email and skills and experience:
        return {
            'name': name,
            'email': email,
            'skills': skills,
            'experience': experience
        }

    return None

# Regex to extract name (simple assumption for names in resumes)
def extract_name_from_text(text):
    name_pattern = re.compile(r"([A-Za-z]+ [A-Za-z]+)")  # Modify this for better detection
    match = name_pattern.search(text)
    if match:
        return match.group(1)
    return "Name not found"

# Regex to extract email (email should follow common patterns)
def extract_email_from_text(text):
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    match = email_pattern.search(text)
    if match:
        return match.group(0)
    return "Email not found"

# Regex to extract skills (simple assumption of skills listed after "Skills:" or similar)
def extract_skills_from_text(text):
    skills_keywords = ['Python', 'Java', 'SQL', 'JavaScript', 'C', 'C++', 'HTML', 'CSS', 'Node.js', 'Django', 'Flask']
    skills = [skill for skill in skills_keywords if skill in text]
    if skills:
        return ', '.join(skills)
    return "Skills not found"

# Regex to extract years of experience (simple assumption based on "X years" or similar)
def extract_experience_from_text(text):
    experience_pattern = re.compile(r'(\d+)\s?years?')
    match = experience_pattern.search(text)
    if match:
        return match.group(1)  # returns the number of years
    return "Experience not found"

# Route for uploading resumes and adding candidate
@app.route('/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return 'No file part', 400

        file = request.files['resume']

        if file.filename == '':
            return 'No selected file', 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Extract candidate information from the resume
            candidate_info = extract_candidate_info_from_resume(filepath)

            if candidate_info:
                # Insert the extracted candidate info into the database
                insert_candidate(candidate_info['name'], candidate_info['email'], candidate_info['skills'], candidate_info['experience'])
                return redirect(url_for('list_candidates'))
            else:
                return 'Could not extract information from resume', 400

        return 'Invalid file format', 400
    
    return render_template('add_candidate.html')

# Route to list all candidates from the database
@app.route('/candidates')
def list_candidates():
    candidates = get_all_candidates()
    return render_template('candidates.html', candidates=candidates)

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
