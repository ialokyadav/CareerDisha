"""
Resume Data Processor for ML Training
Processes resumes from CVs and Resume directories, extracts skills and roles,
filters duplicates, and prepares data for MongoDB training collections.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import hashlib

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from resumes.upload import read_resume_file
from resumes.parser import parse_resume_text
from common.mongodb import get_db


# Role keywords mapping
ROLE_KEYWORDS = {
    "Business Analyst": ["business analyst", "ba", "bsa", "sr ba", "sr. ba", "senior business analyst"],
    "Project Manager": ["project manager", "pm", "pmp", "scrum master", "program manager", "agile"],
    "Java Developer": ["java developer", "java", "j2ee", "spring", "hibernate"],
    "Full Stack Developer": ["full stack", "fullstack", "full-stack"],
    "Frontend Developer": ["frontend", "front-end", "react", "angular", "vue", "ui developer"],
    "Backend Developer": ["backend", "back-end", "api", "microservices"],
    "Data Analyst": ["data analyst", "data analysis", "analytics"],
    "Machine Learning Engineer": ["machine learning", "ml engineer", "data scientist"],
    "DevOps Engineer": ["devops", "dev ops", "ci/cd", "jenkins", "kubernetes"],
    "Mobile Developer": ["mobile", "android", "ios", "kotlin", "swift"],
    "PHP Developer": ["php", "laravel", "symfony"],
    "Python Developer": ["python developer", "django", "flask", "fastapi"],
    "QA Engineer": ["qa", "quality assurance", "testing", "test automation"],
    "Database Administrator": ["dba", "database administrator", "sql server", "oracle dba"],
    "Cloud Engineer": ["cloud engineer", "aws", "azure", "gcp"],
    "Hadoop Developer": ["hadoop", "big data", "spark", "hive"]
}


def detect_role_from_filename(filename):
    """Detect role from filename"""
    filename_lower = filename.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword in filename_lower for keyword in keywords):
            return role
    return None


def detect_role_from_text(text):
    """Detect role from resume text"""
    text_lower = text.lower()
    role_scores = {}
    
    for role, keywords in ROLE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            role_scores[role] = score
    
    if role_scores:
        return max(role_scores, key=role_scores.get)
    return "Software Developer"  # Default


def extract_skills_from_text(text):
    """Extract common tech skills from text"""
    text_lower = text.lower()
    
    # Common technical skills
    skills_list = [
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby", "go", "rust", "kotlin", "swift",
        # Frontend
        "react", "angular", "vue", "html", "css", "sass", "tailwind", "bootstrap", "jquery",
        # Backend
        "node.js", "express", "django", "flask", "spring", "spring boot", "hibernate", "fastapi",
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "oracle", "sql server", "cassandra",
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible",
        # Data & ML
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "spark", "hadoop", "tableau",
        # Tools & Methodologies
        "git", "jira", "agile", "scrum", "rest api", "graphql", "microservices",
        # Business
        "business analysis", "requirements gathering", "stakeholder management", "sdlc"
    ]
    
    found_skills = []
    for skill in skills_list:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills


def compute_text_hash(text):
    """Compute hash of text for duplicate detection"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def process_resume_file(filepath):
    """Process a single resume file"""
    try:
        filename = os.path.basename(filepath)
        
        # Read file
        if filepath.endswith('.docx'):
            with open(filepath, 'rb') as f:
                raw_text, ext = read_resume_file(f, filename)
        else:
            # Text file
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
        
        if not raw_text or len(raw_text.strip()) < 50:
            return None  # Too short, skip
        
        # Parse text
        parsed = parse_resume_text(raw_text)
        cleaned_text = parsed['cleaned_text']
        
        # Detect role
        role = detect_role_from_filename(filename)
        if not role:
            role = detect_role_from_text(cleaned_text)
        
        # Extract skills
        skills = extract_skills_from_text(cleaned_text)
        
        if not skills:
            return None  # No skills found, skip
        
        # Compute hash for duplicate detection
        text_hash = compute_text_hash(cleaned_text)
        
        return {
            "filename": filename,
            "text": cleaned_text[:500],  # First 500 chars for training
            "full_text": cleaned_text,
            "skills": list(set(skills)),  # Unique skills
            "role": role,
            "text_hash": text_hash,
            "source": "bulk_import"
        }
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None


def filter_duplicates(resume_data_list, existing_hashes):
    """Filter out duplicates based on text hash"""
    unique_data = []
    seen_hashes = set(existing_hashes)
    
    for data in resume_data_list:
        if data and data['text_hash'] not in seen_hashes:
            unique_data.append(data)
            seen_hashes.add(data['text_hash'])
    
    return unique_data


def main():
    print("=" * 60)
    print("Resume Data Processor for ML Training")
    print("=" * 60)
    
    # Directories
    cvs_dir = Path("/Users/ialokyadav/Desktop/CVs")
    resume_dir = Path("/Users/ialokyadav/Desktop/Resume")
    
    # Get all files
    cv_files = list(cvs_dir.glob("cv*"))
    resume_files = list(resume_dir.glob("*.docx"))
    
    print(f"\nFound {len(cv_files)} text resumes in CVs directory")
    print(f"Found {len(resume_files)} Word resumes in Resume directory")
    print(f"Total: {len(cv_files) + len(resume_files)} resumes\n")
    
    # Get existing data from MongoDB to filter duplicates
    db = get_db()
    existing_skill_hashes = set(
        doc.get('text_hash') for doc in db['skill_training'].find({}, {'text_hash': 1})
        if doc.get('text_hash')
    )
    existing_role_hashes = set(
        doc.get('text_hash') for doc in db['role_training'].find({}, {'text_hash': 1})
        if doc.get('text_hash')
    )
    
    print(f"Existing skill training samples: {db['skill_training'].count_documents({})}")
    print(f"Existing role training samples: {db['role_training'].count_documents({})}")
    print(f"Existing unique hashes: {len(existing_skill_hashes | existing_role_hashes)}\n")
    
    # Process all resumes
    print("Processing resumes...")
    all_resume_data = []
    
    for i, filepath in enumerate(cv_files + resume_files, 1):
        if i % 50 == 0:
            print(f"Processed {i}/{len(cv_files) + len(resume_files)} resumes...")
        
        data = process_resume_file(str(filepath))
        if data:
            all_resume_data.append(data)
    
    print(f"\nSuccessfully parsed: {len(all_resume_data)} resumes")
    
    # Filter duplicates
    unique_data = filter_duplicates(all_resume_data, existing_skill_hashes | existing_role_hashes)
    print(f"After filtering duplicates: {len(unique_data)} unique resumes\n")
    
    if not unique_data:
        print("No new unique data to add. Exiting.")
        return
    
    # Prepare data for MongoDB
    skill_training_docs = []
    role_training_docs = []
    
    for data in unique_data:
        # Skill training document
        skill_training_docs.append({
            "text": data['text'],
            "skills": data['skills'],
            "source": data['source'],
            "filename": data['filename'],
            "text_hash": data['text_hash'],
            "is_new": True,
            "created_at": datetime.utcnow()
        })
        
        # Role training document
        role_training_docs.append({
            "skills": data['skills'],
            "role": data['role'],
            "source": data['source'],
            "filename": data['filename'],
            "text_hash": data['text_hash'],
            "is_new": True,
            "created_at": datetime.utcnow()
        })
    
    # Insert into MongoDB
    print("Inserting data into MongoDB...")
    
    if skill_training_docs:
        result1 = db['skill_training'].insert_many(skill_training_docs)
        print(f"✅ Inserted {len(result1.inserted_ids)} skill training samples")
    
    if role_training_docs:
        result2 = db['role_training'].insert_many(role_training_docs)
        print(f"✅ Inserted {len(result2.inserted_ids)} role training samples")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total resumes processed: {len(all_resume_data)}")
    print(f"Unique new resumes: {len(unique_data)}")
    print(f"Skill training samples added: {len(skill_training_docs)}")
    print(f"Role training samples added: {len(role_training_docs)}")
    print(f"\nNew total in MongoDB:")
    print(f"  - Skill training: {db['skill_training'].count_documents({})}")
    print(f"  - Role training: {db['role_training'].count_documents({})}")
    print("=" * 60)
    
    # Role distribution
    print("\nRole Distribution:")
    role_counts = {}
    for data in unique_data:
        role = data['role']
        role_counts[role] = role_counts.get(role, 0) + 1
    
    for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {role}: {count}")
    
    print("\n✅ Data processing complete!")
    print("Next step: Run model retraining")


if __name__ == "__main__":
    main()
