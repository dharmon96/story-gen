"""
Research Tab GUI - Dashboard for trending content analysis
Displays trending data, research sessions, and configuration options
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import webbrowser

from database import DatabaseManager
from research_engine import ResearchEngine, ResearchScheduler

class ResearchTab:
    """Research tab for the main application"""
    
    def __init__(self, parent_frame, db_manager: DatabaseManager, api_keys: Dict[str, str] = None):
        self.parent = parent_frame
        self.db = db_manager
        
        # Initialize research components
        self.research_engine = ResearchEngine(self.db, api_keys)
        self.scheduler = ResearchScheduler(self.research_engine)
        
        # GUI state
        self.current_session = None
        self.research_thread = None
        self.auto_refresh = True
        
        # Setup callbacks
        self.research_engine.set_progress_callback(self.update_progress)
        self.research_engine.set_status_callback(self.update_status)
        
        # Create UI
        self.setup_ui()
        
        # Load initial data
        self.refresh_data()
        
        # Start scheduler
        self.scheduler.start_scheduler()
    
    def setup_ui(self):
        """Setup the research tab UI"""
        # Main container with padding
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="AI Content Research Dashboard", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(side='left')
        
        # Status label
        self.status_label = ttk.Label(title_frame, text="Ready", 
                                     font=('Arial', 10), foreground='green')
        self.status_label.pack(side='right')
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.setup_dashboard_tab()
        self.setup_trends_tab()
        self.setup_sessions_tab()
        self.setup_settings_tab()
        
        # Control panel at bottom
        self.setup_control_panel(main_frame)
    
    def setup_dashboard_tab(self):
        """Setup main dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text='Dashboard')
        
        # Quick stats frame
        stats_frame = ttk.LabelFrame(dashboard_frame, text="Research Overview", padding="10")
        stats_frame.pack(fill='x', pady=(0, 10))
        
        # Stats grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x')
        
        # Stat boxes
        self.stat_vars = {
            'today_sessions': tk.StringVar(value="0"),
            'trending_keywords': tk.StringVar(value="0"),
            'generated_prompts': tk.StringVar(value="0"),
            'last_research': tk.StringVar(value="Never")
        }
        
        stat_labels = [
            ("Today's Sessions", self.stat_vars['today_sessions']),
            ("Trending Keywords", self.stat_vars['trending_keywords']),
            ("Generated Prompts", self.stat_vars['generated_prompts']),
            ("Last Research", self.stat_vars['last_research'])
        ]
        
        for i, (label_text, var) in enumerate(stat_labels):
            col = i % 2
            row = i // 2
            
            stat_frame = ttk.Frame(stats_grid)
            stat_frame.grid(row=row, column=col, padx=10, pady=5, sticky='w')
            
            ttk.Label(stat_frame, text=label_text, font=('Arial', 10, 'bold')).pack()
            ttk.Label(stat_frame, textvariable=var, font=('Arial', 12)).pack()
        
        # Progress bar
        progress_frame = ttk.LabelFrame(dashboard_frame, text="Research Progress", padding="10")
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to start research")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill='x', pady=(5, 0))
        
        # Recent trends display
        trends_frame = ttk.LabelFrame(dashboard_frame, text="Top Trending Topics", padding="10")
        trends_frame.pack(fill='both', expand=True)
        
        # Trends treeview
        trends_columns = ('Keyword', 'Category', 'Trend Score', 'Platforms', 'Engagement')
        self.trends_tree = ttk.Treeview(trends_frame, columns=trends_columns, show='tree headings', height=8)
        
        # Configure columns
        self.trends_tree.column('#0', width=0, stretch=False)
        for col in trends_columns:
            self.trends_tree.heading(col, text=col)
            if col == 'Keyword':
                self.trends_tree.column(col, width=120)
            elif col == 'Category':
                self.trends_tree.column(col, width=100)
            elif col == 'Trend Score':
                self.trends_tree.column(col, width=80, anchor='center')
            elif col == 'Platforms':
                self.trends_tree.column(col, width=100, anchor='center')
            elif col == 'Engagement':
                self.trends_tree.column(col, width=80, anchor='center')
        
        # Scrollbar for trends
        trends_scroll = ttk.Scrollbar(trends_frame, orient='vertical', command=self.trends_tree.yview)
        self.trends_tree.configure(yscrollcommand=trends_scroll.set)
        
        self.trends_tree.pack(side='left', fill='both', expand=True)
        trends_scroll.pack(side='right', fill='y')
    
    def setup_trends_tab(self):
        """Setup detailed trends analysis tab"""
        trends_frame = ttk.Frame(self.notebook)
        self.notebook.add(trends_frame, text='Trend Analysis')
        
        # Filter frame
        filter_frame = ttk.Frame(trends_frame)
        filter_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Category:").pack(side='left', padx=(0, 5))
        self.category_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, 
                                     values=["All", "ai-comedy", "ai-drama", "ai-showcase", "ai-tutorial"],
                                     state='readonly', width=15)
        category_combo.pack(side='left', padx=(0, 10))
        category_combo.bind('<<ComboboxSelected>>', self.filter_trends)
        
        ttk.Button(filter_frame, text="Refresh", command=self.refresh_trends).pack(side='left', padx=(0, 10))
        ttk.Button(filter_frame, text="Export Data", command=self.export_trends).pack(side='left')
        
        # Detailed trends table
        detailed_columns = ('Keyword', 'Category', 'Score', 'Growth', 'Occurrences', 'Avg Engagement', 'Platforms', 'Last Seen')
        self.detailed_tree = ttk.Treeview(trends_frame, columns=detailed_columns, show='tree headings')
        
        # Configure detailed columns
        self.detailed_tree.column('#0', width=0, stretch=False)
        for i, col in enumerate(detailed_columns):
            self.detailed_tree.heading(col, text=col)
            width = [100, 90, 60, 60, 80, 90, 80, 100][i]
            anchor = 'center' if i in [2, 3, 4, 5, 6] else 'w'
            self.detailed_tree.column(col, width=width, anchor=anchor)
        
        # Scrollbars for detailed trends
        detailed_v_scroll = ttk.Scrollbar(trends_frame, orient='vertical', command=self.detailed_tree.yview)
        detailed_h_scroll = ttk.Scrollbar(trends_frame, orient='horizontal', command=self.detailed_tree.xview)
        self.detailed_tree.configure(yscrollcommand=detailed_v_scroll.set, xscrollcommand=detailed_h_scroll.set)
        
        self.detailed_tree.pack(side='left', fill='both', expand=True)
        detailed_v_scroll.pack(side='right', fill='y')
        detailed_h_scroll.pack(side='bottom', fill='x')
        
        # Bind double-click to show content samples
        self.detailed_tree.bind('<Double-1>', self.show_trend_details)
    
    def setup_sessions_tab(self):
        """Setup research sessions history tab"""
        sessions_frame = ttk.Frame(self.notebook)
        self.notebook.add(sessions_frame, text='Research Sessions')
        
        # Sessions controls
        controls_frame = ttk.Frame(sessions_frame)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(controls_frame, text="View Session Details", 
                  command=self.view_session_details).pack(side='left', padx=(0, 5))
        ttk.Button(controls_frame, text="Delete Old Sessions", 
                  command=self.cleanup_old_sessions).pack(side='left', padx=(0, 5))
        ttk.Button(controls_frame, text="Export Session Data", 
                  command=self.export_session_data).pack(side='left')
        
        # Sessions table
        session_columns = ('Date', 'Status', 'Platforms', 'Content Found', 'AI Content', 'Keywords', 'Duration')
        self.sessions_tree = ttk.Treeview(sessions_frame, columns=session_columns, show='tree headings')
        
        # Configure session columns
        self.sessions_tree.column('#0', width=0, stretch=False)
        for i, col in enumerate(session_columns):
            self.sessions_tree.heading(col, text=col)
            width = [80, 70, 80, 80, 70, 60, 70][i]
            anchor = 'center' if i in [1, 3, 4, 5, 6] else 'w'
            self.sessions_tree.column(col, width=width, anchor=anchor)
        
        # Session scrollbars
        session_v_scroll = ttk.Scrollbar(sessions_frame, orient='vertical', command=self.sessions_tree.yview)
        session_h_scroll = ttk.Scrollbar(sessions_frame, orient='horizontal', command=self.sessions_tree.xview)
        self.sessions_tree.configure(yscrollcommand=session_v_scroll.set, xscrollcommand=session_h_scroll.set)
        
        self.sessions_tree.pack(side='left', fill='both', expand=True)
        session_v_scroll.pack(side='right', fill='y')
        session_h_scroll.pack(side='bottom', fill='x')
    
    def setup_settings_tab(self):
        """Setup research settings and configuration tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text='Settings')
        
        # API Configuration
        api_frame = ttk.LabelFrame(settings_frame, text="API Configuration", padding="10")
        api_frame.pack(fill='x', pady=(0, 10))
        
        # API key fields
        self.api_keys = {
            'tiktok': tk.StringVar(),
            'instagram': tk.StringVar(),
            'youtube': tk.StringVar()
        }
        
        api_labels = ["TikTok Research API Key:", "Instagram Access Token:", "YouTube API Key:"]
        for i, (platform, var) in enumerate(self.api_keys.items()):
            ttk.Label(api_frame, text=api_labels[i]).grid(row=i, column=0, sticky='w', pady=2, padx=(0, 5))
            entry = ttk.Entry(api_frame, textvariable=var, width=40, show='*')
            entry.grid(row=i, column=1, sticky='ew', pady=2, padx=(0, 5))
            ttk.Button(api_frame, text="Test", 
                      command=lambda p=platform: self.test_api_connection(p)).grid(row=i, column=2, pady=2)
        
        api_frame.columnconfigure(1, weight=1)
        
        ttk.Button(api_frame, text="Save API Keys", command=self.save_api_keys).grid(row=3, column=0, pady=10)
        ttk.Button(api_frame, text="Test All Connections", command=self.test_all_connections).grid(row=3, column=1, pady=10)
        
        # Research Settings
        research_settings_frame = ttk.LabelFrame(settings_frame, text="Research Settings", padding="10")
        research_settings_frame.pack(fill='x', pady=(0, 10))
        
        # Platform toggles
        ttk.Label(research_settings_frame, text="Enabled Platforms:", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 5))
        
        self.platform_vars = {
            'tiktok': tk.BooleanVar(value=True),
            'instagram': tk.BooleanVar(value=True),
            'youtube': tk.BooleanVar(value=True)
        }
        
        for i, (platform, var) in enumerate(self.platform_vars.items()):
            ttk.Checkbutton(research_settings_frame, text=platform.title(), 
                           variable=var).grid(row=1, column=i, sticky='w', padx=(0, 20))
        
        # Research parameters
        ttk.Label(research_settings_frame, text="Max Content per Platform:").grid(row=2, column=0, sticky='w', pady=(10, 0))
        self.max_content_var = tk.StringVar(value="50")
        ttk.Spinbox(research_settings_frame, from_=10, to=200, textvariable=self.max_content_var, width=10).grid(row=2, column=1, sticky='w', pady=(10, 0))
        
        ttk.Label(research_settings_frame, text="Min Engagement Rate:").grid(row=3, column=0, sticky='w', pady=(5, 0))
        self.min_engagement_var = tk.StringVar(value="0.02")
        ttk.Entry(research_settings_frame, textvariable=self.min_engagement_var, width=10).grid(row=3, column=1, sticky='w', pady=(5, 0))
        
        # Scheduler Settings
        scheduler_frame = ttk.LabelFrame(settings_frame, text="Automatic Research Scheduler", padding="10")
        scheduler_frame.pack(fill='x', pady=(0, 10))
        
        self.scheduler_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(scheduler_frame, text="Enable daily automatic research", 
                       variable=self.scheduler_enabled_var, 
                       command=self.update_scheduler_settings).pack(anchor='w')
        
        schedule_time_frame = ttk.Frame(scheduler_frame)
        schedule_time_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(schedule_time_frame, text="Daily run time:").pack(side='left')
        self.schedule_time_var = tk.StringVar(value="09:00")
        time_entry = ttk.Entry(schedule_time_frame, textvariable=self.schedule_time_var, width=10)
        time_entry.pack(side='left', padx=(5, 10))
        ttk.Label(schedule_time_frame, text="(24-hour format, e.g., 09:00)").pack(side='left')
        
        # Log display
        log_frame = ttk.LabelFrame(settings_frame, text="Research Log", padding="10")
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True)
    
    def setup_control_panel(self, parent):
        """Setup control panel with main action buttons"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', pady=(10, 0))
        
        # Main action buttons
        ttk.Button(control_frame, text="Start Research Now", 
                  command=self.start_manual_research, 
                  style='Accent.TButton').pack(side='left', padx=(0, 10))
        
        ttk.Button(control_frame, text="Stop Research", 
                  command=self.stop_research).pack(side='left', padx=(0, 10))
        
        ttk.Button(control_frame, text="Refresh Data", 
                  command=self.refresh_data).pack(side='left', padx=(0, 10))
        
        ttk.Button(control_frame, text="View Generated Prompts", 
                  command=self.view_generated_prompts).pack(side='left', padx=(0, 10))
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Auto-refresh (30s)", 
                       variable=self.auto_refresh_var).pack(side='right')
        
        # Start auto-refresh timer
        self.auto_refresh_timer()
    
    def start_manual_research(self):
        """Start manual research process"""
        if self.research_engine.is_running:
            messagebox.showwarning("Research Running", "Research is already in progress!")
            return
        
        enabled_platforms = [platform for platform, var in self.platform_vars.items() if var.get()]
        
        if not enabled_platforms:
            messagebox.showerror("No Platforms", "Please enable at least one platform for research!")
            return
        
        # Update research settings
        self.research_engine.max_content_per_platform = int(self.max_content_var.get())
        self.research_engine.min_engagement_threshold = float(self.min_engagement_var.get())
        self.research_engine.enabled_platforms = enabled_platforms
        
        # Start research in separate thread
        self.research_thread = threading.Thread(target=self._run_research_thread, daemon=True)
        self.research_thread.start()
        
        self.log_message("Started manual research...")
    
    def _run_research_thread(self):
        """Run research in separate thread"""
        try:
            result = self.research_engine.run_daily_research()
            
            if result.get('success'):
                self.log_message(f"Research completed successfully! Found {result.get('trends_found', 0)} trends, generated {result.get('prompts_generated', 0)} prompts.")
                # Refresh data after completion
                self.parent.after(1000, self.refresh_data)
            else:
                error_msg = result.get('error', 'Unknown error')
                self.log_message(f"Research failed: {error_msg}")
                
        except Exception as e:
            self.log_message(f"Research error: {str(e)}")
    
    def stop_research(self):
        """Stop ongoing research"""
        # This would need to be implemented in the research engine
        self.log_message("Stop research functionality not yet implemented")
    
    def update_progress(self, message: str, progress: float):
        """Update progress display"""
        def update_ui():
            self.progress_var.set(message)
            self.progress_bar['value'] = progress
            self.log_message(f"Progress: {message} ({progress:.1f}%)")
        
        self.parent.after(0, update_ui)
    
    def update_status(self, status: str):
        """Update status display"""
        def update_ui():
            self.status_label.config(text=status)
            color = 'green' if 'completed' in status.lower() else 'orange' if 'running' in status.lower() else 'red'
            self.status_label.config(foreground=color)
        
        self.parent.after(0, update_ui)
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        try:
            # Update stats
            self.update_dashboard_stats()
            
            # Update trends
            self.refresh_trends()
            
            # Update sessions
            self.refresh_sessions()
            
            self.log_message("Dashboard refreshed")
            
        except Exception as e:
            self.log_message(f"Error refreshing data: {e}")
    
    def update_dashboard_stats(self):
        """Update dashboard statistics"""
        try:
            # Today's sessions
            today = date.today()
            sessions = self.db.get_research_sessions(10)
            today_sessions = len([s for s in sessions if s['date'] == str(today)])
            self.stat_vars['today_sessions'].set(str(today_sessions))
            
            # Trending keywords
            trends = self.db.get_trending_summary(100)
            self.stat_vars['trending_keywords'].set(str(len(trends)))
            
            # Generated prompts
            prompts = self.db.get_research_prompts(limit=1000)
            self.stat_vars['generated_prompts'].set(str(len(prompts)))
            
            # Last research
            if sessions:
                last_date = sessions[0]['date']
                self.stat_vars['last_research'].set(last_date)
            else:
                self.stat_vars['last_research'].set("Never")
            
        except Exception as e:
            self.log_message(f"Error updating stats: {e}")
    
    def refresh_trends(self):
        """Refresh trends display"""
        try:
            # Clear existing items
            for item in self.trends_tree.get_children():
                self.trends_tree.delete(item)
            
            for item in self.detailed_tree.get_children():
                self.detailed_tree.delete(item)
            
            # Get trends data
            trends = self.db.get_trending_summary(20)
            
            for trend in trends:
                # Dashboard trends tree
                platforms_str = ', '.join(json.loads(trend.get('platforms', '[]')))[:15] + '...' if len(json.loads(trend.get('platforms', '[]'))) > 2 else ', '.join(json.loads(trend.get('platforms', '[]')))
                
                self.trends_tree.insert('', 'end', values=(
                    trend['keyword'][:20],
                    trend['category'],
                    f"{trend['trend_score']:.2f}",
                    platforms_str,
                    f"{trend.get('avg_engagement', 0):.3f}"
                ))
                
                # Detailed trends tree
                self.detailed_tree.insert('', 'end', values=(
                    trend['keyword'],
                    trend['category'],
                    f"{trend['trend_score']:.2f}",
                    f"{trend.get('growth_rate', 0):.1f}%",
                    trend.get('content_count', 0),
                    f"{trend.get('avg_engagement', 0):.3f}",
                    platforms_str,
                    trend.get('last_seen', 'Unknown')[:10] if trend.get('last_seen') else 'Unknown'
                ))
            
        except Exception as e:
            self.log_message(f"Error refreshing trends: {e}")
    
    def refresh_sessions(self):
        """Refresh sessions display"""
        try:
            # Clear existing items
            for item in self.sessions_tree.get_children():
                self.sessions_tree.delete(item)
            
            # Get sessions data
            sessions = self.db.get_research_sessions(20)
            
            for session in sessions:
                platforms = json.loads(session.get('platforms_scraped', '[]'))
                platforms_str = ', '.join(platforms)
                
                # Calculate duration (simplified)
                duration = "N/A"
                if session.get('completed_at') and session.get('created_at'):
                    try:
                        start = datetime.fromisoformat(session['created_at'])
                        end = datetime.fromisoformat(session['completed_at'])
                        duration_sec = (end - start).total_seconds()
                        duration = f"{duration_sec/60:.1f}m" if duration_sec < 3600 else f"{duration_sec/3600:.1f}h"
                    except:
                        pass
                
                self.sessions_tree.insert('', 'end', values=(
                    session['date'],
                    session['status'].title(),
                    platforms_str,
                    session.get('total_content_found', 0),
                    session.get('ai_content_found', 0),
                    len(json.loads(session.get('trending_keywords', '[]'))),
                    duration
                ))
            
        except Exception as e:
            self.log_message(f"Error refreshing sessions: {e}")
    
    def filter_trends(self, event=None):
        """Filter trends by category"""
        # This would implement category filtering
        self.refresh_trends()
    
    def export_trends(self):
        """Export trends data"""
        messagebox.showinfo("Export", "Trends export functionality would be implemented here")
    
    def show_trend_details(self, event):
        """Show detailed information about a trend"""
        selection = self.detailed_tree.selection()
        if not selection:
            return
        
        item = self.detailed_tree.item(selection[0])
        keyword = item['values'][0]
        
        # Create details window
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Trend Details: {keyword}")
        details_window.geometry("600x400")
        
        # Add details content (simplified)
        ttk.Label(details_window, text=f"Keyword: {keyword}", font=('Arial', 12, 'bold')).pack(pady=10)
        ttk.Label(details_window, text="Sample content and detailed analysis would be shown here").pack(pady=20)
        
        ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)
    
    def view_session_details(self):
        """View detailed session information"""
        selection = self.sessions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a research session to view details.")
            return
        
        item = self.sessions_tree.item(selection[0])
        session_date = item['values'][0]
        
        messagebox.showinfo("Session Details", f"Detailed session view for {session_date} would be implemented here")
    
    def cleanup_old_sessions(self):
        """Clean up old research sessions"""
        if messagebox.askyesno("Cleanup Confirmation", "Delete research sessions older than 30 days?"):
            try:
                self.db.cleanup_old_research_data(30)
                self.refresh_data()
                self.log_message("Old research data cleaned up")
                messagebox.showinfo("Success", "Old research sessions have been cleaned up.")
            except Exception as e:
                messagebox.showerror("Error", f"Error cleaning up data: {e}")
    
    def export_session_data(self):
        """Export session data"""
        messagebox.showinfo("Export", "Session data export functionality would be implemented here")
    
    def test_api_connection(self, platform):
        """Test connection to specific platform API"""
        self.log_message(f"Testing {platform} API connection...")
        # This would test the actual API connection
        messagebox.showinfo("API Test", f"API test for {platform} would be implemented here")
    
    def test_all_connections(self):
        """Test all API connections"""
        self.log_message("Testing all API connections...")
        try:
            results = self.research_engine.test_api_connections()
            
            message = "API Connection Test Results:\\n"
            for platform, status in results.items():
                status_text = "✓ Connected" if status else "✗ Failed"
                message += f"{platform.title()}: {status_text}\\n"
            
            messagebox.showinfo("Connection Test", message)
            self.log_message("API connection test completed")
            
        except Exception as e:
            messagebox.showerror("Test Error", f"Error testing connections: {e}")
    
    def save_api_keys(self):
        """Save API keys (in a real implementation, these would be encrypted)"""
        self.log_message("API keys saving functionality would be implemented here")
        messagebox.showinfo("Save Keys", "API keys would be saved securely here")
    
    def update_scheduler_settings(self):
        """Update scheduler settings"""
        enabled = self.scheduler_enabled_var.get()
        time_str = self.schedule_time_var.get()
        
        try:
            self.scheduler.set_schedule(enabled, time_str)
            self.log_message(f"Scheduler {'enabled' if enabled else 'disabled'} for {time_str}")
        except Exception as e:
            self.log_message(f"Error updating scheduler: {e}")
    
    def view_generated_prompts(self):
        """View prompts generated from research"""
        prompts_window = tk.Toplevel(self.parent)
        prompts_window.title("Generated Story Prompts")
        prompts_window.geometry("800x600")
        
        # Prompts frame
        prompts_frame = ttk.Frame(prompts_window, padding="10")
        prompts_frame.pack(fill='both', expand=True)
        
        # Filter frame
        filter_frame = ttk.Frame(prompts_frame)
        filter_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Genre:").pack(side='left', padx=(0, 5))
        genre_var = tk.StringVar(value="All")
        genre_combo = ttk.Combobox(filter_frame, textvariable=genre_var, 
                                  values=["All", "Comedy", "Drama", "Sci-Fi", "Thriller", "Horror"],
                                  state='readonly')
        genre_combo.pack(side='left')
        
        # Prompts table
        prompt_columns = ('Prompt', 'Genre', 'Source Keyword', 'Expected Performance', 'Usage Count', 'Success Rate')
        prompts_tree = ttk.Treeview(prompts_frame, columns=prompt_columns, show='tree headings')
        
        # Configure columns
        prompts_tree.column('#0', width=0, stretch=False)
        for i, col in enumerate(prompt_columns):
            prompts_tree.heading(col, text=col)
            width = [300, 80, 120, 100, 80, 80][i]
            prompts_tree.column(col, width=width)
        
        # Load prompts
        try:
            prompts = self.db.get_research_prompts(limit=50)
            for prompt in prompts:
                prompts_tree.insert('', 'end', values=(
                    prompt['prompt'][:100] + '...' if len(prompt['prompt']) > 100 else prompt['prompt'],
                    prompt.get('genre', 'Unknown'),
                    prompt.get('source_keyword', 'N/A'),
                    f"{prompt.get('expected_performance', 0):.2f}",
                    prompt.get('usage_count', 0),
                    f"{prompt.get('success_rate', 0):.1%}"
                ))
        except Exception as e:
            self.log_message(f"Error loading prompts: {e}")
        
        # Scrollbar
        prompt_scroll = ttk.Scrollbar(prompts_frame, orient='vertical', command=prompts_tree.yview)
        prompts_tree.configure(yscrollcommand=prompt_scroll.set)
        
        prompts_tree.pack(side='left', fill='both', expand=True)
        prompt_scroll.pack(side='right', fill='y')
        
        # Close button
        ttk.Button(prompts_frame, text="Close", command=prompts_window.destroy).pack(pady=(10, 0))
    
    def log_message(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\\n"
        
        try:
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
        except:
            # Handle case where log_text doesn't exist yet
            print(log_entry.strip())
    
    def auto_refresh_timer(self):
        """Auto-refresh timer"""
        if self.auto_refresh_var.get() and not self.research_engine.is_running:
            self.update_dashboard_stats()
        
        # Schedule next refresh in 30 seconds
        self.parent.after(30000, self.auto_refresh_timer)