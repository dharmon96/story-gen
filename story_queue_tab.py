"""
Story Queue Tab GUI Component
Provides interface for managing story generation queue
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional

from story_queue import StoryQueue
from data_models import StoryConfig, QueueConfig
from generation_progress_popup import GenerationProgressWindow


class StoryQueueTab:
    """GUI component for story queue management"""
    
    def __init__(self, parent_frame, story_queue: StoryQueue, 
                 story_generator=None, db_manager=None, main_app=None):
        self.parent_frame = parent_frame
        self.story_queue = story_queue
        self.story_generator = story_generator
        self.db = db_manager
        self.main_app = main_app
        
        # Progress windows for each queue item
        self.progress_windows = {}
        
        # Refresh timer
        self.refresh_timer = None
        
        # Setup UI
        self.setup_ui()
        
        # Set up callbacks
        self.story_queue.set_callbacks(
            progress_callback=self.on_queue_progress,
            completion_callback=self.on_queue_completion,
            error_callback=self.on_queue_error
        )
        
        # Start auto-refresh
        self.start_auto_refresh()
    
    def setup_ui(self):
        """Setup the queue tab UI"""
        main_frame = ttk.Frame(self.parent_frame, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Story Generation Queue", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Control Panel
        self.setup_control_panel(main_frame)
        
        # Queue Statistics
        self.setup_statistics_panel(main_frame)
        
        # Queue List
        self.setup_queue_list(main_frame)
        
        # Queue Configuration
        self.setup_config_panel(main_frame)
    
    def setup_control_panel(self, parent):
        """Setup queue control buttons"""
        control_frame = ttk.LabelFrame(parent, text="Queue Controls", padding="10")
        control_frame.pack(fill='x', pady=(0, 10))
        
        # Left side - Queue controls
        left_frame = ttk.Frame(control_frame)
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Add to queue button
        ttk.Button(left_frame, text="➕ Add Story to Queue", 
                  command=self.add_story_to_queue,
                  style='Accent.TButton').pack(side='left', padx=(0, 5))
        
        # Queue management buttons
        ttk.Button(left_frame, text="⏸️ Pause Queue", 
                  command=self.pause_queue).pack(side='left', padx=2)
        
        ttk.Button(left_frame, text="▶️ Resume Queue", 
                  command=self.resume_queue).pack(side='left', padx=2)
        
        ttk.Button(left_frame, text="🔄 Refresh", 
                  command=self.refresh_queue_display).pack(side='left', padx=2)
        
        # Right side - Cleanup controls
        right_frame = ttk.Frame(control_frame)
        right_frame.pack(side='right')
        
        ttk.Button(right_frame, text="🗑️ Clear Completed", 
                  command=self.clear_completed_items).pack(side='left', padx=2)
        
        ttk.Button(right_frame, text="🗑️ Clear All", 
                  command=self.clear_all_items).pack(side='left', padx=2)
    
    def setup_statistics_panel(self, parent):
        """Setup queue statistics display"""
        stats_frame = ttk.LabelFrame(parent, text="Queue Statistics", padding="10")
        stats_frame.pack(fill='x', pady=(0, 10))
        
        # Create statistics grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack()
        
        self.stats_labels = {
            'queued': ttk.Label(stats_grid, text="Queued: 0", font=('Arial', 10, 'bold')),
            'processing': ttk.Label(stats_grid, text="Processing: 0", font=('Arial', 10, 'bold'), foreground='blue'),
            'completed': ttk.Label(stats_grid, text="Completed: 0", font=('Arial', 10, 'bold'), foreground='green'),
            'failed': ttk.Label(stats_grid, text="Failed: 0", font=('Arial', 10, 'bold'), foreground='red'),
            'paused': ttk.Label(stats_grid, text="Paused: 0", font=('Arial', 10, 'bold'), foreground='orange')
        }
        
        # Layout statistics
        row = 0
        col = 0
        for key, label in self.stats_labels.items():
            label.grid(row=row, column=col, padx=15, pady=5, sticky='w')
            col += 1
            if col > 2:  # 3 columns per row
                col = 0
                row += 1
        
        # Current processing info
        self.current_processing_frame = ttk.Frame(stats_frame)
        self.current_processing_frame.pack(fill='x', pady=(10, 0))
        
        self.current_processing_label = ttk.Label(self.current_processing_frame, 
                                                 text="No items currently processing",
                                                 font=('Arial', 9, 'italic'))
        self.current_processing_label.pack()
    
    def setup_queue_list(self, parent):
        """Setup queue items list"""
        queue_frame = ttk.LabelFrame(parent, text="Queue Items", padding="10")
        queue_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create treeview for queue items
        columns = ('Position', 'Priority', 'Story Name', 'Genre', 'Length', 'Status', 'Current Step', 
                  'Progress', 'Actions', 'Created', 'Started', 'ETA')
        
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show='tree headings', height=12)
        
        # Configure columns
        self.queue_tree.heading('#0', text='ID')
        self.queue_tree.column('#0', width=50, minwidth=50)
        
        column_widths = {
            'Position': 60, 'Priority': 60, 'Story Name': 150, 'Genre': 80, 'Length': 60,
            'Status': 80, 'Current Step': 120, 'Progress': 100, 'Actions': 100,
            'Created': 80, 'Started': 80, 'ETA': 80
        }
        
        for col in columns:
            self.queue_tree.heading(col, text=col)
            self.queue_tree.column(col, width=column_widths.get(col, 100), minwidth=50)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(queue_frame, orient='vertical', command=self.queue_tree.yview)
        h_scrollbar = ttk.Scrollbar(queue_frame, orient='horizontal', command=self.queue_tree.xview)
        self.queue_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.queue_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        queue_frame.grid_rowconfigure(0, weight=1)
        queue_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.setup_context_menu()
        
        # Bind events
        self.queue_tree.bind('<Double-1>', self.on_queue_item_double_click)
        self.queue_tree.bind('<Button-3>', self.show_context_menu)
        self.queue_tree.bind('<Button-1>', self.on_queue_item_click)
    
    def setup_context_menu(self):
        """Setup right-click context menu for queue items"""
        self.context_menu = tk.Menu(self.queue_tree, tearoff=0)
        self.context_menu.add_command(label="📊 View Progress", command=self.view_item_progress)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="⬆️ Increase Priority", command=self.increase_priority)
        self.context_menu.add_command(label="⬇️ Decrease Priority", command=self.decrease_priority)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔄 Retry Item", command=self.retry_item)
        self.context_menu.add_command(label="⏸️ Pause Item", command=self.pause_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Remove from Queue", command=self.remove_item)
    
    def setup_config_panel(self, parent):
        """Setup queue configuration panel"""
        config_frame = ttk.LabelFrame(parent, text="Queue Configuration", padding="10")
        config_frame.pack(fill='x')
        
        # Left column - Continuous generation
        left_col = ttk.Frame(config_frame)
        left_col.pack(side='left', fill='x', expand=True)
        
        self.continuous_var = tk.BooleanVar()
        continuous_cb = ttk.Checkbutton(left_col, text="Enable Continuous Generation",
                                       variable=self.continuous_var,
                                       command=self.update_queue_config)
        continuous_cb.pack(anchor='w', pady=2)
        
        # Thresholds frame
        thresholds_frame = ttk.Frame(left_col)
        thresholds_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(thresholds_frame, text="Render Queue Thresholds:").pack(anchor='w')
        
        threshold_grid = ttk.Frame(thresholds_frame)
        threshold_grid.pack(fill='x', pady=2)
        
        ttk.Label(threshold_grid, text="High:").grid(row=0, column=0, sticky='w')
        self.high_threshold_var = tk.StringVar(value="50")
        ttk.Entry(threshold_grid, textvariable=self.high_threshold_var, width=8).grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(threshold_grid, text="Low:").grid(row=0, column=2, sticky='w')
        self.low_threshold_var = tk.StringVar(value="10")
        ttk.Entry(threshold_grid, textvariable=self.low_threshold_var, width=8).grid(row=0, column=3, padx=5)
        
        # Right column - Other settings
        right_col = ttk.Frame(config_frame)
        right_col.pack(side='right', padx=(20, 0))
        
        ttk.Label(right_col, text="Max Concurrent:").pack(anchor='w')
        self.max_concurrent_var = tk.StringVar(value="1")
        ttk.Entry(right_col, textvariable=self.max_concurrent_var, width=8).pack(anchor='w', pady=2)
        
        ttk.Button(right_col, text="💾 Save Config", 
                  command=self.save_queue_config).pack(pady=10)
        
        # Load current config
        self.load_queue_config()
    
    def load_queue_config(self):
        """Load current queue configuration"""
        try:
            config = self.story_queue.config
            self.continuous_var.set(config.continuous_enabled)
            self.high_threshold_var.set(str(config.render_queue_high_threshold))
            self.low_threshold_var.set(str(config.render_queue_low_threshold))
            self.max_concurrent_var.set(str(config.max_concurrent_generations))
        except Exception as e:
            print(f"Error loading queue config: {e}")
    
    def save_queue_config(self):
        """Save queue configuration"""
        try:
            config_updates = {
                'continuous_enabled': self.continuous_var.get(),
                'render_queue_high_threshold': int(self.high_threshold_var.get()),
                'render_queue_low_threshold': int(self.low_threshold_var.get()),
                'max_concurrent_generations': int(self.max_concurrent_var.get())
            }
            
            self.story_queue.update_config(**config_updates)
            messagebox.showinfo("Success", "Queue configuration saved successfully!")
            
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid numbers for thresholds and max concurrent.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def update_queue_config(self):
        """Update queue configuration when checkboxes change"""
        self.save_queue_config()
    
    def add_story_to_queue(self):
        """Show dialog to add story to queue"""
        AddStoryDialog(self.parent_frame, self.story_queue, self.refresh_queue_display)
    
    def pause_queue(self):
        """Pause queue processing"""
        self.story_queue.pause_queue()
        messagebox.showinfo("Queue Paused", "Story generation queue has been paused.")
    
    def resume_queue(self):
        """Resume queue processing"""
        self.story_queue.resume_queue()
        messagebox.showinfo("Queue Resumed", "Story generation queue has been resumed.")
    
    def clear_completed_items(self):
        """Clear completed queue items"""
        if messagebox.askyesno("Clear Completed", 
                              "Remove all completed and failed items from the queue?"):
            cleared = self.story_queue.clear_completed_items()
            messagebox.showinfo("Cleared", f"Removed {cleared} completed items from queue.")
            self.refresh_queue_display()
    
    def clear_all_items(self):
        """Clear all queue items"""
        if messagebox.askyesno("Clear All", 
                              "Remove ALL items from the story queue? This will stop any currently running generation."):
            try:
                # Stop queue processing first
                self.story_queue.stop_processing()
                
                # Clear all items from database
                cursor = self.story_queue.db.conn.cursor()
                cursor.execute("DELETE FROM story_queue")
                self.story_queue.db.conn.commit()
                
                # Restart queue processing
                self.story_queue.start_processing()
                
                messagebox.showinfo("Cleared", "All items removed from story queue.")
                self.refresh_queue_display()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear queue: {e}")
    
    def refresh_queue_display(self):
        """Refresh the queue display"""
        try:
            # Update statistics
            stats = self.story_queue.get_queue_statistics()
            for key, label in self.stats_labels.items():
                count = stats.get(key, 0)
                label.config(text=f"{key.title()}: {count}")
            
            # Update current processing info
            current_item = self.story_queue.get_current_processing_item()
            if current_item:
                config = current_item['story_config']
                step = current_item.get('current_step', 'unknown')
                text = f"Processing: {config.get('genre', 'Unknown')} {config.get('length', '')} story - {step}"
                self.current_processing_label.config(text=text, foreground='blue')
            else:
                self.current_processing_label.config(text="No items currently processing", foreground='gray')
            
            # Update queue list
            for item in self.queue_tree.get_children():
                self.queue_tree.delete(item)
            
            queue_items = self.story_queue.get_queue_items()
            for item in queue_items:
                self._add_queue_item_to_tree(item)
                
        except Exception as e:
            print(f"Error refreshing queue display: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_queue_item_to_tree(self, item: Dict):
        """Add a queue item to the treeview"""
        try:
            config = item['story_config']
            
            # Get story name if available
            story_name = "Generating..."
            if item.get('story_id'):
                # Try to get the actual story title from the database
                try:
                    cursor = self.story_queue.db.conn.cursor()
                    cursor.execute('SELECT title FROM stories WHERE id = ?', (item['story_id'],))
                    result = cursor.fetchone()
                    if result:
                        story_name = result[0][:25] + "..." if len(result[0]) > 25 else result[0]
                except:
                    story_name = "Story Generated"
            
            # Format progress with bar
            progress_data = item.get('progress_data', {})
            progress_percent = progress_data.get('progress', 0)
            progress_text = self._create_progress_bar(progress_percent)
            
            # Format times
            created_time = self._format_time(item.get('created_at', ''))
            started_time = self._format_time(item.get('started_at', '')) if item.get('started_at') else '-'
            eta_time = self._format_time(item.get('estimated_completion', '')) if item.get('estimated_completion') else '-'
            
            # Determine row color based on status
            tags = []
            status = item['status']
            if status == 'processing':
                tags.append('processing')
            elif status == 'completed':
                tags.append('completed')
            elif status == 'failed':
                tags.append('failed')
            elif status == 'paused':
                tags.append('paused')
            
            item_id = self.queue_tree.insert('', 'end', 
                                  text=str(item['id']),
                                  values=(
                                      item.get('queue_position', '-'),
                                      item['priority'],
                                      story_name,
                                      config.get('genre', 'Unknown'),
                                      config.get('length', 'Unknown'),
                                      status.title(),
                                      item.get('current_step', 'pending'),
                                      progress_text,
                                      "📊 View",  # Actions column
                                      created_time,
                                      started_time,
                                      eta_time
                                  ),
                                  tags=tags)
            
            # Configure tag colors
            self.queue_tree.tag_configure('processing', background='lightblue')
            self.queue_tree.tag_configure('completed', background='lightgreen')
            self.queue_tree.tag_configure('failed', background='lightcoral')
            self.queue_tree.tag_configure('paused', background='lightyellow')
            
        except Exception as e:
            print(f"Error adding queue item to tree: {e}")
            import traceback
            traceback.print_exc()
    
    def _format_time(self, time_str: str) -> str:
        """Format timestamp for display"""
        if not time_str:
            return '-'
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime('%H:%M')
        except:
            return '-'
    
    def _create_progress_bar(self, percent: float) -> str:
        """Create a text-based progress bar"""
        if percent is None:
            percent = 0
        
        # Ensure percent is between 0 and 100
        percent = max(0, min(100, percent))
        
        # Create progress bar (20 characters wide)
        bar_length = 15
        filled_length = int(bar_length * percent / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        return f"{bar} {percent:.0f}%"
    
    def on_queue_item_click(self, event):
        """Handle single click on queue item - check if Actions column clicked"""
        item = self.queue_tree.selection()[0] if self.queue_tree.selection() else None
        if not item:
            return
            
        # Get the column that was clicked
        column = self.queue_tree.identify_column(event.x)
        # Actions column is column 9 (0-indexed, including #0)
        if column == '#9':  # Actions column
            self.view_item_progress()
    
    def on_queue_item_double_click(self, event):
        """Handle double-click on queue item"""
        self.view_item_progress()
    
    def show_context_menu(self, event):
        """Show context menu"""
        item = self.queue_tree.selection()
        if item:
            self.context_menu.post(event.x_root, event.y_root)
    
    def view_item_progress(self):
        """View progress for selected queue item"""
        selection = self.queue_tree.selection()
        if not selection:
            return
        
        item_id = int(self.queue_tree.item(selection[0], 'text'))
        
        # Find the queue item
        queue_items = self.story_queue.get_queue_items()
        queue_item = None
        for item in queue_items:
            if item['id'] == item_id:
                queue_item = item
                break
        
        if not queue_item:
            messagebox.showerror("Error", "Queue item not found.")
            return
        
        # Show or create progress window
        if item_id in self.progress_windows:
            # Bring existing window to front
            window = self.progress_windows[item_id]
            if window.window:  # Check if window exists
                window.window.lift()
                window.window.focus()
        else:
            # Create new progress window
            self._create_progress_window(queue_item)
    
    def _create_progress_window(self, queue_item: Dict):
        """Create progress window for queue item"""
        try:
            # Create a fake config from the queue item for the progress window
            from data_models import StoryConfig
            config = queue_item['story_config']
            story_config = StoryConfig(**config) if isinstance(config, dict) else config
            
            # Get root window from parent frame
            parent = self.parent_frame
            while parent and not hasattr(parent, 'master'):
                parent = parent.master if hasattr(parent, 'master') else None
            if not parent:
                parent = self.parent_frame.winfo_toplevel()
            
            # Create a new window for this queue item  
            def on_window_close():
                # Remove reference when window closes
                if item_id in self.progress_windows:
                    del self.progress_windows[item_id]
            
            # The GenerationProgressWindow now creates the window automatically in __init__
            progress_window = GenerationProgressWindow(parent, story_config, on_complete_callback=on_window_close, db_manager=self.db)
            
            # Store reference
            item_id = queue_item['id']
            self.progress_windows[item_id] = progress_window
            
            # Set the progress window on the story generator so AI messages are logged
            if self.story_generator:
                self.story_generator.progress_window = progress_window
            
            # Set window title
            config = queue_item['story_config']
            title = f"Queue Item #{item_id} - {config.get('genre', 'Unknown')} Story"
            progress_window.update_story_title(title)
            
            # Load existing data if the item is completed or has progress (with slight delay for UI initialization)
            def load_existing_data():
                self._load_queue_item_data(progress_window, queue_item, title)
            
            # Delay loading to ensure window is fully initialized
            progress_window.window.after(150, load_existing_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create progress window: {e}")
    
    def _load_queue_item_data(self, progress_window, queue_item: Dict, title: str):
        """Load existing data for a queue item into the progress window"""
        if queue_item.get('status') == 'completed' and queue_item.get('story_id'):
            # Load story data from database
            try:
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT * FROM stories WHERE id = ?', (queue_item['story_id'],))
                story_row = cursor.fetchone()
                if story_row:
                    # Convert row to dict (assuming we know the column order)
                    story_dict = dict(zip([col[0] for col in cursor.description], story_row))
                    progress_window.update_story_title(story_dict.get('title', title))
                    progress_window.update_story_content(story_dict)
                    # Mark all steps as completed
                    for step in ['story', 'shots', 'characters', 'style', 'prompts', 'narration', 'music', 'queue']:
                        progress_window.update_step(step, 100, 'completed', 'Generation completed')
                    
                    # Load shots if available
                    cursor.execute('SELECT * FROM shots WHERE story_id = ?', (queue_item['story_id'],))
                    shots_rows = cursor.fetchall()
                    if shots_rows:
                        shots_dicts = [dict(zip([col[0] for col in cursor.description], row)) for row in shots_rows]
                        progress_window.update_shot_list(shots_dicts)
            except Exception as e:
                print(f"Error loading completed story data: {e}")
        
        elif queue_item.get('current_step'):
            # Update with current progress
            step = queue_item.get('current_step', 'pending')
            progress_data = queue_item.get('progress_data', {})
            progress_value = progress_data.get('progress', 0)
            # Map current step to proper step key
            step_key = self._map_step_to_key(step)
            status = 'processing' if queue_item.get('status') == 'processing' else 'pending'
            progress_window.update_step(step_key, progress_value, status, step)
            
            # Auto-complete previous steps based on current progress
            self._auto_complete_previous_steps(progress_window, progress_value, step_key)
            
            # Update node information for current step
            try:
                step_models = {
                    'story': 'story',
                    'shot': 'shots',
                    'character': 'characters',
                    'style': 'style'
                }
                
                for key, model_key in step_models.items():
                    if key in step.lower():
                        if hasattr(self.story_generator.ollama, 'step_model_assignments'):
                            instance_key, model_name = self.story_generator.ollama.step_model_assignments.get(model_key, (None, None))
                            if instance_key and model_name:
                                progress_window.update_step_node_info(step_key, instance_key, 'OLLAMA', model_name)
                        break
            except Exception as e:
                print(f"Error setting initial node info: {e}")
            
            # Try to load existing story data if available (for processing items)
            if queue_item.get('story_id'):
                try:
                    cursor = self.db.conn.cursor()
                    cursor.execute('SELECT * FROM stories WHERE id = ?', (queue_item['story_id'],))
                    story_row = cursor.fetchone()
                    if story_row:
                        story_dict = dict(zip([col[0] for col in cursor.description], story_row))
                        if story_dict.get('title'):
                            progress_window.update_story_title(story_dict['title'])
                        if story_dict.get('content'):
                            progress_window.update_story_content(story_dict)
                        
                        # Load shots if available
                        cursor.execute('SELECT * FROM shots WHERE story_id = ?', (queue_item['story_id'],))
                        shots_rows = cursor.fetchall()
                        if shots_rows:
                            shots_dicts = [dict(zip([col[0] for col in cursor.description], row)) for row in shots_rows]
                            progress_window.update_shot_list(shots_dicts)
                except Exception as e:
                    print(f"Error loading processing story data: {e}")
    
    def _map_step_to_key(self, step_name: str) -> str:
        """Map step name to progress window step key"""
        step_lower = step_name.lower()
        
        # Map based on the actual step descriptions from story_generator.py
        if 'selecting optimal' in step_lower or 'optimal prompt' in step_lower:
            return 'story'  # Prompt selection is part of story generation
        elif 'generating story' in step_lower or 'story with ai' in step_lower:
            return 'story'
        elif 'breaking story' in step_lower or 'shot list' in step_lower or 'into shots' in step_lower:
            return 'shots'
        elif 'analyzing characters' in step_lower or 'characters and locations' in step_lower:
            return 'characters'
        elif 'processing style' in step_lower or 'style sheet' in step_lower:
            return 'style'
        elif 'processing shot' in step_lower or 'generating prompts' in step_lower or 'wan' in step_lower:
            return 'prompts'
        elif 'generating narration' in step_lower or 'elevenlabs' in step_lower:
            return 'narration'
        elif 'generating music' in step_lower or 'suno' in step_lower or 'music cue' in step_lower:
            return 'music'
        elif 'completed' in step_lower or 'finished' in step_lower:
            return 'queue'
        else:
            # Try fallback patterns
            if 'story' in step_lower:
                return 'story'
            elif 'shot' in step_lower:
                return 'shots' 
            elif 'character' in step_lower:
                return 'characters'
            elif 'prompt' in step_lower:
                return 'prompts'
            elif 'narration' in step_lower:
                return 'narration'
            elif 'music' in step_lower:
                return 'music'
            elif 'queue' in step_lower or 'render' in step_lower or 'complet' in step_lower:
                return 'queue'
            else:
                return 'story'  # Default fallback
    
    def _convert_global_to_step_progress(self, global_progress: int, step_key: str, current_step: str) -> int:
        """Convert global progress percentage to step-specific progress (0-100)"""
        # Define the global progress ranges for each step based on actual story_generator.py values
        step_ranges = {
            'story': (0, 25),      # Prompt selection (10) + Story generation (15-25)
            'shots': (25, 40),     # Shot list creation (30) + Character analysis starts (40)
            'characters': (40, 45), # Character analysis (40-42) + ComfyUI prompts + Style (45)
            'style': (45, 50),     # Style processing (45) + Shot processing starts
            'prompts': (50, 95),   # Shot processing with prompts (50-95)
            'narration': (95, 99), # Part of finalization (95)
            'music': (99, 100),    # Part of completion (100)
            'queue': (100, 100)    # Queue completion (100)
        }
        
        # Get the range for this step
        step_range = step_ranges.get(step_key, (0, 100))
        min_progress, max_progress = step_range
        
        # Special handling for steps that might be completed in one update
        if global_progress >= max_progress:
            return 100  # Step is complete
        elif global_progress < min_progress:
            return 0    # Step hasn't started yet
        else:
            # Calculate progress within the step's range
            range_size = max_progress - min_progress
            if range_size <= 0:
                return 100
            progress_in_range = global_progress - min_progress
            step_progress = (progress_in_range / range_size) * 100
            return min(100, max(0, int(step_progress)))
    
    def _auto_complete_previous_steps(self, window, global_progress: int, current_step_key: str):
        """Auto-complete previous steps when global progress moves past their ranges"""
        step_order = ['story', 'shots', 'characters', 'style', 'prompts', 'narration', 'music', 'queue']
        step_ranges = {
            'story': (0, 25),
            'shots': (25, 30),
            'characters': (30, 45),
            'style': (45, 50),
            'prompts': (50, 85),
            'narration': (85, 95),
            'music': (95, 98),
            'queue': (98, 100)
        }
        
        # Find current step index
        try:
            current_index = step_order.index(current_step_key)
        except ValueError:
            return  # Unknown step
        
        # Complete all previous steps that should be done by now
        for i in range(current_index):
            prev_step = step_order[i]
            prev_range = step_ranges.get(prev_step, (0, 100))
            
            # If global progress is past this step's range, mark it complete
            if global_progress > prev_range[1]:
                window.update_step(prev_step, 100, 'completed', f'{prev_step.title()} completed')
    
    def increase_priority(self):
        """Increase priority of selected item"""
        self._change_priority(1)
    
    def decrease_priority(self):
        """Decrease priority of selected item"""
        self._change_priority(-1)
    
    def _change_priority(self, delta: int):
        """Change priority of selected item"""
        selection = self.queue_tree.selection()
        if not selection:
            return
        
        item_id = int(self.queue_tree.item(selection[0], 'text'))
        current_priority = int(self.queue_tree.item(selection[0], 'values')[1])
        new_priority = max(1, min(10, current_priority + delta))
        
        if self.story_queue.update_item_priority(item_id, new_priority):
            self.refresh_queue_display()
    
    def retry_item(self):
        """Retry failed item"""
        selection = self.queue_tree.selection()
        if not selection:
            return
        
        item_id = int(self.queue_tree.item(selection[0], 'text'))
        
        if self.story_queue.retry_failed_item(item_id):
            messagebox.showinfo("Success", "Item queued for retry.")
            self.refresh_queue_display()
        else:
            messagebox.showerror("Error", "Failed to retry item.")
    
    def pause_item(self):
        """Pause individual item"""
        messagebox.showinfo("Not Implemented", "Individual item pausing not yet implemented.")
    
    def remove_item(self):
        """Remove item from queue"""
        selection = self.queue_tree.selection()
        if not selection:
            return
        
        item_id = int(self.queue_tree.item(selection[0], 'text'))
        
        if messagebox.askyesno("Remove Item", "Remove this item from the queue?"):
            if self.story_queue.remove_from_queue(item_id):
                self.refresh_queue_display()
            else:
                messagebox.showerror("Error", "Cannot remove item (may be currently processing).")
    
    def on_queue_progress(self, queue_id: int, status: str, current_step: str, progress_data: Dict):
        """Handle queue progress updates"""
        # Update progress window if it exists
        if queue_id in self.progress_windows:
            window = self.progress_windows[queue_id]
            progress_value = progress_data.get('progress', 0)
            
            # Handle special AI message updates
            if current_step == 'ai_message':
                ai_msg = progress_data.get('ai_message', {})
                window.add_ai_message(
                    ai_msg.get('type', 'info'),
                    ai_msg.get('content', ''),
                    ai_msg.get('step', '')
                )
            else:
                # Map current step to proper step key
                step_key = self._map_step_to_key(current_step)
                
                # Convert global progress to step-specific progress
                step_progress = self._convert_global_to_step_progress(progress_value, step_key, current_step)
                
                # Auto-complete previous steps based on global progress
                self._auto_complete_previous_steps(window, progress_value, step_key)
                
                window.update_step(step_key, step_progress, 'processing', current_step)
                
                # Update node info if we can determine the node
                try:
                    if hasattr(self.story_generator, 'ollama') and hasattr(self.story_generator.ollama, 'step_model_assignments'):
                        # Determine which step we're on and show appropriate node
                        step_models = {
                            'story': 'story',
                            'shot': 'shots', 
                            'character': 'characters',
                            'prompt': 'prompts',
                            'style': 'style'
                        }
                        
                        for key, model_key in step_models.items():
                            if key in current_step.lower():
                                instance_key, model_name = self.story_generator.ollama.step_model_assignments.get(model_key, (None, None))
                                if instance_key and model_name:
                                    window.update_step_node_info(step_key, instance_key, 'OLLAMA', model_name)
                                break
                except:
                    pass  # Ignore node info errors
        
        # Schedule immediate refresh of main display to show progress updates
        self.parent_frame.after(10, self.refresh_queue_display)
    
    def on_queue_completion(self, queue_id: int, story_data: Dict):
        """Handle queue item completion"""
        # Update progress window
        if queue_id in self.progress_windows:
            window = self.progress_windows[queue_id]
            # Mark all steps as completed
            for step in ['story', 'shots', 'characters', 'style', 'prompts', 'narration', 'music', 'queue']:
                window.update_step(step, 100, 'completed', 'Generation completed')
            
            # Add completion message
            window.add_ai_message('success', 'Story generation completed successfully!', 'completion')
            
            # Update with story content if available
            if 'story' in story_data:
                story = story_data['story']
                window.update_story_title(story.get('title', 'Generated Story'))
                window.update_story_content(story)
                window.add_ai_message('success', f"Generated story: {story.get('title', 'Untitled')}", 'story')
                
            if 'shots' in story_data:
                shots = story_data['shots']
                window.update_shot_list(shots)
                window.add_ai_message('success', f"Created {len(shots)} shots for the story", 'shots')
        
        # Refresh display immediately
        self.parent_frame.after(10, self.refresh_queue_display)
        
        # Check if this was the last item in queue and auto-randomize for next generation
        self.parent_frame.after(50, self._maybe_auto_randomize_after_completion)
    
    def _maybe_auto_randomize_after_completion(self):
        """Auto-randomize inputs if queue is now empty"""
        try:
            # Check if there are any more queued items
            queue_stats = self.story_queue.get_queue_statistics()
            queued_count = queue_stats.get('queued', 0)
            processing_count = queue_stats.get('processing', 0)
            
            # If no items are queued or processing, randomize for next generation
            if queued_count == 0 and processing_count == 0:
                if self.main_app and hasattr(self.main_app, 'randomize_inputs'):
                    self.main_app.randomize_inputs()
                    self.main_app.add_log("Auto-randomized settings after queue completion", "Info")
        except Exception as e:
            print(f"Error in auto-randomization: {e}")
    
    def on_queue_error(self, error_message: str):
        """Handle queue errors"""
        # Show error in a non-blocking way
        self.parent_frame.after(100, lambda: messagebox.showerror("Queue Error", error_message))
    
    def start_auto_refresh(self):
        """Start automatic refresh timer"""
        self.refresh_queue_display()
        self.refresh_timer = self.parent_frame.after(2000, self.start_auto_refresh)  # Refresh every 2 seconds for better responsiveness
    
    def stop_auto_refresh(self):
        """Stop automatic refresh timer"""
        if self.refresh_timer:
            self.parent_frame.after_cancel(self.refresh_timer)
            self.refresh_timer = None


class AddStoryDialog:
    """Dialog for adding story to queue"""
    
    def __init__(self, parent, story_queue: StoryQueue, refresh_callback):
        self.story_queue = story_queue
        self.refresh_callback = refresh_callback
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Story to Queue")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_dialog(self):
        """Setup the dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(main_frame, text="Add Story to Generation Queue", 
                 font=('Arial', 14, 'bold')).pack(pady=(0, 20))
        
        # Story configuration
        config_frame = ttk.LabelFrame(main_frame, text="Story Configuration", padding="10")
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Prompt
        ttk.Label(config_frame, text="Story Prompt:").pack(anchor='w', pady=(0, 5))
        self.prompt_text = tk.Text(config_frame, height=4, wrap=tk.WORD)
        self.prompt_text.pack(fill='x', pady=(0, 10))
        
        # Genre and Length
        row1 = ttk.Frame(config_frame)
        row1.pack(fill='x', pady=(0, 10))
        
        ttk.Label(row1, text="Genre:").pack(side='left')
        self.genre_var = tk.StringVar(value="Drama")
        genre_combo = ttk.Combobox(row1, textvariable=self.genre_var, 
                                  values=["Drama", "Comedy", "Thriller", "Sci-Fi", 
                                         "Romance", "Horror", "Mystery", "Fantasy"],
                                  state="readonly", width=15)
        genre_combo.pack(side='left', padx=(5, 20))
        
        ttk.Label(row1, text="Length:").pack(side='left')
        self.length_var = tk.StringVar(value="Medium")
        length_combo = ttk.Combobox(row1, textvariable=self.length_var,
                                   values=["Short", "Medium", "Long"],
                                   state="readonly", width=10)
        length_combo.pack(side='left', padx=(5, 0))
        
        # Auto options
        auto_frame = ttk.Frame(config_frame)
        auto_frame.pack(fill='x', pady=(0, 10))
        
        self.auto_prompt_var = tk.BooleanVar()
        self.auto_genre_var = tk.BooleanVar()
        self.auto_length_var = tk.BooleanVar()
        self.auto_style_var = tk.BooleanVar()
        
        ttk.Checkbutton(auto_frame, text="Auto Prompt", 
                       variable=self.auto_prompt_var).pack(side='left', padx=(0, 10))
        ttk.Checkbutton(auto_frame, text="Auto Genre", 
                       variable=self.auto_genre_var).pack(side='left', padx=(0, 10))
        ttk.Checkbutton(auto_frame, text="Auto Length", 
                       variable=self.auto_length_var).pack(side='left', padx=(0, 10))
        ttk.Checkbutton(auto_frame, text="Auto Style", 
                       variable=self.auto_style_var).pack(side='left')
        
        # Queue settings
        queue_frame = ttk.LabelFrame(main_frame, text="Queue Settings", padding="10")
        queue_frame.pack(fill='x', pady=(0, 20))
        
        settings_row = ttk.Frame(queue_frame)
        settings_row.pack(fill='x')
        
        ttk.Label(settings_row, text="Priority:").pack(side='left')
        self.priority_var = tk.StringVar(value="5")
        priority_spin = ttk.Spinbox(settings_row, from_=1, to=10, 
                                   textvariable=self.priority_var, width=8)
        priority_spin.pack(side='left', padx=(5, 20))
        
        self.continuous_var = tk.BooleanVar()
        ttk.Checkbutton(settings_row, text="Continuous Generation", 
                       variable=self.continuous_var).pack(side='left')
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="Add to Queue", 
                  command=self.add_to_queue,
                  style='Accent.TButton').pack(side='right')
    
    def add_to_queue(self):
        """Add the configured story to the queue"""
        try:
            # Get prompt text
            prompt = self.prompt_text.get("1.0", tk.END).strip()
            if not prompt and not self.auto_prompt_var.get():
                messagebox.showerror("Error", "Please enter a story prompt or enable Auto Prompt.")
                return
            
            # Create story config
            story_config = StoryConfig(
                prompt=prompt,
                genre=self.genre_var.get(),
                length=self.length_var.get(),
                auto_prompt=self.auto_prompt_var.get(),
                auto_genre=self.auto_genre_var.get(),
                auto_length=self.auto_length_var.get(),
                auto_style=self.auto_style_var.get()
            )
            
            # Add to queue
            queue_id = self.story_queue.add_to_queue(
                story_config,
                priority=int(self.priority_var.get()),
                continuous=self.continuous_var.get()
            )
            
            messagebox.showinfo("Success", f"Story added to queue (ID: {queue_id})")
            self.refresh_callback()
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add story to queue: {e}")