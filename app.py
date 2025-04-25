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
@app.route('/upload_job_description', methods=['POST'])
def upload_job_description():
    if 'job_description' not in request.files:
        return 'No file part', 400

    file = request.files['job_description']

    if file.filename == '':
        return 'No selected file', 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        job_desc_text = extract_job_description(filepath)

        # Now we can use this job description to compare candidates
        candidates = get_all_candidates()
        job_fit_scores = match_candidates_to_job(candidates, job_desc_text)

        # Return the scores for display
        return render_template('candidate_matching.html', job_fit_scores=job_fit_scores)

    return 'Invalid file format', 400

# Function to extract text from the job description file (PDF/Text)
def extract_job_description(filepath):
    text = ""
    if filepath.endswith('.pdf'):
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in range(len(reader.pages)):
                text += reader.pages[page].extract_text()
    elif filepath.endswith('.txt'):
        with open(filepath, 'r') as file:
            text = file.read()
    return text

# Function to match candidates to job description
def match_candidates_to_job(candidates, job_desc):
    job_desc_keywords = job_desc.lower().split()  # Basic keyword matching
    job_fit_scores = []

    for candidate in candidates:
        skills = candidate[3].lower().split(',')  # Extract skills from candidate (assuming 4th column is skills)
        score = sum(1 for skill in skills if skill.strip() in job_desc_keywords)
        job_fit_scores.append({
            'candidate_name': candidate[1],
            'email': candidate[2],
            'score': score
        })

    # Sort by score in descending order
    job_fit_scores.sort(key=lambda x: x['score'], reverse=True)
    return job_fit_scores
# Route for Job Description Page
@app.route('/job_description')
def job_description():
    return render_template('job_description.html')

# Route for Candidate Matching Page
@app.route('/candidate_matching')
def candidate_matching():
    return render_template('candidate_matching.html')

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
