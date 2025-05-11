import re

text = "Name: John Doe\nEmail: john.doe@example.com\nSkills: Python, Java\nExperience: 5 years"

def extract_name(text):
    name_match = re.search(r"Name:\s*([A-Za-z\s]+)", text)
    return name_match.group(1) if name_match else None

def extract_email(text):
    email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
    return email_match.group(1) if email_match else None

def extract_skills(text):
    skills_match = re.search(r"Skills?:\s*([A-Za-z, \.]+)", text)
    return skills_match.group(1) if skills_match else "Not Available"

def extract_experience(text):
    experience_match = re.search(r"Experience?:\s*(\d+)\s*(years|year)", text)
    return experience_match.group(1) if experience_match else "Not Available"
name = extract_name(text)
email = extract_email(text)
skills = extract_skills(text)
experience = extract_experience(text)

print(f"Name: {name}, Email: {email}, Skills: {skills}, Experience: {experience}")
