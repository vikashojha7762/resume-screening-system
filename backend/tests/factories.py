"""
Test data factories for generating test data
"""
import factory
from faker import Faker
from datetime import datetime, timedelta
from app.models.user import User
from app.models.job import Job
from app.models.resume import Resume
from app.models.candidate import Candidate
from app.core.security import get_password_hash

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for creating test users"""
    class Meta:
        model = dict
    
    email = factory.LazyAttribute(lambda obj: fake.email())
    password = "testpassword123"
    is_active = True
    is_superuser = False


class JobFactory(factory.Factory):
    """Factory for creating test jobs"""
    class Meta:
        model = dict
    
    title = factory.LazyAttribute(lambda obj: fake.job())
    description = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=500))
    requirements_json = factory.LazyAttribute(lambda obj: {
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "preferred_skills": ["Docker", "Kubernetes"],
        "min_experience_years": fake.random_int(min=0, max=10),
        "required_degree": "Bachelor's"
    })
    status = factory.Iterator(["draft", "active", "closed"])


class ResumeFactory(factory.Factory):
    """Factory for creating test resumes"""
    class Meta:
        model = dict
    
    file_name = factory.LazyAttribute(lambda obj: f"{fake.word()}_resume.pdf")
    file_type = "application/pdf"
    status = factory.Iterator(["uploaded", "parsing", "parsed", "processed"])
    parsed_data_json = factory.LazyAttribute(lambda obj: {
        "skills": ["Python", "JavaScript", "SQL"],
        "experience": [
            {
                "title": fake.job(),
                "company": fake.company(),
                "start_date": (datetime.now() - timedelta(days=365*2)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "duration_months": 24
            }
        ],
        "education": [
            {
                "degree": "Bachelor's",
                "institution": fake.company(),
                "field": "Computer Science",
                "graduation_year": fake.year()
            }
        ]
    })


class CandidateFactory(factory.Factory):
    """Factory for creating test candidates"""
    class Meta:
        model = dict
    
    anonymized_id = factory.LazyAttribute(lambda obj: f"anon_{fake.uuid4()}")
    masked_data_json = {
        "name": "[MASKED]",
        "email": "[MASKED]",
        "phone": "[MASKED]"
    }


def generate_synthetic_resume_text():
    """Generate synthetic resume text for testing"""
    return f"""
    {fake.name()}
    {fake.email()}
    {fake.phone_number()}
    
    PROFESSIONAL SUMMARY
    {fake.text(max_nb_chars=200)}
    
    EXPERIENCE
    {fake.job()} | {fake.company()} | {fake.date()}
    {fake.text(max_nb_chars=150)}
    
    {fake.job()} | {fake.company()} | {fake.date()}
    {fake.text(max_nb_chars=150)}
    
    EDUCATION
    {fake.random_element(elements=("Bachelor's", "Master's", "PhD"))} in {fake.job()}
    {fake.company()} | {fake.year()}
    
    SKILLS
    {', '.join(fake.words(nb=10))}
    """


def generate_job_description():
    """Generate synthetic job description for testing"""
    return f"""
    Job Title: {fake.job()}
    
    Company: {fake.company()}
    
    Description:
    {fake.text(max_nb_chars=500)}
    
    Requirements:
    - {fake.random_element(elements=("Python", "Java", "JavaScript"))} experience
    - {fake.random_int(min=2, max=10)} years of experience
    - {fake.random_element(elements=("Bachelor's", "Master's"))} degree
    - Strong communication skills
    
    Benefits:
    {fake.text(max_nb_chars=200)}
    """

