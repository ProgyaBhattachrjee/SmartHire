import os
import re
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for
from backend.database import insert_candidate, get_all_candidates
import PyPDF2
app = Flask(__name__, template_folder='frontend/templates')
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
def extract_candidate_info_from_resume(filepath):
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''

        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
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
def extract_name_from_text(text):
    name_pattern = re.compile(r"([A-Za-z]+ [A-Za-z]+)") 
    match = name_pattern.search(text)
    if match:
        return match.group(1)
    return "Name not found"
def extract_email_from_text(text):
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    match = email_pattern.search(text)
    if match:
        return match.group(0)
    return "Email not found"
def extract_skills_from_text(text):
    skills_keywords = ['Python', 'Java', 'SQL', 'JavaScript', 'C', 'C++', 'HTML', 'CSS', 'Node.js', 'Django', 'Flask']
    skills = [skill for skill in skills_keywords if skill in text]
    if skills:
        return ', '.join(skills)
    return "Skills not found"
def extract_experience_from_text(text):
    experience_pattern = re.compile(r'(\d+)\s?years?')
    match = experience_pattern.search(text)
    if match:
        return match.group(1) 
    return "Experience not found"
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

            candidate_info = extract_candidate_info_from_resume(filepath)

            if candidate_info:
                insert_candidate(candidate_info['name'], candidate_info['email'], candidate_info['skills'], candidate_info['experience'])
                return redirect(url_for('list_candidates'))
            else:
                return 'Could not extract information from resume', 400

        return 'Invalid file format', 400
    
    return render_template('add_candidate.html')
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
        candidates = get_all_candidates()
        job_fit_scores = match_candidates_to_job(candidates, job_desc_text)
        return render_template('candidate_matching.html', job_fit_scores=job_fit_scores)

    return 'Invalid file format', 400
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
def match_candidates_to_job(candidates, job_desc):
    job_desc_lower = job_desc.lower()
    job_fit_scores = []

    for candidate in candidates:
        skills = candidate[3].lower().split(',')
        score = sum(1 for skill in skills if skill.strip() in job_desc_lower)
        job_fit_scores.append({
            'candidate_name': candidate[1],
            'email': candidate[2],
            'score': score
        })

    job_fit_scores.sort(key=lambda x: x['score'], reverse=True)
    return job_fit_scores

@app.route('/job_description')
def job_description():
    return render_template('job_description.html')
@app.route('/candidate_matching')
def candidate_matching():
    return render_template('candidate_matching.html')
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
