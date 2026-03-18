import time
import requests

def measure_analytics_performance():
    print("🚀 Starting performance benchmark for /api/analytics...")
    
    # We'll use the existing admin user for testing
    login_data = {
        "school_id": "admin",
        "password": "adminpass"
    }
    
    session = requests.Session()
    login_res = session.post("http://localhost:5000/api/login", data=login_data)
    
    if login_res.status_code != 200:
        print("❌ Login failed. Is the server running?")
        return

    # Warm up the cache
    session.get("http://localhost:5000/api/analytics")
    
    # Measure 10 requests
    times = []
    for i in range(10):
        start = time.time()
        res = session.get("http://localhost:5000/api/analytics")
        end = time.time()
        if res.status_code == 200:
            times.append(end - start)
        else:
            print(f"❌ Request {i} failed with status {res.status_code}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"✅ Average response time over 10 requests: {avg_time:.4f} seconds")
        print(f"📊 Best time: {min(times):.4f}s, Worst time: {max(times):.4f}s")
    else:
        print("❌ No successful requests recorded.")

if __name__ == "__main__":
    measure_analytics_performance()
