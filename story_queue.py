"""
Story Queue Management System
Handles batch story generation with priority management and continuous generation
"""

import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import asdict
from datetime import datetime, timedelta
import json

from database import DatabaseManager
from data_models import StoryConfig, QueueItem, QueueConfig
from story_generator import StoryGenerator


class StoryQueue:
    """Manages story generation queue with continuous generation and render throttling"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.story_generator = None
        self.running = False
        self.paused = False
        self.current_queue_item = None
        self.worker_thread = None
        self.progress_callback = None
        self.completion_callback = None
        self.error_callback = None
        self.lock = threading.Lock()
        
        # Load queue configuration
        self.config = self._load_config()
    
    def set_story_generator(self, story_generator: StoryGenerator):
        """Set the story generator instance"""
        self.story_generator = story_generator
    
    def set_callbacks(self, progress_callback: Callable = None, 
                     completion_callback: Callable = None,
                     error_callback: Callable = None):
        """Set callback functions for queue events"""
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
    
    def _load_config(self) -> QueueConfig:
        """Load queue configuration from database"""
        config_data = self.db.get_queue_config()
        return QueueConfig(
            continuous_enabled=config_data.get('continuous_enabled', False),
            render_queue_high_threshold=config_data.get('render_queue_high_threshold', 50),
            render_queue_low_threshold=config_data.get('render_queue_low_threshold', 10),
            max_concurrent_generations=config_data.get('max_concurrent_generations', 1),
            auto_priority_boost=config_data.get('auto_priority_boost', True),
            retry_failed_items=config_data.get('retry_failed_items', True)
        )
    
    def update_config(self, **kwargs):
        """Update queue configuration"""
        config_dict = asdict(self.config)
        config_dict.update(kwargs)
        self.config = QueueConfig(**config_dict)
        self.db.update_queue_config(config_dict)
    
    def add_to_queue(self, story_config: StoryConfig, priority: int = 5, 
                    continuous: bool = False) -> int:
        """Add story to generation queue"""
        config_dict = asdict(story_config)
        queue_id = self.db.add_to_story_queue(config_dict, priority, continuous)
        
        # Start processing if not already running
        if not self.running:
            self.start_processing()
        
        return queue_id
    
    def get_queue_items(self, status: str = None, limit: int = None) -> List[Dict]:
        """Get queue items"""
        return self.db.get_queue_items(status, limit)
    
    def get_queue_statistics(self) -> Dict:
        """Get queue statistics"""
        return self.db.get_queue_statistics()
    
    def remove_from_queue(self, queue_id: int) -> bool:
        """Remove item from queue"""
        with self.lock:
            # Don't remove if currently processing
            if self.current_queue_item and self.current_queue_item.get('id') == queue_id:
                return False
        
        return self.db.remove_from_queue(queue_id)
    
    def reorder_queue_item(self, queue_id: int, new_position: int) -> bool:
        """Reorder queue item"""
        return self.db.reorder_queue_item(queue_id, new_position)
    
    def pause_queue(self):
        """Pause queue processing"""
        self.paused = True
    
    def resume_queue(self):
        """Resume queue processing"""
        self.paused = False
    
    def start_processing(self):
        """Start queue processing thread"""
        if not self.running and self.story_generator:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
    
    def stop_processing(self):
        """Stop queue processing"""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
    
    def _process_queue(self):
        """Main queue processing loop"""
        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Check if we should wait for render queue to clear
                if self._should_wait_for_render_queue():
                    time.sleep(5)
                    continue
                
                # Get next queue item
                with self.lock:
                    next_item = self.db.get_next_queue_item()
                    if not next_item:
                        # No items to process
                        if self.config.continuous_enabled:
                            self._maybe_add_continuous_story()
                        time.sleep(2)
                        continue
                    
                    self.current_queue_item = next_item
                
                # Process the item
                self._process_queue_item(next_item)
                
            except Exception as e:
                print(f"Error in queue processing: {e}")
                if self.error_callback:
                    self.error_callback(f"Queue processing error: {e}")
                time.sleep(5)
            finally:
                with self.lock:
                    self.current_queue_item = None
    
    def _should_wait_for_render_queue(self) -> bool:
        """Check if we should wait for render queue to clear"""
        if not self.config.continuous_enabled:
            return False
        
        render_stats = self.db.get_render_queue_status()
        queued_renders = render_stats.get('queued', 0)
        
        # If render queue is above high threshold, wait
        return queued_renders >= self.config.render_queue_high_threshold
    
    def _maybe_add_continuous_story(self):
        """Add a new story for continuous generation if conditions are met"""
        if not self.config.continuous_enabled:
            return
        
        # Check render queue level
        render_stats = self.db.get_render_queue_status()
        queued_renders = render_stats.get('queued', 0)
        
        if queued_renders >= self.config.render_queue_low_threshold:
            return  # Still too many in render queue
        
        # Check if we already have enough queued items
        queue_stats = self.get_queue_statistics()
        if queue_stats.get('queued', 0) > 0:
            return  # Already have items queued
        
        # Generate a random story config for continuous generation
        from config import GENRE_PROMPTS
        import random
        
        genres = list(GENRE_PROMPTS.keys())
        lengths = ["Short", "Medium", "Long"]
        
        random_config = StoryConfig(
            prompt="Auto-generated story",
            genre=random.choice(genres),
            length=random.choice(lengths),
            auto_prompt=True,
            auto_genre=True,
            auto_length=True,
            auto_style=True
        )
        
        # Add to queue with continuous flag
        self.add_to_queue(random_config, priority=3, continuous=True)
    
    def _process_queue_item(self, queue_item: Dict):
        """Process a single queue item"""
        queue_id = queue_item['id']
        story_config_dict = queue_item['story_config']
        
        try:
            # Convert dict back to StoryConfig
            story_config = StoryConfig(**story_config_dict)
            
            # Update status to processing
            self.db.update_queue_item_status(
                queue_id, 'processing', 'story_generation'
            )
            
            if self.progress_callback:
                self.progress_callback(queue_id, 'processing', 'story_generation', {})
            
            # Set up progress callback for story generator
            def story_progress_callback(progress, text):
                progress_data = {
                    'progress': progress,
                    'current_step': text
                }
                self.db.update_queue_item_status(
                    queue_id, 'processing', text, progress_data
                )
                if self.progress_callback:
                    self.progress_callback(queue_id, 'processing', text, progress_data)
            
            # Set up log callback - forward to progress callback for AI messages
            def log_callback(message, log_type):
                print(f"[{log_type}] {message}")
                if self.progress_callback:
                    # Send log messages as AI messages to the progress window
                    progress_data = {
                        'progress': 0,  # Will be updated by progress callback
                        'current_step': text if 'text' in locals() else 'processing',
                        'ai_message': {
                            'type': log_type.lower(),
                            'content': message,
                            'step': text if 'text' in locals() else 'processing'
                        }
                    }
                    self.progress_callback(queue_id, 'processing', 'ai_message', progress_data)
            
            # Generate the complete story (story + shots)
            story_data, shots = self.story_generator.generate_complete_story(
                story_config, progress_callback=story_progress_callback, log_callback=log_callback
            )
            
            if story_data and shots:
                # Update with completion
                self.db.update_queue_item_status(
                    queue_id, 'completed', 'completed', 
                    {'story_data': story_data, 'shots': [shot.__dict__ for shot in shots]}, story_data.get('id')
                )
                
                # Add shots to render queue
                self._add_shots_to_render_queue(story_data)
                
                if self.completion_callback:
                    self.completion_callback(queue_id, {'story': story_data, 'shots': shots})
            else:
                # Generation failed
                self.db.update_queue_item_status(
                    queue_id, 'failed', 'failed', 
                    error="Story generation returned no data"
                )
                
        except Exception as e:
            error_msg = str(e)
            attempts = self.db.increment_queue_attempts(queue_id)
            
            if attempts < queue_item.get('max_attempts', 3) and self.config.retry_failed_items:
                # Retry later
                self.db.update_queue_item_status(
                    queue_id, 'queued', 'retry_pending', error=error_msg
                )
            else:
                # Max attempts reached
                self.db.update_queue_item_status(
                    queue_id, 'failed', 'max_attempts_reached', error=error_msg
                )
            
            if self.error_callback:
                self.error_callback(f"Queue item {queue_id} failed: {error_msg}")
    
    def get_current_processing_item(self) -> Optional[Dict]:
        """Get currently processing queue item"""
        with self.lock:
            return self.current_queue_item.copy() if self.current_queue_item else None
    
    def clear_completed_items(self, older_than_days: int = None):
        """Clear completed queue items"""
        if older_than_days is None:
            # Clear all completed items immediately (for UI calls)
            cursor = self.db.conn.cursor()
            cursor.execute('''
                DELETE FROM story_queue 
                WHERE status IN ('completed', 'failed')
            ''')
            self.db.conn.commit()
            return cursor.rowcount
        else:
            # Clear only old completed items (for maintenance)
            return self.db.clear_completed_queue_items(older_than_days)
    
    def get_queue_item_by_story_id(self, story_id: str) -> Optional[Dict]:
        """Get queue item by associated story ID"""
        items = self.db.get_queue_items()
        for item in items:
            if item.get('story_id') == story_id:
                return item
        return None
    
    def retry_failed_item(self, queue_id: int) -> bool:
        """Retry a failed queue item"""
        try:
            # Reset the item to queued status
            self.db.update_queue_item_status(
                queue_id, 'queued', 'retry_manual', error=None
            )
            return True
        except Exception as e:
            print(f"Error retrying queue item {queue_id}: {e}")
            return False
    
    def update_item_priority(self, queue_id: int, new_priority: int) -> bool:
        """Update queue item priority"""
        try:
            # This would require a new database method
            cursor = self.db.conn.cursor()
            cursor.execute('''
                UPDATE story_queue SET priority = ? WHERE id = ?
            ''', (new_priority, queue_id))
            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating priority for queue item {queue_id}: {e}")
            return False
    
    def _add_shots_to_render_queue(self, story_data: Dict):
        """Add completed story shots to render queue"""
        try:
            story_id = story_data.get('id')
            if not story_id:
                return
            
            # Get all shots for this story
            cursor = self.db.conn.cursor()
            cursor.execute('SELECT id FROM shots WHERE story_id = ?', (story_id,))
            shot_rows = cursor.fetchall()
            
            # Add each shot to render queue
            for shot_row in shot_rows:
                shot_id = shot_row[0]
                self.db.add_to_render_queue(shot_id, priority=5)
            
            print(f"Added {len(shot_rows)} shots to render queue for story {story_id}")
            
        except Exception as e:
            print(f"Error adding shots to render queue: {e}")