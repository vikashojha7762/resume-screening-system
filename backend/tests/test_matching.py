"""
Tests for matching and ranking components
"""
import pytest
from app.services.scoring_engine import scoring_engine
from app.services.ranking_engine import ranking_engine
from app.services.bias_detector import bias_detector


def test_scoring_engine_basic():
    """Test basic scoring functionality"""
    resume_data = {
        'skills': {
            'skills': ['python', 'javascript', 'react']
        },
        'experience': {
            'total_experience_years': 5.0
        },
        'education': {
            'highest_degree': 'B.S. Computer Science'
        }
    }
    
    job_requirements = {
        'required_skills': ['python', 'javascript'],
        'required_experience_years': 3
    }
    
    result = scoring_engine.calculate_match_score(resume_data, job_requirements)
    
    assert 'overall_score' in result
    assert result['overall_score'] > 0
    assert 'component_scores' in result
    assert 'explanation' in result


def test_scoring_mandatory_requirements():
    """Test mandatory requirements checking"""
    resume_data = {
        'skills': {
            'skills': ['python']
        },
        'experience': {
            'total_experience_years': 2.0
        }
    }
    
    job_requirements = {
        'mandatory_requirements': {
            'skills': ['java'],  # Missing mandatory skill
            'min_experience_years': 3
        }
    }
    
    result = scoring_engine.calculate_match_score(resume_data, job_requirements)
    
    assert result['mandatory_met'] is False
    assert result['overall_score'] == 0.0


def test_ranking_engine():
    """Test candidate ranking"""
    candidates = [
        {
            'candidate_id': '1',
            'overall_score': 0.9,
            'resume_data': {
                'experience': {'total_experience_years': 5.0},
                'education': {'highest_degree': 'M.S.'}
            }
        },
        {
            'candidate_id': '2',
            'overall_score': 0.7,
            'resume_data': {
                'experience': {'total_experience_years': 3.0},
                'education': {'highest_degree': 'B.S.'}
            }
        }
    ]
    
    result = ranking_engine.rank_candidates(candidates, 'job1')
    
    assert 'ranked_candidates' in result
    assert len(result['ranked_candidates']) == 2
    assert result['ranked_candidates'][0]['rank'] == 1
    assert result['ranked_candidates'][0]['overall_score'] >= result['ranked_candidates'][1]['overall_score']


def test_bias_detection():
    """Test bias detection in job description"""
    job_description = """
    We are looking for an aggressive, competitive leader who is decisive and strong.
    Must be a recent graduate from a top-tier university.
    """
    
    result = bias_detector.detect_job_description_bias(job_description)
    
    assert 'gender_bias' in result
    assert 'age_bias' in result
    assert 'institution_bias' in result
    assert result['overall_bias_score'] > 0
    assert len(result['recommendations']) > 0


def test_anonymization():
    """Test resume anonymization"""
    resume_data = {
        'contact_info': {
            'email': 'john@example.com',
            'phone': '+1-555-123-4567'
        },
        'raw_text': 'John Doe, Software Engineer',
        'experience': {
            'experiences': [{
                'company': 'Google',
                'achievements': ['Led team of 5']
            }]
        }
    }
    
    anonymized = bias_detector.anonymize_resume(resume_data)
    
    assert anonymized['contact_info']['email'] == '***@***.***'
    assert anonymized['contact_info']['phone'] == '***-***-****'
    assert 'John Doe' not in anonymized.get('raw_text', '')

