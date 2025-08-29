"""
Settings Dialog for Film Generator App
Handles API configuration and system prompt presets
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
from typing import Dict, Any

from config import API_SETTINGS, SYSTEM_PROMPT_PRESETS, ACTIVE_PRESET, DB_DIR


class SettingsDialog:
    """Settings dialog for API keys and system prompts"""
    
    def __init__(self, parent, database_manager=None):
        self.parent = parent
        self.db = database_manager
        self.settings_file = os.path.join(DB_DIR, "user_settings.json")
        self.presets_file = os.path.join(DB_DIR, "custom_presets.json")
        
        # Load saved settings
        self.api_settings = self.load_api_settings()
        self.custom_presets = self.load_custom_presets()
        self.current_preset = ACTIVE_PRESET
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Settings & Configuration")
        self.window.geometry("800x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
        
        self.setup_ui()
        self.load_current_values()
        
    def setup_ui(self):
        """Setup the settings UI"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # API Settings Tab
        self.api_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.api_tab, text='API Configuration')
        self.setup_api_tab()
        
        # System Prompts Tab
        self.prompts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.prompts_tab, text='System Prompts')
        self.setup_prompts_tab()
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Save & Apply", 
                  command=self.save_and_apply, 
                  style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.window.destroy).pack(side='right')
        ttk.Button(button_frame, text="Test Connections", 
                  command=self.test_api_connections).pack(side='left')
    
    def setup_api_tab(self):
        """Setup API configuration tab"""
        main_frame = ttk.Frame(self.api_tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # OpenAI Settings
        openai_frame = ttk.LabelFrame(main_frame, text="OpenAI Configuration", padding="15")
        openai_frame.pack(fill='x', pady=(0, 10))
        
        self.openai_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(openai_frame, text="Enable OpenAI API", 
                       variable=self.openai_enabled_var).pack(anchor='w', pady=(0, 10))
        
        # API Key
        key_frame = ttk.Frame(openai_frame)
        key_frame.pack(fill='x', pady=5)
        ttk.Label(key_frame, text="API Key:", width=12).pack(side='left')
        self.openai_key_var = tk.StringVar()
        self.openai_key_entry = ttk.Entry(key_frame, textvariable=self.openai_key_var, 
                                         width=50, show='*')
        self.openai_key_entry.pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(key_frame, text="Show", 
                  command=lambda: self.toggle_password_visibility(self.openai_key_entry)).pack(side='right')
        
        # Base URL
        url_frame = ttk.Frame(openai_frame)
        url_frame.pack(fill='x', pady=5)
        ttk.Label(url_frame, text="Base URL:", width=12).pack(side='left')
        self.openai_url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.openai_url_var, width=60).pack(side='left', padx=5, fill='x', expand=True)
        
        # Model Selection
        model_frame = ttk.Frame(openai_frame)
        model_frame.pack(fill='x', pady=5)
        ttk.Label(model_frame, text="Model:", width=12).pack(side='left')
        self.openai_model_var = tk.StringVar()
        self.openai_model_combo = ttk.Combobox(model_frame, textvariable=self.openai_model_var,
                                              values=API_SETTINGS['openai']['models'], 
                                              state='readonly', width=30)
        self.openai_model_combo.pack(side='left', padx=5)
        
        # Claude/Anthropic Settings
        claude_frame = ttk.LabelFrame(main_frame, text="Claude (Anthropic) Configuration", padding="15")
        claude_frame.pack(fill='x', pady=(0, 10))
        
        self.claude_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(claude_frame, text="Enable Claude API", 
                       variable=self.claude_enabled_var).pack(anchor='w', pady=(0, 10))
        
        # API Key
        key_frame = ttk.Frame(claude_frame)
        key_frame.pack(fill='x', pady=5)
        ttk.Label(key_frame, text="API Key:", width=12).pack(side='left')
        self.claude_key_var = tk.StringVar()
        self.claude_key_entry = ttk.Entry(key_frame, textvariable=self.claude_key_var, 
                                         width=50, show='*')
        self.claude_key_entry.pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(key_frame, text="Show", 
                  command=lambda: self.toggle_password_visibility(self.claude_key_entry)).pack(side='right')
        
        # Base URL
        url_frame = ttk.Frame(claude_frame)
        url_frame.pack(fill='x', pady=5)
        ttk.Label(url_frame, text="Base URL:", width=12).pack(side='left')
        self.claude_url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.claude_url_var, width=60).pack(side='left', padx=5, fill='x', expand=True)
        
        # Model Selection
        model_frame = ttk.Frame(claude_frame)
        model_frame.pack(fill='x', pady=5)
        ttk.Label(model_frame, text="Model:", width=12).pack(side='left')
        self.claude_model_var = tk.StringVar()
        self.claude_model_combo = ttk.Combobox(model_frame, textvariable=self.claude_model_var,
                                              values=API_SETTINGS['anthropic']['models'], 
                                              state='readonly', width=40)
        self.claude_model_combo.pack(side='left', padx=5)
        
        # Priority Settings
        priority_frame = ttk.LabelFrame(main_frame, text="AI Service Priority", padding="15")
        priority_frame.pack(fill='x')
        
        ttk.Label(priority_frame, text="Service priority (1=highest, 3=lowest):", 
                 font=('Arial', 9)).pack(anchor='w', pady=(0, 10))
        
        priority_grid = ttk.Frame(priority_frame)
        priority_grid.pack(fill='x')
        
        ttk.Label(priority_grid, text="Ollama:", width=15).grid(row=0, column=0, sticky='w', padx=5)
        self.ollama_priority_var = tk.IntVar(value=1)
        ttk.Spinbox(priority_grid, from_=1, to=3, textvariable=self.ollama_priority_var, width=5).grid(row=0, column=1, padx=5)
        
        ttk.Label(priority_grid, text="OpenAI:", width=15).grid(row=1, column=0, sticky='w', padx=5)
        self.openai_priority_var = tk.IntVar(value=2)
        ttk.Spinbox(priority_grid, from_=1, to=3, textvariable=self.openai_priority_var, width=5).grid(row=1, column=1, padx=5)
        
        ttk.Label(priority_grid, text="Claude:", width=15).grid(row=2, column=0, sticky='w', padx=5)
        self.claude_priority_var = tk.IntVar(value=3)
        ttk.Spinbox(priority_grid, from_=1, to=3, textvariable=self.claude_priority_var, width=5).grid(row=2, column=1, padx=5)
    
    def setup_prompts_tab(self):
        """Setup system prompts configuration tab"""
        main_frame = ttk.Frame(self.prompts_tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Preset Selection
        preset_frame = ttk.LabelFrame(main_frame, text="Preset Management", padding="15")
        preset_frame.pack(fill='x', pady=(0, 10))
        
        selection_frame = ttk.Frame(preset_frame)
        selection_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(selection_frame, text="Active Preset:", width=15).pack(side='left')
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(selection_frame, textvariable=self.preset_var,
                                        state='readonly', width=20)
        self.preset_combo.pack(side='left', padx=5)
        self.preset_combo.bind('<<ComboboxSelected>>', self.on_preset_changed)
        
        # Preset buttons
        button_frame = ttk.Frame(preset_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="Create New", 
                  command=self.create_new_preset).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Save As...", 
                  command=self.save_preset_as).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete", 
                  command=self.delete_preset).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Export", 
                  command=self.export_preset).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Import", 
                  command=self.import_preset).pack(side='right', padx=5)
        
        # Preset Description
        desc_frame = ttk.Frame(preset_frame)
        desc_frame.pack(fill='x', pady=(10, 0))
        ttk.Label(desc_frame, text="Description:", width=15).pack(side='left')
        self.preset_desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.preset_desc_var, width=60).pack(side='left', padx=5, fill='x', expand=True)
        
        # Prompt Editing
        prompt_frame = ttk.LabelFrame(main_frame, text="System Prompts", padding="15")
        prompt_frame.pack(fill='both', expand=True)
        
        # Prompt type selection
        type_frame = ttk.Frame(prompt_frame)
        type_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(type_frame, text="Prompt Type:", width=15).pack(side='left')
        self.prompt_type_var = tk.StringVar()
        self.prompt_type_combo = ttk.Combobox(type_frame, textvariable=self.prompt_type_var,
                                             values=['story_writer', 'shot_list_creator', 
                                                   'prompt_engineer', 'narration_writer', 'music_director'],
                                             state='readonly', width=20)
        self.prompt_type_combo.pack(side='left', padx=5)
        self.prompt_type_combo.bind('<<ComboboxSelected>>', self.on_prompt_type_changed)
        
        # Prompt editor
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=20, width=80,
                                                    wrap='word', font=('Consolas', 9))
        self.prompt_text.pack(fill='both', expand=True, pady=10)
        
        # Reset button
        reset_frame = ttk.Frame(prompt_frame)
        reset_frame.pack(fill='x')
        ttk.Button(reset_frame, text="Reset to Default", 
                  command=self.reset_current_prompt).pack(side='right')
    
    def load_api_settings(self) -> Dict[str, Any]:
        """Load API settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        # Return default settings
        return API_SETTINGS.copy()
    
    def load_custom_presets(self) -> Dict[str, Any]:
        """Load custom presets from file"""
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading custom presets: {e}")
        
        return {}
    
    def save_api_settings(self):
        """Save API settings to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.api_settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def save_custom_presets(self):
        """Save custom presets to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.presets_file), exist_ok=True)
            
            with open(self.presets_file, 'w') as f:
                json.dump(self.custom_presets, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save presets: {e}")
    
    def load_current_values(self):
        """Load current settings into UI"""
        # API Settings
        self.openai_enabled_var.set(self.api_settings.get('openai', {}).get('enabled', False))
        self.openai_key_var.set(self.api_settings.get('openai', {}).get('api_key', ''))
        self.openai_url_var.set(self.api_settings.get('openai', {}).get('base_url', API_SETTINGS['openai']['base_url']))
        self.openai_model_var.set(self.api_settings.get('openai', {}).get('default_model', API_SETTINGS['openai']['default_model']))
        
        self.claude_enabled_var.set(self.api_settings.get('anthropic', {}).get('enabled', False))
        self.claude_key_var.set(self.api_settings.get('anthropic', {}).get('api_key', ''))
        self.claude_url_var.set(self.api_settings.get('anthropic', {}).get('base_url', API_SETTINGS['anthropic']['base_url']))
        self.claude_model_var.set(self.api_settings.get('anthropic', {}).get('default_model', API_SETTINGS['anthropic']['default_model']))
        
        # Load presets
        all_presets = {**SYSTEM_PROMPT_PRESETS, **self.custom_presets}
        self.preset_combo['values'] = list(all_presets.keys())
        self.preset_var.set(self.current_preset)
        
        # Load first prompt type
        if all_presets:
            self.prompt_type_var.set('story_writer')
            self.on_preset_changed()
    
    def on_preset_changed(self, event=None):
        """Handle preset selection change"""
        preset_key = self.preset_var.get()
        all_presets = {**SYSTEM_PROMPT_PRESETS, **self.custom_presets}
        
        if preset_key in all_presets:
            preset = all_presets[preset_key]
            self.preset_desc_var.set(preset.get('description', ''))
            self.on_prompt_type_changed()
    
    def on_prompt_type_changed(self, event=None):
        """Handle prompt type selection change"""
        preset_key = self.preset_var.get()
        prompt_type = self.prompt_type_var.get()
        
        if not preset_key or not prompt_type:
            return
        
        all_presets = {**SYSTEM_PROMPT_PRESETS, **self.custom_presets}
        if preset_key in all_presets:
            preset = all_presets[preset_key]
            prompts = preset.get('prompts', {})
            
            if prompt_type in prompts:
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.insert(1.0, prompts[prompt_type])
    
    def create_new_preset(self):
        """Create a new preset"""
        dialog = PresetNameDialog(self.window)
        result = dialog.show()
        
        if result:
            name, description = result
            self.custom_presets[name] = {
                'name': name,
                'description': description,
                'prompts': SYSTEM_PROMPT_PRESETS['default']['prompts'].copy()
            }
            
            self.preset_combo['values'] = list({**SYSTEM_PROMPT_PRESETS, **self.custom_presets}.keys())
            self.preset_var.set(name)
            self.on_preset_changed()
    
    def save_preset_as(self):
        """Save current preset with new name"""
        current_preset = self.get_current_preset_data()
        
        dialog = PresetNameDialog(self.window)
        result = dialog.show()
        
        if result:
            name, description = result
            current_preset['name'] = name
            current_preset['description'] = description
            self.custom_presets[name] = current_preset
            
            self.preset_combo['values'] = list({**SYSTEM_PROMPT_PRESETS, **self.custom_presets}.keys())
            self.preset_var.set(name)
            self.save_custom_presets()
    
    def delete_preset(self):
        """Delete current preset"""
        preset_key = self.preset_var.get()
        
        if preset_key in SYSTEM_PROMPT_PRESETS:
            messagebox.showerror("Error", "Cannot delete built-in presets")
            return
        
        if preset_key in self.custom_presets:
            if messagebox.askyesno("Confirm Delete", f"Delete preset '{preset_key}'?"):
                del self.custom_presets[preset_key]
                self.preset_combo['values'] = list({**SYSTEM_PROMPT_PRESETS, **self.custom_presets}.keys())
                self.preset_var.set('default')
                self.on_preset_changed()
                self.save_custom_presets()
    
    def export_preset(self):
        """Export current preset to file"""
        preset_data = self.get_current_preset_data()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Preset"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(preset_data, f, indent=2)
                messagebox.showinfo("Success", f"Preset exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export preset: {e}")
    
    def import_preset(self):
        """Import preset from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Preset"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    preset_data = json.load(f)
                
                name = preset_data.get('name', os.path.splitext(os.path.basename(filename))[0])
                self.custom_presets[name] = preset_data
                
                self.preset_combo['values'] = list({**SYSTEM_PROMPT_PRESETS, **self.custom_presets}.keys())
                self.preset_var.set(name)
                self.on_preset_changed()
                self.save_custom_presets()
                
                messagebox.showinfo("Success", f"Preset '{name}' imported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import preset: {e}")
    
    def get_current_preset_data(self) -> Dict[str, Any]:
        """Get current preset data from UI"""
        preset_key = self.preset_var.get()
        all_presets = {**SYSTEM_PROMPT_PRESETS, **self.custom_presets}
        
        if preset_key in all_presets:
            preset = all_presets[preset_key].copy()
            
            # Update current prompt
            prompt_type = self.prompt_type_var.get()
            if prompt_type:
                if 'prompts' not in preset:
                    preset['prompts'] = {}
                preset['prompts'][prompt_type] = self.prompt_text.get(1.0, tk.END).strip()
            
            preset['description'] = self.preset_desc_var.get()
            return preset
        
        return {}
    
    def reset_current_prompt(self):
        """Reset current prompt to default"""
        prompt_type = self.prompt_type_var.get()
        if prompt_type in SYSTEM_PROMPT_PRESETS['default']['prompts']:
            default_prompt = SYSTEM_PROMPT_PRESETS['default']['prompts'][prompt_type]
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, default_prompt)
    
    def toggle_password_visibility(self, entry_widget):
        """Toggle password visibility"""
        if entry_widget['show'] == '*':
            entry_widget.config(show='')
        else:
            entry_widget.config(show='*')
    
    def test_api_connections(self):
        """Test API connections"""
        results = []
        
        # Test OpenAI
        if self.openai_enabled_var.get() and self.openai_key_var.get():
            try:
                # Simple test - this would need actual API call implementation
                results.append("OpenAI: Configuration saved (test requires implementation)")
            except Exception as e:
                results.append(f"OpenAI: Error - {e}")
        else:
            results.append("OpenAI: Disabled or no API key")
        
        # Test Claude
        if self.claude_enabled_var.get() and self.claude_key_var.get():
            try:
                results.append("Claude: Configuration saved (test requires implementation)")
            except Exception as e:
                results.append(f"Claude: Error - {e}")
        else:
            results.append("Claude: Disabled or no API key")
        
        messagebox.showinfo("API Test Results", "\n".join(results))
    
    def save_and_apply(self):
        """Save all settings and apply changes"""
        # Update API settings
        self.api_settings['openai']['enabled'] = self.openai_enabled_var.get()
        self.api_settings['openai']['api_key'] = self.openai_key_var.get()
        self.api_settings['openai']['base_url'] = self.openai_url_var.get()
        self.api_settings['openai']['default_model'] = self.openai_model_var.get()
        
        self.api_settings['anthropic']['enabled'] = self.claude_enabled_var.get()
        self.api_settings['anthropic']['api_key'] = self.claude_key_var.get()
        self.api_settings['anthropic']['base_url'] = self.claude_url_var.get()
        self.api_settings['anthropic']['default_model'] = self.claude_model_var.get()
        
        # Save current preset changes
        current_preset_data = self.get_current_preset_data()
        preset_key = self.preset_var.get()
        
        if preset_key in self.custom_presets:
            self.custom_presets[preset_key] = current_preset_data
        
        # Save to files
        self.save_api_settings()
        self.save_custom_presets()
        
        # Save active preset to config
        global ACTIVE_PRESET
        ACTIVE_PRESET = self.preset_var.get()
        
        messagebox.showinfo("Success", "Settings saved successfully!")
        self.window.destroy()


class PresetNameDialog:
    """Dialog for entering preset name and description"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("New Preset")
        self.window.geometry("400x200")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (200)
        y = (self.window.winfo_screenheight() // 2) - (100)
        self.window.geometry(f"400x200+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Name
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(name_frame, text="Name:", width=12).pack(side='left')
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(side='left', fill='x', expand=True)
        
        # Description
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill='x', pady=(0, 20))
        ttk.Label(desc_frame, text="Description:", width=12).pack(side='left')
        self.desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.desc_var, width=30).pack(side='left', fill='x', expand=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side='right')
        
        # Focus name entry
        self.window.after(100, lambda: self.name_var and self.window.focus_set())
    
    def ok_clicked(self):
        """Handle OK button"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a name")
            return
        
        self.result = (name, self.desc_var.get().strip())
        self.window.destroy()
    
    def show(self):
        """Show dialog and return result"""
        self.window.wait_window()
        return self.result