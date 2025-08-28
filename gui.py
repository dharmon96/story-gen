"""
GUI Application for Film Generator
Complete UI with all requested features
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import json
import time
import random
from datetime import datetime
from typing import List, Dict

from config import APP_SETTINGS, GENERATION_SETTINGS, OLLAMA_CONFIG, SYSTEM_PROMPTS, STORY_PROMPTS, VISUAL_STYLES, GENRE_STYLE_MAPPINGS, RENDER_SETTINGS
from data_models import StoryConfig, Shot
from database import DatabaseManager
from ollama_manager import OllamaManager
from story_generator import StoryGenerator
from generation_progress_popup import GenerationProgressWindow, EnhancedGenerationManager
from model_selection_dialog import ModelSelectionDialog
from research_tab import ResearchTab
from settings_dialog import SettingsDialog

class FilmGeneratorApp:
    """Main GUI Application Class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(APP_SETTINGS['window_title'])
        self.root.geometry(APP_SETTINGS['window_size'])
        
        # Initialize components
        self.db = DatabaseManager()
        self.ollama = OllamaManager()
        self.story_gen = StoryGenerator(self.ollama, self.db)
        
        # Queue for thread communication
        self.log_queue = queue.Queue()
        
        # Generation state
        self.is_generating = False
        self.continuous_mode = False
        self.current_story = None
        self.current_shots = []
        self.manual_generation = False
        
        # Background workers
        self.render_worker_active = False
        
        # Setup UI
        self.setup_ui()
        
        # Initialize with random values
        self.randomize_inputs()
        
        # Start background workers
        self.start_background_workers()
        
        # Load initial data
        self.load_initial_data()

        self.enhanced_generator = None
        self.progress_window = None
    
    def setup_ui(self):
        """Setup main UI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.story_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)
        self.metrics_tab = ttk.Frame(self.notebook)
        self.queue_tab = ttk.Frame(self.notebook)
        self.research_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.story_tab, text='Story Generator')
        self.notebook.add(self.research_tab, text='Research')
        self.notebook.add(self.logs_tab, text='Logs')
        self.notebook.add(self.metrics_tab, text='Metrics')
        self.notebook.add(self.queue_tab, text='Render Queue')
        self.notebook.add(self.settings_tab, text='Settings')
        
        # Setup each tab
        self.setup_story_tab()
        self.setup_research_tab()
        self.setup_logs_tab()
        self.setup_metrics_tab()
        self.setup_queue_tab()
        self.setup_settings_tab()
    
    def setup_story_tab(self):
        """Setup story generation tab with model selector"""
        main_frame = ttk.Frame(self.story_tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Story Configuration", 
                                font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # AI Status Frame - ENHANCED with multi-network model selector
        ai_frame = ttk.LabelFrame(main_frame, text="AI Configuration", padding="10")
        ai_frame.pack(fill='x', pady=(0, 10))
        
        # Top row - Status and discovery
        status_row = ttk.Frame(ai_frame)
        status_row.pack(fill='x', pady=(0, 10))
        
        # Status display
        instances = self.ollama.get_available_instances()
        total_models = sum(len(inst.get('models', [])) for inst in instances.values())
        
        if self.ollama.available and instances:
            ai_status_text = f"Connected - {len(instances)} instances, {total_models} models"
            ai_color = "green"
        elif self.ollama.available:
            ai_status_text = "Connected - No instances found"
            ai_color = "orange"  
        else:
            ai_status_text = "Simulation Mode"
            ai_color = "red"
        
        self.ai_status_label = ttk.Label(status_row, 
                                        text=f"Status: {ai_status_text}",
                                        foreground=ai_color)
        self.ai_status_label.pack(side='left', padx=10)
        
        # Control buttons
        ttk.Button(status_row, text="🔍 Network Scan", 
                command=self.scan_network_instances).pack(side='right', padx=2)
        ttk.Button(status_row, text="🔄 Refresh", 
                command=self.refresh_all_connections).pack(side='right', padx=2)
        ttk.Button(status_row, text="🔧 Configure Models", 
                command=self.open_model_dialog, style='Accent.TButton').pack(side='right', padx=2)
        
        # Current assignments display
        assignments_row = ttk.Frame(ai_frame)
        assignments_row.pack(fill='x', pady=(5, 0))
        
        ttk.Label(assignments_row, text="Model Assignments:", 
                 font=('Arial', 9, 'bold')).pack(side='left')
        
        self.assignments_display = ttk.Label(assignments_row, text="Not configured", 
                                           font=('Arial', 8), foreground='gray')
        self.assignments_display.pack(side='left', padx=(10, 0))
        
        # Update assignments display
        self.update_assignments_display()
        
        # Legacy model selection (for backward compatibility)
        legacy_row = ttk.Frame(ai_frame)
        legacy_row.pack(fill='x', pady=(10, 0))
        
        ttk.Label(legacy_row, text="Quick Select:", width=15).pack(side='left')
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(legacy_row, textvariable=self.model_var,
                                        width=30, state='readonly')
        self.model_combo.pack(side='left', padx=5)
        self.model_combo.bind('<<ComboboxSelected>>', self.on_legacy_model_selected)
        
        # Initialize model dropdown
        self.refresh_model_list()
        
        # Info label
        if not self.ollama.available:
            ttk.Label(ai_frame, text="Install ollama and run 'ollama serve' to enable AI", 
                    font=('Arial', 9, 'italic')).pack(pady=5)
        else:
            ttk.Label(ai_frame, text="Use 'Configure Models' for per-step assignments or 'Quick Select' for all steps", 
                    font=('Arial', 8, 'italic')).pack(pady=(5, 0))
        
        # Rest of existing setup_story_tab code...
        # (Progress Frame, Configuration frame, etc. - keep all existing code)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(main_frame, text="Generation Progress", padding="10")
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=600)
        self.progress_bar.pack(fill='x', pady=(0, 5))
        
        self.progress_text = ttk.Label(progress_frame, text="Ready to generate stories...", 
                                      font=('Arial', 9, 'italic'))
        self.progress_text.pack()
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="15")
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Story Prompt
        prompt_frame = ttk.Frame(config_frame)
        prompt_frame.pack(fill='x', pady=5)
        
        ttk.Label(prompt_frame, text="Story Prompt:", width=15).pack(side='left')
        self.prompt_entry = ttk.Entry(prompt_frame, width=50)
        self.prompt_entry.pack(side='left', padx=5)
        
        self.auto_prompt_var = tk.BooleanVar()
        ttk.Checkbutton(prompt_frame, text="Auto", 
                       variable=self.auto_prompt_var).pack(side='left', padx=10)
        
        # Genre
        genre_frame = ttk.Frame(config_frame)
        genre_frame.pack(fill='x', pady=5)
        
        ttk.Label(genre_frame, text="Genre:", width=15).pack(side='left')
        self.genre_var = tk.StringVar()
        self.genre_combo = ttk.Combobox(genre_frame, textvariable=self.genre_var, 
                                        width=47, state='readonly')
        self.genre_combo['values'] = GENERATION_SETTINGS['genres']
        self.genre_combo.pack(side='left', padx=5)
        
        # Bind genre selection to update style suggestions
        self.genre_combo.bind('<<ComboboxSelected>>', self.on_genre_selected)
        
        self.auto_genre_var = tk.BooleanVar()
        ttk.Checkbutton(genre_frame, text="Auto", 
                       variable=self.auto_genre_var).pack(side='left', padx=10)
        
        # Length
        length_frame = ttk.Frame(config_frame)
        length_frame.pack(fill='x', pady=5)
        
        ttk.Label(length_frame, text="Total Length:", width=15).pack(side='left')
        self.length_var = tk.StringVar()
        self.length_combo = ttk.Combobox(length_frame, textvariable=self.length_var,
                                         width=47, state='readonly')
        self.length_combo['values'] = GENERATION_SETTINGS['lengths']
        self.length_combo.pack(side='left', padx=5)
        
        self.auto_length_var = tk.BooleanVar()
        ttk.Checkbutton(length_frame, text="Auto", 
                       variable=self.auto_length_var).pack(side='left', padx=10)
        
        # Visual Style
        style_frame = ttk.Frame(config_frame)
        style_frame.pack(fill='x', pady=5)
        
        ttk.Label(style_frame, text="Visual Style:", width=15).pack(side='left')
        self.style_var = tk.StringVar()
        self.style_combo = ttk.Combobox(style_frame, textvariable=self.style_var,
                                        width=47, state='readonly')
        from config import VISUAL_STYLES
        self.style_combo['values'] = list(VISUAL_STYLES.keys())
        self.style_combo.pack(side='left', padx=5)
        
        # Bind selection event to show style description
        self.style_combo.bind('<<ComboboxSelected>>', self.on_style_selected)
        
        self.auto_style_var = tk.BooleanVar()
        ttk.Checkbutton(style_frame, text="Auto", 
                       variable=self.auto_style_var).pack(side='left', padx=10)
        
        # Style description label
        self.style_description_label = ttk.Label(config_frame, text="", 
                                                font=('Arial', 8, 'italic'), 
                                                foreground='gray')
        self.style_description_label.pack(pady=(0, 5))
        
        # Render Settings Frame
        render_frame = ttk.LabelFrame(config_frame, text="Render Settings", padding="10")
        render_frame.pack(fill='x', pady=(10, 5))
        
        # Aspect Ratio
        aspect_frame = ttk.Frame(render_frame)
        aspect_frame.pack(fill='x', pady=5)
        
        ttk.Label(aspect_frame, text="Aspect Ratio:", width=15).pack(side='left')
        self.aspect_ratio_var = tk.StringVar()
        self.aspect_ratio_combo = ttk.Combobox(aspect_frame, textvariable=self.aspect_ratio_var,
                                               width=25, state='readonly')
        from config import RENDER_SETTINGS
        self.aspect_ratio_combo['values'] = [RENDER_SETTINGS['aspect_ratios'][key]['name'] 
                                            for key in RENDER_SETTINGS['aspect_ratios']]
        self.aspect_ratio_combo.pack(side='left', padx=5)
        
        # Set default aspect ratio
        default_aspect = RENDER_SETTINGS['defaults']['aspect_ratio']
        default_name = RENDER_SETTINGS['aspect_ratios'][default_aspect]['name']
        self.aspect_ratio_var.set(default_name)
        
        # FPS
        fps_frame = ttk.Frame(render_frame)  
        fps_frame.pack(fill='x', pady=5)
        
        ttk.Label(fps_frame, text="Frame Rate:", width=15).pack(side='left')
        self.fps_var = tk.StringVar()
        self.fps_combo = ttk.Combobox(fps_frame, textvariable=self.fps_var,
                                      width=25, state='readonly')
        self.fps_combo['values'] = [RENDER_SETTINGS['fps_options'][key]['name'] 
                                   for key in RENDER_SETTINGS['fps_options']]
        self.fps_combo.pack(side='left', padx=5)
        
        # Set default FPS
        default_fps = RENDER_SETTINGS['defaults']['fps']
        default_fps_name = RENDER_SETTINGS['fps_options'][default_fps]['name']
        self.fps_var.set(default_fps_name)
        
        # Generation Options
        options_frame = ttk.LabelFrame(main_frame, text="Generation Options", padding="15")
        options_frame.pack(fill='x', pady=(0, 10))
        
        self.continuous_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Continuous Generation Mode", 
                       variable=self.continuous_var).pack(anchor='w')
        
        ttk.Label(options_frame, text="(When enabled, will continuously generate stories based on metrics)",
                 font=('Arial', 9, 'italic')).pack(anchor='w')
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        self.run_button = ttk.Button(button_frame, text="▶ Run Generation", 
                                     command=self.start_generation,
                                     style='Accent.TButton')
        self.run_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="■ Stop", 
                                      command=self.stop_generation,
                                      state='disabled')
        self.stop_button.pack(side='left')
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Status: Ready", 
                                      font=('Arial', 10))
        self.status_label.pack(pady=5)
        
        # Recent Stories
        recent_frame = ttk.LabelFrame(main_frame, text="Recent Stories", padding="10")
        recent_frame.pack(fill='both', expand=True)
        
        columns = ('ID', 'Title', 'Genre', 'Status', 'Created')
        self.stories_tree = ttk.Treeview(recent_frame, columns=columns, 
                                         show='tree headings', height=6)
        
        for col in columns:
            self.stories_tree.heading(col, text=col)
            self.stories_tree.column(col, width=150)
        
        self.stories_tree.column('#0', width=0, stretch=False)
        self.stories_tree.column('ID', width=100)
        
        scrollbar = ttk.Scrollbar(recent_frame, orient='vertical', 
                                 command=self.stories_tree.yview)
        self.stories_tree.configure(yscrollcommand=scrollbar.set)
        
        self.stories_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Current Story Display
        story_display_frame = ttk.LabelFrame(main_frame, text="Current Story", padding="10")
        story_display_frame.pack(fill='both', expand=True)
        
        export_frame = ttk.Frame(story_display_frame)
        export_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Button(export_frame, text="Export Story & Shots", 
                  command=self.export_current_story).pack(side='right')
        
        self.story_display = scrolledtext.ScrolledText(story_display_frame, 
                                                       height=8, wrap='word')
        self.story_display.pack(fill='both', expand=True)
    
    def setup_research_tab(self):
        """Setup research tab"""
        # Initialize research tab with API keys (empty for now)
        api_keys = {}  # In a real implementation, these would be loaded from secure storage
        self.research_tab_instance = ResearchTab(self.research_tab, self.db, api_keys)
    
    def setup_logs_tab(self):
        """Setup logs tab"""
        main_frame = ttk.Frame(self.logs_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        title_label = ttk.Label(main_frame, text="System Logs", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter:").pack(side='left', padx=5)
        
        self.log_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.log_filter_var,
                                    width=20, state='readonly')
        filter_combo['values'] = ('All', 'AI', 'Rendering', 'Upload', 'Database', 'Error', 'Info')
        filter_combo.pack(side='left')
        
        ttk.Button(filter_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side='right', padx=5)
        
        ttk.Button(filter_frame, text="Export Logs", 
                  command=self.export_logs).pack(side='right', padx=5)
        
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill='both', expand=True)
        
        self.log_display = scrolledtext.ScrolledText(log_frame, height=25, wrap='word',
                                                     bg='#1e1e1e', fg='#00ff00',
                                                     font=('Consolas', 9))
        self.log_display.pack(fill='both', expand=True)
        
        self.log_display.tag_config('AI', foreground='#00ffff')
        self.log_display.tag_config('Rendering', foreground='#ffff00')
        self.log_display.tag_config('Upload', foreground='#00ff00')
        self.log_display.tag_config('Database', foreground='#ff00ff')
        self.log_display.tag_config('Error', foreground='#ff0000')
        self.log_display.tag_config('Info', foreground='#ffffff')
    
    def setup_metrics_tab(self):
        """Setup metrics tab with delete functionality"""
        main_frame = ttk.Frame(self.metrics_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        title_label = ttk.Label(main_frame, text="Performance Metrics", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        stats_frame = ttk.LabelFrame(main_frame, text="Summary Statistics", padding="10")
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack()
        
        self.total_stories_label = ttk.Label(stats_grid, text="Total Stories: 0")
        self.total_stories_label.grid(row=0, column=0, padx=20, pady=5, sticky='w')
        
        self.total_views_label = ttk.Label(stats_grid, text="Total Views: 0")
        self.total_views_label.grid(row=0, column=1, padx=20, pady=5, sticky='w')
        
        self.avg_engagement_label = ttk.Label(stats_grid, text="Avg Engagement: 0%")
        self.avg_engagement_label.grid(row=0, column=2, padx=20, pady=5, sticky='w')
        
        self.best_genre_label = ttk.Label(stats_grid, text="Best Genre: N/A")
        self.best_genre_label.grid(row=1, column=0, padx=20, pady=5, sticky='w')
        
        self.best_length_label = ttk.Label(stats_grid, text="Optimal Length: N/A")
        self.best_length_label.grid(row=1, column=1, padx=20, pady=5, sticky='w')
        
        self.completion_rate_label = ttk.Label(stats_grid, text="Avg Completion: 0%")
        self.completion_rate_label.grid(row=1, column=2, padx=20, pady=5, sticky='w')
        
        table_frame = ttk.LabelFrame(main_frame, text="Story Performance", padding="10")
        table_frame.pack(fill='both', expand=True)
        
        table_container = ttk.Frame(table_frame)
        table_container.pack(fill='both', expand=True)
        
        columns = ('Story ID', 'Title', 'Genre', 'Parts', 'Views', 'Engagement', 'Completion', 'Status', 'Delete')
        self.metrics_tree = ttk.Treeview(table_container, columns=columns, show='tree headings')
        
        for col in columns:
            if col == 'Delete':
                self.metrics_tree.heading(col, text='')
                self.metrics_tree.column(col, width=60)
            else:
                self.metrics_tree.heading(col, text=col)
                self.metrics_tree.column(col, width=110)
        
        self.metrics_tree.column('#0', width=0, stretch=False)
        self.metrics_tree.column('Story ID', width=100)
        self.metrics_tree.column('Title', width=200)
        
        self.metrics_tree.bind('<ButtonRelease-1>', self.on_metrics_click)
        
        scrollbar = ttk.Scrollbar(table_container, orient='vertical', command=self.metrics_tree.yview)
        self.metrics_tree.configure(yscrollcommand=scrollbar.set)
        
        self.metrics_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=10)
        
        ttk.Button(control_frame, text="Refresh Metrics", 
                  command=self.refresh_metrics).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Simulate Metrics", 
                  command=self.simulate_metrics).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Export Report", 
                  command=self.export_metrics_report).pack(side='left', padx=5)
        
        # Database management
        ttk.Separator(control_frame, orient='vertical').pack(side='left', fill='y', padx=10)
        ttk.Button(control_frame, text="🗑️ Delete Database", 
                  command=self.delete_database_with_backup, 
                  style='Danger.TButton').pack(side='left', padx=5)
    
    def setup_queue_tab(self):
        """Setup render queue tab with clear all functionality"""
        main_frame = ttk.Frame(self.queue_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        title_label = ttk.Label(main_frame, text="Render Queue Monitor", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        stats_frame = ttk.LabelFrame(main_frame, text="Queue Statistics", padding="10")
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack()
        
        self.queue_stats_labels = {
            'queued': ttk.Label(stats_grid, text="Queued: 0"),
            'processing': ttk.Label(stats_grid, text="Processing: 0"),
            'completed': ttk.Label(stats_grid, text="Completed: 0"),
            'failed': ttk.Label(stats_grid, text="Failed: 0")
        }
        
        col = 0
        for label in self.queue_stats_labels.values():
            label.grid(row=0, column=col, padx=20, pady=5)
            col += 1
        
        queue_frame = ttk.LabelFrame(main_frame, text="Render Queue", padding="10")
        queue_frame.pack(fill='both', expand=True)
        
        columns = ('ID', 'Shot', 'Story Title', 'Status', 'Attempts', 'Queued At')
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show='tree headings')
        
        for col in columns:
            self.queue_tree.heading(col, text=col)
            if col == 'Story Title':
                self.queue_tree.column(col, width=200)
            else:
                self.queue_tree.column(col, width=100)
        
        self.queue_tree.column('#0', width=0, stretch=False)
        
        scrollbar = ttk.Scrollbar(queue_frame, orient='vertical', command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=scrollbar.set)
        
        self.queue_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=10)
        
        ttk.Button(control_frame, text="Refresh Queue", 
                  command=self.refresh_queue).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Clear All", 
                  command=self.clear_all_queue).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Clear Completed", 
                  command=self.clear_completed_queue).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Retry Failed", 
                  command=self.retry_failed).pack(side='left', padx=5)
    
    def setup_settings_tab(self):
        """Setup settings and configuration tab"""
        main_frame = ttk.Frame(self.settings_tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Settings & Configuration", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # API Configuration Section
        api_frame = ttk.LabelFrame(main_frame, text="API Configuration", padding="15")
        api_frame.pack(fill='x', pady=(0, 15))
        
        # Load saved API settings
        api_settings = self.load_api_settings()
        
        # OpenAI Status
        openai_frame = ttk.Frame(api_frame)
        openai_frame.pack(fill='x', pady=5)
        ttk.Label(openai_frame, text="OpenAI:", width=12).pack(side='left')
        
        openai_enabled = api_settings.get('openai', {}).get('enabled', False)
        openai_has_key = bool(api_settings.get('openai', {}).get('api_key', ''))
        
        if openai_enabled and openai_has_key:
            status_text = f"✅ Enabled - {api_settings['openai'].get('default_model', 'Unknown model')}"
            status_color = "green"
        elif openai_has_key:
            status_text = "⚠️ Configured but disabled"
            status_color = "orange"
        else:
            status_text = "❌ Not configured"
            status_color = "red"
        
        ttk.Label(openai_frame, text=status_text, foreground=status_color).pack(side='left', padx=10)
        
        # Claude Status  
        claude_frame = ttk.Frame(api_frame)
        claude_frame.pack(fill='x', pady=5)
        ttk.Label(claude_frame, text="Claude:", width=12).pack(side='left')
        
        claude_enabled = api_settings.get('anthropic', {}).get('enabled', False)
        claude_has_key = bool(api_settings.get('anthropic', {}).get('api_key', ''))
        
        if claude_enabled and claude_has_key:
            status_text = f"✅ Enabled - {api_settings['anthropic'].get('default_model', 'Unknown model')}"
            status_color = "green"
        elif claude_has_key:
            status_text = "⚠️ Configured but disabled"
            status_color = "orange"
        else:
            status_text = "❌ Not configured"
            status_color = "red"
        
        ttk.Label(claude_frame, text=status_text, foreground=status_color).pack(side='left', padx=10)
        
        # System Prompts Section
        prompts_frame = ttk.LabelFrame(main_frame, text="System Prompts", padding="15")
        prompts_frame.pack(fill='x', pady=(0, 15))
        
        # Current preset display
        preset_frame = ttk.Frame(prompts_frame)
        preset_frame.pack(fill='x', pady=5)
        ttk.Label(preset_frame, text="Active Preset:", width=12).pack(side='left')
        
        # Load current preset info
        current_preset = self.load_current_preset()
        preset_info = f"'{current_preset.get('name', 'Default')}' - {current_preset.get('description', 'Standard prompts')}"
        ttk.Label(preset_frame, text=preset_info, font=('Arial', 9)).pack(side='left', padx=10)
        
        # Settings buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        ttk.Button(button_frame, text="🔧 Configure APIs & Prompts", 
                  command=self.open_settings_dialog, 
                  style='Accent.TButton').pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="🔄 Reload Settings", 
                  command=self.reload_settings).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="📁 Open Settings Folder", 
                  command=self.open_settings_folder).pack(side='left', padx=5)
        
        # Info section
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="15")
        info_frame.pack(fill='both', expand=True)
        
        info_text = """
Settings Storage:
• API keys and configuration are stored in 'user_settings.json'
• Custom system prompt presets are stored in 'custom_presets.json' 
• Database settings are stored in the SQLite database

Security Notes:
• API keys are stored locally in plain text
• Keep your settings files secure and do not share them
• Use environment variables for production deployments

System Prompt Presets:
• Create custom presets for different content types
• Built-in presets: Default, Comedy Enhanced, Horror Atmospheric, Quick Generation
• Export/import presets to share configurations
        """
        
        info_label = ttk.Label(info_frame, text=info_text.strip(), 
                              font=('Arial', 9), justify='left')
        info_label.pack(anchor='w')
    
    def load_api_settings(self):
        """Load API settings from database or config"""
        try:
            # Try to load from database first
            return self.db.get_setting('api_config', {})
        except:
            # Fallback to empty dict
            return {}
    
    def load_current_preset(self):
        """Load current system prompt preset info"""
        try:
            preset_name = self.db.get_setting('active_preset', 'default')
            if preset_name != 'default':
                preset = self.db.get_preset(preset_name)
                if preset:
                    return preset['preset_data']
            
            # Fallback to built-in default
            from config import SYSTEM_PROMPT_PRESETS
            return SYSTEM_PROMPT_PRESETS.get('default', {
                'name': 'Default',
                'description': 'Standard prompts'
            })
        except:
            return {'name': 'Default', 'description': 'Standard prompts'}
    
    def open_settings_dialog(self):
        """Open the settings configuration dialog"""
        dialog = SettingsDialog(self.root, self.db)
        # Refresh settings tab after dialog closes
        self.root.after(100, self.refresh_settings_display)
    
    def reload_settings(self):
        """Reload settings from files/database"""
        self.refresh_settings_display()
        self.add_log("Settings reloaded from storage", "Info")
    
    def open_settings_folder(self):
        """Open the folder containing settings files"""
        import os
        import subprocess
        import sys
        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            if sys.platform == "win32":
                subprocess.Popen(f'explorer "{current_dir}"')
            elif sys.platform == "darwin":
                subprocess.Popen(["open", current_dir])
            else:
                subprocess.Popen(["xdg-open", current_dir])
                
            self.add_log(f"Opened settings folder: {current_dir}", "Info")
        except Exception as e:
            self.add_log(f"Failed to open settings folder: {e}", "Error")
    
    def refresh_settings_display(self):
        """Refresh the settings tab display"""
        # This would refresh the settings tab content
        # For now, just log that it should be refreshed
        self.add_log("Settings display refreshed", "Info")
    
    # Action Methods
    def randomize_inputs(self):
        """Randomize all input fields on startup with genre-appropriate style"""
        genre = random.choice(GENERATION_SETTINGS['genres'])
        self.genre_var.set(genre)
        
        length = random.choice(GENERATION_SETTINGS['lengths'])
        self.length_var.set(length)
        
        # Select genre-appropriate style
        style = self.get_genre_appropriate_style(genre)
        self.style_var.set(style)
        self.update_style_description()
        
        if genre in STORY_PROMPTS:
            prompt = random.choice(STORY_PROMPTS[genre])
            self.prompt_entry.delete(0, tk.END)
            self.prompt_entry.insert(0, prompt)
        
        self.add_log(f"Initialized with random values: {genre}, {length}, {style}", "Info")
    
    def randomize_auto_inputs(self):
        """Randomize only inputs with auto checkbox selected with genre-style pairing"""
        if self.auto_genre_var.get():
            genre = random.choice(GENERATION_SETTINGS['genres'])
            self.genre_var.set(genre)
            self.add_log(f"Auto-selected genre: {genre}", "AI")
        else:
            genre = self.genre_var.get()
        
        if self.auto_length_var.get():
            length = random.choice(GENERATION_SETTINGS['lengths'])
            self.length_var.set(length)
            self.add_log(f"Auto-selected length: {length}", "AI")
        
        if self.auto_style_var.get():
            # Use genre-appropriate style if available, otherwise random
            if genre and genre in GENRE_STYLE_MAPPINGS:
                style = self.get_genre_appropriate_style(genre)
                self.add_log(f"Auto-selected {style} style for {genre} genre", "AI")
            else:
                style = random.choice(list(VISUAL_STYLES.keys()))
                self.add_log(f"Auto-selected style: {style}", "AI")
            
            self.style_var.set(style)
            self.update_style_description()
        
        if self.auto_prompt_var.get():
            if genre in STORY_PROMPTS:
                prompt = random.choice(STORY_PROMPTS[genre])
                self.prompt_entry.delete(0, tk.END)
                self.prompt_entry.insert(0, prompt)
                self.add_log(f"Auto-selected prompt: {prompt[:50]}...", "AI")
    
    def on_genre_selected(self, event=None):
        """Handle genre selection change - auto-suggest matching style if auto is enabled"""
        selected_genre = self.genre_var.get()
        if selected_genre:
            self.add_log(f"Selected genre: {selected_genre}", "UI")
            
            # Auto-select matching style if auto_style is enabled
            if self.auto_style_var.get() and selected_genre in GENRE_STYLE_MAPPINGS:
                genre_styles = GENRE_STYLE_MAPPINGS[selected_genre]
                if genre_styles:
                    # Select the first (primary) style for this genre
                    suggested_style = genre_styles[0]
                    self.style_var.set(suggested_style)
                    self.update_style_description()
                    self.add_log(f"Auto-selected {suggested_style} style for {selected_genre}", "AI")
    
    def on_style_selected(self, event=None):
        """Handle style selection change"""
        self.update_style_description()
        selected_style = self.style_var.get()
        if selected_style:
            self.add_log(f"Selected visual style: {selected_style}", "UI")
    
    def update_style_description(self):
        """Update the style description label"""
        selected_style = self.style_var.get()
        if selected_style and selected_style in VISUAL_STYLES:
            description = VISUAL_STYLES[selected_style]['description']
            self.style_description_label.config(text=f"Style: {description}")
        else:
            self.style_description_label.config(text="")
    
    def get_genre_appropriate_style(self, genre: str) -> str:
        """Get a style that matches the given genre"""
        if genre in GENRE_STYLE_MAPPINGS:
            genre_styles = GENRE_STYLE_MAPPINGS[genre]
            if genre_styles:
                return random.choice(genre_styles)
        
        # Fallback to any available style
        return random.choice(list(VISUAL_STYLES.keys()))
    
    def update_progress(self, value: float, text: str):
        """Update progress bar and text"""
        self.progress_var.set(value)
        self.progress_text.config(text=text)
        self.root.update_idletasks()
    
    def start_generation(self):
        """Start story generation with enhanced progress popup"""
        if self.is_generating:
            return
        
        self.is_generating = True
        self.run_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Status: Generating...")
        
        config = self.get_story_config()
        
        # Create progress popup
        self.progress_window = GenerationProgressWindow(
            self.root, 
            config,
            self.on_generation_popup_complete
        )
        
        # Start enhanced generation
        self.start_enhanced_generation_worker(config)

   # Update the enhanced generation worker in gui.py to handle errors properly:

    def start_enhanced_generation_worker(self, config):
        """Enhanced generation worker - STOPS on AI errors, no simulation"""
        def generation_thread():
            try:
                # Pre-check: Verify Ollama is available
                if not self.ollama.available:
                    error_msg = "Ollama not available - check connection and select a model"
                    if self.progress_window:
                        self.progress_window.add_ai_message('error', error_msg, 'system')
                    self.add_log(error_msg, "Error")
                    return
                
                if not self.ollama.get_current_model() or self.ollama.get_current_model() == 'None':
                    error_msg = "No model selected - select a model from the dropdown first"
                    if self.progress_window:
                        self.progress_window.add_ai_message('error', error_msg, 'system')
                    self.add_log(error_msg, "Error")
                    return
                
                # Set progress window reference
                if hasattr(self.story_gen, 'set_progress_window'):
                    self.story_gen.set_progress_window(self.progress_window)
                
                # Step 1: Story Generation
                self.progress_window.update_step('story', 10, 'processing', 'Sending request to AI...')
                
                try:
                    story = self.story_gen.generate_story(config)
                    
                    if not story:
                        raise Exception("Story generation returned empty result")
                    
                    self.progress_window.update_step('story', 100, 'completed', f"Created: {story['title']}")
                    self.add_log(f"Story generated successfully: {story['title']}", "AI")
                    
                except Exception as e:
                    self.progress_window.update_step('story', 0, 'error', f'Failed: {str(e)}')
                    self.add_log(f"Story generation failed: {str(e)}", "Error")
                    return  # STOP here - don't continue
                
                # Save story to database
                try:
                    story_id = self.db.save_story(story)
                    self.db.save_generation_history(story_id, config)
                    self.add_log(f"Story saved to database: {story_id}", "Database")
                except Exception as e:
                    self.add_log(f"Database save failed: {str(e)}", "Error")
                    return
                
                # Step 2: Shot List Creation
                self.progress_window.update_step('shots', 10, 'processing', 'Converting to shot list...')
                
                try:
                    shots = self.story_gen.create_shot_list(story)
                    
                    if not shots:
                        raise Exception("Shot list creation returned empty result")
                    
                    self.progress_window.update_step('shots', 100, 'completed', f"{len(shots)} shots created")
                    self.add_log(f"Shot list created: {len(shots)} shots", "AI")
                    
                except Exception as e:
                    self.progress_window.update_step('shots', 0, 'error', f'Failed: {str(e)}')
                    self.add_log(f"Shot list creation failed: {str(e)}", "Error")
                    return  # STOP here
                
                # Step 3-5: Process individual shots
                total_shots = len(shots)
                completed_prompts = 0
                completed_narration = 0
                completed_music = 0
                
                for idx, shot in enumerate(shots):
                    try:
                        # Save shot to database first
                        shot_id = self.db.save_shot(shot)
                        shot.id = shot_id
                        
                        current_progress = ((idx + 1) / total_shots) * 100
                        
                        # Generate visual prompts
                        try:
                            self.progress_window.update_step('prompts', current_progress, 'processing', f'Shot {idx+1}/{total_shots}')
                            self.story_gen.generate_wan_prompt(shot)
                            completed_prompts += 1
                        except Exception as e:
                            self.progress_window.update_step('prompts', current_progress, 'error', f'Shot {idx+1} failed: {str(e)}')
                            self.add_log(f"Prompt generation failed for shot {idx+1}: {str(e)}", "Error")
                            return  # STOP on error
                        
                        # Generate narration
                        try:
                            self.progress_window.update_step('narration', current_progress, 'processing', f'Shot {idx+1}/{total_shots}')
                            self.story_gen.generate_elevenlabs_script(shot)
                            completed_narration += 1
                        except Exception as e:
                            self.progress_window.update_step('narration', current_progress, 'error', f'Shot {idx+1} failed: {str(e)}')
                            self.add_log(f"Narration generation failed for shot {idx+1}: {str(e)}", "Error")
                            return  # STOP on error
                        
                        # Generate music if needed
                        if shot.music_cue:
                            try:
                                self.progress_window.update_step('music', current_progress, 'processing', f'Shot {idx+1}/{total_shots}')
                                self.story_gen.generate_suno_prompt(shot)
                                completed_music += 1
                            except Exception as e:
                                self.progress_window.update_step('music', current_progress, 'error', f'Shot {idx+1} failed: {str(e)}')
                                self.add_log(f"Music generation failed for shot {idx+1}: {str(e)}", "Error")
                                return  # STOP on error
                        
                        # Update shot in database with generated content
                        try:
                            cursor = self.db.conn.cursor()
                            cursor.execute('''
                                UPDATE shots 
                                SET wan_prompt = ?, narration = ?, music_cue = ?, status = 'ready'
                                WHERE id = ?
                            ''', (shot.wan_prompt, shot.narration, shot.music_cue, shot_id))
                            self.db.conn.commit()
                            
                            # Add to render queue
                            priority = 10 if shot.shot_number == 1 else 5
                            self.db.add_to_render_queue(shot_id, priority)
                            
                        except Exception as e:
                            self.add_log(f"Database update failed for shot {idx+1}: {str(e)}", "Error")
                            return
                    
                    except Exception as e:
                        self.add_log(f"Failed processing shot {idx+1}: {str(e)}", "Error")
                        return  # STOP on any shot processing error
                
                # Mark completion only if ALL steps succeeded
                self.progress_window.update_step('prompts', 100, 'completed', f'{completed_prompts} visual prompts generated')
                self.progress_window.update_step('narration', 100, 'completed', f'{completed_narration} narration scripts created')
                self.progress_window.update_step('music', 100, 'completed', f'Music cues completed')
                self.progress_window.update_step('queue', 100, 'completed', f'{total_shots} shots queued for rendering')
                
                # Mark story as ready
                try:
                    self.db.conn.execute("UPDATE stories SET status = 'ready' WHERE id = ?", (story_id,))
                    self.db.conn.commit()
                except Exception as e:
                    self.add_log(f"Failed to mark story as ready: {str(e)}", "Error")
                    return
                
                # Update current story display
                self.current_story = story
                self.current_shots = shots
                self.root.after(0, lambda: self.update_story_display(story))
                
                self.progress_window.add_ai_message('success', f"Story '{story['title']}' fully generated and queued for rendering!", 'complete')
                self.add_log(f"Generation completed successfully: {story['title']}", "AI")
                
            except Exception as e:
                # Top-level error handling
                error_msg = f"Generation process failed: {str(e)}"
                if self.progress_window:
                    self.progress_window.add_ai_message('error', error_msg, 'system')
                self.add_log(error_msg, "Error")
                import traceback
                self.add_log(traceback.format_exc(), "Error")
            
            finally:
                # Always clean up
                self.root.after(0, self.on_generation_popup_complete)
        
        # Start generation thread
        thread = threading.Thread(target=generation_thread, daemon=True)
        thread.start()

    # Also add this method to prevent simulation mode entirely:

    def check_ai_ready(self):
        """Check if AI is ready before allowing generation"""
        if not self.ollama.available:
            messagebox.showerror("AI Not Available", 
                            "Ollama is not available. Please:\n"
                            "1. Make sure 'ollama serve' is running\n"
                            "2. Click 'Test Connection'\n" 
                            "3. Select a model from the dropdown")
            return False
        
        if not self.ollama.get_current_model() or self.ollama.get_current_model() == 'None':
            messagebox.showerror("No Model Selected",
                            "Please select a model from the dropdown before generating stories.")
            return False
        
        return True

    # Update the start_generation method to use the check:

    def start_generation(self):
        """Start story generation with AI verification"""
        if self.is_generating:
            return
        
        # Check AI readiness FIRST
        if not self.check_ai_ready():
            return  # Don't start if AI isn't ready
        
        self.is_generating = True
        self.run_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Status: Generating...")
        
        config = self.get_story_config()
        
        # Create progress popup
        self.progress_window = GenerationProgressWindow(
            self.root, 
            config,
            self.on_generation_popup_complete
        )
        
        # Start enhanced generation
        self.start_enhanced_generation_worker(config)

    def on_generation_popup_complete(self):
        """Called when generation popup closes"""
        self.is_generating = False
        self.run_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Status: Ready")
        
        # Refresh all displays
        self.refresh_recent_stories()
        self.refresh_queue()
        self.refresh_metrics()
        
        self.add_log("Enhanced generation completed", "Info")
    
    def stop_generation(self):
        """Stop story generation"""
        self.is_generating = False
        self.continuous_mode = False
        
        self.run_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Status: Stopped")
        
        self.update_progress(0, "Ready to generate stories...")
        self.add_log("Generation stopped by user", "Info")
    
    def generation_worker(self):
        """Main generation loop in separate thread"""
        try:
            generation_count = 0
            
            while self.is_generating:
                generation_count += 1
                self.add_log(f"Starting generation #{generation_count}", "Info")
                
                self.root.after(0, self.update_progress, 5, "Getting story configuration...")
                
                config = self.get_story_config()
                
                self.root.after(0, self.update_progress, 10, f"Generating {config.genre} story...")
                self.add_log(f"Configuration: Genre={config.genre}, Length={config.length}", "Info")
                self.add_log(f"Prompt: {config.prompt}", "Info")
                
                story, shots = self.story_gen.generate_complete_story(
                    config,
                    progress_callback=lambda v, t: self.root.after(0, self.update_progress, v, t),
                    log_callback=lambda msg, typ: self.add_log(msg, typ)
                )
                
                if story:
                    self.current_story = story
                    self.current_shots = shots
                    
                    self.root.after(0, self.update_story_display, story)
                    self.root.after(0, self.refresh_recent_stories)
                    self.root.after(0, self.refresh_queue)
                    
                    self.add_log(f"✅ Story '{story['title']}' ready with {len(shots)} shots", "Info")
                    self.root.after(0, self.update_progress, 100, f"Completed: {story['title']}")
                else:
                    self.add_log("❌ Failed to generate story", "Error")
                    self.root.after(0, self.update_progress, 0, "Generation failed")
                
                if not self.continuous_mode:
                    self.is_generating = False
                    self.add_log("Single generation complete", "Info")
                else:
                    wait_time = GENERATION_SETTINGS.get('generation_wait_time', 5)
                    self.add_log(f"Waiting {wait_time} seconds before next generation...", "Info")
                    
                    if (self.auto_prompt_var.get() or self.auto_genre_var.get() or 
                        self.auto_length_var.get()):
                        self.root.after(0, self.randomize_auto_inputs)
                    
                    for i in range(wait_time, 0, -1):
                        if not self.is_generating:
                            break
                        self.root.after(0, self.update_progress, 0, f"Next generation in {i} seconds...")
                        time.sleep(1)
                    
        except Exception as e:
            self.add_log(f"❌ Error in generation: {str(e)}", "Error")
            import traceback
            self.add_log(traceback.format_exc(), "Error")
        finally:
            self.root.after(0, self.stop_generation)
    
    def get_story_config(self) -> StoryConfig:
        """Get story configuration from UI"""
        length = self.length_var.get()
        
        # Calculate parts from length using GENERATION_SETTINGS
        parts_range = GENERATION_SETTINGS['length_to_parts'].get(length, (3, 5))
        parts = parts_range[0]  # Use minimum parts for consistency
        
        # Get render settings key from display names
        aspect_ratio_name = self.aspect_ratio_var.get()
        aspect_ratio_key = None
        for key, data in RENDER_SETTINGS['aspect_ratios'].items():
            if data['name'] == aspect_ratio_name:
                aspect_ratio_key = key
                break
        
        fps_name = self.fps_var.get()
        fps_key = None
        for key, data in RENDER_SETTINGS['fps_options'].items():
            if data['name'] == fps_name:
                fps_key = key
                break
        
        return StoryConfig(
            prompt=self.prompt_entry.get(),
            genre=self.genre_var.get(),
            length=length,
            visual_style=self.style_var.get(),
            aspect_ratio=aspect_ratio_key or RENDER_SETTINGS['defaults']['aspect_ratio'],
            fps=fps_key or RENDER_SETTINGS['defaults']['fps'],
            auto_prompt=self.auto_prompt_var.get(),
            auto_genre=self.auto_genre_var.get(),
            auto_length=self.auto_length_var.get(),
            auto_style=self.auto_style_var.get(),
            parts=parts
        )
    
    def test_ollama_connection(self):
        """Test Ollama connection"""
        self.add_log("Testing Ollama connection...", "Info")
        
        success, message = self.ollama.test_connection()
        
        if success:
            messagebox.showinfo("Ollama Status", f"✅ {message}")
            self.add_log(f"✅ Ollama test successful: {message}", "Info")
        else:
            messagebox.showwarning("Ollama Status", f"⚠️ {message}")
            self.add_log(f"⚠️ Ollama test failed: {message}", "Error")
    
    def on_metrics_click(self, event):
        """Handle click on metrics table for delete"""
        item = self.metrics_tree.identify('item', event.x, event.y)
        column = self.metrics_tree.identify_column(event.x)
        
        if item and column == '#9':  # Delete column
            values = self.metrics_tree.item(item, 'values')
            story_id = values[0]
            story_title = values[1]
            
            if messagebox.askyesno("Delete Story", 
                                   f"Delete story '{story_title}' and all related data?"):
                self.delete_story(story_id)
    
    def delete_story(self, story_id: str):
        """Delete a story and refresh displays"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM stories WHERE id LIKE ?", (story_id.replace('...', '%'),))
        result = cursor.fetchone()
        
        if result:
            full_story_id = result['id']
            if self.db.delete_story(full_story_id):
                self.add_log(f"Deleted story: {full_story_id}", "Database")
                self.refresh_metrics()
                self.refresh_recent_stories()
                self.refresh_queue()
                messagebox.showinfo("Success", "Story deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete story")
    
    def clear_all_queue(self):
        """Clear all items from render queue"""
        if messagebox.askyesno("Clear Queue", "Clear ALL items from render queue?"):
            self.db.clear_render_queue()
            self.refresh_queue()
            self.add_log("Cleared all items from render queue", "Database")
    
    def clear_completed_queue(self):
        """Clear completed items from render queue"""
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM render_queue WHERE status = 'completed'")
        self.db.conn.commit()
        self.refresh_queue()
        self.add_log("Cleared completed items from render queue", "Database")
    
    def retry_failed(self):
        """Retry failed render queue items"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE render_queue 
            SET status = 'queued', error_message = NULL 
            WHERE status = 'failed' AND attempts < 3
        """)
        self.db.conn.commit()
        self.refresh_queue()
        self.add_log("Reset failed items in render queue for retry", "Database")
    
    def update_story_display(self, story: Dict):
        """Update story display"""
        self.story_display.delete('1.0', tk.END)
        
        display_text = f"{'='*60}\n"
        display_text += f"STORY GENERATED\n"
        display_text += f"{'='*60}\n\n"
        display_text += f"Title: {story['title']}\n"
        display_text += f"Genre: {story['genre']}\n"
        display_text += f"Length: {story['length']}\n"
        display_text += f"Parts: {story['parts']}\n\n"
        display_text += f"{'='*60}\n"
        display_text += f"STORY CONTENT:\n"
        display_text += f"{'='*60}\n\n"
        display_text += story['content']
        
        self.story_display.insert('1.0', display_text)
        self.story_display.see('1.0')
    
    def export_current_story(self):
        """Export current story and shots"""
        if not self.current_story:
            messagebox.showwarning("No Story", "Generate a story first before exporting")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"story_export_{timestamp}.json"
        
        export_data = {
            'story': self.current_story,
            'shots': [
                {
                    'shot_number': shot.shot_number,
                    'description': shot.description,
                    'duration': shot.duration,
                    'wan_prompt': shot.wan_prompt,
                    'narration': shot.narration,
                    'music_cue': shot.music_cue,
                    'status': shot.status
                } for shot in self.current_shots
            ],
            'generation_timestamp': timestamp,
            'ollama_model': OLLAMA_CONFIG['model'] if self.ollama.available else 'simulation'
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("Export Complete", 
                           f"Story and {len(self.current_shots)} shots exported to:\n{filename}")
        self.add_log(f"Exported story to {filename}", "Info")
    
    # Helper Methods
    def add_log(self, message: str, log_type: str = "Info"):
        """Add message to log queue with detailed timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_queue.put((timestamp, message, log_type))
    
    def update_logs(self):
        """Update log display from queue"""
        try:
            while True:
                timestamp, message, log_type = self.log_queue.get_nowait()
                
                if self.log_filter_var.get() != "All" and self.log_filter_var.get() != log_type:
                    continue
                
                self.log_display.insert(tk.END, f"[{timestamp}] ", 'Info')
                self.log_display.insert(tk.END, f"[{log_type}] ", log_type)
                self.log_display.insert(tk.END, f"{message}\n", 'Info')
                self.log_display.see(tk.END)
                
        except queue.Empty:
            pass
        finally:
            self.root.after(APP_SETTINGS['log_refresh_rate'], self.update_logs)
    
    def clear_logs(self):
        """Clear log display"""
        self.log_display.delete('1.0', tk.END)
        self.add_log("Logs cleared", "Info")
    
    def export_logs(self):
        """Export logs to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(self.log_display.get('1.0', tk.END))
        
        messagebox.showinfo("Export Complete", f"Logs exported to {filename}")
        self.add_log(f"Logs exported to {filename}", "Info")
    
    def refresh_recent_stories(self):
        """Refresh recent stories list"""
        for item in self.stories_tree.get_children():
            self.stories_tree.delete(item)
        
        stories = self.db.get_recent_stories(20)
        
        for story in stories:
            self.stories_tree.insert('', 'end', values=(
                story['id'][:12] + '...',
                story['title'],
                story['genre'],
                story['status'],
                story['created_at'][:16]
            ))
    
    def refresh_metrics(self):
        """Refresh metrics display"""
        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)
        
        performance_data = self.db.get_story_performance()
        
        for perf in performance_data:
            self.metrics_tree.insert('', 'end', values=(
                perf['story_id'][:12] + '...',
                perf['title'],
                perf['genre'],
                perf['total_parts'],
                f"{perf['total_views']:,}",
                f"{perf['avg_engagement']:.1%}",
                f"{perf['avg_completion']:.1%}",
                perf['status'],
                '❌ Delete'
            ))
        
        if performance_data:
            total_stories = len(performance_data)
            total_views = sum(p['total_views'] for p in performance_data)
            avg_engagement = sum(p['avg_engagement'] for p in performance_data) / len(performance_data)
            avg_completion = sum(p['avg_completion'] for p in performance_data) / len(performance_data)
            
            self.total_stories_label.config(text=f"Total Stories: {total_stories}")
            self.total_views_label.config(text=f"Total Views: {total_views:,}")
            self.avg_engagement_label.config(text=f"Avg Engagement: {avg_engagement:.1%}")
            self.completion_rate_label.config(text=f"Avg Completion: {avg_completion:.1%}")
            
            genre_perf = self.db.get_genre_performance()
            if genre_perf:
                best_genre = max(genre_perf.items(), key=lambda x: x[1]['avg_engagement'])[0]
                self.best_genre_label.config(text=f"Best Genre: {best_genre}")
            
            length_perf = self.db.get_length_performance()
            if length_perf:
                best_length = max(length_perf.items(), key=lambda x: x[1]['avg_completion'])[0]
                self.best_length_label.config(text=f"Optimal Length: {best_length}")
    
    def refresh_queue(self):
        """Refresh render queue display with story titles"""
        stats = self.db.get_render_queue_status()
        for key, label in self.queue_stats_labels.items():
            label.config(text=f"{key.capitalize()}: {stats.get(key, 0)}")
        
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT rq.*, s.shot_number, s.story_id, st.title as story_title
            FROM render_queue rq
            JOIN shots s ON rq.shot_id = s.id
            JOIN stories st ON s.story_id = st.id
            WHERE DATE(rq.queued_at) = DATE('now')
            ORDER BY rq.queued_at DESC
            LIMIT 50
        ''')
        
        for row in cursor.fetchall():
            self.queue_tree.insert('', 'end', values=(
                row['id'],
                f"Shot {row['shot_number']}",
                row['story_title'],
                row['status'],
                row['attempts'],
                row['queued_at'][:16]
            ))
    
    def simulate_metrics(self):
        """Simulate metrics for testing"""
        self.add_log("Simulating metrics for testing...", "Info")
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT id FROM videos ORDER BY RANDOM() LIMIT 5')
        videos = cursor.fetchall()
        
        if not videos:
            messagebox.showwarning("No Videos", "Generate some stories first before simulating metrics")
            return
        
        for video in videos:
            metrics = {
                'video_id': video['id'],
                'story_id': video['id'].split('_part_')[0],
                'views': random.randint(100, 10000),
                'likes': random.randint(10, 1000),
                'comments': random.randint(5, 200),
                'shares': random.randint(2, 100),
                'completion_rate': random.uniform(0.3, 0.95),
                'engagement_rate': random.uniform(0.05, 0.30),
                'avg_watch_time': random.uniform(20, 120)
            }
            self.db.save_metrics(metrics)
            self.add_log(f"Added metrics for video {video['id']}: {metrics['views']} views", "Info")
        
        self.refresh_metrics()
        self.add_log(f"✅ Added simulated metrics for {len(videos)} videos", "Info")
    
    def export_metrics_report(self):
        """Export metrics report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_report_{timestamp}.json"
        
        self.add_log("Generating metrics report...", "Info")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'story_performance': self.db.get_story_performance(),
            'genre_performance': self.db.get_genre_performance(),
            'length_performance': self.db.get_length_performance(),
            'queue_status': self.db.get_render_queue_status()
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        messagebox.showinfo("Export Complete", f"Metrics report exported to {filename}")
        self.add_log(f"✅ Metrics report exported to {filename}", "Info")
    
    def render_queue_worker(self):
        """Background worker to process render queue"""
        while self.render_worker_active:
            try:
                item = self.db.get_next_render_item()
                
                if item:
                    queue_id = item['id']
                    shot_id = item['shot_id']
                    story_id = item['story_id']
                    
                    cursor = self.db.conn.cursor()
                    cursor.execute("SELECT title FROM stories WHERE id = ?", (story_id,))
                    story_result = cursor.fetchone()
                    story_title = story_result['title'] if story_result else "Unknown"
                    
                    self.db.update_render_queue_status(queue_id, 'processing')
                    self.add_log(f"Starting render for shot {shot_id} from '{story_title}'", "Rendering")
                    
                    time.sleep(random.uniform(2, 5))
                    
                    if random.random() < 0.9:
                        render_path = f"renders/shot_{shot_id}_{int(time.time())}.mp4"
                        self.db.update_shot_status(shot_id, 'completed', render_path)
                        self.db.update_render_queue_status(queue_id, 'completed')
                        self.add_log(f"✅ Completed render for shot {shot_id} from '{story_title}'", "Rendering")
                        
                        self.check_story_completion(story_id)
                    else:
                        error = "Simulated render failure"
                        self.db.update_render_queue_status(queue_id, 'failed', error)
                        self.add_log(f"❌ Failed to render shot {shot_id} from '{story_title}': {error}", "Error")
                    
                    self.root.after(0, self.refresh_queue)
                else:
                    time.sleep(2)
                    
            except Exception as e:
                self.add_log(f"Error in render worker: {str(e)}", "Error")
                time.sleep(5)
    
    def check_story_completion(self, story_id: str):
        """Check if all shots for a story are complete"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
            FROM shots WHERE story_id = ?
        ''', (story_id,))
        result = cursor.fetchone()
        
        if result['total'] == result['completed'] and result['total'] > 0:
            cursor.execute("SELECT title FROM stories WHERE id = ?", (story_id,))
            story_result = cursor.fetchone()
            story_title = story_result['title'] if story_result else "Unknown"
            
            self.add_log(f"All shots complete for '{story_title}', compiling video...", "Rendering")
            self.compile_and_upload_story(story_id)
    
    def compile_and_upload_story(self, story_id: str):
        """Compile shots and upload final video"""
        time.sleep(2)
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM stories WHERE id = ?', (story_id,))
        story = dict(cursor.fetchone())
        
        parts = story['parts']
        for i in range(parts):
            video_data = {
                'id': f"{story_id}_part_{i+1}",
                'story_id': story_id,
                'part_number': i + 1,
                'title': f"{story['title']} - Part {i+1}",
                'upload_url': f"https://platform.com/videos/{story_id}_{i+1}",
                'duration': random.uniform(30, 120)
            }
            self.db.save_video(video_data)
            
            metrics = {
                'video_id': video_data['id'],
                'story_id': story_id,
                'views': random.randint(100, 5000),
                'likes': random.randint(10, 500),
                'comments': random.randint(5, 100),
                'shares': random.randint(2, 50),
                'completion_rate': random.uniform(0.3, 0.95),
                'engagement_rate': random.uniform(0.05, 0.25),
                'avg_watch_time': random.uniform(20, video_data['duration'])
            }
            self.db.save_metrics(metrics)
            
            self.add_log(f"✅ Uploaded {video_data['title']}", "Upload")
        
        self.db.conn.execute("UPDATE stories SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?", (story_id,))
        self.db.conn.commit()
        
        self.root.after(0, self.refresh_metrics)
        self.root.after(0, self.refresh_recent_stories)
        
        self.add_log(f"✅ Story '{story['title']}' fully compiled and uploaded", "Upload")
    
    def auto_refresh_metrics(self):
        """Auto-refresh metrics periodically"""
        self.refresh_metrics()
        self.refresh_queue()
        self.root.after(APP_SETTINGS['metrics_refresh_rate'], self.auto_refresh_metrics)
    
    def start_background_workers(self):
        """Start background worker threads"""
        self.update_logs()
        
        self.render_worker_active = True
        render_thread = threading.Thread(target=self.render_queue_worker, daemon=True)
        render_thread.start()
        
        self.auto_refresh_metrics()
        
        self.add_log("Background workers started", "Info")
    
    def load_initial_data(self):
        """Load initial data from database"""
        self.refresh_recent_stories()
        self.refresh_metrics()
        self.refresh_queue()
        self.add_log("Initial data loaded from database", "Info")
    
    def cleanup(self):
        """Cleanup on exit"""
        self.render_worker_active = False
        if hasattr(self, 'db'):
            self.db.close()
        self.add_log("Application cleanup complete", "Info")

    def refresh_model_list(self):
        """Refresh the model dropdown with available models"""
        try:
            # Refresh connections and get available models
            self.ollama.refresh_connections()
            models = self.ollama.available_models
            
            if models:
                self.model_combo['values'] = models
                
                # Set current selection based on saved settings
                current_model = self.ollama.get_current_model()
                if current_model and current_model != 'None' and current_model in models:
                    self.model_var.set(current_model)
                elif models:
                    # Default to first available model if none selected
                    self.model_var.set(models[0])
                    self.ollama.set_model(models[0])
                
                self.add_log(f"Refreshed model list: {len(models)} models available", "Info")
            else:
                self.model_combo['values'] = ["No models available"]
                self.model_var.set("No models available")
                self.add_log("No models available. Run: ollama pull llama3.1", "Error")
        
        except Exception as e:
            self.add_log(f"Error refreshing models: {str(e)}", "Error")
            self.model_combo['values'] = ["Error loading models"]
            self.model_var.set("Error loading models")

    def on_model_selected(self, event=None):
        """Handle model selection change"""
        selected_model = self.model_var.get()
        
        if selected_model and selected_model not in ["No models available", "Error loading models"]:
            if self.ollama.set_model(selected_model):
                self.add_log(f"Selected model: {selected_model}", "AI")
                
                # Update status display
                self.ai_status_label.config(text=f"Status: Connected - {selected_model}")
            else:
                self.add_log(f"Failed to select model: {selected_model}", "Error")

    def test_ollama_connection(self):
        """Enhanced test Ollama connection with model info"""
        self.add_log("Testing Ollama connection...", "Info")
        
        success, message = self.ollama.test_connection()
        
        if success:
            messagebox.showinfo("Ollama Status", f"✅ {message}")
            self.add_log(f"✅ Ollama test successful: {message}", "Info")
            
            # Refresh models after successful connection
            self.refresh_model_list()
        else:
            messagebox.showwarning("Ollama Status", f"⚠️ {message}")
            self.add_log(f"⚠️ Ollama test failed: {message}", "Error")
    
    # New methods for multi-network model management
    
    def scan_network_instances(self):
        """Fast network scan with immediate feedback"""
        self.add_log("Starting fast network scan...", "Info")
        
        # Immediate update with cached data
        cached = self.ollama.network_discovery.get_cached_instances()
        if cached:
            self.update_status_display()
            self.add_log(f"Loaded {len(cached)} cached instances", "Info")
        
        def fast_scan_thread():
            try:
                # Force a fresh scan
                discovered = self.ollama.network_discovery.force_refresh()
                self.root.after(0, lambda: self.on_network_scan_complete(len(discovered)))
            except Exception as e:
                self.root.after(0, lambda: self.add_log(f"Network scan failed: {str(e)}", "Error"))
        
        # Non-blocking scan
        threading.Thread(target=fast_scan_thread, daemon=True).start()
    
    def on_network_scan_complete(self, count):
        """Handle network scan completion"""
        self.add_log(f"Network scan complete - found {count} instances", "Info")
        self.refresh_all_connections()
        messagebox.showinfo("Network Scan", f"Found {count} Ollama instances on network")
    
    def refresh_all_connections(self):
        """Fast refresh with immediate UI updates"""
        self.add_log("Refreshing connections...", "Info")
        
        # Immediate update with current data
        self.update_status_display()
        self.refresh_model_list()
        self.update_assignments_display()
        
        # Background refresh for new data
        def background_refresh():
            try:
                self.ollama.refresh_connections(force=False)  # Use cache when possible
                self.root.after(0, self.update_all_ui_elements)
            except Exception as e:
                self.root.after(0, lambda: self.add_log(f"Background refresh error: {str(e)}", "Error"))
        
        threading.Thread(target=background_refresh, daemon=True).start()
    
    def update_all_ui_elements(self):
        """Update all UI elements with latest data"""
        self.refresh_model_list()
        self.update_assignments_display() 
        self.update_status_display()
        self.add_log("UI updated with latest connection data", "Info")
    
    def update_status_display(self):
        """Update AI status display"""
        instances = self.ollama.get_available_instances()
        total_models = sum(len(inst.get('models', [])) for inst in instances.values())
        
        if self.ollama.available and instances:
            ai_status_text = f"Connected - {len(instances)} instances, {total_models} models"
            ai_color = "green"
        elif self.ollama.available:
            ai_status_text = "Connected - No instances found"
            ai_color = "orange"  
        else:
            ai_status_text = "Simulation Mode"
            ai_color = "red"
        
        self.ai_status_label.config(text=f"Status: {ai_status_text}", foreground=ai_color)
    
    def open_model_dialog(self):
        """Open model selection dialog"""
        def on_assignments_updated(assignments):
            self.update_assignments_display()
            self.add_log(f"Updated model assignments for {len(assignments)} steps", "AI")
        
        dialog = ModelSelectionDialog(self.root, self.ollama, on_assignments_updated)
        result = dialog.show()
        
        if result:
            self.add_log("Model configuration updated", "AI")
    
    def update_assignments_display(self):
        """Update the assignments display label"""
        assignments = self.ollama.get_step_assignments()
        configured_steps = [step for step, (instance, model) in assignments.items() 
                           if instance and model]
        
        if configured_steps:
            self.assignments_display.config(
                text=f"{len(configured_steps)}/5 steps configured",
                foreground="green"
            )
        else:
            self.assignments_display.config(
                text="Not configured",
                foreground="gray"
            )
    
    def on_legacy_model_selected(self, event=None):
        """Handle legacy model selection (sets all steps to same model)"""
        selected_model = self.model_var.get()
        
        if selected_model and selected_model not in ["No models available", "Error loading models"]:
            # Find which instance has this model
            instance_key = None
            for key, instance in self.ollama.ollama_instances.items():
                if selected_model in instance.get('models', []):
                    instance_key = key
                    break
            
            if instance_key:
                # Set this model for all AI generation steps
                success_count = 0
                ai_steps = ['story', 'characters', 'shots', 'prompts', 'narration', 'music']
                
                for step in ai_steps:
                    if self.ollama.set_step_model(step, instance_key, selected_model):
                        success_count += 1
                
                if success_count > 0:
                    self.add_log(f"Quick Select: Applied '{selected_model}' to {success_count} AI steps", "AI")
                    self.update_assignments_display()
                    self.update_status_display()
                else:
                    self.add_log(f"Failed to apply model '{selected_model}' to any steps", "Error")
            else:
                # Legacy fallback
                if self.ollama.set_model(selected_model):
                    self.add_log(f"Set legacy model: {selected_model}", "AI")
                else:
                    self.add_log(f"Failed to select model: {selected_model}", "Error")
    
    def delete_database_with_backup(self):
        """Delete database with backup functionality"""
        if not messagebox.askyesno("Confirm Database Deletion", 
                                  "This will delete ALL story data and create a backup.\n\n"
                                  "Are you absolutely sure you want to continue?",
                                  icon='warning'):
            return
        
        try:
            import os
            import shutil
            from datetime import datetime
            
            # Create backups directory
            backup_dir = os.path.join(os.path.dirname(self.db.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"film_generator_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Close current database connection
            self.db.close()
            
            # Copy database to backup
            if os.path.exists(self.db.db_path):
                shutil.copy2(self.db.db_path, backup_path)
                self.add_log(f"Database backed up to: {backup_path}", "Database")
                
                # Delete original database
                os.remove(self.db.db_path)
                self.add_log("Original database deleted", "Database")
            
            # Reinitialize database
            self.db = DatabaseManager()
            
            # Refresh all displays
            self.refresh_recent_stories()
            self.refresh_metrics() 
            self.refresh_queue()
            
            # Clear story display
            self.story_display.delete('1.0', tk.END)
            self.current_story = None
            self.current_shots = []
            
            messagebox.showinfo("Database Reset Complete", 
                               f"Database has been reset!\n\nBackup saved to:\n{backup_path}")
            
            self.add_log("Database successfully reset with backup created", "Database")
            
        except Exception as e:
            error_msg = f"Failed to delete database: {str(e)}"
            self.add_log(error_msg, "Error")
            messagebox.showerror("Database Deletion Failed", error_msg)
            
            # Try to reinitialize database connection
            try:
                self.db = DatabaseManager()
            except:
                pass