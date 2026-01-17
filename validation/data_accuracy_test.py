"""
Data Accuracy Validation Tests
Verify resume parsing, skill extraction, and scoring accuracy
"""
import pytest
from app.services.resume_parser import ResumeParser
from app.services.skill_extractor import SkillExtractor
from app.services.scoring_engine import ScoringEngine
from app.services.ranking_engine import RankingEngine


class TestDataAccuracy:
    """Data accuracy validation tests"""
    
    def test_resume_parsing_accuracy(self):
        """Test resume parsing accuracy"""
        print("\n📊 Testing resume parsing accuracy...")
        
        parser = ResumeParser()
        
        test_cases = [
            {
                "input": """
                SKILLS
                Python, JavaScript, PostgreSQL, Docker
                
                EXPERIENCE
                Software Engineer | Google | 2020-2024
                - Developed web applications
                - Managed databases
                
                EDUCATION
                Bachelor's in Computer Science | MIT | 2020
                """,
                "expected_skills": ["Python", "JavaScript", "PostgreSQL", "Docker"],
                "expected_experience": 1,
                "expected_education": 1
            }
        ]
        
        for case in test_cases:
            result = parser.parse_text(case["input"])
            
            # Check skills extraction
            extracted_skills = [s.lower() for s in result.get("skills", [])]
            expected_skills = [s.lower() for s in case["expected_skills"]]
            
            matches = sum(1 for skill in expected_skills if skill in extracted_skills)
            accuracy = matches / len(expected_skills) if expected_skills else 0
            
            assert accuracy >= 0.8, f"Skills extraction accuracy too low: {accuracy}"
            print(f"  ✅ Skills extraction accuracy: {accuracy*100:.1f}%")
    
    def test_skill_extraction_precision(self):
        """Test skill extraction precision and recall"""
        print("\n📊 Testing skill extraction precision...")
        
        extractor = SkillExtractor()
        
        test_text = """
        I have extensive experience with Python, JavaScript, and PostgreSQL.
        I've worked with Docker and Kubernetes for containerization.
        My database skills include MySQL and MongoDB.
        """
        
        skills = extractor.extract_skills(test_text)
        extracted_names = [s.name.lower() for s in skills]
        
        expected_skills = ["python", "javascript", "postgresql", "docker", "kubernetes", "mysql", "mongodb"]
        
        # Calculate precision
        true_positives = sum(1 for skill in extracted_names if skill in expected_skills)
        precision = true_positives / len(extracted_names) if extracted_names else 0
        
        # Calculate recall
        recall = true_positives / len(expected_skills) if expected_skills else 0
        
        assert precision >= 0.7, f"Precision too low: {precision}"
        assert recall >= 0.7, f"Recall too low: {recall}"
        
        print(f"  ✅ Precision: {precision*100:.1f}%")
        print(f"  ✅ Recall: {recall*100:.1f}%")
    
    def test_scoring_algorithm_fairness(self):
        """Test scoring algorithm fairness"""
        print("\n📊 Testing scoring algorithm fairness...")
        
        engine = ScoringEngine()
        
        # Test case: Equal candidates should get similar scores
        job = {
            "requirements_json": {
                "required_skills": ["Python", "FastAPI"],
                "min_experience_years": 3
            }
        }
        
        candidate1 = {
            "skills": {"skills": [{"name": "Python"}, {"name": "FastAPI"}]},
            "experience": {"total_experience_years": 5.0},
            "education": {"highest_degree": "Bachelor's"}
        }
        
        candidate2 = {
            "skills": {"skills": [{"name": "Python"}, {"name": "FastAPI"}]},
            "experience": {"total_experience_years": 5.0},
            "education": {"highest_degree": "Bachelor's"}
        }
        
        score1 = engine.calculate_score(job, candidate1)
        score2 = engine.calculate_score(job, candidate2)
        
        # Scores should be similar for identical candidates
        score_diff = abs(score1["overall_score"] - score2["overall_score"])
        assert score_diff < 0.1, "Scoring not consistent for identical candidates"
        
        print("  ✅ Scoring algorithm is consistent")
    
    def test_bias_detection_effectiveness(self):
        """Test bias detection effectiveness"""
        print("\n📊 Testing bias detection...")
        
        from app.services.bias_detector import BiasDetector
        
        detector = BiasDetector()
        
        # Test gender bias detection
        biased_job = """
        We are looking for an aggressive, competitive leader who is decisive.
        Must be a recent graduate from a top-tier university.
        """
        
        result = detector.detect_job_description_bias(biased_job)
        
        assert "gender_bias" in result
        assert "age_bias" in result
        assert result["overall_bias_score"] > 0
        
        print(f"  ✅ Bias detection score: {result['overall_bias_score']}")
        print(f"  ✅ Recommendations: {len(result.get('recommendations', []))}")
    
    def test_ranking_consistency(self):
        """Test ranking consistency"""
        print("\n📊 Testing ranking consistency...")
        
        engine = RankingEngine()
        
        candidates = [
            {"candidate_id": "1", "overall_score": 0.9},
            {"candidate_id": "2", "overall_score": 0.7},
            {"candidate_id": "3", "overall_score": 0.8},
            {"candidate_id": "4", "overall_score": 0.95}
        ]
        
        ranked = engine.rank_candidates(candidates)
        
        # Verify ranking order
        scores = [c["overall_score"] for c in ranked]
        assert scores == sorted(scores, reverse=True), "Ranking not in descending order"
        
        # Verify ranks are assigned
        ranks = [c["rank"] for c in ranked]
        assert ranks == [1, 2, 3, 4], "Ranks not assigned correctly"
        
        print("  ✅ Ranking is consistent and correct")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

