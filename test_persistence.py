#!/usr/bin/env python
"""
Test script to verify the persistence functionality
"""
import json
import os
from datetime import datetime
from health_check_dashboard import HealthCheckDashboard

def test_persistence():
    print("Testing persistence functionality...")
    
    # Create a dashboard instance
    dashboard = HealthCheckDashboard()
    
    # Test that files are created with default data
    print("\n1. Checking if default files are created...")
    if os.path.exists(dashboard.urls_file):
        print(f"[OK] {dashboard.urls_file} exists")
        with open(dashboard.urls_file, 'r') as f:
            urls_data = json.load(f)
            print(f"  URLs in file: {len(urls_data)}")
    else:
        print(f"[FAIL] {dashboard.urls_file} does not exist")
    
    if os.path.exists(dashboard.history_file):
        print(f"[OK] {dashboard.history_file} exists")
        with open(dashboard.history_file, 'r') as f:
            history_data = json.load(f)
            print(f"  History entries in file: {len(history_data)}")
    else:
        print(f"[FAIL] {dashboard.history_file} does not exist")
    
    # Test saving custom data
    print("\n2. Testing saving custom URLs...")
    test_urls = [
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    # Simulate updating session state
    import streamlit as st
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    st.session_state.urls = test_urls
    
    # Save the data
    dashboard.save_persisted_data()
    
    # Verify the data was saved
    with open(dashboard.urls_file, 'r') as f:
        saved_urls = json.load(f)
    
    if saved_urls == test_urls:
        print("[OK] URLs saved correctly")
    else:
        print(f"[FAIL] URLs not saved correctly. Expected: {test_urls}, Got: {saved_urls}")
    
    print("\n3. Testing loading data...")
    # Create a new dashboard instance to simulate fresh start
    dashboard2 = HealthCheckDashboard()
    
    # Check if the URLs were loaded
    if hasattr(st.session_state, 'urls') and st.session_state.urls == test_urls:
        print("[OK] URLs loaded correctly on fresh start")
    else:
        print("[FAIL] URLs not loaded correctly on fresh start")
        print(f"  Current URLs: {getattr(st.session_state, 'urls', 'Not found')}")
        print(f"  Expected: {test_urls}")
    
    print("\nPersistence functionality test completed!")

if __name__ == "__main__":
    test_persistence()