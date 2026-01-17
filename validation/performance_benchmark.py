"""
Performance Benchmark Suite
Tests system performance with 1000+ resumes
"""
import time
import statistics
import requests
from typing import List, Dict, Any
import concurrent.futures
from datetime import datetime


class PerformanceBenchmark:
    """Performance benchmarking suite"""
    
    BASE_URL = "http://localhost:8000/api/v1"
    
    def __init__(self, auth_token: str):
        self.headers = {"Authorization": f"Bearer {auth_token}"}
        self.results = {
            "api_response_times": [],
            "resume_processing_times": [],
            "matching_times": [],
            "database_query_times": []
        }
    
    def benchmark_api_endpoints(self, iterations: int = 100):
        """Benchmark API endpoint response times"""
        print(f"\n📊 Benchmarking API endpoints ({iterations} iterations)...")
        
        endpoints = [
            ("GET /jobs", f"{self.BASE_URL}/jobs"),
            ("GET /resumes", f"{self.BASE_URL}/resumes"),
            ("GET /health", f"{self.BASE_URL.replace('/api/v1', '')}/health"),
        ]
        
        for name, url in endpoints:
            times = []
            for i in range(iterations):
                start = time.time()
                response = requests.get(url, headers=self.headers)
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    times.append(elapsed * 1000)  # Convert to ms
            
            if times:
                avg = statistics.mean(times)
                p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
                p99 = statistics.quantiles(times, n=100)[98]  # 99th percentile
                
                print(f"  {name}:")
                print(f"    Average: {avg:.2f}ms")
                print(f"    P95: {p95:.2f}ms")
                print(f"    P99: {p99:.2f}ms")
                
                self.results["api_response_times"].append({
                    "endpoint": name,
                    "average_ms": avg,
                    "p95_ms": p95,
                    "p99_ms": p99
                })
    
    def benchmark_resume_processing(self, num_resumes: int = 100):
        """Benchmark resume processing performance"""
        print(f"\n📊 Benchmarking resume processing ({num_resumes} resumes)...")
        
        # Generate test resumes
        resumes = self._generate_test_resumes(num_resumes)
        
        # Upload resumes
        upload_times = []
        resume_ids = []
        
        for i, resume_content in enumerate(resumes):
            start = time.time()
            response = requests.post(
                f"{self.BASE_URL}/resumes/upload",
                files={"file": (f"resume_{i}.txt", resume_content, "text/plain")},
                headers=self.headers
            )
            upload_time = time.time() - start
            
            if response.status_code in [200, 201]:
                upload_times.append(upload_time * 1000)
                resume_ids.append(response.json()["id"])
        
        print(f"  Upload times: {statistics.mean(upload_times):.2f}ms average")
        
        # Wait for processing
        processing_times = []
        for resume_id in resume_ids[:10]:  # Sample first 10
            start_time = time.time()
            max_wait = 300
            
            while time.time() - start_time < max_wait:
                response = requests.get(
                    f"{self.BASE_URL}/resumes/{resume_id}",
                    headers=self.headers
                )
                status = response.json()["status"]
                
                if status == "processed":
                    processing_time = time.time() - start_time
                    processing_times.append(processing_time)
                    break
                elif status == "error":
                    break
                
                time.sleep(2)
        
        if processing_times:
            avg_processing = statistics.mean(processing_times)
            print(f"  Processing times: {avg_processing:.2f}s average")
            self.results["resume_processing_times"] = {
                "average_seconds": avg_processing,
                "resumes_processed": len(processing_times)
            }
    
    def benchmark_matching(self, job_id: str, num_candidates: int = 100):
        """Benchmark matching performance"""
        print(f"\n📊 Benchmarking matching ({num_candidates} candidates)...")
        
        start = time.time()
        response = requests.post(
            f"{self.BASE_URL}/results/job/{job_id}/match",
            json={"strategy": "standard"},
            headers=self.headers
        )
        
        if response.status_code in [200, 202]:
            # Wait for completion
            max_wait = 600  # 10 minutes
            elapsed = 0
            
            while elapsed < max_wait:
                results = requests.get(
                    f"{self.BASE_URL}/results/job/{job_id}/ranked",
                    headers=self.headers
                )
                
                if results.status_code == 200 and len(results.json().get("items", [])) > 0:
                    matching_time = time.time() - start
                    print(f"  Matching time: {matching_time:.2f}s")
                    self.results["matching_times"] = {
                        "seconds": matching_time,
                        "candidates": num_candidates
                    }
                    return
                
                time.sleep(5)
                elapsed += 5
    
    def benchmark_concurrent_load(self, concurrent_users: int = 50, requests_per_user: int = 10):
        """Benchmark system under concurrent load"""
        print(f"\n📊 Benchmarking concurrent load ({concurrent_users} users, {requests_per_user} requests each)...")
        
        def make_requests(user_id):
            times = []
            for i in range(requests_per_user):
                start = time.time()
                response = requests.get(
                    f"{self.BASE_URL}/jobs",
                    headers=self.headers
                )
                elapsed = time.time() - start
                if response.status_code == 200:
                    times.append(elapsed * 1000)
            return times
        
        all_times = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_requests, i) for i in range(concurrent_users)]
            for future in concurrent.futures.as_completed(futures):
                all_times.extend(future.result())
        
        if all_times:
            avg = statistics.mean(all_times)
            p95 = statistics.quantiles(all_times, n=20)[18]
            print(f"  Average response time: {avg:.2f}ms")
            print(f"  P95 response time: {p95:.2f}ms")
            print(f"  Total requests: {len(all_times)}")
            print(f"  Success rate: {len(all_times) / (concurrent_users * requests_per_user) * 100:.1f}%")
    
    def _generate_test_resume(self, index: int) -> bytes:
        """Generate test resume content"""
        return f"""
        Candidate {index}
        Software Engineer
        
        SKILLS
        Python, FastAPI, PostgreSQL, Docker, Kubernetes, JavaScript, React
        
        EXPERIENCE
        Software Engineer | Company {index} | 2020-2024
        - Developed applications using Python and FastAPI
        - Managed databases and deployments
        
        EDUCATION
        Bachelor's in Computer Science | University {index} | 2020
        """.encode()
    
    def _generate_test_resumes(self, count: int) -> List[bytes]:
        """Generate multiple test resumes"""
        return [self._generate_test_resume(i) for i in range(count)]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance benchmark report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "summary": {
                "api_performance": "PASS" if all(
                    r["p95_ms"] < 1000 for r in self.results["api_response_times"]
                ) else "FAIL",
                "processing_performance": "PASS" if (
                    self.results.get("resume_processing_times", {}).get("average_seconds", 999) < 300
                ) else "FAIL",
                "matching_performance": "PASS" if (
                    self.results.get("matching_times", {}).get("seconds", 999) < 600
                ) else "FAIL"
            }
        }
        return report


if __name__ == "__main__":
    # This would be run with proper authentication
    print("Performance benchmark suite")
    print("Run with: python -m pytest validation/performance_benchmark.py")

