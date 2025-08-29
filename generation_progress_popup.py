"""
Dynamic Generation Progress Popup Window
Shows real-time AI generation progress with live updates
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional
from config import estimate_step_time, estimate_total_time, format_time_estimate


class GenerationProgressWindow:
    """Dynamic progress window for story generation"""
    
    def __init__(self, parent, config, on_complete_callback: Optional[Callable] = None, db_manager=None):
        self.parent = parent
        self.config = config
        self.on_complete_callback = on_complete_callback
        self.db_manager = db_manager
        
        # Window state
        self.window = None
        self.is_open = False
        
        # Progress tracking
        self.story_title = "Generating..."
        self.current_step = ""
        self.steps_completed = 0
        self.total_steps = 8  # Story, Shots, Characters, Style, Prompts, Narration, Music, Queue
        self.step_progress = {}
        
        # Chat history tracking
        self.current_story_id = None
        
        # Time tracking
        self.generation_start_time = datetime.now()
        self.step_start_times = {}  # Track when each step starts
        self.step_estimated_times = {}  # Store estimated times for each step
        self.total_estimated_time = 0
        self.actual_step_times = {}  # Track actual completion times for learning
        
        # UI elements
        self.title_label = None
        self.progress_bars = {}
        self.status_labels = {}
        self.ai_chat = None
        self.overall_progress = None
        self.time_labels = {}  # Labels for time estimates
        self.remaining_time_label = None
        self.elapsed_time_label = None
        
        # Create the window
        self.create_window()
        
        # Initialize time estimates (delay to ensure UI is ready)
        self.window.after(100, self.initialize_time_estimates)
        
        # Load existing content if opening mid-generation (delay more to ensure DB is ready)
        self.window.after(300, self.load_existing_content)
        
        # Force refresh of all content after UI is fully initialized
        self.window.after(500, self.force_refresh_all_content)
        
        # Start periodic time updates
        self.start_periodic_updates()
    
    def create_window(self):
        """Create the progress popup window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Generating Story...")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Make it modal and centered
        self.window.transient(self.parent)
        self.window.grab_set()
        self.center_window()
        
        # Configure styles
        style = ttk.Style()
        style.configure("Title.TLabel", font=('Arial', 16, 'bold'))
        style.configure("Step.TLabel", font=('Arial', 11, 'bold'))
        style.configure("Status.TLabel", font=('Arial', 9))
        style.configure("Success.TLabel", foreground='green')
        style.configure("Processing.TLabel", foreground='blue')
        style.configure("Pending.TLabel", foreground='gray')
        
        self.setup_ui()
        self.is_open = True
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
    
    def setup_ui(self):
        """Setup the UI components"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 20))
        
        self.title_label = ttk.Label(title_frame, text=self.story_title, 
                                    style="Title.TLabel")
        self.title_label.pack()
        
        config_text = f"{self.config.genre} • {self.config.length} • \"{self.config.prompt[:50]}...\""
        ttk.Label(title_frame, text=config_text, style="Status.TLabel").pack()
        
        # Create main container with two columns
        container = ttk.Frame(main_frame)
        container.pack(fill='both', expand=True)
        
        # Left column - Progress tracking with scrollbar
        progress_frame = ttk.LabelFrame(container, text="Generation Progress", padding="15")
        progress_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Create scrollable progress section
        progress_canvas_frame = ttk.Frame(progress_frame)
        progress_canvas_frame.pack(fill='both', expand=True)
        
        self.progress_canvas = tk.Canvas(progress_canvas_frame, bg='#f0f0f0', highlightthickness=0)
        progress_scrollbar = ttk.Scrollbar(progress_canvas_frame, orient="vertical", command=self.progress_canvas.yview)
        self.progress_scrollable_frame = ttk.Frame(self.progress_canvas)
        
        self.progress_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.progress_canvas.configure(scrollregion=self.progress_canvas.bbox("all"))
        )
        
        self.progress_canvas_window = self.progress_canvas.create_window((0, 0), window=self.progress_scrollable_frame, anchor="nw")
        self.progress_canvas.configure(yscrollcommand=progress_scrollbar.set)
        
        # Configure canvas to expand the scrollable frame to full width (accounting for scrollbar)
        def _configure_canvas(event):
            canvas_width = event.width - 10  # Larger margin to prevent overflow
            self.progress_canvas.itemconfig(self.progress_canvas_window, width=canvas_width)
        
        self.progress_canvas.bind('<Configure>', _configure_canvas)
        
        self.progress_canvas.pack(side="left", fill="both", expand=True)
        progress_scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to progress canvas
        def _on_progress_mousewheel(event):
            self.progress_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.progress_canvas.bind("<MouseWheel>", _on_progress_mousewheel)
        self.progress_scrollable_frame.bind("<MouseWheel>", _on_progress_mousewheel)
        
        self.setup_progress_section(self.progress_scrollable_frame)
        
        # Right column - Content Display with Tabs
        content_frame = ttk.LabelFrame(container, text="Generated Content", padding="10")
        content_frame.pack(side='right', fill='both', expand=True)
        
        self.setup_content_tabs(content_frame)
        
        # Bottom section - Overall progress
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill='x', pady=(20, 0))
        
        # Overall progress header with time info
        progress_header = ttk.Frame(bottom_frame)
        progress_header.pack(fill='x')
        
        ttk.Label(progress_header, text="Overall Progress", style="Step.TLabel").pack(side='left')
        
        # Time information on the right
        time_info_frame = ttk.Frame(progress_header)
        time_info_frame.pack(side='right')
        
        self.elapsed_time_label = ttk.Label(time_info_frame, text="Elapsed: 0s", 
                                           font=('Arial', 9), foreground='#666666')
        self.elapsed_time_label.pack(side='right', padx=(10, 0))
        
        self.remaining_time_label = ttk.Label(time_info_frame, text="Estimating...", 
                                            font=('Arial', 9), foreground='#666666')
        self.remaining_time_label.pack(side='right', padx=(10, 0))
        
        # Progress bar
        self.overall_progress = ttk.Progressbar(bottom_frame, mode='determinate', length=600)
        self.overall_progress.pack(fill='x', pady=5)
        
        # Status label
        self.overall_status = ttk.Label(bottom_frame, text="Initializing...", style="Status.TLabel")
        self.overall_status.pack()
    
    def setup_progress_section(self, parent):
        """Setup the progress tracking section"""
        # Define generation steps (reordered)
        self.steps = [
            {"key": "story", "title": "Story Generation", "description": "Creating narrative content"},
            {"key": "shots", "title": "Shot List Creation", "description": "Breaking story into filmable shots"},
            {"key": "characters", "title": "Character Analysis", "description": "Extracting characters with ComfyUI prompts"},
            {"key": "style", "title": "Style Sheets", "description": "Visual style consistency (placeholder)"},
            {"key": "prompts", "title": "Visual Prompts", "description": "Generating AI art prompts"},
            {"key": "narration", "title": "Narration Scripts", "description": "Creating voice-over text"},
            {"key": "music", "title": "Music Cues", "description": "Defining audio requirements"},
            {"key": "queue", "title": "Render Queue", "description": "Preparing for rendering"}
        ]
        
        # Create progress elements for each step
        for i, step in enumerate(self.steps):
            step_frame = ttk.Frame(parent)
            step_frame.pack(fill='x', pady=5)  # Reduced padding for more compact layout
            
            # Step header
            header_frame = ttk.Frame(step_frame)
            header_frame.pack(fill='x')
            
            # Step number and title
            step_label = ttk.Label(header_frame, 
                                  text=f"{i+1}. {step['title']}", 
                                  style="Step.TLabel")
            step_label.pack(side='left')
            
            # Render node info (initially empty)
            node_info_label = ttk.Label(header_frame, text="", 
                                      font=('Arial', 8), foreground='#666666')
            node_info_label.pack(side='left', padx=(10, 0))
            
            # Status indicator
            status_label = ttk.Label(header_frame, text="⏳ Pending", 
                                   style="Pending.TLabel")
            status_label.pack(side='right')
            self.status_labels[step['key']] = status_label
            
            # Description
            ttk.Label(step_frame, text=step['description'], 
                     style="Status.TLabel").pack(anchor='w')
            
            # Progress bar (spans full width)
            progress_bar = ttk.Progressbar(step_frame, mode='determinate')
            progress_bar.pack(fill='x', pady=(3, 0))
            self.progress_bars[step['key']] = progress_bar
            
            # Details label (will show generated content info)
            details_label = ttk.Label(step_frame, text="", style="Status.TLabel")
            details_label.pack(anchor='w')
            # Time estimate label
            time_frame = ttk.Frame(step_frame)
            time_frame.pack(fill='x')
            
            time_label = ttk.Label(time_frame, text="Calculating...", 
                                 font=('Arial', 8), foreground='#888888')
            time_label.pack(side='right')
            
            self.step_progress[step['key']] = {
                'progress': 0,
                'status': 'pending',
                'details': '',
                'details_label': details_label,
                'node_info_label': node_info_label,
                'time_label': time_label
            }
    
    def setup_content_tabs(self, parent):
        """Setup tabbed content display for generated content"""
        # Create notebook for tabs
        self.content_notebook = ttk.Notebook(parent)
        self.content_notebook.pack(fill='both', expand=True)
        
        # Bind tab selection to refresh content
        self.content_notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # Tab 1: Story Content
        self.setup_story_tab()
        
        # Tab 2: Character & Style References
        self.setup_style_references_tab()
        
        # Tab 3: Shot List Storyboard
        self.setup_storyboard_tab()
        
        # Tab 4: AI Chat (for debugging)
        self.setup_ai_chat_tab()
    
    def setup_story_tab(self):
        """Setup story content display tab"""
        story_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(story_frame, text="📖 Story")
        
        # Story title and metadata
        header_frame = ttk.Frame(story_frame)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        self.story_title_display = ttk.Label(header_frame, text="Story not yet generated", 
                                           font=('Arial', 14, 'bold'))
        self.story_title_display.pack(anchor='w')
        
        self.story_metadata = ttk.Label(header_frame, text="", 
                                      font=('Arial', 9), foreground='gray')
        self.story_metadata.pack(anchor='w', pady=(5, 0))
        
        # Story content display
        story_container = ttk.Frame(story_frame)
        story_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.story_content = scrolledtext.ScrolledText(
            story_container,
            wrap='word',
            font=('Georgia', 11),
            bg='#fefefe',
            fg='#333333',
            padx=15,
            pady=15,
            state='disabled'
        )
        self.story_content.pack(fill='both', expand=True)
        
        # Configure story text tags
        self.story_content.tag_config('title', font=('Georgia', 16, 'bold'), spacing1=10, spacing3=10)
        self.story_content.tag_config('logline', font=('Georgia', 11, 'italic'), foreground='#666666')
        self.story_content.tag_config('part_header', font=('Georgia', 12, 'bold'), spacing1=15, spacing3=5)
        self.story_content.tag_config('content', font=('Georgia', 11), spacing1=5, spacing3=5)
        self.story_content.tag_config('hook', font=('Georgia', 11, 'bold'), foreground='#cc6600')
    
    def setup_style_references_tab(self):
        """Setup character and style references tab"""
        style_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(style_frame, text="🎨 Style Refs")
        
        # Header
        header_frame = ttk.Frame(style_frame)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        self.style_header_label = ttk.Label(header_frame, text="Character & Style References", 
                                          font=('Arial', 12, 'bold'))
        self.style_header_label.pack(anchor='w')
        
        # Scrollable content area
        canvas_frame = ttk.Frame(style_frame)
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.style_canvas = tk.Canvas(canvas_frame, bg='#f8f9fa')
        style_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.style_canvas.yview)
        self.style_scrollable_frame = ttk.Frame(self.style_canvas)
        
        self.style_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.style_canvas.configure(scrollregion=self.style_canvas.bbox("all"))
        )
        
        self.style_canvas_window = self.style_canvas.create_window((0, 0), window=self.style_scrollable_frame, anchor="nw")
        self.style_canvas.configure(yscrollcommand=style_scrollbar.set)
        
        def _configure_style_canvas(event):
            canvas_width = event.width - 4
            self.style_canvas.itemconfig(self.style_canvas_window, width=canvas_width)
        
        self.style_canvas.bind('<Configure>', _configure_style_canvas)
        
        self.style_canvas.pack(side="left", fill="both", expand=True)
        style_scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel binding
        def _on_style_mousewheel(event):
            self.style_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.style_canvas.bind("<MouseWheel>", _on_style_mousewheel)
        self.style_scrollable_frame.bind("<MouseWheel>", _on_style_mousewheel)
        
        # Store initial placeholder for later clearing
        self.style_placeholder_frame = ttk.Frame(self.style_scrollable_frame)
        self.style_placeholder_frame.pack(fill='x', pady=20)
        
        ttk.Label(self.style_placeholder_frame, text="Character and style references will appear here", 
                 foreground='gray').pack()
        ttk.Label(self.style_placeholder_frame, text="Generated after story analysis completes", 
                 foreground='gray', font=('Arial', 9, 'italic')).pack(pady=5)
    
    def setup_storyboard_tab(self):
        """Setup storyboard shot list display"""
        storyboard_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(storyboard_frame, text="🎬 Shot List")
        
        # Header with shot count
        header_frame = ttk.Frame(storyboard_frame)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        self.shot_count_label = ttk.Label(header_frame, text="No shots generated yet", 
                                        font=('Arial', 12, 'bold'))
        self.shot_count_label.pack(anchor='w')
        
        # Store reference to header for placeholder management
        self.storyboard_header_frame = header_frame
        
        # Scrollable storyboard container
        canvas_frame = ttk.Frame(storyboard_frame)
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create canvas with vertical scrollbar only
        self.storyboard_canvas = tk.Canvas(canvas_frame, bg='#f8f9fa')
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.storyboard_canvas.yview)
        self.storyboard_scrollable_frame = ttk.Frame(self.storyboard_canvas)
        
        self.storyboard_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.storyboard_canvas.configure(scrollregion=self.storyboard_canvas.bbox("all"))
        )
        
        self.storyboard_canvas_window = self.storyboard_canvas.create_window((0, 0), window=self.storyboard_scrollable_frame, anchor="nw")
        self.storyboard_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Configure canvas to expand the scrollable frame to full width
        def _configure_storyboard_canvas(event):
            canvas_width = event.width - 4  # Small margin to prevent overflow
            self.storyboard_canvas.itemconfig(self.storyboard_canvas_window, width=canvas_width)
        
        self.storyboard_canvas.bind('<Configure>', _configure_storyboard_canvas)
        
        self.storyboard_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to storyboard canvas (vertical only)
        def _on_storyboard_mousewheel(event):
            self.storyboard_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.storyboard_canvas.bind("<MouseWheel>", _on_storyboard_mousewheel)
        self.storyboard_scrollable_frame.bind("<MouseWheel>", _on_storyboard_mousewheel)
        
        # Store shot cards for updates
        self.shot_cards = {}
    
    def on_tab_changed(self, event):
        """Handle tab change events to refresh content"""
        if not self.db_manager:
            return
            
        selected_tab = self.content_notebook.select()
        tab_text = self.content_notebook.tab(selected_tab, "text")
        
        # Refresh content when switching to tabs that might have been updated
        if "🎬 Shot List" in tab_text:
            self.refresh_shot_list_content()
        elif "🎨 Style Refs" in tab_text:
            self.refresh_style_references_content()
        elif "🤖 AI Chat" in tab_text:
            self.refresh_ai_chat_content()
    
    def refresh_shot_list_content(self):
        """Refresh shot list content from database"""
        try:
            # Get most recent story
            recent_stories = self.db_manager.get_recent_stories(limit=1)
            if recent_stories:
                story_id = recent_stories[0]['id']
                shots = self.db_manager.get_shots_by_story_id(story_id)
                if shots:
                    # update_shot_list will handle prompts during card creation
                    self.update_shot_list(shots)
        except Exception as e:
            print(f"Error refreshing shot list: {e}")
    
    def refresh_style_references_content(self):
        """Refresh style references content from database"""
        try:
            # Get most recent story
            recent_stories = self.db_manager.get_recent_stories(limit=1)
            if recent_stories:
                story_id = recent_stories[0]['id']
                characters = self.db_manager.get_story_characters(story_id)
                locations = self.db_manager.get_story_locations(story_id)
                
                if characters or locations:
                    # Create a basic visual style dict
                    visual_style = {
                        'overall_mood': 'Generated', 
                        'characters': len(characters), 
                        'locations': len(locations)
                    }
                    self.update_style_references(characters, locations, visual_style)
        except Exception as e:
            print(f"Error refreshing style references: {e}")
    
    def refresh_ai_chat_content(self):
        """Refresh AI chat content from database"""
        try:
            if self.current_story_id:
                self.load_ai_chat_history(self.current_story_id)
            else:
                # Try to get current story ID
                recent_stories = self.db_manager.get_recent_stories(limit=1)
                if recent_stories:
                    story_id = recent_stories[0]['id']
                    self.current_story_id = story_id
                    self.load_ai_chat_history(story_id)
        except Exception as e:
            print(f"Error refreshing AI chat content: {e}")
    
    def force_refresh_all_content(self):
        """Force refresh all content tabs after UI is fully initialized"""
        if not self.db_manager:
            return
            
        try:
            # Force refresh shot list regardless of active tab
            recent_stories = self.db_manager.get_recent_stories(limit=1)
            if recent_stories:
                story_id = recent_stories[0]['id']
                shots = self.db_manager.get_shots_by_story_id(story_id)
                if shots:
                    # update_shot_list will handle prompts during card creation
                    self.update_shot_list(shots)
                
                # Force refresh style references
                characters = self.db_manager.get_story_characters(story_id)
                locations = self.db_manager.get_story_locations(story_id)
                if characters or locations:
                    visual_style = {'overall_mood': 'Generated', 'characters': len(characters), 'locations': len(locations)}
                    self.update_style_references(characters, locations, visual_style)
                
                # Load AI chat history  
                self.current_story_id = story_id
                self.load_ai_chat_history(story_id)
        except Exception as e:
            print(f"Error in force refresh: {e}")
    
    def load_ai_chat_history(self, story_id: str):
        """Load existing AI chat messages for a story"""
        if not self.db_manager or not hasattr(self, 'ai_chat'):
            return
            
        try:
            messages = self.db_manager.get_ai_chat_messages(story_id)
            if messages:
                # Clear current chat content
                self.ai_chat.config(state='normal')
                self.ai_chat.delete('1.0', tk.END)
                
                # Add historical messages
                for message in messages:
                    self.display_historical_message(message)
                
                self.ai_chat.config(state='disabled')
                self.ai_chat.see(tk.END)
                
        except Exception as e:
            print(f"Error loading AI chat history: {e}")
    
    def display_historical_message(self, message_data: dict):
        """Display a historical AI message with proper formatting"""
        try:
            message_type = message_data['message_type']
            content = message_data['content']
            step = message_data['step']
            timestamp_str = message_data['timestamp']
            
            # Parse timestamp and format it
            from datetime import datetime
            try:
                # Try parsing with full timestamp format first
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                time_display = timestamp.strftime("%H:%M:%S")
            except:
                # Fallback to simple time display
                time_display = timestamp_str[-8:] if len(timestamp_str) >= 8 else "--:--:--"
            
            # Add to chat display using existing formatting logic
            self.ai_chat.insert(tk.END, f"[{time_display}] ", 'timestamp')
            
            # Add step indicator if provided
            if step:
                self.ai_chat.insert(tk.END, f"[{step.upper()}] ", 'system')
            
            # Add message based on type
            if message_type == 'request':
                self.ai_chat.insert(tk.END, "🤖 AI Request: ", 'ai_request')
                self.ai_chat.insert(tk.END, f"{content}\n\n", 'ai_request')
            elif message_type == 'response':
                # Parse response for <think> tags
                think_content, actual_content = self.parse_ai_response(content)
                
                if think_content:
                    # Display thinking process
                    self.ai_chat.insert(tk.END, "🧠 AI Thinking: ", 'ai_think')
                    self.ai_chat.insert(tk.END, f"{think_content}\n\n", 'ai_think')
                
                # Display actual response
                self.ai_chat.insert(tk.END, "💬 AI Response: ", 'ai_response')
                self.ai_chat.insert(tk.END, f"{actual_content}\n\n", 'ai_response')
            elif message_type == 'error':
                self.ai_chat.insert(tk.END, "❌ Error: ", 'error')
                self.ai_chat.insert(tk.END, f"{content}\n\n", 'error')
            elif message_type == 'success':
                self.ai_chat.insert(tk.END, "✅ Success: ", 'success')
                self.ai_chat.insert(tk.END, f"{content}\n\n", 'success')
            else:
                self.ai_chat.insert(tk.END, f"{content}\n\n")
            
        except Exception as e:
            print(f"Error displaying historical message: {e}")
    
    def setup_ai_chat_tab(self):
        """Setup AI chat tab (for debugging)"""
        chat_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(chat_frame, text="🤖 AI Chat")
        
        # Chat display (keep existing functionality)
        self.ai_chat = scrolledtext.ScrolledText(
            chat_frame, 
            height=25, 
            wrap='word',
            font=('Consolas', 9),
            bg='#f8f9fa',
            fg='#333333',
            state='disabled'
        )
        self.ai_chat.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configure text tags for different message types
        self.ai_chat.tag_config('timestamp', foreground='#666666', font=('Consolas', 8))
        self.ai_chat.tag_config('system', foreground='#0066cc', font=('Consolas', 9, 'bold'))
        self.ai_chat.tag_config('ai_request', foreground='#cc6600')
        self.ai_chat.tag_config('ai_response', foreground='#006600')
        self.ai_chat.tag_config('ai_think', foreground='#9966cc', font=('Consolas', 8, 'italic'))
        self.ai_chat.tag_config('error', foreground='#cc0000')
        self.ai_chat.tag_config('success', foreground='#009900', font=('Consolas', 9, 'bold'))
    
    
    def update_step(self, step_key: str, progress: int, status: str, details: str = ""):
        """Update a specific step's progress with time tracking"""
        if not self.is_open or step_key not in self.step_progress:
            return
        
        # Handle step timing
        old_status = self.step_progress[step_key].get('status', 'pending')
        
        if old_status == 'pending' and status == 'processing':
            # Step just started
            self.start_step_timing(step_key)
        elif old_status == 'processing' and status == 'completed':
            # Step just completed
            self.complete_step_timing(step_key)
        
        def update_ui():
            # Update progress bar
            self.progress_bars[step_key]['value'] = progress
            
            # Update status label
            status_icons = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'error': '❌'
            }
            
            status_styles = {
                'pending': 'Pending.TLabel',
                'processing': 'Processing.TLabel', 
                'completed': 'Success.TLabel',
                'error': 'Error.TLabel'
            }
            
            icon = status_icons.get(status, '⏳')
            style = status_styles.get(status, 'Status.TLabel')
            
            self.status_labels[step_key].config(
                text=f"{icon} {status.title()}", 
                style=style
            )
            
            # Update details
            if details:
                self.step_progress[step_key]['details_label'].config(text=details[:80] + "..." if len(details) > 80 else details)
            
            # Update time display based on status
            if 'time_label' in self.step_progress[step_key]:
                if status == 'processing' and step_key in self.step_start_times:
                    # Show elapsed time for current step
                    elapsed = (datetime.now() - self.step_start_times[step_key]).total_seconds()
                    self.step_progress[step_key]['time_label'].config(text=f"Running: {format_time_estimate(int(elapsed))}")
                elif status == 'completed' and step_key in self.actual_step_times:
                    # Show actual completion time
                    actual_time = self.actual_step_times[step_key]
                    self.step_progress[step_key]['time_label'].config(text=f"Took: {format_time_estimate(int(actual_time))}")
            
            # Update overall progress
            self.update_overall_progress()
            
            # Store step data
            self.step_progress[step_key].update({
                'progress': progress,
                'status': status,
                'details': details
            })
        
        if self.window:
            self.window.after(0, update_ui)
    
    def update_step_estimates(self, shot_count: int = None, character_count: int = None):
        """Update time estimates based on actual story/shot data"""
        if not self.is_open:
            return
            
        try:
            # Convert config to dict for estimation
            config_dict = {
                'genre': getattr(self.config, 'genre', 'Drama'),
                'length': getattr(self.config, 'length', '3-5 minutes')
            }
            
            # Re-calculate estimates with actual data
            self.total_estimated_time = estimate_total_time(config_dict, shot_count, character_count)
            
            # Update step estimates
            steps = ['story', 'shots', 'characters', 'style', 'prompts', 'narration', 'music', 'queue']
            for step_key in steps:
                if step_key not in self.actual_step_times:  # Don't update completed steps
                    estimated_time = estimate_step_time(step_key, config_dict, shot_count or 0, character_count or 0)
                    self.step_estimated_times[step_key] = estimated_time
                    
                    # Update display for pending steps
                    if (step_key in self.step_progress and 
                        'time_label' in self.step_progress[step_key] and
                        self.step_progress[step_key]['status'] == 'pending'):
                        
                        time_text = f"Est: {format_time_estimate(estimated_time)}"
                        self.step_progress[step_key]['time_label'].config(text=time_text)
            
            # Update overall display
            self.update_overall_progress()
            
        except Exception as e:
            print(f"Error updating step estimates: {e}")
    
    def update_step_node_info(self, step_key: str, node_name: str, service_type: str, model: str):
        """Update render node information for a step"""
        if not self.is_open or step_key not in self.step_progress:
            return
        
        def update_node_info():
            # Format the node information
            if node_name and service_type and model:
                node_text = f"[{service_type.upper()}] {node_name} • {model}"
            elif service_type and model:
                node_text = f"[{service_type.upper()}] {model}"
            else:
                node_text = ""
            
            # Update the label
            self.step_progress[step_key]['node_info_label'].config(text=node_text)
        
        if self.window:
            self.window.after(0, update_node_info)
    
    def initialize_time_estimates(self):
        """Initialize time estimates for each step based on configuration"""
        try:
            # Convert config to dict for estimation
            config_dict = {
                'genre': getattr(self.config, 'genre', 'Drama'),
                'length': getattr(self.config, 'length', '3-5 minutes')
            }
            
            # Estimate total time
            self.total_estimated_time = estimate_total_time(config_dict)
            
            # Estimate time for each step
            steps = ['story', 'shots', 'characters', 'style', 'prompts', 'narration', 'music', 'queue']
            for step_key in steps:
                estimated_time = estimate_step_time(step_key, config_dict)
                self.step_estimated_times[step_key] = estimated_time
                
                # Update time display if step exists
                if step_key in self.step_progress and 'time_label' in self.step_progress[step_key]:
                    time_text = f"Est: {format_time_estimate(estimated_time)}"
                    self.step_progress[step_key]['time_label'].config(text=time_text)
            
            # Update overall time estimate
            if hasattr(self, 'remaining_time_label') and self.remaining_time_label:
                self.remaining_time_label.config(text=f"Estimated: {format_time_estimate(self.total_estimated_time)}")
                
        except Exception as e:
            print(f"Error initializing time estimates: {e}")
            # Set default estimates
            self.total_estimated_time = 180  # 3 minutes default
            for step_key in ['story', 'shots', 'characters', 'style', 'prompts', 'narration', 'music', 'queue']:
                self.step_estimated_times[step_key] = 22  # ~3 minutes / 8 steps
    
    def start_step_timing(self, step_key: str):
        """Start timing a specific step"""
        self.step_start_times[step_key] = datetime.now()
    
    def complete_step_timing(self, step_key: str):
        """Complete timing for a step and update estimates"""
        if step_key in self.step_start_times:
            elapsed = (datetime.now() - self.step_start_times[step_key]).total_seconds()
            self.actual_step_times[step_key] = elapsed
            
            # Update time display for completed step
            if step_key in self.step_progress and 'time_label' in self.step_progress[step_key]:
                actual_text = f"Took: {format_time_estimate(int(elapsed))}"
                self.step_progress[step_key]['time_label'].config(text=actual_text)
    
    def get_remaining_time_estimate(self) -> int:
        """Calculate remaining time based on completed steps and current progress"""
        try:
            elapsed_total = (datetime.now() - self.generation_start_time).total_seconds()
            
            # Calculate remaining time based on completed steps
            completed_time = sum(self.actual_step_times.values())
            remaining_estimated = 0
            
            for step_key, estimated_time in self.step_estimated_times.items():
                if step_key not in self.actual_step_times:
                    # Step not completed yet, use estimate
                    remaining_estimated += estimated_time
                    
                    # If this is the current step, adjust based on progress
                    if step_key in self.step_progress:
                        progress = self.step_progress[step_key].get('progress', 0)
                        if progress > 0:
                            remaining_for_current_step = estimated_time * (100 - progress) / 100
                            remaining_estimated = remaining_estimated - estimated_time + remaining_for_current_step
                            break
            
            return max(0, int(remaining_estimated))
            
        except Exception as e:
            print(f"Error calculating remaining time: {e}")
            return 60  # Default 1 minute remaining
    
    def start_periodic_updates(self):
        """Start periodic updates for time tracking"""
        self.update_running_step_times()
        
    def update_running_step_times(self):
        """Update time display for currently running steps"""
        if not self.is_open:
            return
            
        try:
            # Update elapsed time for any processing steps
            for step_key, step_data in self.step_progress.items():
                if (step_data['status'] == 'processing' and 
                    step_key in self.step_start_times and 
                    'time_label' in step_data):
                    
                    elapsed = (datetime.now() - self.step_start_times[step_key]).total_seconds()
                    step_data['time_label'].config(text=f"Running: {format_time_estimate(int(elapsed))}")
            
            # Update overall time displays
            self.update_overall_progress()
            
        except Exception as e:
            print(f"Error updating running step times: {e}")
        
        # Schedule next update
        if self.is_open:
            self.window.after(2000, self.update_running_step_times)  # Update every 2 seconds
    
    def update_overall_progress(self):
        """Update the overall progress bar and time estimates"""
        # Calculate overall progress based on individual step progress
        total_progress = 0
        for step_data in self.step_progress.values():
            if step_data['status'] == 'completed':
                total_progress += 100
            elif step_data['status'] == 'processing':
                total_progress += step_data.get('progress', 0)
            # pending steps contribute 0
        
        overall_progress = total_progress / self.total_steps if self.total_steps > 0 else 0
        completed_steps = sum(1 for step in self.step_progress.values() if step['status'] == 'completed')
        
        self.overall_progress['value'] = overall_progress
        
        # Update elapsed time
        elapsed = (datetime.now() - self.generation_start_time).total_seconds()
        if hasattr(self, 'elapsed_time_label') and self.elapsed_time_label:
            self.elapsed_time_label.config(text=f"Elapsed: {format_time_estimate(int(elapsed))}")
        
        # Update remaining time estimate
        remaining = self.get_remaining_time_estimate()
        if hasattr(self, 'remaining_time_label') and self.remaining_time_label:
            if completed_steps == self.total_steps:
                self.remaining_time_label.config(text="✅ Complete!")
            else:
                self.remaining_time_label.config(text=f"Remaining: {format_time_estimate(remaining)}")
        
        if completed_steps == self.total_steps:
            self.overall_status.config(text="✅ Generation Complete!")
        else:
            processing_step = next((k for k, v in self.step_progress.items() if v['status'] == 'processing'), None)
            if processing_step:
                step_title = next(s['title'] for s in self.steps if s['key'] == processing_step)
                self.overall_status.config(text=f"Processing: {step_title}... (ETA: {format_time_estimate(remaining)})")
    
    def setup_chat_section(self, parent):
        """Setup the AI chat response section"""
        # Chat display
        self.ai_chat = scrolledtext.ScrolledText(
            parent, 
            height=25, 
            wrap='word',
            font=('Consolas', 9),
            bg='#f8f9fa',
            fg='#333333',
            state='disabled'
        )
        self.ai_chat.pack(fill='both', expand=True)
        
        # Configure text tags for different message types
        self.ai_chat.tag_config('timestamp', foreground='#666666', font=('Consolas', 8))
        self.ai_chat.tag_config('system', foreground='#0066cc', font=('Consolas', 9, 'bold'))
        self.ai_chat.tag_config('ai_request', foreground='#cc6600')
        self.ai_chat.tag_config('ai_response', foreground='#006600')
        self.ai_chat.tag_config('ai_think', foreground='#9966cc', font=('Consolas', 8, 'italic'))
        self.ai_chat.tag_config('error', foreground='#cc0000')
        self.ai_chat.tag_config('success', foreground='#009900', font=('Consolas', 9, 'bold'))
    
    def parse_ai_response(self, content: str):
        """Parse AI response to separate <think> tags from actual content"""
        think_content = ""
        actual_content = content
        
        # Extract <think> content
        think_start = content.find('<think>')
        think_end = content.find('</think>')
        
        if think_start >= 0 and think_end >= 0 and think_end > think_start:
            # Extract thinking content
            think_content = content[think_start + 7:think_end].strip()
            
            # Remove <think> tags from actual content
            actual_content = content[:think_start] + content[think_end + 8:]
            actual_content = actual_content.strip()
        
        return think_content, actual_content
    
    def add_ai_message(self, message_type: str, content: str, step: str = ""):
        """Add full message to AI chat section with <think> tag handling"""
        if not self.is_open:
            return
        
        # Save message to database if we have a story ID
        if self.current_story_id and self.db_manager:
            try:
                self.db_manager.save_ai_chat_message(self.current_story_id, message_type, content, step)
            except Exception as e:
                print(f"Warning: Could not save AI message to database: {e}")
        
        def add_message():
            self.ai_chat.config(state='normal')
            
            # Add timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.ai_chat.insert(tk.END, f"[{timestamp}] ", 'timestamp')
            
            # Add step indicator if provided
            if step:
                self.ai_chat.insert(tk.END, f"[{step.upper()}] ", 'system')
            
            # Add message based on type
            if message_type == 'request':
                self.ai_chat.insert(tk.END, "🤖 AI Request: ", 'ai_request')
                self.ai_chat.insert(tk.END, f"{content}\n\n", 'ai_request')
            elif message_type == 'response':
                # Parse response for <think> tags
                think_content, actual_content = self.parse_ai_response(content)
                
                if think_content:
                    # Display thinking process
                    self.ai_chat.insert(tk.END, "🧠 AI Thinking: ", 'ai_think')
                    self.ai_chat.insert(tk.END, f"{think_content}\n\n", 'ai_think')
                
                # Display actual response
                self.ai_chat.insert(tk.END, "💬 AI Response: ", 'ai_response')
                self.ai_chat.insert(tk.END, f"{actual_content}\n\n", 'ai_response')
            elif message_type == 'error':
                self.ai_chat.insert(tk.END, "❌ Error: ", 'error')
                self.ai_chat.insert(tk.END, f"{content}\n\n", 'error')
            elif message_type == 'success':
                self.ai_chat.insert(tk.END, "✅ Success: ", 'success')
                self.ai_chat.insert(tk.END, f"{content}\n\n", 'success')
            else:
                self.ai_chat.insert(tk.END, f"{content}\n\n")
            
            self.ai_chat.config(state='disabled')
            self.ai_chat.see(tk.END)
        
        if self.window:
            self.window.after(0, add_message)
    
    def get_cleaned_ai_response(self, content: str):
        """Get AI response with <think> tags removed for actual use"""
        _, actual_content = self.parse_ai_response(content)
        return actual_content
    
    def update_story_title(self, title: str):
        """Update the story title at the top"""
        if not self.is_open:
            return
        
        def update_title():
            self.story_title = title
            self.title_label.config(text=title)
            self.window.title(f"Generating: {title}")
        
        if self.window:
            self.window.after(0, update_title)
    
    
    def load_existing_content(self):
        """Load existing content when popup is opened mid-generation"""
        if not self.db_manager:
            return
            
        try:
            # Get the most recent story that might be in progress
            recent_stories = self.db_manager.get_recent_stories(limit=1)
            if not recent_stories:
                return
                
            story_data = recent_stories[0]
            story_id = story_data['id']
            
            # Load and display story content
            if story_data:
                # Convert database dict to format expected by update methods
                story_dict = {
                    'title': story_data.get('title', 'Untitled Story'),
                    'content': story_data.get('content', ''),
                    'full_story': story_data.get('content', ''),
                    'duration': story_data.get('duration', 'Unknown duration'),
                    'genre': story_data.get('genre', 'Unknown')
                }
                self.update_story_content(story_dict)
                
                # Update window title with story title
                if story_dict['title'] != 'Untitled Story':
                    self.update_story_title(story_dict['title'])
                
                # Set current story ID for chat message saving
                self.current_story_id = story_id
            
            # Load and display shots if they exist
            shots = self.db_manager.get_shots_by_story_id(story_id)
            if shots:
                # update_shot_list will handle prompts during card creation
                self.update_shot_list(shots)
            
            # Load and display character/style references if they exist
            characters = self.db_manager.get_story_characters(story_id)
            locations = self.db_manager.get_story_locations(story_id)
            
            if characters or locations:
                # Create a basic visual style dict for consistency
                visual_style = {'overall_mood': 'Generated', 'characters': len(characters), 'locations': len(locations)}
                self.update_style_references(characters, locations, visual_style)
            
            # Try to determine current progress state from story status
            story_status = story_data.get('status', 'pending')
            if story_status == 'ready':
                # Story is complete - set all progress bars to complete
                self.set_completed_state()
            elif story_status == 'generating':
                # Story is in progress - try to determine current step
                self.estimate_current_progress(story_data, shots, characters)
                        
        except Exception as e:
            print(f"Error loading existing content: {e}")
    
    def set_completed_state(self):
        """Set all progress bars to completed state"""
        steps = ['story', 'shots', 'characters', 'style', 'prompts', 'narration', 'music', 'queue']
        for step in steps:
            self.update_step(step, 100, 'completed', f'{step.title()} generation complete')
    
    def estimate_current_progress(self, story_data, shots, characters):
        """Estimate current progress based on available data"""
        # Story exists, so mark as complete
        self.update_step('story', 100, 'completed', f'Story: {story_data.get("title", "Untitled")}')
        
        # If shots exist, mark shots as complete
        if shots:
            self.update_step('shots', 100, 'completed', f'{len(shots)} shots created')
            
            # If characters exist, mark character analysis as complete
            if characters:
                self.update_step('characters', 100, 'completed', f'{len(characters)} characters analyzed')
            
            # Check shot completion status
            shots_with_prompts = sum(1 for shot in shots if shot.get('wan_prompt', '').strip())
            shots_with_narration = sum(1 for shot in shots if shot.get('narration', '').strip())
            shots_with_music = sum(1 for shot in shots if shot.get('music_cue', '').strip())
            
            total_shots = len(shots)
            if shots_with_prompts == total_shots:
                self.update_step('prompts', 100, 'completed', f'{total_shots} visual prompts generated')
            elif shots_with_prompts > 0:
                progress = int((shots_with_prompts / total_shots) * 100)
                self.update_step('prompts', progress, 'processing', f'{shots_with_prompts}/{total_shots} shots have prompts')
            
            if shots_with_narration > 0:
                if shots_with_narration == total_shots:
                    self.update_step('narration', 100, 'completed', f'{total_shots} narration scripts created')
                else:
                    progress = int((shots_with_narration / total_shots) * 100)
                    self.update_step('narration', progress, 'processing', f'{shots_with_narration}/{total_shots} shots have narration')
            
            if shots_with_music > 0:
                if shots_with_music == total_shots:
                    self.update_step('music', 100, 'completed', f'{total_shots} music cues defined')
                else:
                    progress = int((shots_with_music / total_shots) * 100)
                    self.update_step('music', progress, 'processing', f'{shots_with_music}/{total_shots} shots have music')
        
        # Update overall progress
        self.update_overall_progress()
    
    # Content Display Update Methods
    
    def update_story_content(self, story_data: dict):
        """Update the story content display"""
        if not self.is_open or not hasattr(self, 'story_content'):
            return
            
        def update_content():
            # Update title and metadata
            self.story_title_display.config(text=story_data.get('title', 'Untitled Story'))
            
            duration = story_data.get('duration', 'Unknown duration')
            genre = getattr(self.config, 'genre', 'Unknown genre')
            metadata = f"{genre} • {duration}"
            self.story_metadata.config(text=metadata)
            
            # Update story content
            self.story_content.config(state='normal')
            self.story_content.delete('1.0', tk.END)
            
            # Insert formatted story content
            content = story_data.get('content', story_data.get('full_story', ''))
            if content:
                self.format_and_insert_story(content, story_data)
            else:
                self.story_content.insert(tk.END, "Story content not available", 'content')
            
            self.story_content.config(state='disabled')
        
        if self.window:
            self.window.after(0, update_content)
    
    def format_and_insert_story(self, content: str, story_data: dict):
        """Format and insert story content with proper styling"""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                self.story_content.insert(tk.END, '\n')
                continue
                
            # Format different parts of the story
            if line.startswith('Title:'):
                self.story_content.insert(tk.END, line, 'title')
                self.story_content.insert(tk.END, '\n')
            elif line.startswith('Logline:'):
                self.story_content.insert(tk.END, line, 'logline')
                self.story_content.insert(tk.END, '\n')
            elif line.startswith('PART ') or line.startswith('Duration:'):
                self.story_content.insert(tk.END, line, 'part_header')
                self.story_content.insert(tk.END, '\n')
            elif line.startswith('HOOK:'):
                self.story_content.insert(tk.END, line, 'hook')
                self.story_content.insert(tk.END, '\n')
            else:
                self.story_content.insert(tk.END, line, 'content')
                self.story_content.insert(tk.END, '\n')
    
    def update_shot_list(self, shots: list):
        """Update the storyboard shot list display"""
        if not self.is_open or not hasattr(self, 'shot_cards'):
            return
        
        def update_shots():
            try:
                # Update header
                shot_count = len(shots)
                self.shot_count_label.config(text=f"Shot List ({shot_count} shots)")
                
                # Clear existing shots
                for widget in self.storyboard_scrollable_frame.winfo_children():
                    widget.destroy()
                self.shot_cards.clear()
                
                # Add shots in grid layout
                for idx, shot in enumerate(shots):
                    self.create_shot_card(shot, idx)
                
            except Exception as e:
                print(f"Error in update_shots: {e}")
                import traceback
                traceback.print_exc()
            
            # Update scroll region
            self.storyboard_scrollable_frame.update_idletasks()
            self.storyboard_canvas.configure(scrollregion=self.storyboard_canvas.bbox("all"))
        
        if self.window:
            self.window.after(0, update_shots)
    
    def create_shot_card(self, shot, index: int):
        """Create a shot card for the storyboard"""
        # Handle both dict and object formats
        def get_attr(obj, attr, default=None):
            if isinstance(obj, dict):
                return obj.get(attr, default)
            else:
                return getattr(obj, attr, default)
        
        shot_number = get_attr(shot, 'shot_number', index + 1)
        wan_prompt = get_attr(shot, 'wan_prompt', '')
        
        # Create shot card frame in vertical layout
        card_frame = ttk.LabelFrame(self.storyboard_scrollable_frame, 
                                   text=f"Shot {shot_number}", 
                                   padding="10")
        card_frame.pack(fill='x', padx=5, pady=5)
        
        # Compact vertical layout for shot card
        # Preview placeholder (small and centered)
        preview_placeholder = tk.Label(card_frame, 
                                     text="📷 ComfyUI Render", 
                                     bg='#e9ecef', fg='#6c757d',
                                     font=('Arial', 8),
                                     width=20, height=2,
                                     justify='center')
        preview_placeholder.pack(pady=(0, 8))
        
        # Shot details in compact format
        details_frame = ttk.Frame(card_frame)
        details_frame.pack(fill='x')
        
        # Duration and camera info (single line)
        duration = get_attr(shot, 'duration', '0')
        camera = get_attr(shot, 'camera', '')
        
        info_text = f"Duration: {duration}s"
        if camera:
            info_text += f" • {camera}"
        
        ttk.Label(details_frame, text=info_text, 
                 font=('Arial', 8), foreground='gray').pack(anchor='w')
        
        # Shot description (compact)
        description_text = tk.Text(details_frame, 
                                 height=2, wrap='word',
                                 font=('Arial', 9),
                                 bg='#f8f9fa', fg='#333333',
                                 state='disabled')
        description_text.pack(fill='x', pady=(3, 5))
        
        # Insert description
        description_text.config(state='normal')
        description = get_attr(shot, 'description', 'No description available')
        description_text.insert(tk.END, description)
        description_text.config(state='disabled')
        
        # ComfyUI Prompts Section
        prompts_frame = ttk.LabelFrame(card_frame, text="ComfyUI Prompts", padding="8")
        prompts_frame.pack(fill='x', pady=(5, 5))
        
        # Positive Prompt
        ttk.Label(prompts_frame, text="Positive:", font=('Arial', 8, 'bold')).pack(anchor='w')
        positive_prompt_text = tk.Text(prompts_frame, 
                                     height=3, wrap='word',
                                     font=('Arial', 8),
                                     bg='#f8fff8', fg='#333333',
                                     state='disabled')
        positive_prompt_text.pack(fill='x', pady=(2, 8))
        
        # Negative Prompt
        ttk.Label(prompts_frame, text="Negative:", font=('Arial', 8, 'bold')).pack(anchor='w')
        negative_prompt_text = tk.Text(prompts_frame, 
                                     height=2, wrap='word',
                                     font=('Arial', 8),
                                     bg='#fff8f8', fg='#333333',
                                     state='disabled')
        negative_prompt_text.pack(fill='x', pady=(2, 5))
        
        # Fill with prompt data or pending state
        if wan_prompt and wan_prompt.strip():
            # Parse positive/negative from wan_prompt
            positive, negative = self._parse_wan_prompt(wan_prompt)
            
            positive_prompt_text.config(state='normal', bg='#f8fff8')
            positive_prompt_text.insert(tk.END, positive)
            positive_prompt_text.config(state='disabled')
            
            negative_prompt_text.config(state='normal', bg='#fff8f8')
            negative_prompt_text.insert(tk.END, negative)
            negative_prompt_text.config(state='disabled')
        else:
            # Show pending state
            positive_prompt_text.config(state='normal', bg='#f5f5f5')
            positive_prompt_text.insert(tk.END, "⏳ Pending generation...")
            positive_prompt_text.config(state='disabled')
            
            negative_prompt_text.config(state='normal', bg='#f5f5f5')
            negative_prompt_text.insert(tk.END, "⏳ Pending generation...")
            negative_prompt_text.config(state='disabled')
        
        # Narration Section (if available)
        narration_text = get_attr(shot, 'narration', '')
        if narration_text and narration_text.strip():
            narration_frame = ttk.LabelFrame(card_frame, text="Narration Script", padding="5")
            narration_frame.pack(fill='x', pady=(5, 0))
            
            narration_widget = tk.Text(narration_frame, 
                                     height=2, wrap='word',
                                     font=('Arial', 8),
                                     bg='#fffef8', fg='#333333',
                                     state='disabled')
            narration_widget.pack(fill='x', pady=2)
            
            narration_widget.config(state='normal')
            narration_widget.insert(tk.END, narration_text)
            narration_widget.config(state='disabled')
        
        # Music Section (if available)
        music_text = get_attr(shot, 'music_cue', '')
        if music_text and music_text.strip():
            music_frame = ttk.LabelFrame(card_frame, text="Music Cue", padding="5")
            music_frame.pack(fill='x', pady=(5, 0))
            
            music_widget = tk.Text(music_frame, 
                                 height=2, wrap='word',
                                 font=('Arial', 8),
                                 bg='#f8f8ff', fg='#333333',
                                 state='disabled')
            music_widget.pack(fill='x', pady=2)
            
            music_widget.config(state='normal')
            music_widget.insert(tk.END, music_text)
            music_widget.config(state='disabled')
        
        # Status indicators (inline)
        status_frame = ttk.Frame(details_frame)
        status_frame.pack(fill='x', pady=(0, 5))
        
        # Visual prompt status
        prompt_status = "✅" if wan_prompt and wan_prompt.strip() else "⏳"
        ttk.Label(status_frame, text=f"{prompt_status} Prompt", font=('Arial', 8)).pack(side='left')
        
        # Narration status  
        narration_status = "✅" if narration_text and narration_text.strip() else "⏳"
        ttk.Label(status_frame, text=f"{narration_status} Audio", font=('Arial', 8)).pack(side='left', padx=(10, 0))
        
        # Music status
        music_status = "✅" if music_text and music_text.strip() else "⏳"
        ttk.Label(status_frame, text=f"{music_status} Music", font=('Arial', 8)).pack(side='right')
        
        # Progress bar at bottom
        render_progress = ttk.Progressbar(card_frame, mode='determinate')
        render_progress.pack(fill='x', pady=(5, 0))
        render_progress['value'] = 0
        
        # Store card references (including optional widgets)
        card_refs = {
            'frame': card_frame,
            'progress': render_progress,
            'preview': preview_placeholder,
            'description': description_text,
            'positive_prompt': positive_prompt_text,
            'negative_prompt': negative_prompt_text
        }
        
        # Add narration widget reference if it exists
        if narration_text and narration_text.strip():
            card_refs['narration_widget'] = narration_widget
        
        # Add music widget reference if it exists  
        if music_text and music_text.strip():
            card_refs['music_widget'] = music_widget
            
        self.shot_cards[shot_number] = card_refs
    
    def _parse_wan_prompt(self, wan_prompt: str) -> tuple[str, str]:
        """Parse wan_prompt to extract positive and negative prompts"""
        if not wan_prompt or not wan_prompt.strip():
            return ("⏳ Pending generation...", "⏳ Pending generation...")
        
        # Split by "Negative:" keyword if present
        parts = wan_prompt.split("Negative:")
        
        positive = parts[0].strip()
        # Remove "Positive:" prefix if present
        if positive.startswith("Positive:"):
            positive = positive[9:].strip()
        
        negative = ""
        if len(parts) > 1:
            negative = parts[1].strip()
            # Remove any trailing settings or other content after negative prompt
            if "\nSettings:" in negative:
                negative = negative.split("\nSettings:")[0].strip()
        
        # Fallback for empty prompts
        if not positive:
            positive = "⏳ Prompt not yet generated"
        if not negative:
            negative = "text, watermark, blurry, distorted, extra limbs, low quality, bad anatomy"
        
        return (positive, negative)
    
    def update_shot_prompts(self, shot_number: int, wan_prompt: str):
        """Update the ComfyUI prompts for a specific shot (only used during real-time generation)"""
        if not self.is_open:
            return
        
        if shot_number not in self.shot_cards:
            # This can happen if the shot list hasn't been created yet
            return
            
        def update_prompts():
            # Parse the wan_prompt
            positive, negative = self._parse_wan_prompt(wan_prompt)
            
            # Get the text widgets
            positive_widget = self.shot_cards[shot_number]['positive_prompt']
            negative_widget = self.shot_cards[shot_number]['negative_prompt']
            
            # Update positive prompt
            positive_widget.config(state='normal', bg='#f8fff8')
            positive_widget.delete(1.0, tk.END)
            positive_widget.insert(tk.END, positive)
            positive_widget.config(state='disabled')
            
            # Update negative prompt
            negative_widget.config(state='normal', bg='#fff8f8')
            negative_widget.delete(1.0, tk.END)
            negative_widget.insert(tk.END, negative)
            negative_widget.config(state='disabled')
        
        if self.window:
            self.window.after(0, update_prompts)
    
    def update_shot_narration(self, shot_number: int, narration: str):
        """Update narration for a specific shot (future-proof for real-time updates)"""
        if not self.is_open or shot_number not in self.shot_cards:
            return
        
        def update_narration():
            card_refs = self.shot_cards[shot_number]
            
            # If narration widget doesn't exist, we need to recreate the shot card
            if 'narration_widget' not in card_refs and narration and narration.strip():
                # For now, we'll need to recreate the entire shot card
                # This is a limitation that could be improved in the future
                return
            
            # Update existing narration widget
            if 'narration_widget' in card_refs:
                narration_widget = card_refs['narration_widget']
                narration_widget.config(state='normal')
                narration_widget.delete(1.0, tk.END)
                narration_widget.insert(tk.END, narration)
                narration_widget.config(state='disabled')
        
        if self.window:
            self.window.after(0, update_narration)
    
    def update_shot_music(self, shot_number: int, music_cue: str):
        """Update music cue for a specific shot (future-proof for real-time updates)"""
        if not self.is_open or shot_number not in self.shot_cards:
            return
        
        def update_music():
            card_refs = self.shot_cards[shot_number]
            
            # If music widget doesn't exist, we need to recreate the shot card
            if 'music_widget' not in card_refs and music_cue and music_cue.strip():
                # For now, we'll need to recreate the entire shot card
                # This is a limitation that could be improved in the future
                return
            
            # Update existing music widget
            if 'music_widget' in card_refs:
                music_widget = card_refs['music_widget']
                music_widget.config(state='normal')
                music_widget.delete(1.0, tk.END)
                music_widget.insert(tk.END, music_cue)
                music_widget.config(state='disabled')
        
        if self.window:
            self.window.after(0, update_music)
    
    def update_shot_render_progress(self, shot_number: int, progress: float):
        """Update render progress for a specific shot (future ComfyUI integration)"""
        if not self.is_open or shot_number not in self.shot_cards:
            return
        
        def update_progress():
            progress_bar = self.shot_cards[shot_number]['progress']
            progress_bar['value'] = progress
        
        if self.window:
            self.window.after(0, update_progress)
    
    def update_style_references(self, characters: list, locations: list, visual_style: dict):
        """Update the style references display"""
        if not self.is_open or not hasattr(self, 'style_scrollable_frame'):
            return
            
        def update_references():
            # Clear existing content including placeholder
            for widget in self.style_scrollable_frame.winfo_children():
                widget.destroy()
            
            # Clear placeholder reference if it exists
            if hasattr(self, 'style_placeholder_frame'):
                try:
                    self.style_placeholder_frame.destroy()
                except:
                    pass
            
            # Create content sections
            main_frame = ttk.Frame(self.style_scrollable_frame)
            main_frame.pack(fill='x', padx=10, pady=10)
            
            # Characters section
            if characters:
                char_frame = ttk.LabelFrame(main_frame, text="Characters", padding="10")
                char_frame.pack(fill='x', pady=(0, 10))
                
                for char in characters:
                    # Character card
                    card_frame = ttk.Frame(char_frame)
                    card_frame.pack(fill='x', pady=5)
                    
                    # Character info
                    info_frame = ttk.Frame(card_frame)
                    info_frame.pack(fill='x')
                    
                    # Name and role
                    name_label = ttk.Label(info_frame, text=f"{char['name']} ({char['role']})", 
                                         font=('Arial', 11, 'bold'))
                    name_label.pack(anchor='w')
                    
                    # Description
                    desc_label = ttk.Label(info_frame, text=char['physical_description'], 
                                         font=('Arial', 9), wraplength=400)
                    desc_label.pack(anchor='w', pady=2)
                    
                    # Additional details
                    details = []
                    if char.get('age_range'):
                        details.append(f"Age: {char['age_range']}")
                    if char.get('clothing_style'):
                        details.append(f"Style: {char['clothing_style']}")
                    if char.get('importance_level'):
                        details.append(f"Importance: {char['importance_level']}/3")
                    
                    if details:
                        detail_label = ttk.Label(info_frame, text=" • ".join(details), 
                                               font=('Arial', 8), foreground='gray')
                        detail_label.pack(anchor='w')
                    
                    # Separator
                    ttk.Separator(char_frame, orient='horizontal').pack(fill='x', pady=5)
            
            # Locations section
            if locations:
                loc_frame = ttk.LabelFrame(main_frame, text="Locations", padding="10")
                loc_frame.pack(fill='x', pady=(0, 10))
                
                for loc in locations:
                    # Location card
                    card_frame = ttk.Frame(loc_frame)
                    card_frame.pack(fill='x', pady=5)
                    
                    # Location info
                    info_frame = ttk.Frame(card_frame)
                    info_frame.pack(fill='x')
                    
                    # Name
                    name_label = ttk.Label(info_frame, text=loc['name'], 
                                         font=('Arial', 11, 'bold'))
                    name_label.pack(anchor='w')
                    
                    # Description
                    desc_label = ttk.Label(info_frame, text=loc['description'], 
                                         font=('Arial', 9), wraplength=400)
                    desc_label.pack(anchor='w', pady=2)
                    
                    # Additional details
                    details = []
                    if loc.get('time_of_day'):
                        details.append(f"Time: {loc['time_of_day']}")
                    if loc.get('lighting_style'):
                        details.append(f"Lighting: {loc['lighting_style']}")
                    if loc.get('weather_mood'):
                        details.append(f"Mood: {loc['weather_mood']}")
                    
                    if details:
                        detail_label = ttk.Label(info_frame, text=" • ".join(details), 
                                               font=('Arial', 8), foreground='gray')
                        detail_label.pack(anchor='w')
                    
                    # Separator
                    ttk.Separator(loc_frame, orient='horizontal').pack(fill='x', pady=5)
            
            # Visual style section
            if visual_style:
                style_frame = ttk.LabelFrame(main_frame, text="Visual Style", padding="10")
                style_frame.pack(fill='x', pady=(0, 10))
                
                style_info = ttk.Frame(style_frame)
                style_info.pack(fill='x')
                
                # Style details
                style_details = []
                if visual_style.get('overall_mood'):
                    style_details.append(f"Mood: {visual_style['overall_mood']}")
                if visual_style.get('color_palette'):
                    style_details.append(f"Colors: {visual_style['color_palette']}")
                if visual_style.get('cinematography'):
                    style_details.append(f"Style: {visual_style['cinematography']}")
                if visual_style.get('era_setting'):
                    style_details.append(f"Era: {visual_style['era_setting']}")
                
                for detail in style_details:
                    ttk.Label(style_info, text=f"• {detail}", font=('Arial', 10)).pack(anchor='w')
            
            # Update header
            total_refs = len(characters) + len(locations) + (1 if visual_style else 0)
            self.style_header_label.config(text=f"Character & Style References ({total_refs} items)")
            
            # Update scroll region
            self.style_scrollable_frame.update_idletasks()
            self.style_canvas.configure(scrollregion=self.style_canvas.bbox("all"))
        
        if self.window:
            self.window.after(0, update_references)
    
    def update_shot_status(self, shot_number: int, status: str, progress: int = 0):
        """Update individual shot rendering status"""
        if shot_number not in self.shot_cards:
            return
            
        def update_status():
            card = self.shot_cards[shot_number]
            card['progress']['value'] = progress
            
            # Update preview placeholder based on status
            if status == 'rendering':
                card['preview'].config(text=f"🎬 Rendering...\n{progress}%", bg='#fff3cd')
            elif status == 'completed':
                card['preview'].config(text="✅ Render Complete", bg='#d4edda')
            elif status == 'error':
                card['preview'].config(text="❌ Render Failed", bg='#f8d7da')
        
        if self.window:
            self.window.after(0, update_status)
    
    def close(self):
        """Close the progress window"""
        if not self.is_open:
            return
        
        self.is_open = False
        
        if self.on_complete_callback:
            self.on_complete_callback()
        
        if self.window:
            self.window.grab_release()
            self.window.destroy()
            self.window = None
    
    def on_window_close(self):
        """Handle window close event"""
        self.close()

# Integration class for the main application
class EnhancedGenerationManager:
    """Enhanced generation manager with progress popup"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.progress_window = None
    
    def start_generation_with_popup(self, config):
        """Start generation with progress popup"""
        # Create progress window with database manager
        self.progress_window = GenerationProgressWindow(
            self.main_app.root, 
            config,
            self.on_generation_complete,
            self.main_app.db
        )
        
        # Start generation in thread
        generation_thread = threading.Thread(
            target=self.enhanced_generation_worker, 
            args=(config,), 
            daemon=True
        )
        generation_thread.start()
    
    def enhanced_generation_worker(self, config):
        """Enhanced generation worker with detailed progress tracking"""
        try:
            # Step 1: Generate story
            self.progress_window.update_step('story', 10, 'processing', 'Sending prompt to AI...')
            self.progress_window.add_ai_message('request', f"Generate {config.genre} story: {config.prompt}", 'story')
            
            story = self.main_app.story_gen.generate_story(config)
            
            if story:
                self.progress_window.update_story_title(story['title'])
                self.progress_window.add_ai_message('response', f"Generated story: {story['title']}", 'story')
                self.progress_window.update_step('story', 100, 'completed', f"Created: {story['title']}")
                
                # Step 2: Create shots
                self.progress_window.update_step('shots', 10, 'processing', 'Breaking story into shots...')
                self.progress_window.add_ai_message('request', 'Creating detailed shot list...', 'shots')
                
                shots = self.main_app.story_gen.create_shot_list(story)
                
                if shots:
                    self.progress_window.add_ai_message('response', f"Created {len(shots)} shots", 'shots')
                    self.progress_window.update_step('shots', 100, 'completed', f"{len(shots)} shots created")
                    
                    # Update time estimates with actual shot count
                    if hasattr(self.progress_window, 'update_step_estimates'):
                        self.progress_window.update_step_estimates(shot_count=len(shots))
                    
                    # Step 3: Character Analysis
                    self.progress_window.update_step('characters', 10, 'processing', 'Analyzing characters and locations...')
                    self.progress_window.add_ai_message('request', 'Extracting character and location data...', 'characters')
                    
                    try:
                        characters, locations, visual_style = self.main_app.story_gen.analyze_story_characters_and_locations(story)
                        character_prompts = self.main_app.story_gen.generate_character_comfyui_prompts(characters)
                        
                        self.progress_window.add_ai_message('response', f"Found {len(characters)} characters, {len(locations)} locations", 'characters')
                        self.progress_window.update_step('characters', 100, 'completed', f"{len(characters)} characters analyzed")
                        
                        # Update time estimates with actual character count
                        if hasattr(self.progress_window, 'update_step_estimates'):
                            self.progress_window.update_step_estimates(shot_count=len(shots), character_count=len(characters))
                        
                        # Update style references display
                        if hasattr(self.progress_window, 'update_style_references'):
                            self.progress_window.update_style_references(characters, locations, visual_style)
                        
                    except Exception as e:
                        self.progress_window.add_ai_message('error', f"Character analysis failed: {str(e)}", 'characters')
                        self.progress_window.update_step('characters', 0, 'error', 'Analysis failed')
                    
                    # Step 4: Style Sheets (placeholder)
                    self.progress_window.update_step('style', 10, 'processing', 'Processing style sheets...')
                    self.progress_window.add_ai_message('request', 'Style sheet processing (placeholder)...', 'style')
                    self.progress_window.update_step('style', 100, 'completed', 'Placeholder completed')
                    
                    # Step 5-7: Process each shot
                    total_shots = len(shots)
                    for idx, shot in enumerate(shots):
                        shot_progress = (idx / total_shots) * 100
                        
                        # Prompts
                        self.progress_window.update_step('prompts', shot_progress, 'processing', f'Shot {idx+1}/{total_shots}')
                        self.progress_window.add_ai_message('request', f"Generating visual prompt for shot {shot.shot_number}", 'prompts')
                        
                        self.main_app.story_gen.generate_wan_prompt(shot)
                        
                        # Narration  
                        self.progress_window.update_step('narration', shot_progress, 'processing', f'Shot {idx+1}/{total_shots}')
                        self.progress_window.add_ai_message('request', f"Creating narration for shot {shot.shot_number}", 'narration')
                        
                        self.main_app.story_gen.generate_elevenlabs_script(shot)
                        
                        # Music (if needed)
                        if shot.music_cue:
                            self.progress_window.update_step('music', shot_progress, 'processing', f'Shot {idx+1}/{total_shots}')
                            self.progress_window.add_ai_message('request', f"Defining music for shot {shot.shot_number}", 'music')
                            
                            self.main_app.story_gen.generate_suno_prompt(shot)
                    
                    # Complete steps
                    self.progress_window.update_step('prompts', 100, 'completed', f'{total_shots} visual prompts generated')
                    self.progress_window.update_step('narration', 100, 'completed', f'{total_shots} narration scripts created')
                    self.progress_window.update_step('music', 100, 'completed', 'Music cues defined')
                    
                    # Refresh the shot list with all final data to ensure prompts are displayed
                    updated_shots = self.main_app.db.get_shots_by_story_id(story['id'])
                    if updated_shots:
                        # update_shot_list will handle all prompts during card creation
                        self.progress_window.update_shot_list(updated_shots)
                    
                    # Step 6: Queue setup
                    self.progress_window.update_step('queue', 50, 'processing', 'Adding shots to render queue...')
                    
                    for shot in shots:
                        priority = 10 if shot.shot_number == 1 else 5
                        self.main_app.db.add_to_render_queue(shot.id, priority)
                    
                    self.progress_window.update_step('queue', 100, 'completed', f'{total_shots} shots queued for rendering')
                    self.progress_window.add_ai_message('success', f"Story '{story['title']}' fully generated and queued!", 'complete')
                    
                else:
                    self.progress_window.update_step('shots', 0, 'error', 'Failed to create shot list')
                    self.progress_window.add_ai_message('error', 'Shot list generation failed', 'shots')
            else:
                self.progress_window.update_step('story', 0, 'error', 'Story generation failed')
                self.progress_window.add_ai_message('error', 'Story generation failed', 'story')
                
        except Exception as e:
            self.progress_window.add_ai_message('error', f'Generation error: {str(e)}', 'system')
    
    def on_generation_complete(self):
        """Called when generation popup closes"""
        self.progress_window = None
        # Refresh main app displays
        self.main_app.refresh_recent_stories()
        self.main_app.refresh_queue()
        self.main_app.refresh_metrics()
        
        # Auto-randomize inputs for next generation
        self.main_app.randomize_inputs()
        self.main_app.add_log("Auto-randomized settings for next generation", "Info")