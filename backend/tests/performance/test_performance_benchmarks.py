"""
Performance Benchmark Tests
Benchmark system with 1000+ resumes and measure performance
"""
import pytest
import time
import statistics
from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures.database import override_get_db, test_db
from tests.factories import JobFactory, ResumeFactory
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.fixture
def client(test_db, override_get_db):
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestResumeProcessingPerformance:
    """Benchmark resume processing performance"""
    
    @pytest.mark.performance
    def test_single_resume_processing_time(self, client, auth_token):
        """Measure single resume processing time"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        start = time.time()
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test.pdf", b"PDF content", "application/pdf")},
            headers=headers
        )
        elapsed = time.time() - start
        
        assert response.status_code in [200, 201]
        assert elapsed < 5.0  # Should process in under 5 seconds
        
        print(f"✅ Single resume processing: {elapsed:.2f}s")
    
    @pytest.mark.performance
    def test_batch_resume_processing(self, client, auth_token):
        """Test processing 100 resumes"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        num_resumes = 100
        processing_times = []
        
        start_total = time.time()
        
        for i in range(num_resumes):
            start = time.time()
            response = client.post(
                "/api/v1/resumes/upload",
                files={"file": (f"resume_{i}.pdf", b"PDF content", "application/pdf")},
                headers=headers
            )
            elapsed = time.time() - start
            processing_times.append(elapsed)
            
            if response.status_code not in [200, 201]:
                print(f"Warning: Resume {i} upload failed")
        
        total_time = time.time() - start_total
        avg_time = statistics.mean(processing_times)
        median_time = statistics.median(processing_times)
        
        print(f"✅ Processed {num_resumes} resumes:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average: {avg_time:.2f}s per resume")
        print(f"   Median: {median_time:.2f}s per resume")
        print(f"   Throughput: {num_resumes/total_time:.2f} resumes/second")
        
        assert avg_time < 2.0  # Average should be under 2 seconds
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_scale_processing(self, client, auth_token):
        """Test processing 1000+ resumes"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        num_resumes = 1000
        
        start = time.time()
        
        # Process in batches to avoid overwhelming the system
        batch_size = 100
        for batch_start in range(0, num_resumes, batch_size):
            batch_end = min(batch_start + batch_size, num_resumes)
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for i in range(batch_start, batch_end):
                    future = executor.submit(
                        client.post,
                        "/api/v1/resumes/upload",
                        files={"file": (f"resume_{i}.pdf", b"PDF content", "application/pdf")},
                        headers=headers
                    )
                    futures.append(future)
                
                # Wait for batch completion
                for future in as_completed(futures):
                    try:
                        response = future.result()
                        assert response.status_code in [200, 201]
                    except Exception as e:
                        print(f"Error in batch processing: {e}")
        
        total_time = time.time() - start
        
        print(f"✅ Processed {num_resumes} resumes in {total_time:.2f}s")
        print(f"   Average: {total_time/num_resumes:.2f}s per resume")
        print(f"   Throughput: {num_resumes/total_time:.2f} resumes/second")
        
        # Target: Process 1000 resumes in under 30 minutes
        assert total_time < 1800  # 30 minutes


class TestAPIPerformance:
    """Benchmark API response times"""
    
    @pytest.mark.performance
    def test_api_response_times(self, client, auth_token):
        """Measure API endpoint response times"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        endpoints = [
            ("GET", "/api/v1/jobs", None),
            ("GET", "/api/v1/resumes", None),
            ("GET", "/api/v1/auth/me", None),
        ]
        
        response_times = {}
        
        for method, endpoint, data in endpoints:
            times = []
            for _ in range(10):  # Run 10 times for average
                start = time.time()
                if method == "GET":
                    response = client.get(endpoint, headers=headers)
                elif method == "POST":
                    response = client.post(endpoint, json=data, headers=headers)
                elapsed = time.time() - start
                times.append(elapsed)
                assert response.status_code in [200, 201]
            
            avg_time = statistics.mean(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]
            response_times[endpoint] = {
                "avg": avg_time,
                "p95": p95_time
            }
            
            print(f"✅ {method} {endpoint}:")
            print(f"   Average: {avg_time*1000:.2f}ms")
            print(f"   P95: {p95_time*1000:.2f}ms")
            
            # Target: P95 response time < 1 second
            assert p95_time < 1.0
        
        return response_times
    
    @pytest.mark.performance
    def test_concurrent_requests(self, client, auth_token):
        """Test API performance under concurrent load"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        num_requests = 100
        concurrent_workers = 20
        
        start = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [
                executor.submit(client.get, "/api/v1/jobs", headers=headers)
                for _ in range(num_requests)
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    response = future.result()
                    results.append(response.status_code)
                except Exception as e:
                    print(f"Request failed: {e}")
                    results.append(None)
        
        elapsed = time.time() - start
        success_rate = sum(1 for r in results if r == 200) / len(results)
        
        print(f"✅ Concurrent requests ({num_requests} requests, {concurrent_workers} workers):")
        print(f"   Total time: {elapsed:.2f}s")
        print(f"   Requests/second: {num_requests/elapsed:.2f}")
        print(f"   Success rate: {success_rate*100:.1f}%")
        
        assert success_rate > 0.95  # 95% success rate
        assert elapsed < 30.0  # Complete in under 30 seconds


class TestDatabasePerformance:
    """Benchmark database performance"""
    
    @pytest.mark.performance
    def test_query_performance(self, db_session):
        """Test database query performance"""
        from app.models.job import Job
        
        # Create test data
        num_jobs = 1000
        for i in range(num_jobs):
            job = Job(
                title=f"Job {i}",
                description="Test",
                status="active",
                created_by="test_user"
            )
            db_session.add(job)
        db_session.commit()
        
        # Benchmark queries
        queries = [
            ("Simple SELECT", lambda: db_session.query(Job).filter(Job.status == "active").all()),
            ("COUNT", lambda: db_session.query(Job).filter(Job.status == "active").count()),
            ("LIMIT", lambda: db_session.query(Job).limit(10).all()),
        ]
        
        for query_name, query_func in queries:
            times = []
            for _ in range(10):
                start = time.time()
                result = query_func()
                elapsed = time.time() - start
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            print(f"✅ {query_name}: {avg_time*1000:.2f}ms average")
            
            # Target: Queries should be fast
            assert avg_time < 0.1  # Under 100ms


class TestMatchingPerformance:
    """Benchmark matching performance"""
    
    @pytest.mark.performance
    def test_matching_performance(self, client, auth_token):
        """Test matching performance with varying candidate counts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create job
        job = client.post(
            "/api/v1/jobs",
            json=JobFactory(),
            headers=headers
        ).json()
        
        candidate_counts = [10, 50, 100, 500]
        
        for count in candidate_counts:
            # Upload resumes
            for i in range(count):
                client.post(
                    "/api/v1/resumes/upload",
                    files={"file": (f"resume_{i}.pdf", b"PDF content", "application/pdf")},
                    headers=headers
                )
            
            # Measure matching time
            start = time.time()
            match_response = client.post(
                f"/api/v1/results/job/{job['id']}/match",
                json={"strategy": "standard"},
                headers=headers
            )
            elapsed = time.time() - start
            
            if match_response.status_code in [200, 202]:
                print(f"✅ Matching {count} candidates: {elapsed:.2f}s")
                print(f"   Time per candidate: {elapsed/count:.3f}s")
            
            # Cleanup for next iteration
            # (In real test, would clean up test data)

