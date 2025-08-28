# Updated ollama_manager.py - Multi-network support with model selection per step:

"""
Ollama AI integration for Film Generator App
Supports multiple network connections and per-step model selection
"""

import json
import os
import requests
import threading
from typing import Dict, List, Optional
from config import OLLAMA_CONFIG, SYSTEM_PROMPTS, DB_DIR, MODEL_CONFIGS
from network_discovery import FastNetworkDiscovery

# Try to import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Warning: Ollama not installed. Install with: pip install ollama")
    print("Running in simulation mode...")

class OllamaManager:
    """Manages multiple Ollama connections and per-step model selection"""
    
    def __init__(self, config=OLLAMA_CONFIG):
        self.config = config
        self.available = OLLAMA_AVAILABLE
        self.network_discovery = FastNetworkDiscovery()
        self.settings_file = os.path.join(DB_DIR, "model_settings.json")
        
        # Multiple connection support
        self.ollama_instances = {}  # instance_key -> connection info
        self.step_model_assignments = {  # AI step -> (instance_key, model)
            'story': (None, None),
            'characters': (None, None),
            'shots': (None, None),
            'prompts': (None, None),
            'narration': (None, None),
            'music': (None, None)
        }
        
        # Legacy support
        self.available_models = []
        
        # Load persistent settings
        self.load_model_settings()
        
        if self.available:
            print("Initializing Ollama connections...")
            self.refresh_connections()
    
    def refresh_connections(self, force=False):
        """Refresh connections - uses cache for speed"""
        if not self.available:
            return {}
        
        # Always add localhost first (fast)
        self.add_localhost_connection()
        
        # Get cached instances first (instant)
        cached_instances = self.network_discovery.get_cached_instances()
        if cached_instances and not force:
            self.ollama_instances.update(cached_instances)
        else:
            # Background scan for new instances
            def background_scan():
                try:
                    discovered = self.network_discovery.fast_scan()
                    self.ollama_instances.update(discovered)
                    self.update_available_models()
                    print(f"Background scan found {len(discovered)} instances")
                except Exception as e:
                    print(f"Background scan error: {e}")
            
            # Non-blocking background scan
            threading.Thread(target=background_scan, daemon=True).start()
        
        self.update_available_models()
        return self.ollama_instances
    
    def update_available_models(self):
        """Update available models list from all instances"""
        self.available_models = []
        for instance in self.ollama_instances.values():
            self.available_models.extend(instance.get('models', []))
        
        # Remove duplicates
        self.available_models = list(set(self.available_models))
        print(f"Total instances: {len(self.ollama_instances)}, models: {len(self.available_models)}")
    
    def add_localhost_connection(self):
        """Add localhost Ollama connection using ollama library"""
        try:
            import ollama
            
            # Try local connection
            response = ollama.list()
            models = []
            
            if hasattr(response, 'models'):
                for model in response.models:
                    if hasattr(model, 'name'):
                        models.append(model.name)
                    elif hasattr(model, 'model'):
                        models.append(model.model)
                    else:
                        models.append(str(model))
            
            if models:
                self.ollama_instances['localhost:11434'] = {
                    'host': 'localhost',
                    'port': 11434,
                    'url': 'http://localhost:11434',
                    'models': models,
                    'status': 'online',
                    'display_name': 'Local Ollama',
                    'connection_type': 'library'  # Use ollama library
                }
                print(f"Added localhost with {len(models)} models")
                
        except Exception as e:
            print(f"Failed to add localhost connection: {e}")
    
    def refresh_models(self):
        """Legacy method for backward compatibility"""
        return self.refresh_connections()
    
    def test_connection(self, instance_key: str = None):
        """Test connection to specific instance or all instances"""
        if not OLLAMA_AVAILABLE:
            return False, "Ollama not installed"
        
        if instance_key:
            # Test specific instance
            if instance_key not in self.ollama_instances:
                return False, f"Instance {instance_key} not found"
            
            instance = self.ollama_instances[instance_key]
            try:
                if instance.get('connection_type') == 'library':
                    import ollama
                    response = ollama.list()
                    model_count = len(response.models) if hasattr(response, 'models') else 0
                else:
                    url = f"{instance['url']}/api/tags"
                    response = requests.get(url, timeout=3)
                    response.raise_for_status()
                    data = response.json()
                    model_count = len(data.get('models', []))
                
                models = instance.get('models', [])
                return True, f"{instance['display_name']}: {model_count} models available"
                
            except Exception as e:
                return False, f"{instance['display_name']}: Connection failed - {str(e)}"
        else:
            # Test all instances
            results = []
            total_models = 0
            
            for key, instance in self.ollama_instances.items():
                success, message = self.test_connection(key)
                if success:
                    total_models += len(instance.get('models', []))
                results.append(f"{key}: {'✓' if success else '✗'}")
            
            if total_models > 0:
                return True, f"Found {len(self.ollama_instances)} instances with {total_models} total models"
            else:
                return False, "No working Ollama instances found"
    
    def generate(self, prompt: str, system: str = None, temperature: float = None, step: str = 'story') -> str:
        """Generate response using assigned model for specific step"""
        if not self.available:
            raise Exception("Ollama not available - cannot generate content")
        
        # Get assigned instance and model for this step
        instance_key, model_name = self.step_model_assignments.get(step, (None, None))
        
        if not instance_key or not model_name:
            # Fallback to legacy single model
            if not self.config.get('selected_model'):
                raise Exception(f"No model assigned for step '{step}' - configure model assignments first")
            instance_key = 'localhost:11434'
            model_name = self.config['selected_model']
        
        if instance_key not in self.ollama_instances:
            raise Exception(f"Instance {instance_key} not available")
            
        instance = self.ollama_instances[instance_key]
        
        if model_name not in instance.get('models', []):
            raise Exception(f"Model {model_name} not available on {instance_key}")
        
        try:
            # Apply model-specific configurations
            enhanced_system = self._enhance_system_prompt(model_name, system)
            model_temperature = self._get_model_temperature(model_name, temperature)
            
            # Use appropriate connection method
            if instance.get('connection_type') == 'library':
                return self._generate_with_library(model_name, prompt, enhanced_system, model_temperature)
            else:
                return self._generate_with_api(instance, model_name, prompt, enhanced_system, model_temperature)
                
        except Exception as e:
            print(f"Generation error for step {step}: {e}")
            raise Exception(f"AI generation failed for {step}: {str(e)}")
    
    def _enhance_system_prompt(self, model_name: str, system_prompt: str) -> str:
        """Apply model-specific system prefix to enhance system prompt"""
        if not system_prompt:
            return system_prompt
        
        # Get model-specific config
        model_config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS.get('default', {}))
        system_prefix = model_config.get('system_prefix', '')
        
        if system_prefix:
            return system_prefix + system_prompt
        
        return system_prompt
    
    def _get_model_temperature(self, model_name: str, fallback_temperature: float = None) -> float:
        """Get model-specific temperature or fallback"""
        model_config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS.get('default', {}))
        model_temp = model_config.get('temperature')
        
        if model_temp is not None:
            return model_temp
        elif fallback_temperature is not None:
            return fallback_temperature
        else:
            return self.config['temperature']
    
    def _generate_with_library(self, model: str, prompt: str, system: str = None, temperature: float = None) -> str:
        """Generate using ollama library for localhost - NO TIMEOUT"""
        import ollama
        import os
        
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        
        # Try multiple approaches to remove timeouts
        try:
            # Method 1: Try environment variable for ollama client
            original_timeout = os.environ.get('OLLAMA_REQUEST_TIMEOUT', '')
            os.environ['OLLAMA_REQUEST_TIMEOUT'] = '0'  # 0 means no timeout
            
            try:
                response = ollama.chat(
                    model=model,
                    messages=messages,
                    options={
                        'temperature': temperature or self.config['temperature'],
                        'top_p': self.config['top_p']
                    }
                )
            finally:
                # Restore original timeout
                if original_timeout:
                    os.environ['OLLAMA_REQUEST_TIMEOUT'] = original_timeout
                else:
                    os.environ.pop('OLLAMA_REQUEST_TIMEOUT', None)
            
        except Exception as e:
            # Method 2: If that fails, try with custom client
            try:
                client = ollama.Client(timeout=None)
                response = client.chat(
                    model=model,
                    messages=messages,
                    options={
                        'temperature': temperature or self.config['temperature'],
                        'top_p': self.config['top_p']
                    }
                )
            except Exception:
                # Method 3: Fall back to HTTP API directly
                print(f"Ollama library timeout issue, falling back to HTTP API: {e}")
                return self._generate_with_direct_http('localhost', 11434, model, prompt, system, temperature)
        
        # Handle ChatResponse object
        if hasattr(response, 'message'):
            if hasattr(response.message, 'content'):
                return response.message.content
        elif isinstance(response, dict) and 'message' in response:
            return response['message']['content']
        
        raise Exception(f"Could not extract content from response: {type(response)}")
    
    def _generate_with_direct_http(self, host: str, port: int, model: str, prompt: str, system: str = None, temperature: float = None) -> str:
        """Direct HTTP call as fallback when ollama library has timeout issues"""
        url = f"http://{host}:{port}/api/chat"
        
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        
        data = {
            'model': model,
            'messages': messages,
            'options': {
                'temperature': temperature or self.config['temperature'],
                'top_p': self.config['top_p']
            },
            'stream': False
        }
        
        # NO TIMEOUT - AI generation can take as long as needed
        response = requests.post(url, json=data, timeout=None)
        response.raise_for_status()
        
        result = response.json()
        if 'message' in result and 'content' in result['message']:
            return result['message']['content']
            
        raise Exception(f"Invalid response format from direct HTTP call")
    
    def _generate_with_api(self, instance: dict, model: str, prompt: str, system: str = None, temperature: float = None) -> str:
        """Generate using HTTP API for network instances - NO TIMEOUT"""
        url = f"{instance['url']}/api/chat"
        
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        
        data = {
            'model': model,
            'messages': messages,
            'options': {
                'temperature': temperature or self.config['temperature'],
                'top_p': self.config['top_p']
            },
            'stream': False
        }
        
        # NO TIMEOUT - AI generation can take as long as needed
        response = requests.post(url, json=data, timeout=None)
        response.raise_for_status()
        
        result = response.json()
        if 'message' in result and 'content' in result['message']:
            return result['message']['content']
            
        raise Exception(f"Invalid response format from {instance['url']}")
    
    def set_step_model(self, step: str, instance_key: str, model_name: str) -> bool:
        """Assign specific model to AI generation step"""
        if instance_key not in self.ollama_instances:
            print(f"Instance {instance_key} not found")
            return False
            
        instance = self.ollama_instances[instance_key]
        if model_name not in instance.get('models', []):
            print(f"Model {model_name} not available on {instance_key}")
            return False
        
        self.step_model_assignments[step] = (instance_key, model_name)
        self.save_model_settings()  # Save settings immediately
        print(f"Assigned {step}: {model_name} on {instance_key}")
        return True
    
    def get_step_model(self, step: str) -> tuple:
        """Get assigned model for specific step"""
        return self.step_model_assignments.get(step, (None, None))
    
    def set_model(self, model_name: str):
        """Legacy: Set active model for backward compatibility"""
        if model_name in self.available_models:
            self.config['selected_model'] = model_name
            # Also set for story step as default
            for instance_key, instance in self.ollama_instances.items():
                if model_name in instance.get('models', []):
                    self.step_model_assignments['story'] = (instance_key, model_name)
                    break
            self.save_model_settings()  # Save settings immediately
            print(f"Set active model to: {model_name}")
            return True
        return False
    
    def get_step_assignments(self) -> Dict[str, tuple]:
        """Get all step model assignments"""
        return self.step_model_assignments.copy()
    
    def get_available_instances(self) -> Dict[str, Dict]:
        """Get all available Ollama instances"""
        return self.ollama_instances.copy()
    
    def get_current_model(self):
        """Legacy: Get current model for backward compatibility"""
        story_instance, story_model = self.step_model_assignments.get('story', (None, None))
        if story_model:
            return story_model
        return self.config.get('selected_model', 'None')
    
    def save_model_settings(self):
        """Save model assignments to persistent storage"""
        try:
            settings = {
                'step_model_assignments': self.step_model_assignments,
                'config': {
                    'selected_model': self.config.get('selected_model'),
                    'temperature': self.config.get('temperature'),
                    'top_p': self.config.get('top_p')
                },
                'version': '1.0'
            }
            
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            print(f"Model settings saved to {self.settings_file}")
            
        except Exception as e:
            print(f"Failed to save model settings: {e}")
    
    def load_model_settings(self):
        """Load model assignments from persistent storage with fallback to none"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Load step assignments with validation
                saved_assignments = settings.get('step_model_assignments', {})
                for step, assignment in saved_assignments.items():
                    if step in self.step_model_assignments:
                        # Validate assignment format
                        if isinstance(assignment, (list, tuple)) and len(assignment) == 2:
                            instance_key, model_name = assignment
                            if instance_key and model_name:
                                self.step_model_assignments[step] = (instance_key, model_name)
                
                # Load legacy config
                saved_config = settings.get('config', {})
                if saved_config.get('selected_model'):
                    self.config['selected_model'] = saved_config['selected_model']
                
                print(f"Model settings loaded from {self.settings_file}")
                
        except Exception as e:
            print(f"Failed to load model settings (using defaults): {e}")
            # Reset to defaults on any error
            self.step_model_assignments = {
                'story': (None, None),
                'characters': (None, None),
                'shots': (None, None),
                'prompts': (None, None),
                'narration': (None, None),
                'music': (None, None)
            }
    
    # Keep all existing simulation methods
    def _simulate_response(self, prompt: str, system: str) -> str:
        if "story" in prompt.lower():
            return self._simulate_story()
        elif "shot" in prompt.lower():
            return self._simulate_shot_list()
        elif "prompt" in prompt.lower():
            return self._simulate_wan_prompt()
        elif "narration" in prompt.lower():
            return self._simulate_narration()
        elif "music" in prompt.lower():
            return self._simulate_music()
        else:
            return "Simulated response"
    
    def _simulate_story(self) -> str:
        return """Title: The Last Message
        
Logline: A teenager discovers their deceased grandmother's phone still sends texts, leading to an impossible connection.

Story:

Part 1 - Discovery (0-30 seconds)
Sarah is cleaning out her grandmother's attic when an old phone buzzes. A text appears: "Don't forget to water the roses." The phone has been disconnected for months. Sarah's hands tremble as she types back: "Grandma?"

Part 2 - Connection (30-60 seconds)  
The replies keep coming, each containing memories only her grandmother would know. Sarah races to the garden, finding a time capsule exactly where the texts describe. Inside: letters from the past and one addressed to "My future granddaughter."

Part 3 - Resolution (60-90 seconds)
The final text arrives with GPS coordinates. Sarah discovers her grandmother had scheduled messages before passing, creating one last adventure. At the location, Sarah finds her grandmother's favorite rose bush and a bench with a plaque: "For all the conversations yet to come."

Tone: Emotional, mysterious, ultimately uplifting
Key Themes: Connection across time, love transcending death, the power of memory"""

    def _simulate_shot_list(self) -> str:
        return json.dumps({
            "shots": [
                {
                    "shot_number": 1,
                    "description": "Close-up of dusty phone screen lighting up in dark attic",
                    "duration": 3.0,
                    "camera": "Macro close-up, slow push in",
                    "subjects": ["phone", "dust particles", "light beam"],
                    "mood": "mysterious",
                    "narration": "Some messages transcend time...",
                    "music_cue": "Soft piano, mysterious"
                }
            ]
        }, indent=2)
    
    def _simulate_wan_prompt(self) -> str:
        return """Positive prompt: Close-up shot of vintage phone screen illuminating in dark dusty attic, cinematic lighting, dust particles floating in light beam, shallow depth of field, mysterious atmosphere, film grain, professional cinematography, masterpiece, best quality, ultra-detailed, 8k resolution

Negative prompt: blurry, low quality, oversaturated, cartoon, anime, painting, illustration, bad composition, amateur

Technical specs: Resolution: 1920x1080, Steps: 30, CFG Scale: 7.5, Sampler: DPM++ 2M Karras"""

    def _simulate_narration(self) -> str:
        return """[00:00-00:03] "Some messages... transcend time itself."
[Tone: Mysterious, slow, contemplative]"""

    def _simulate_music(self) -> str:
        return """Scene: 1 (Opening)
Music style: Ambient piano with subtle strings
Duration: 30 seconds"""