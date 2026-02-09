import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import threading
from collections import defaultdict
import json
import os


class HealthCheckDashboard:
    def __init__(self):
        # Define file paths for persistence
        self.urls_file = "urls.json"
        self.history_file = "history.json"
        
        # Load persisted data
        self.load_persisted_data()
        
        # Initialize session state for storing health check results
        if 'results' not in st.session_state:
            st.session_state.results = {}
        if 'last_check_time' not in st.session_state:
            st.session_state.last_check_time = None
        if 'urls' not in st.session_state:
            # Default URLs for demonstration if no persisted data
            st.session_state.urls = [
                "https://httpbin.org/status/200",
                "https://httpbin.org/status/404",
                "https://httpbin.org/delay/2",
                "https://jsonplaceholder.typicode.com/posts/1"
            ]
        if 'history' not in st.session_state:
            st.session_state.history = {}
    
    def load_persisted_data(self):
        """Load persisted URLs and history from JSON files."""
        # Load URLs
        if os.path.exists(self.urls_file):
            try:
                with open(self.urls_file, 'r') as f:
                    loaded_urls = json.load(f)
                    if isinstance(loaded_urls, list):
                        st.session_state.urls = loaded_urls
                    else:
                        # If file format is wrong, use defaults
                        st.session_state.urls = [
                            "https://httpbin.org/status/200",
                            "https://httpbin.org/status/404",
                            "https://httpbin.org/delay/2",
                            "https://jsonplaceholder.typicode.com/posts/1"
                        ]
            except (json.JSONDecodeError, IOError):
                st.session_state.urls = [
                    "https://httpbin.org/status/200",
                    "https://httpbin.org/status/404",
                    "https://httpbin.org/delay/2",
                    "https://jsonplaceholder.typicode.com/posts/1"
                ]
        else:
            # Default URLs if no persisted data
            st.session_state.urls = [
                "https://httpbin.org/status/200",
                "https://httpbin.org/status/404",
                "https://httpbin.org/delay/2",
                "https://jsonplaceholder.typicode.com/posts/1"
            ]
        
        # Load history
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    loaded_history = json.load(f)
                    if isinstance(loaded_history, dict):
                        # Convert timestamp strings back to datetime objects
                        processed_history = {}
                        for url, entries in loaded_history.items():
                            processed_entries = []
                            for entry in entries:
                                # Create a copy of the entry to avoid modifying the original
                                processed_entry = entry.copy()
                                # Convert timestamp string back to datetime
                                if 'timestamp' in processed_entry and isinstance(processed_entry['timestamp'], str):
                                    try:
                                        processed_entry['timestamp'] = datetime.fromisoformat(processed_entry['timestamp'])
                                    except ValueError:
                                        # If parsing fails, keep the original timestamp
                                        pass
                                processed_entries.append(processed_entry)
                            processed_history[url] = processed_entries
                        st.session_state.history = processed_history
                    else:
                        st.session_state.history = {}
            except (json.JSONDecodeError, IOError):
                st.session_state.history = {}
        else:
            st.session_state.history = {}
    
    def save_persisted_data(self):
        """Save current URLs and history to JSON files."""
        # Save URLs
        try:
            with open(self.urls_file, 'w') as f:
                json.dump(st.session_state.urls, f, indent=2)
        except IOError as e:
            st.error(f"Error saving URLs: {e}")
        
        # Save history with datetime converted to ISO format strings
        try:
            history_to_save = {}
            for url, entries in st.session_state.history.items():
                serialized_entries = []
                for entry in entries:
                    # Convert datetime to ISO format string for JSON serialization
                    serialized_entry = entry.copy()
                    if 'timestamp' in serialized_entry and isinstance(serialized_entry['timestamp'], datetime):
                        serialized_entry['timestamp'] = serialized_entry['timestamp'].isoformat()
                    serialized_entries.append(serialized_entry)
                history_to_save[url] = serialized_entries
            
            with open(self.history_file, 'w') as f:
                json.dump(history_to_save, f, indent=2)
        except IOError as e:
            st.error(f"Error saving history: {e}")

    def check_url_health(self, url, timeout=10):
        """
        Check the health of a single URL
        Returns status (UP/DOWN), response time, and status code
        """
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            end_time = time.time()
            
            response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
            
            # Consider UP if status code is 2xx, DOWN otherwise
            status = "UP" if 200 <= response.status_code < 300 else "DOWN"
            
            return {
                "url": url,
                "status": status,
                "response_time": response_time,
                "status_code": response.status_code,
                "timestamp": datetime.now(),
                "error": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "status": "DOWN",
                "response_time": None,
                "status_code": None,
                "timestamp": datetime.now(),
                "error": str(e)
            }

    def check_all_urls(self):
        """Check health of all URLs in the list"""
        results = {}
        
        for url in st.session_state.urls:
            result = self.check_url_health(url)
            results[url] = result
            
            # Store in history for visualization
            # Initialize the history list for this URL if it doesn't exist
            if url not in st.session_state.history:
                st.session_state.history[url] = []
                
            st.session_state.history[url].append(result)
            
            # Keep only last 100 entries per URL to prevent memory issues
            if len(st.session_state.history[url]) > 100:
                st.session_state.history[url] = st.session_state.history[url][-100:]
        
        st.session_state.results = results
        st.session_state.last_check_time = datetime.now()
        
        # Save the updated history to file
        self.save_persisted_data()
        
        return results

    def get_status_summary(self):
        """Get summary of current status"""
        # Total should be the count of all URLs we're monitoring
        total = len(st.session_state.urls) if st.session_state.urls else 0
        
        if not st.session_state.results:
            # If no results yet, all services are considered unchecked (count as down for metrics)
            return {"total": total, "up": 0, "down": total}
        
        # Count results only for URLs that are still in the list
        active_results = {url: result for url, result in st.session_state.results.items() 
                         if url in st.session_state.urls}
        
        up_count = sum(1 for r in active_results.values() if r["status"] == "UP")
        down_count = sum(1 for r in active_results.values() if r["status"] == "DOWN")
        
        # Add any URLs that haven't been checked yet to the down count
        checked_urls = set(active_results.keys())
        unchecked_count = len([url for url in st.session_state.urls if url not in checked_urls])
        down_count += unchecked_count
        
        return {"total": total, "up": up_count, "down": down_count}

    def create_status_chart(self):
        """Create a pie chart showing status distribution"""
        if not st.session_state.results:
            return None
        
        summary = self.get_status_summary()
        
        df = pd.DataFrame({
            'Status': ['UP', 'DOWN'],
            'Count': [summary['up'], summary['down']]
        })
        
        fig = px.pie(df, values='Count', names='Status', title='Service Status Distribution',
                     color_discrete_map={'UP': 'green', 'DOWN': 'red'})
        return fig

    def create_response_time_chart(self):
        """Create a bar chart showing response times"""
        if not st.session_state.results:
            return None
        
        # Filter out DOWN services for response time chart
        up_services = {k: v for k, v in st.session_state.results.items() 
                      if v["status"] == "UP" and v["response_time"] is not None}
        
        if not up_services:
            return None
        
        urls = list(up_services.keys())
        response_times = [up_services[url]["response_time"] for url in urls]
        
        df = pd.DataFrame({
            'URL': urls,
            'Response Time (ms)': response_times
        })
        
        fig = px.bar(df, x='URL', y='Response Time (ms)', 
                     title='Response Times (Services UP)',
                     color='Response Time (ms)',
                     color_continuous_scale='viridis')
        fig.update_xaxes(tickangle=45)
        return fig

    def create_history_chart(self, selected_urls=None):
        """Create a line chart showing historical status"""
        if not st.session_state.history:
            return None
        
        if selected_urls is None:
            selected_urls = list(st.session_state.history.keys())
        
        if not selected_urls:
            return None
        
        # Prepare data for the chart
        timestamps = []
        statuses = []
        urls = []
        
        for url in selected_urls:
            if url in st.session_state.history:
                for entry in st.session_state.history[url]:
                    timestamps.append(entry["timestamp"])
                    # Convert status to numeric for plotting (UP=1, DOWN=0)
                    statuses.append(1 if entry["status"] == "UP" else 0)
                    urls.append(url)
        
        if not timestamps:
            return None
        
        df = pd.DataFrame({
            'Timestamp': timestamps,
            'Status': statuses,
            'URL': urls
        })
        
        # Create the chart
        fig = go.Figure()
        
        for url in selected_urls:
            url_data = df[df['URL'] == url]
            if not url_data.empty:
                fig.add_trace(go.Scatter(
                    x=url_data['Timestamp'],
                    y=url_data['Status'],
                    mode='lines+markers',
                    name=url,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
        
        fig.update_layout(
            title="Historical Service Status",
            xaxis_title="Time",
            yaxis_title="Status (1=UP, 0=DOWN)",
            yaxis=dict(
                tickmode='array',
                tickvals=[0, 1],
                ticktext=['DOWN', 'UP']
            ),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.01)
        )
        
        return fig

    def run(self):
        """Main application interface"""
        st.set_page_config(page_title="Health Check Dashboard", layout="wide")
        st.title("🔍 Health Check Dashboard")
        
        # Main content area - calculate metrics after potential URL changes
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Services", self.get_status_summary()["total"])
        with col2:
            st.metric("Services UP", self.get_status_summary()["up"], delta=None)
        with col3:
            st.metric("Services DOWN", self.get_status_summary()["down"], delta=None)
        
        # Sidebar for configuration
        with st.sidebar:
            st.header("Configuration")
            
            # URL management
            st.subheader("Manage URLs")
            new_url = st.text_input("Add new URL:", key="new_url_input")
            
            # Check if URL has proper schema
            if new_url and not (new_url.startswith("http://") or new_url.startswith("https://")):
                st.warning("⚠️ URL should start with http:// or https://")
            
            if st.button("Add URL") and new_url:
                if new_url not in st.session_state.urls:
                    # Validate URL format
                    if not (new_url.startswith("http://") or new_url.startswith("https://")):
                        st.warning("⚠️ Please enter a valid URL starting with http:// or https://")
                    else:
                        st.session_state.urls.append(new_url)
                        # Save the updated URLs to file
                        self.save_persisted_data()
                        # Don't reset all results - just let the new URL be treated as unchecked
                        # The metrics will correctly show it as down until checked
                        # Clear the input field by rerunning
                        st.rerun()
                else:
                    st.warning(f"{new_url} already exists")
            
            # Display current URLs with option to remove
            st.subheader("Current URLs")
            urls_to_remove = []
            for i, url in enumerate(st.session_state.urls):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"`{url}`")
                with col2:
                    if st.button("❌", key=f"remove_{i}"):
                        urls_to_remove.append(url)
            
            for url in urls_to_remove:
                st.session_state.urls.remove(url)
                if url in st.session_state.history:
                    del st.session_state.history[url]
                if url in st.session_state.results:
                    del st.session_state.results[url]
            
            # Save the updated URLs and history to file if any URLs were removed
            if urls_to_remove:
                self.save_persisted_data()
                st.rerun()
            
            # Auto-refresh settings
            auto_refresh = st.checkbox("Enable Auto Refresh", value=False)
            refresh_interval = st.slider("Refresh Interval (seconds)", min_value=5, max_value=300, value=30)
        
        # Check button
        col1, col2 = st.columns([1, 3])
        with col1:
            # Disable the button if a check is in progress (either manual or auto-refresh)
            button_disabled = st.session_state.get('checking_in_progress', False)
            
            if st.button("🔄 Check Now", type="primary", disabled=button_disabled):
                # Set the flag to indicate a manual check is in progress
                st.session_state.checking_in_progress = True
                # Rerun to update the button state immediately
                st.rerun()
            
            # Run manual check if button was pressed and no auto-refresh is happening
            if st.session_state.get('checking_in_progress', False) and not auto_refresh:
                with st.spinner("Checking service health..."):
                    self.check_all_urls()
                    # Reset the flag after the check is complete
                    st.session_state.checking_in_progress = False
                    st.success("Health check completed!")
                # Rerun to update the metrics display and re-enable the button
                st.rerun()
        with col2:
            if st.session_state.last_check_time:
                st.caption(f"Last checked: {st.session_state.last_check_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Auto-refresh logic
        if auto_refresh:
            # Check if it's time for the next auto-refresh
            if 'last_auto_check' not in st.session_state:
                st.session_state.last_auto_check = datetime.now() - timedelta(seconds=refresh_interval)
            
            # Only perform auto-check if enough time has passed since the last check
            time_since_last_check = datetime.now() - st.session_state.last_auto_check
            if time_since_last_check.total_seconds() >= refresh_interval:
                # Perform auto-check
                st.session_state.checking_in_progress = True
                st.rerun()  # Rerun to update the button state immediately
            
            # Run the auto-refresh check if the flag is set
            if st.session_state.get('checking_in_progress', False) and auto_refresh:
                with st.spinner("Auto-refresh checking service health..."):
                    self.check_all_urls()
                    # Reset the flag after the check is complete
                    st.session_state.checking_in_progress = False
                    st.session_state.last_auto_check = datetime.now()
                # Rerun to update the metrics display and re-enable the button
                st.rerun()
        
        # Display results table
        if st.session_state.results:
            st.subheader("Current Status")
            df_results = pd.DataFrame([
                {
                    "URL": result["url"],
                    "Status": result["status"],
                    "Response Time (ms)": result["response_time"] if result["response_time"] else "N/A",
                    "Status Code": result["status_code"] if result["status_code"] else "N/A",
                    "Last Checked": result["timestamp"].strftime('%H:%M:%S')
                }
                for result in st.session_state.results.values()
            ])
            
            # Color-code the status column
            def color_status(val):
                color = 'green' if val == 'UP' else 'red'
                return f'background-color: {color}; color: white;'
            
            st.dataframe(
                df_results.style.applymap(color_status, subset=['Status']),
                use_container_width=True
            )
        
        # Charts section
        if st.session_state.results:
            st.subheader("Visualizations")
            
            # Status distribution chart
            status_chart = self.create_status_chart()
            if status_chart:
                st.plotly_chart(status_chart, use_container_width=True)
            
            # Response time chart
            response_time_chart = self.create_response_time_chart()
            if response_time_chart:
                st.plotly_chart(response_time_chart, use_container_width=True)
            
            # Historical chart
            st.subheader("Historical Status")
            selected_urls = st.multiselect(
                "Select URLs to view history",
                options=list(st.session_state.history.keys()),
                default=list(st.session_state.history.keys())[:3]  # Show first 3 by default
            )
            
            history_chart = self.create_history_chart(selected_urls)
            if history_chart:
                st.plotly_chart(history_chart, use_container_width=True)


def main():
    dashboard = HealthCheckDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()