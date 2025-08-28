"""
Fast Network Discovery for Ollama Instances
Optimized for speed with session caching and background updates
"""

import socket
import threading
import time
import json
import requests
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import subprocess
import platform

class FastNetworkDiscovery:
    """Fast Ollama instance discovery with caching"""
    
    def __init__(self):
        self.ollama_instances = {}
        self.scan_active = False
        self.cache_timestamp = 0
        self.cache_duration = 300  # 5 minutes cache
        self.background_thread = None
        self.update_callbacks = []
        
        # Start background refresh
        self.start_background_refresh()
        
    def fast_scan(self, progress_callback=None) -> Dict[str, Dict]:
        """Fast network scan using optimized techniques"""
        # Check cache first
        if self.is_cache_valid():
            if progress_callback:
                progress_callback(100, 100)
            return self.ollama_instances.copy()
        
        self.scan_active = True
        found_instances = {}
        
        try:
            # Get active IPs quickly using system tools
            active_ips = self.get_active_ips_fast()
            
            if not active_ips:
                return found_instances
            
            # Check only active IPs for Ollama
            total_checks = len(active_ips) * 2  # Check main port + one alternative
            completed = 0
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {}
                
                for ip in active_ips:
                    if not self.scan_active:
                        break
                    
                    # Check main port (11434)
                    future = executor.submit(self.quick_check_ollama, ip, 11434)
                    futures[future] = (ip, 11434)
                    
                    # Check one alternative port (11435)
                    future = executor.submit(self.quick_check_ollama, ip, 11435)
                    futures[future] = (ip, 11435)
                
                for future in as_completed(futures):
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total_checks)
                        
                    ip, port = futures[future]
                    try:
                        result = future.result(timeout=0.5)  # Much faster timeout
                        if result:
                            instance_key = f"{ip}:{port}"
                            found_instances[instance_key] = {
                                'host': ip,
                                'port': port,
                                'url': f"http://{ip}:{port}",
                                'models': result.get('models', []),
                                'status': 'online',
                                'info': result.get('info', {}),
                                'display_name': f"Ollama @ {ip}:{port}",
                                'last_seen': time.time()
                            }
                    except Exception:
                        pass
            
            # Update cache
            self.ollama_instances.update(found_instances)
            self.cache_timestamp = time.time()
            
            # Notify callbacks
            self.notify_updates()
            
        except Exception as e:
            print(f"Fast scan error: {e}")
        finally:
            self.scan_active = False
            
        return found_instances
    
    def get_active_ips_fast(self) -> List[str]:
        """Get list of active IPs on network quickly"""
        active_ips = []
        
        try:
            # Get local network info
            local_ip = self.get_local_ip()
            if not local_ip:
                return active_ips
            
            # Add localhost
            active_ips.append('localhost')
            
            # Use ARP table to find active devices (much faster than ping)
            if platform.system().lower() == 'windows':
                try:
                    result = subprocess.run(['arp', '-a'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'dynamic' in line.lower() or 'static' in line.lower():
                                parts = line.strip().split()
                                if parts and self.is_valid_ip(parts[0]):
                                    active_ips.append(parts[0])
                except:
                    pass
            else:
                # Linux/Mac - use arp command
                try:
                    result = subprocess.run(['arp', '-a'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        import re
                        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                        ips = re.findall(ip_pattern, result.stdout)
                        active_ips.extend(ips)
                except:
                    pass
            
            # Fallback: check common local IPs quickly
            if len(active_ips) <= 2:  # Only localhost found
                network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
                common_ips = [str(network.network_address + i) 
                             for i in [1, 2, 10, 100, 101, 200, 254]]
                active_ips.extend(common_ips)
                
        except Exception as e:
            print(f"Error getting active IPs: {e}")
            # Fallback to localhost only
            active_ips = ['localhost']
        
        return list(set(active_ips))  # Remove duplicates
    
    def quick_check_ollama(self, ip: str, port: int) -> Optional[Dict]:
        """Quick check if Ollama is running - optimized for speed"""
        try:
            # Super fast socket check first
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)  # Very fast timeout
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result != 0:
                return None
            
            # Quick HTTP check
            url = f"http://{ip}:{port}/api/tags"
            response = requests.get(url, timeout=0.5)  # Fast timeout
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                if 'models' in data:
                    for model in data['models'][:10]:  # Limit to first 10 models
                        if isinstance(model, dict) and 'name' in model:
                            models.append(model['name'])
                        elif hasattr(model, 'name'):
                            models.append(model.name)
                        else:
                            models.append(str(model))
                
                return {
                    'models': models,
                    'url': f"http://{ip}:{port}"
                }
                
        except Exception:
            pass
        
        return None
    
    def start_background_refresh(self):
        """Start background thread for periodic updates"""
        def background_worker():
            while True:
                try:
                    time.sleep(30)  # Check every 30 seconds
                    if not self.is_cache_valid():
                        self.fast_scan()
                except Exception as e:
                    print(f"Background refresh error: {e}")
        
        self.background_thread = threading.Thread(target=background_worker, daemon=True)
        self.background_thread.start()
    
    def add_update_callback(self, callback: Callable):
        """Add callback for when instances are updated"""
        self.update_callbacks.append(callback)
    
    def notify_updates(self):
        """Notify all callbacks of updates"""
        for callback in self.update_callbacks:
            try:
                callback(self.ollama_instances)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        return (time.time() - self.cache_timestamp) < self.cache_duration
    
    def is_valid_ip(self, ip_str: str) -> bool:
        """Check if string is valid IP address"""
        try:
            ipaddress.IPv4Address(ip_str)
            return True
        except:
            return False
    
    def get_local_ip(self) -> Optional[str]:
        """Get local IP address"""
        try:
            # Connect to Google DNS to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return None
    
    def get_discovered_instances(self) -> Dict[str, Dict]:
        """Get all discovered Ollama instances"""
        return self.ollama_instances
    
    def stop_scan(self):
        """Stop network scanning"""
        self.scan_active = False
    
    def refresh_models_for_instance(self, instance_key: str) -> List[str]:
        """Refresh model list for specific instance - for discovery only"""
        if instance_key not in self.ollama_instances:
            return []
            
        instance = self.ollama_instances[instance_key]
        try:
            url = instance['url']
            # Keep timeout for discovery - this is just for finding instances, not AI generation
            response = requests.get(f"{url}/api/tags", timeout=3)  # Reasonable timeout for discovery
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                if 'models' in data:
                    for model in data['models']:
                        if isinstance(model, dict) and 'name' in model:
                            models.append(model['name'])
                        elif hasattr(model, 'name'):
                            models.append(model.name)
                        else:
                            models.append(str(model))
                
                # Update stored models and mark as online
                self.ollama_instances[instance_key]['models'] = models
                self.ollama_instances[instance_key]['status'] = 'online'
                self.ollama_instances[instance_key]['last_seen'] = time.time()
                return models
                
        except Exception as e:
            # Mark as offline if can't connect
            self.ollama_instances[instance_key]['status'] = 'offline'
            
        return []
    
    def get_cached_instances(self) -> Dict[str, Dict]:
        """Get cached instances immediately"""
        return self.ollama_instances.copy()
    
    def force_refresh(self):
        """Force immediate refresh (invalidate cache)"""
        self.cache_timestamp = 0
        return self.fast_scan()
    
    def scan_network(self, progress_callback=None):
        """Legacy method - redirect to fast_scan"""
        return self.fast_scan(progress_callback)