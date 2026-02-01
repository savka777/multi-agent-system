#!/usr/bin/env python3
"""
Example client demonstrating how to use the async due diligence API.

Usage:
    python example_client.py
"""

import requests
import time
import json

API_BASE_URL = "http://localhost:8000"


def submit_analysis(startup_name: str, startup_description: str):
    """Submit a due diligence analysis job"""
    print(f"📤 Submitting analysis for: {startup_name}")
    
    response = requests.post(
        f"{API_BASE_URL}/analyze",
        json={
            "startup_name": startup_name,
            "startup_description": startup_description,
            "funding_stage": "series-a"
        }
    )
    
    if response.status_code == 202:
        data = response.json()
        print(f"✅ Job submitted! Job ID: {data['job_id']}")
        return data['job_id']
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None


def check_status(job_id: str):
    """Check the status of a job"""
    response = requests.get(f"{API_BASE_URL}/analyze/status/{job_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error checking status: {response.status_code}")
        return None


def wait_for_completion(job_id: str, max_wait_seconds: int = 600, poll_interval: int = 5):
    """
    Poll job status until completion.
    
    Args:
        job_id: The job ID to monitor
        max_wait_seconds: Maximum time to wait (default 10 minutes)
        poll_interval: How often to check status (default 5 seconds)
    """
    print(f"⏳ Waiting for job {job_id} to complete...")
    print(f"   (Polling every {poll_interval}s, max wait {max_wait_seconds}s)")
    
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait_seconds:
            print(f"⏰ Timeout! Job did not complete in {max_wait_seconds}s")
            return None
        
        status_data = check_status(job_id)
        
        if not status_data:
            time.sleep(poll_interval)
            continue
        
        status = status_data['status']
        
        if status == 'finished':
            print(f"✅ Job completed in {elapsed:.1f}s!")
            return status_data['result']
        
        elif status == 'failed':
            print(f"❌ Job failed: {status_data.get('error', 'Unknown error')}")
            return None
        
        elif status == 'started':
            print(f"🔄 Job running... ({elapsed:.1f}s elapsed)")
        
        elif status == 'queued':
            print(f"⏸️  Job queued... ({elapsed:.1f}s elapsed)")
        
        time.sleep(poll_interval)


def print_results(result):
    """Pretty-print the analysis results"""
    if not result:
        print("No results to display")
        return
    
    print("\n" + "="*80)
    print("📊 DUE DILIGENCE RESULTS")
    print("="*80)
    
    # Investment Decision
    if 'investment_decision' in result:
        decision = result['investment_decision']
        print(f"\n🎯 INVESTMENT DECISION:")
        print(json.dumps(decision, indent=2))
    
    # Full Report (truncated)
    if 'full_report' in result and result['full_report']:
        report = result['full_report']
        print(f"\n📄 FULL REPORT (first 500 chars):")
        print(report[:500] + "..." if len(report) > 500 else report)
    
    # Error Summary
    if 'errors' in result and result['errors']:
        print(f"\n⚠️  ERRORS ({len(result['errors'])}):")
        for error in result['errors'][:5]:  # Show first 5
            print(f"  - {error}")
    
    print("\n" + "="*80)


def main():
    """Run example analysis"""
    print("🚀 Due Diligence API Client Example\n")
    
    # Example startups to analyze
    examples = [
        {
            "name": "Stripe",
            "description": """
            Stripe is a technology company that builds economic infrastructure
            for the internet. Businesses of every size use Stripe's software
            to accept payments and manage their businesses online.
            """
        },
        {
            "name": "OpenAI",
            "description": """
            OpenAI is an AI research and deployment company. Their mission is
            to ensure that artificial general intelligence benefits all of humanity.
            They created GPT models and ChatGPT.
            """
        }
    ]
    
    # Use the first example
    startup = examples[0]
    
    # Step 1: Submit job
    job_id = submit_analysis(startup["name"], startup["description"])
    
    if not job_id:
        return
    
    # Step 2: Wait for completion
    result = wait_for_completion(job_id, max_wait_seconds=600, poll_interval=5)
    
    # Step 3: Display results
    if result:
        print_results(result)
    else:
        print("\n❌ Analysis failed or timed out")
    
    print("\n✨ Done!")


if __name__ == "__main__":
    main()
