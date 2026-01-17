"""
Performance benchmarks for NLP components
"""
import pytest
import time
from pathlib import Path
from app.services.nlp_pipeline import nlp_pipeline

SAMPLE_RESUMES_DIR = Path(__file__).parent / "sample_resumes"


@pytest.mark.slow
def test_benchmark_nlp_pipeline():
    """Benchmark NLP pipeline processing time"""
    sample_file = SAMPLE_RESUMES_DIR / "sample_resume_1.txt"
    
    if not sample_file.exists():
        pytest.skip("Sample resume file not found")
    
    with open(sample_file, 'rb') as f:
        content = f.read()
    
    start_time = time.time()
    result = nlp_pipeline.process_resume(
        file_content=content,
        file_type='txt',
        filename='sample_resume_1.txt',
        generate_embeddings=True
    )
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    assert result['success'] is True
    assert processing_time < 10.0  # Should complete in under 10 seconds
    print(f"\nNLP Pipeline processing time: {processing_time:.2f} seconds")
    print(f"Quality metrics: {result.get('quality_metrics', {})}")


@pytest.mark.slow
def test_benchmark_batch_processing():
    """Benchmark batch processing performance"""
    resumes = []
    
    sample_file = SAMPLE_RESUMES_DIR / "sample_resume_1.txt"
    if sample_file.exists():
        with open(sample_file, 'rb') as f:
            resumes.append({
                'content': f.read(),
                'type': 'txt',
                'filename': 'sample_resume_1.txt'
            })
    
    if not resumes:
        pytest.skip("No sample resumes found")
    
    start_time = time.time()
    results = nlp_pipeline.process_batch(resumes, generate_embeddings=False)
    end_time = time.time()
    
    processing_time = end_time - start_time
    avg_time = processing_time / len(resumes)
    
    assert len(results) == len(resumes)
    print(f"\nBatch processing time: {processing_time:.2f} seconds")
    print(f"Average time per resume: {avg_time:.2f} seconds")

