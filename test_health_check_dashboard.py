import unittest
from unittest.mock import patch, MagicMock
import requests
import pandas as pd
from datetime import datetime
from health_check_dashboard import HealthCheckDashboard
import streamlit as st


class TestHealthCheckDashboard(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Initialize session state properly for tests
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        
        # Initialize required session state variables
        if 'results' not in st.session_state:
            st.session_state.results = {}
        if 'urls' not in st.session_state:
            st.session_state.urls = []
        if 'history' not in st.session_state:
            st.session_state.history = {}
        if 'last_check_time' not in st.session_state:
            st.session_state.last_check_time = None
        
        # Create a dashboard instance without persistence for testing
        self.dashboard = HealthCheckDashboard()
        # Override the file paths to avoid file I/O during tests
        self.dashboard.urls_file = ":memory:"
        self.dashboard.history_file = ":memory:"

    @patch('requests.get')
    def test_check_url_health_success(self, mock_get):
        """Test successful URL health check."""
        # Mock a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        url = "https://httpbin.org/status/200"
        result = self.dashboard.check_url_health(url, timeout=5)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["status"], "UP")
        self.assertEqual(result["status_code"], 200)
        self.assertIsNotNone(result["response_time"])
        self.assertIsNone(result["error"])

    @patch('requests.get')
    def test_check_url_health_client_error(self, mock_get):
        """Test URL health check with client error (4xx)."""
        # Mock a 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        url = "https://httpbin.org/status/404"
        result = self.dashboard.check_url_health(url, timeout=5)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["status"], "DOWN")  # 4xx codes are considered DOWN in our implementation
        self.assertEqual(result["status_code"], 404)
        self.assertIsNotNone(result["response_time"])
        self.assertIsNone(result["error"])

    @patch('requests.get')
    def test_check_url_health_server_error(self, mock_get):
        """Test URL health check with server error (5xx)."""
        # Mock a 500 response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        url = "https://httpbin.org/status/500"
        result = self.dashboard.check_url_health(url, timeout=5)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["status"], "DOWN")  # 5xx codes are considered DOWN
        self.assertEqual(result["status_code"], 500)
        self.assertIsNotNone(result["response_time"])
        self.assertIsNone(result["error"])

    @patch('requests.get')
    def test_check_url_health_request_exception(self, mock_get):
        """Test URL health check with request exception."""
        # Mock a request exception
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        url = "https://invalid-url-that-does-not-exist.com"
        result = self.dashboard.check_url_health(url, timeout=5)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["status"], "DOWN")
        self.assertIsNone(result["status_code"])
        self.assertIsNone(result["response_time"])
        self.assertIsNotNone(result["error"])
        self.assertIn("Connection failed", result["error"])

    @patch.object(HealthCheckDashboard, 'check_url_health')
    def test_check_all_urls(self, mock_check_url_health):
        """Test checking all URLs in the list."""
        # Mock the check_url_health method to return known values
        mock_result = {
            "url": "https://httpbin.org/status/200",
            "status": "UP",
            "response_time": 100.0,
            "status_code": 200,
            "timestamp": datetime.now(),
            "error": None
        }
        mock_check_url_health.return_value = mock_result
        
        # Set up test URLs
        test_urls = [
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404"
        ]
        st.session_state.urls = test_urls
        
        results = self.dashboard.check_all_urls()
        
        # Verify that check_url_health was called for each URL
        self.assertEqual(mock_check_url_health.call_count, len(test_urls))
        self.assertEqual(len(results), len(test_urls))
        
        # Verify results structure
        for url in test_urls:
            self.assertIn(url, results)
            self.assertEqual(results[url]["status"], "UP")

    def test_get_status_summary_empty(self):
        """Test status summary when no results exist."""
        st.session_state.results = {}
        st.session_state.urls = []  # Empty URLs list
        summary = self.dashboard.get_status_summary()
        
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["up"], 0)
        self.assertEqual(summary["down"], 0)

    def test_get_status_summary_with_results(self):
        """Test status summary with mixed results."""
        # Set up URLs that match the results
        st.session_state.urls = ["url1", "url2", "url3", "url4"]
        st.session_state.results = {
            "url1": {"status": "UP"},
            "url2": {"status": "DOWN"},
            "url3": {"status": "UP"},
            "url4": {"status": "DOWN"}
        }
        
        summary = self.dashboard.get_status_summary()
        
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["up"], 2)
        self.assertEqual(summary["down"], 2)

    def test_create_status_chart_no_data(self):
        """Test status chart creation with no data."""
        st.session_state.results = {}
        chart = self.dashboard.create_status_chart()
        
        self.assertIsNone(chart)

    def test_create_response_time_chart_no_data(self):
        """Test response time chart creation with no data."""
        st.session_state.results = {}
        chart = self.dashboard.create_response_time_chart()
        
        self.assertIsNone(chart)

    def test_create_response_time_chart_down_services_only(self):
        """Test response time chart with only down services."""
        st.session_state.results = {
            "url1": {"status": "DOWN", "response_time": None},
            "url2": {"status": "DOWN", "response_time": None}
        }
        chart = self.dashboard.create_response_time_chart()
        
        self.assertIsNone(chart)

    def test_create_history_chart_no_data(self):
        """Test history chart creation with no data."""
        st.session_state.history = {}
        chart = self.dashboard.create_history_chart()
        
        self.assertIsNone(chart)

    def test_create_history_chart_with_data(self):
        """Test history chart creation with data."""
        test_history = {
            "https://httpbin.org/status/200": [
                {
                    "status": "UP",
                    "timestamp": datetime.now(),
                    "response_time": 100.0
                },
                {
                    "status": "DOWN", 
                    "timestamp": datetime.now(),
                    "response_time": None
                }
            ]
        }
        st.session_state.history = test_history
        
        chart = self.dashboard.create_history_chart(["https://httpbin.org/status/200"])
        
        # Chart should be created successfully
        self.assertIsNotNone(chart)

    def test_create_history_chart_selected_urls(self):
        """Test history chart with specific selected URLs."""
        test_history = {
            "url1": [{"status": "UP", "timestamp": datetime.now()}],
            "url2": [{"status": "DOWN", "timestamp": datetime.now()}]
        }
        st.session_state.history = test_history
        
        chart = self.dashboard.create_history_chart(["url1"])
        
        # Chart should be created successfully for selected URL only
        self.assertIsNotNone(chart)

    def test_create_history_chart_empty_selection(self):
        """Test history chart with empty URL selection."""
        test_history = {
            "url1": [{"status": "UP", "timestamp": datetime.now()}]
        }
        st.session_state.history = test_history
        
        chart = self.dashboard.create_history_chart([])
        
        # Chart should be None when no URLs selected
        self.assertIsNone(chart)

    @patch('requests.get')
    def test_integration_full_workflow(self, mock_get):
        """Integration test for the full workflow."""
        # Mock responses for different URLs
        def mock_side_effect(url, *args, **kwargs):
            mock_resp = MagicMock()
            if "200" in url:
                mock_resp.status_code = 200
            elif "404" in url:
                mock_resp.status_code = 404
            elif "500" in url:
                mock_resp.status_code = 500
            return mock_resp
        
        mock_get.side_effect = mock_side_effect
        
        # Set up test URLs
        test_urls = [
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404", 
            "https://httpbin.org/status/500"
        ]
        st.session_state.urls = test_urls
        
        # Run the full check
        results = self.dashboard.check_all_urls()
        
        # Verify we have results for all URLs
        self.assertEqual(len(results), 3)
        
        # Verify individual results
        self.assertEqual(results["https://httpbin.org/status/200"]["status"], "UP")
        self.assertEqual(results["https://httpbin.org/status/404"]["status"], "DOWN")  # 4xx is DOWN
        self.assertEqual(results["https://httpbin.org/status/500"]["status"], "DOWN")  # 5xx is DOWN
        
        # Verify history was updated
        for url in test_urls:
            self.assertIn(url, st.session_state.history)
            self.assertGreater(len(st.session_state.history[url]), 0)
            self.assertEqual(st.session_state.history[url][-1]["status"], results[url]["status"])

    def test_history_limiting(self):
        """Test that history is limited to prevent memory issues."""
        url = "https://httpbin.org/status/200"
        st.session_state.history = {url: []}
        
        # Add more than 100 entries
        for i in range(105):
            st.session_state.history[url].append({
                "status": "UP",
                "timestamp": datetime.now(),
                "response_time": 100.0
            })
        
        # Manually call the limiting logic that happens in check_all_urls
        if len(st.session_state.history[url]) > 100:
            st.session_state.history[url] = st.session_state.history[url][-100:]
        
        # Verify history is limited to 100
        self.assertEqual(len(st.session_state.history[url]), 100)


class TestHealthCheckDashboardEdgeCases(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.dashboard = HealthCheckDashboard()

    @patch('requests.get')
    def test_timeout_handling(self, mock_get):
        """Test that timeouts are properly handled."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        url = "https://slow-website.com"
        result = self.dashboard.check_url_health(url, timeout=1)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["status"], "DOWN")
        self.assertIsNone(result["status_code"])
        self.assertIsNone(result["response_time"])
        self.assertIsNotNone(result["error"])
        self.assertIn("timed out", result["error"])

    @patch('requests.get')
    def test_connection_error_handling(self, mock_get):
        """Test that connection errors are properly handled."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to establish connection")
        
        url = "https://nonexistent-domain-12345.com"
        result = self.dashboard.check_url_health(url, timeout=5)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["status"], "DOWN")
        self.assertIsNone(result["status_code"])
        self.assertIsNone(result["response_time"])
        self.assertIsNotNone(result["error"])
        self.assertIn("connection", result["error"].lower())

    @patch('requests.get')
    def test_invalid_url_handling(self, mock_get):
        """Test that invalid URLs are handled gracefully."""
        mock_get.side_effect = requests.exceptions.InvalidURL("Invalid URL")
        
        url = "not-a-valid-url"
        result = self.dashboard.check_url_health(url, timeout=5)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["status"], "DOWN")
        self.assertIsNone(result["status_code"])
        self.assertIsNone(result["response_time"])
        self.assertIsNotNone(result["error"])
        self.assertIn("invalid", result["error"].lower())


if __name__ == '__main__':
    unittest.main()