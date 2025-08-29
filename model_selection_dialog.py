"""
Model Selection Dialog for Multi-Step AI Configuration
Allows selection of different models for each AI generation step
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, List, Optional, Tuple
from node_manager import NodeManager, NodeType


class ModelSelectionDialog:
    """Dialog for configuring AI models for each generation step"""
    
    def __init__(self, parent, ollama_manager, callback=None):
        self.parent = parent
        self.ollama_manager = ollama_manager
        self.callback = callback
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AI Model Configuration")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
        
        # Model assignments storage
        self.step_assignments = self.ollama_manager.get_step_assignments()
        self.instances = self.ollama_manager.get_available_instances()
        
        # Multi-node assignments storage
        self.multi_node_assignments = {}  # step -> [(instance_key, model), ...]
        self.load_multi_node_assignments()
        
        # UI components
        self.instance_vars = {}
        self.model_vars = {}
        self.model_combos = {}
        self.instance_combos = {}
        self.node_listboxes = {}  # For multi-node selection
        self.add_node_buttons = {}
        self.remove_node_buttons = {}
        
        # Setup UI
        self.setup_ui()
        self.refresh_instances()
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup dialog UI components"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="AI Model Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="Configure which AI models to use for each generation step.\n"
                                   "You can use different models on different network instances for optimal performance.",
                              justify='center', font=('Arial', 9))
        desc_label.pack(pady=(0, 20))
        
        # Network discovery frame
        discovery_frame = ttk.LabelFrame(main_frame, text="Network Discovery", padding="10")
        discovery_frame.pack(fill='x', pady=(0, 10))
        
        discovery_controls = ttk.Frame(discovery_frame)
        discovery_controls.pack(fill='x')
        
        ttk.Button(discovery_controls, text="🔍 Scan Network", 
                  command=self.scan_network).pack(side='left', padx=5)
        ttk.Button(discovery_controls, text="🔄 Refresh All", 
                  command=self.refresh_instances).pack(side='left', padx=5)
        
        self.discovery_status = ttk.Label(discovery_controls, text="Ready to scan")
        self.discovery_status.pack(side='right')
        
        # Progress bar for network scan
        self.scan_progress = ttk.Progressbar(discovery_frame, mode='determinate')
        self.scan_progress.pack(fill='x', pady=(10, 0))
        self.scan_progress.pack_forget()  # Hide initially
        
        # Model configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Model Assignments", padding="10")
        config_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create scrollable frame
        canvas = tk.Canvas(config_frame)
        scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # AI generation steps
        self.ai_steps = [
            ('story', 'Story Generation', 'Generate the main story content and structure'),
            ('characters', 'Character Analysis', 'Extract characters and locations for visual consistency'),
            ('shots', 'Shot List Creation', 'Break story into filmable shots with camera directions'),
            ('prompts', 'Visual Prompt Generation', 'Create AI video generation prompts'),
            ('narration', 'Narration Scripts', 'Generate voice-over narration text'),
            ('music', 'Music Cues', 'Create music timing and style specifications')
        ]
        
        self.setup_step_controls()
        
        # Future AI services placeholder
        self.setup_future_services()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Apply Settings", 
                  command=self.on_apply, style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.on_cancel).pack(side='right')
        ttk.Button(button_frame, text="Test All Connections", 
                  command=self.test_all_connections).pack(side='left')
    
    def setup_step_controls(self):
        """Setup controls for each AI generation step with multi-node support"""
        for step_id, step_name, step_desc in self.ai_steps:
            # Step frame
            step_frame = ttk.LabelFrame(self.scrollable_frame, text=step_name, padding="10")
            step_frame.pack(fill='x', pady=5)
            
            # Description
            ttk.Label(step_frame, text=step_desc, font=('Arial', 8), 
                     foreground='gray').pack(anchor='w')
            
            # Primary node selection (backward compatibility)
            primary_frame = ttk.LabelFrame(step_frame, text="Primary Node", padding="5")
            primary_frame.pack(fill='x', pady=(5, 0))
            
            controls_frame = ttk.Frame(primary_frame)
            controls_frame.pack(fill='x')
            
            # Instance selection
            ttk.Label(controls_frame, text="Instance:", width=12).pack(side='left')
            
            self.instance_vars[step_id] = tk.StringVar()
            instance_combo = ttk.Combobox(controls_frame, 
                                         textvariable=self.instance_vars[step_id],
                                         width=25, state='readonly')
            instance_combo.pack(side='left', padx=5)
            instance_combo.bind('<<ComboboxSelected>>', 
                               lambda e, s=step_id: self.on_instance_changed(s))
            self.instance_combos[step_id] = instance_combo
            
            # Model selection
            ttk.Label(controls_frame, text="Model:", width=8).pack(side='left', padx=(20, 0))
            
            self.model_vars[step_id] = tk.StringVar()
            model_combo = ttk.Combobox(controls_frame, 
                                      textvariable=self.model_vars[step_id],
                                      width=30, state='readonly')
            model_combo.pack(side='left', padx=5)
            self.model_combos[step_id] = model_combo
            
            # Multi-node section
            multi_frame = ttk.LabelFrame(step_frame, text="Additional Nodes (Load Balancing)", padding="5")
            multi_frame.pack(fill='x', pady=(5, 0))
            
            # Node list display
            list_frame = ttk.Frame(multi_frame)
            list_frame.pack(fill='x', pady=(0, 5))
            
            # Create listbox for assigned nodes
            listbox_frame = ttk.Frame(list_frame)
            listbox_frame.pack(side='left', fill='both', expand=True)
            
            node_listbox = tk.Listbox(listbox_frame, height=3, font=('Arial', 8))
            node_listbox.pack(side='left', fill='both', expand=True)
            
            list_scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=node_listbox.yview)
            list_scrollbar.pack(side='right', fill='y')
            node_listbox.configure(yscrollcommand=list_scrollbar.set)
            
            self.node_listboxes[step_id] = node_listbox
            
            # Control buttons
            button_frame = ttk.Frame(list_frame)
            button_frame.pack(side='right', padx=(5, 0))
            
            add_btn = ttk.Button(button_frame, text="➕ Add Node", 
                               command=lambda s=step_id: self.add_node_to_step(s))
            add_btn.pack(pady=2)
            self.add_node_buttons[step_id] = add_btn
            
            remove_btn = ttk.Button(button_frame, text="➖ Remove", 
                                  command=lambda s=step_id: self.remove_node_from_step(s))
            remove_btn.pack(pady=2)
            self.remove_node_buttons[step_id] = remove_btn
            
            # Status indicator
            status_frame = ttk.Frame(step_frame)
            status_frame.pack(fill='x', pady=(5, 0))
            
            status_label = ttk.Label(status_frame, text="Status: Not configured", 
                                    font=('Arial', 8))
            status_label.pack(side='left')
            
            # Store reference to status label
            setattr(self, f'{step_id}_status', status_label)
            
            # Load existing multi-node assignments
            self.update_node_listbox(step_id)
    
    def setup_future_services(self):
        """Setup placeholder sections for future AI services"""
        # Future services frame
        future_frame = ttk.LabelFrame(self.scrollable_frame, text="Future AI Services (Coming Soon)", 
                                     padding="10")
        future_frame.pack(fill='x', pady=(20, 5))
        
        services = [
            ("ComfyUI", "Video generation and processing workflows"),
            ("ElevenLabs", "High-quality AI voice synthesis"),
            ("Suno", "AI music and audio generation")
        ]
        
        for service_name, service_desc in services:
            service_frame = ttk.Frame(future_frame)
            service_frame.pack(fill='x', pady=2)
            
            ttk.Label(service_frame, text=f"• {service_name}:", 
                     font=('Arial', 9, 'bold')).pack(side='left')
            ttk.Label(service_frame, text=service_desc, 
                     font=('Arial', 9), foreground='gray').pack(side='left', padx=(5, 0))
    
    def refresh_instances(self):
        """Fast refresh using cached data first"""
        self.discovery_status.config(text="Loading...")
        self.dialog.update()
        
        # Get cached instances first (instant)
        cached_instances = self.ollama_manager.network_discovery.get_cached_instances()
        if cached_instances:
            self.instances.update(cached_instances)
            self.update_instance_dropdowns()
            self.discovery_status.config(text=f"Loaded {len(self.instances)} instances (cached)")
        
        # Background refresh for updates
        def background_refresh():
            try:
                fresh_instances = self.ollama_manager.refresh_connections(force=False)
                self.dialog.after(0, lambda: self.on_background_refresh_complete(fresh_instances))
            except Exception as e:
                self.dialog.after(0, lambda: self.discovery_status.config(text=f"Refresh failed: {str(e)}"))
        
        threading.Thread(target=background_refresh, daemon=True).start()
    
    def update_instance_dropdowns(self):
        """Update dropdown lists with current instances"""
        instance_list = []
        for key, instance in self.instances.items():
            status = "●" if instance.get('status') == 'online' else "○"
            display_name = f"{status} {instance['display_name']} ({key})"
            instance_list.append(display_name)
        
        for step_id in self.ai_steps:
            step_key = step_id[0]  # Extract step key from tuple
            combo = self.instance_combos[step_key]
            combo['values'] = instance_list
            
            # Try to restore previous selection
            instance_key, model_name = self.step_assignments.get(step_key, (None, None))
            if instance_key and instance_key in self.instances:
                instance_info = self.instances[instance_key]
                status = "●" if instance_info.get('status') == 'online' else "○"
                display_name = f"{status} {instance_info['display_name']} ({instance_key})"
                if display_name in instance_list:
                    self.instance_vars[step_key].set(display_name)
                    self.on_instance_changed(step_key)
    
    def on_background_refresh_complete(self, fresh_instances):
        """Handle completion of background refresh"""
        self.instances.update(fresh_instances)
        self.update_instance_dropdowns()
        self.discovery_status.config(text=f"Updated: {len(self.instances)} instances")
    
    def scan_network(self):
        """Fast network scan with progress"""
        self.scan_progress.pack(fill='x', pady=(10, 0))
        self.discovery_status.config(text="Fast scanning network...")
        
        def fast_scan_thread():
            try:
                def progress_callback(current, total):
                    if total > 0:
                        progress = (current / total) * 100
                        self.dialog.after(0, lambda p=progress: self.scan_progress.configure(value=p))
                
                # Use fast scan
                discovered = self.ollama_manager.network_discovery.fast_scan(progress_callback)
                
                # Update UI on main thread
                self.dialog.after(0, self.on_scan_complete, len(discovered))
                
            except Exception as e:
                self.dialog.after(0, lambda: self.discovery_status.config(text=f"Scan failed: {str(e)}"))
        
        # Start fast scan
        threading.Thread(target=fast_scan_thread, daemon=True).start()
    
    def on_scan_complete(self, new_count):
        """Handle completion of network scan"""
        self.scan_progress.pack_forget()
        self.refresh_instances()
        self.discovery_status.config(text=f"Scan complete - found {new_count} new instances")
    
    def on_instance_changed(self, step_id):
        """Handle instance selection change"""
        selected_display = self.instance_vars[step_id].get()
        if not selected_display:
            return
        
        # Extract instance key from display name
        instance_key = selected_display.split('(')[-1].rstrip(')')
        
        if instance_key in self.instances:
            instance = self.instances[instance_key]
            models = instance.get('models', [])
            
            # Update model dropdown
            model_combo = self.model_combos[step_id]
            model_combo['values'] = models
            
            # Try to restore previous model selection
            _, prev_model = self.step_assignments.get(step_id, (None, None))
            if prev_model and prev_model in models:
                self.model_vars[step_id].set(prev_model)
            elif models:
                self.model_vars[step_id].set(models[0])
            
            # Update status
            status_label = getattr(self, f'{step_id}_status')
            if models:
                status_label.config(text=f"Status: {len(models)} models available")
            else:
                status_label.config(text="Status: No models found")
    
    def test_all_connections(self):
        """Test connections to all configured instances"""
        def test_thread():
            results = []
            for step_id, _, _ in self.ai_steps:
                instance_key = self.get_instance_key_for_step(step_id)
                if instance_key:
                    success, message = self.ollama_manager.test_connection(instance_key)
                    results.append(f"{step_id}: {'✓' if success else '✗'} {message}")
            
            result_text = "Connection Test Results:\n\n" + "\n".join(results)
            self.dialog.after(0, lambda: messagebox.showinfo("Connection Test", result_text))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def get_instance_key_for_step(self, step_id):
        """Get instance key from display name for step"""
        selected_display = self.instance_vars[step_id].get()
        if selected_display:
            return selected_display.split('(')[-1].rstrip(')')
        return None
    
    def on_apply(self):
        """Apply model assignments and close dialog"""
        assignments = {}
        
        for step_id, _, _ in self.ai_steps:
            instance_key = self.get_instance_key_for_step(step_id)
            model_name = self.model_vars[step_id].get()
            
            if instance_key and model_name:
                if self.ollama_manager.set_step_model(step_id, instance_key, model_name):
                    assignments[step_id] = (instance_key, model_name)
        
        if assignments:
            self.result = assignments
            if self.callback:
                self.callback(assignments)
            messagebox.showinfo("Success", f"Applied model assignments for {len(assignments)} steps")
            self.dialog.destroy()
        else:
            messagebox.showwarning("No Assignments", "Please configure at least one model assignment")
    
    def on_cancel(self):
        """Cancel and close dialog"""
        self.result = None
        self.dialog.destroy()
    
    def load_multi_node_assignments(self):
        """Load existing multi-node assignments"""
        # Initialize with primary assignments from ollama_manager
        for step_id, (instance_key, model) in self.step_assignments.items():
            if instance_key and model:
                if step_id not in self.multi_node_assignments:
                    self.multi_node_assignments[step_id] = []
                # Add primary assignment if not already in multi-node list
                assignment = (instance_key, model)
                if assignment not in self.multi_node_assignments[step_id]:
                    self.multi_node_assignments[step_id].append(assignment)
    
    def update_node_listbox(self, step_id: str):
        """Update the node listbox for a specific step"""
        if step_id not in self.node_listboxes:
            return
            
        listbox = self.node_listboxes[step_id]
        listbox.delete(0, tk.END)
        
        assignments = self.multi_node_assignments.get(step_id, [])
        for i, (instance_key, model) in enumerate(assignments):
            instance_info = self.instances.get(instance_key, {})
            display_name = instance_info.get('display_name', instance_key)
            status = "●" if instance_info.get('status') == 'online' else "○"
            
            # Mark primary node
            primary_marker = "[PRIMARY] " if i == 0 else ""
            listbox.insert(tk.END, f"{status} {primary_marker}{display_name}: {model}")
    
    def add_node_to_step(self, step_id: str):
        """Add a new node assignment to a step"""
        # Create selection dialog
        selection_dialog = NodeSelectionDialog(self.dialog, self.instances, step_id)
        result = selection_dialog.show()
        
        if result:
            instance_key, model = result
            
            # Add to multi-node assignments
            if step_id not in self.multi_node_assignments:
                self.multi_node_assignments[step_id] = []
            
            assignment = (instance_key, model)
            if assignment not in self.multi_node_assignments[step_id]:
                self.multi_node_assignments[step_id].append(assignment)
                self.update_node_listbox(step_id)
                self.update_step_status(step_id)
                print(f"Added node {instance_key} with model {model} to step {step_id}")
            else:
                messagebox.showwarning("Duplicate Assignment", 
                                      "This node and model combination is already assigned to this step.")
    
    def remove_node_from_step(self, step_id: str):
        """Remove selected node assignment from a step"""
        if step_id not in self.node_listboxes:
            return
            
        listbox = self.node_listboxes[step_id]
        selection = listbox.curselection()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select a node to remove.")
            return
        
        index = selection[0]
        assignments = self.multi_node_assignments.get(step_id, [])
        
        if index < len(assignments):
            if index == 0 and len(assignments) > 1:
                # Removing primary node - confirm and promote next node
                if messagebox.askyesno("Remove Primary Node", 
                                     "This will remove the primary node. The next node will become primary. Continue?"):
                    assignments.pop(index)
                    self.update_node_listbox(step_id)
                    self.update_step_status(step_id)
            else:
                assignments.pop(index)
                self.update_node_listbox(step_id)
                self.update_step_status(step_id)
    
    def update_step_status(self, step_id: str):
        """Update status display for a step"""
        assignments = self.multi_node_assignments.get(step_id, [])
        status_label = getattr(self, f'{step_id}_status')
        
        if assignments:
            total_nodes = len(assignments)
            online_nodes = 0
            for instance_key, model in assignments:
                if instance_key in self.instances:
                    instance = self.instances[instance_key]
                    if instance.get('status') == 'online' and model in instance.get('models', []):
                        online_nodes += 1
            
            status_label.config(text=f"Status: {online_nodes}/{total_nodes} nodes online")
        else:
            status_label.config(text="Status: Not configured")
    
    def show(self):
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result


class NodeSelectionDialog:
    """Dialog for selecting a node and model for multi-node assignment"""
    
    def __init__(self, parent, instances: Dict, step_id: str):
        self.parent = parent
        self.instances = instances
        self.step_id = step_id
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Add Node to {step_id.title()} Step")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        # Variables
        self.instance_var = tk.StringVar()
        self.model_var = tk.StringVar()
        
        # Setup UI
        self.setup_ui()
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def center_dialog(self):
        """Center dialog on parent"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(main_frame, text=f"Select Node for {self.step_id.title()} Step", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        # Instance selection
        instance_frame = ttk.Frame(main_frame)
        instance_frame.pack(fill='x', pady=5)
        
        ttk.Label(instance_frame, text="Instance:", width=12).pack(side='left')
        self.instance_combo = ttk.Combobox(instance_frame, textvariable=self.instance_var,
                                          width=40, state='readonly')
        self.instance_combo.pack(side='left', padx=5, fill='x', expand=True)
        self.instance_combo.bind('<<ComboboxSelected>>', self.on_instance_changed)
        
        # Model selection
        model_frame = ttk.Frame(main_frame)
        model_frame.pack(fill='x', pady=5)
        
        ttk.Label(model_frame, text="Model:", width=12).pack(side='left')
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var,
                                       width=40, state='readonly')
        self.model_combo.pack(side='left', padx=5, fill='x', expand=True)
        
        # Populate instances
        self.populate_instances()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        ttk.Button(button_frame, text="Add Node", command=self.on_add).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='right')
    
    def populate_instances(self):
        """Populate instance dropdown"""
        instance_list = []
        for key, instance in self.instances.items():
            status = "●" if instance.get('status') == 'online' else "○"
            display_name = f"{status} {instance['display_name']} ({key})"
            instance_list.append(display_name)
        
        self.instance_combo['values'] = instance_list
    
    def on_instance_changed(self, event=None):
        """Handle instance selection change"""
        selected_display = self.instance_var.get()
        if not selected_display:
            return
        
        # Extract instance key
        instance_key = selected_display.split('(')[-1].rstrip(')')
        
        if instance_key in self.instances:
            instance = self.instances[instance_key]
            models = instance.get('models', [])
            self.model_combo['values'] = models
            
            if models:
                self.model_var.set(models[0])  # Select first model by default
    
    def on_add(self):
        """Add the selected node"""
        selected_display = self.instance_var.get()
        selected_model = self.model_var.get()
        
        if not selected_display or not selected_model:
            messagebox.showwarning("Incomplete Selection", "Please select both an instance and a model.")
            return
        
        # Extract instance key
        instance_key = selected_display.split('(')[-1].rstrip(')')
        
        self.result = (instance_key, selected_model)
        self.dialog.destroy()
    
    def on_cancel(self):
        """Cancel dialog"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result