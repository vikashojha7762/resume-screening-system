"""
Test data generators for various test scenarios
"""
import random
from faker import Faker
from tests.factories import (
    UserFactory,
    JobFactory,
    ResumeFactory,
    CandidateFactory,
    generate_synthetic_resume_text,
    generate_job_description
)

fake = Faker()


def generate_edge_case_resumes():
    """Generate resumes with edge cases"""
    edge_cases = [
        {
            "name": "empty_resume",
            "text": "",
            "expected_skills": []
        },
        {
            "name": "very_long_resume",
            "text": "Experience " * 10000,
            "expected_skills": []
        },
        {
            "name": "special_characters",
            "text": "Skills: Python@#$%^&*() JavaScript!@#$%",
            "expected_skills": ["Python", "JavaScript"]
        },
        {
            "name": "unicode_resume",
            "text": "Skills: Python, JavaScript, 中文, العربية",
            "expected_skills": ["Python", "JavaScript"]
        },
        {
            "name": "formatted_resume",
            "text": """
            SKILLS
            • Python
            • JavaScript
            • SQL
            
            EXPERIENCE
            1. Software Engineer | Google | 2020-2023
            2. Developer | Startup | 2018-2020
            """,
            "expected_skills": ["Python", "JavaScript", "SQL"]
        }
    ]
    return edge_cases


def generate_security_test_payloads():
    """Generate security test payloads"""
    payloads = {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//etc/passwd"
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /"
        ]
    }
    return payloads


def generate_performance_test_dataset(size=1000):
    """Generate large dataset for performance testing"""
    jobs = [JobFactory() for _ in range(size)]
    resumes = [ResumeFactory() for _ in range(size * 10)]  # 10 resumes per job
    return {
        "jobs": jobs,
        "resumes": resumes
    }


def generate_stress_test_scenarios():
    """Generate stress test scenarios"""
    scenarios = [
        {
            "name": "concurrent_uploads",
            "concurrent_users": 100,
            "actions_per_user": 10,
            "action": "upload_resume"
        },
        {
            "name": "rapid_api_calls",
            "concurrent_users": 50,
            "actions_per_user": 100,
            "action": "get_jobs"
        },
        {
            "name": "large_batch_processing",
            "concurrent_users": 10,
            "actions_per_user": 1,
            "action": "process_1000_resumes"
        }
    ]
    return scenarios


def generate_validation_test_cases():
    """Generate validation test cases"""
    test_cases = {
        "email_validation": [
            "valid@example.com",
            "invalid-email",
            "test@",
            "@example.com",
            "test@example",
            "test..test@example.com"
        ],
        "password_validation": [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "ValidPassword123!",  # Valid
        ],
        "file_validation": [
            ("valid.pdf", "application/pdf", True),
            ("valid.doc", "application/msword", True),
            ("invalid.exe", "application/x-msdownload", False),
            ("large.pdf", "application/pdf", False),  # If > 10MB
        ]
    }
    return test_cases

