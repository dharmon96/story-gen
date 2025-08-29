"""
Story generation logic for Film Generator App
Handles story creation, shot list generation, and prompt engineering
"""

import json
import time
import random
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from config import GENERATION_SETTINGS, SYSTEM_PROMPTS, STORY_PROMPTS, VISUAL_STYLES, RENDER_SETTINGS
from data_models import StoryConfig, Shot
from ollama_manager import OllamaManager
from database import DatabaseManager
from comfyui_manager import ComfyUIManager

class StoryGenerator:
    """Handles all story generation and processing"""
    
    def __init__(self, ollama: OllamaManager, db: DatabaseManager):
        self.ollama = ollama
        self.db = db
        self.comfyui = ComfyUIManager(db)
        self.progress_window = None  # Add this line

    def set_progress_window(self, progress_window):
        """Set reference to progress popup window"""
        self.progress_window = progress_window
        self.comfyui.set_progress_window(progress_window)
    
    def get_trending_prompt(self, genre: str = None, use_research: bool = True) -> Optional[str]:
        """Get a trending prompt based on research data"""
        if not use_research:
            return None
            
        try:
            # Get research-based prompts first
            research_prompts = self.db.get_research_prompts(genre=genre, limit=10)
            
            if research_prompts:
                # Weight prompts by expected performance and success rate
                weighted_prompts = []
                for prompt_data in research_prompts:
                    weight = (
                        prompt_data.get('expected_performance', 0.5) * 0.7 +
                        prompt_data.get('success_rate', 0.5) * 0.3
                    )
                    # Bonus for recent usage
                    usage_count = prompt_data.get('usage_count', 0)
                    if usage_count < 3:  # Prefer less-used prompts
                        weight += 0.1
                    
                    weighted_prompts.append((prompt_data, weight))
                
                # Sort by weight and select from top 3
                weighted_prompts.sort(key=lambda x: x[1], reverse=True)
                top_prompts = weighted_prompts[:3]
                
                if top_prompts:
                    selected_prompt, _ = random.choice(top_prompts)
                    
                    # Update usage statistics
                    self.db.update_prompt_usage(selected_prompt['id'], success=True)
                    
                    return selected_prompt['prompt']
            
        except Exception as e:
            print(f"Error getting trending prompt: {e}")
        
        return None
    
    def enhance_prompt_with_trends(self, original_prompt: str, genre: str = None) -> str:
        """Enhance an existing prompt with trending elements"""
        try:
            # Get top trending keywords for the genre
            trends = self.db.get_trending_summary(limit=10)
            
            if not trends:
                return original_prompt
            
            # Filter by genre/category if specified
            if genre:
                genre_trends = [t for t in trends if genre.lower() in t.get('category', '').lower()]
                if genre_trends:
                    trends = genre_trends
            
            # Select a high-performing trend
            if trends:
                top_trend = trends[0]  # Already sorted by trend_score
                keyword = top_trend['keyword']
                
                # Enhance the prompt with trending keyword
                enhanced_prompt = f"{original_prompt} (incorporating trending AI topic: {keyword})"
                return enhanced_prompt
                
        except Exception as e:
            print(f"Error enhancing prompt with trends: {e}")
        
        return original_prompt
    
    def generate_character_comfyui_prompts(self, characters: List[Dict]) -> List[Dict]:
        """Generate ComfyUI prompts for each character for visual consistency"""
        if not self.ollama.available:
            raise Exception("Ollama not available for character prompt generation")
        
        character_prompts = []
        
        for character in characters:
            try:
                # Create prompt for character reference image
                prompt = f"""Character: {character['name']} ({character['role']})
Physical Description: {character['physical_description']}
Age Range: {character['age_range']}
Clothing Style: {character['clothing_style']}
Personality Traits: {character['personality_traits']}"""
                
                # Log request
                if self.progress_window:
                    self.progress_window.add_ai_message('request', prompt, 'characters')
                
                # Generate ComfyUI prompt using prompt engineer
                raw_response = self.ollama.generate(
                    prompt=prompt,
                    system=SYSTEM_PROMPTS['prompt_engineer'],
                    temperature=0.3,
                    step='characters'
                )
                
                # Log response
                if self.progress_window:
                    self.progress_window.add_ai_message('response', raw_response, 'characters')
                
                # Clean response
                response = self.clean_ai_response(raw_response)
                
                # Extract positive prompt
                if "Positive:" in response:
                    comfyui_prompt = response.split("Positive:")[1].split("Negative:")[0].strip()
                else:
                    comfyui_prompt = response.split('\n')[0].strip()
                
                character_prompt_data = {
                    'character_name': character['name'],
                    'character_role': character['role'],
                    'comfyui_prompt': comfyui_prompt,
                    'importance_level': character.get('importance_level', 1)
                }
                
                character_prompts.append(character_prompt_data)
                
                if self.progress_window:
                    self.progress_window.add_ai_message('success', 
                        f"Generated ComfyUI prompt for {character['name']}: {comfyui_prompt[:50]}...", 'characters')
                
            except Exception as e:
                if self.progress_window:
                    self.progress_window.add_ai_message('error', 
                        f"Failed to generate ComfyUI prompt for {character['name']}: {str(e)}", 'characters')
                # Continue with other characters even if one fails
                continue
        
        return character_prompts
    
    def enhance_prompt_with_style(self, base_prompt: str, visual_style: str) -> Tuple[str, str]:
        """Enhance a base prompt with the selected visual style"""
        if not visual_style or visual_style not in VISUAL_STYLES:
            return base_prompt, ""
        
        style_config = VISUAL_STYLES[visual_style]
        
        # Select style prompts based on strength
        style_strength = style_config['style_strength']
        positive_style = style_config['positive_prompts']
        negative_style = style_config['negative_prompts']
        
        # Choose appropriate style prompt based on strength
        if style_strength > 0.8:
            # High strength - use multiple style elements
            selected_positive = ', '.join(positive_style[:2])
        elif style_strength > 0.6:
            # Medium strength - use one primary style element
            selected_positive = positive_style[0]
        else:
            # Low strength - subtle style influence
            selected_positive = positive_style[0] if positive_style else ""
        
        # Enhance the base prompt
        if selected_positive:
            enhanced_prompt = f"{base_prompt}, {selected_positive}"
        else:
            enhanced_prompt = base_prompt
        
        # Combine negative prompts
        enhanced_negative = ', '.join(negative_style) if negative_style else ""
        
        return enhanced_prompt, enhanced_negative
    
    def analyze_story_characters_and_locations(self, story: Dict) -> Tuple[List[Dict], List[Dict], Dict]:
        """Analyze story to extract characters, locations, and visual style for consistency"""
        if not self.ollama.available:
            raise Exception("Ollama not available for character analysis")
        
        # Simple user prompt with story data - system prompt handles the extraction
        prompt = f"""Story: {story['title']}
Genre: {story['genre']}
Length: {story['length']}

{story['content']}"""

        # Log FULL request
        if self.progress_window:
            self.progress_window.add_ai_message('request', prompt, 'characters')

        try:
            # Generate with Ollama using character analyzer
            raw_response = self.ollama.generate(
                prompt=prompt,
                system=SYSTEM_PROMPTS['character_analyzer'],
                temperature=0.3,
                step='characters'
            )
            
            # Log FULL raw response (including <think> for display)
            if self.progress_window:
                self.progress_window.add_ai_message('response', raw_response, 'characters')
            
            # Clean response for JSON parsing
            response = self.clean_ai_response(raw_response)
            
            # Parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                try:
                    analysis_data = json.loads(json_str)
                    
                    characters = analysis_data.get('characters', [])
                    locations = analysis_data.get('locations', [])
                    visual_style = analysis_data.get('visual_style', {})
                    
                    if self.progress_window:
                        self.progress_window.add_ai_message('success', 
                            f"Extracted {len(characters)} characters and {len(locations)} locations", 'characters')
                    
                    return characters, locations, visual_style
                        
                except json.JSONDecodeError as e:
                    if self.progress_window:
                        self.progress_window.add_ai_message('error', 
                            f"JSON parsing failed: {str(e)}\nCleaned response: {response}", 'characters')
                    raise Exception(f"Invalid JSON from character analyzer: {str(e)}")
            else:
                if self.progress_window:
                    self.progress_window.add_ai_message('error', 
                        f"No JSON found in character analyzer response: {response[:200]}...", 'characters')
                raise Exception("Character analyzer did not return valid JSON format")
                
        except Exception as e:
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Character analysis failed: {str(e)}", 'characters')
            raise Exception(f"Failed to analyze characters and locations: {str(e)}")
    
    def select_optimal_prompt(self, config: StoryConfig) -> str:
        """Select the most optimal prompt considering research data and user preferences"""
        selected_prompt = config.prompt
        prompt_source = "user"
        
        # If using auto-generation or user wants trending content
        if hasattr(config, 'use_trending') and config.use_trending:
            trending_prompt = self.get_trending_prompt(config.genre, use_research=True)
            
            if trending_prompt:
                selected_prompt = trending_prompt
                prompt_source = "trending"
            else:
                # Fallback to enhanced original prompt
                selected_prompt = self.enhance_prompt_with_trends(config.prompt, config.genre)
                prompt_source = "enhanced"
        
        # For auto-prompts, also consider performance data
        elif config.prompt.strip() == "" or "auto" in config.prompt.lower():
            # Try trending first
            trending_prompt = self.get_trending_prompt(config.genre, use_research=True)
            
            if trending_prompt:
                selected_prompt = trending_prompt
                prompt_source = "trending"
            else:
                # Use best-performing traditional prompts
                best_prompts = self.db.get_best_performing_prompts(limit=5)
                if best_prompts:
                    selected_prompt = random.choice(best_prompts)
                    prompt_source = "performance"
                else:
                    # Fall back to traditional genre prompts
                    genre_prompts = STORY_PROMPTS.get(config.genre, STORY_PROMPTS['Drama'])
                    selected_prompt = random.choice(genre_prompts)
                    prompt_source = "traditional"
        
        print(f"Selected prompt from {prompt_source}: {selected_prompt[:100]}...")
        return selected_prompt
    
    def get_trending_elements_for_enhancement(self, genre: str = None) -> Dict:
        """Get trending elements that can enhance story generation"""
        try:
            trends = self.db.get_trending_summary(limit=5)
            
            # Filter and categorize trends
            enhancement_data = {
                'keywords': [],
                'themes': [],
                'content_types': [],
                'performance_indicators': []
            }
            
            for trend in trends:
                if not genre or genre.lower() in trend.get('category', '').lower():
                    enhancement_data['keywords'].append(trend['keyword'])
                    enhancement_data['themes'].append(trend.get('category', ''))
                    enhancement_data['performance_indicators'].append({
                        'keyword': trend['keyword'],
                        'score': trend['trend_score'],
                        'engagement': trend.get('avg_engagement', 0)
                    })
            
            return enhancement_data
            
        except Exception as e:
            print(f"Error getting trending elements: {e}")
            return {'keywords': [], 'themes': [], 'content_types': [], 'performance_indicators': []}
    
    def generate_complete_story(self, config: StoryConfig, progress_callback=None, log_callback=None) -> Tuple[Dict, List[Shot]]:
        """Generate a complete story with shots"""
        
        def update_progress(value, text):
            if progress_callback:
                progress_callback(value, text)
        
        def add_log(message, log_type="Info"):
            if log_callback:
                log_callback(message, log_type)
        
        # Select optimal prompt using research data
        update_progress(10, "Selecting optimal story prompt...")
        optimal_prompt = self.select_optimal_prompt(config)
        
        # Update config with selected prompt
        optimized_config = StoryConfig(
            prompt=optimal_prompt,
            genre=config.genre,
            length=config.length,
            visual_style=config.visual_style,
            aspect_ratio=config.aspect_ratio,
            fps=config.fps,
            auto_prompt=config.auto_prompt,
            auto_genre=config.auto_genre,
            auto_length=config.auto_length,
            auto_style=config.auto_style,
            parts=config.parts
        )
        
        # Generate story
        update_progress(15, "Generating story with AI...")
        add_log(f"Using optimized prompt: {optimal_prompt[:100]}...", "Research")
        add_log(f"Sending prompt to AI: {optimal_prompt[:100]}...", "AI")
        
        # Update progress window with render node info
        if self.progress_window and hasattr(self.progress_window, 'update_step_node_info'):
            selected_model = getattr(self.ollama, 'selected_model', {}).get('story', 'llama3.1')
            node_name = getattr(self.ollama, 'selected_instance', 'localhost')
            self.progress_window.update_step_node_info('story', node_name, 'ollama', selected_model)
        
        story = self.generate_story(optimized_config)
        
        if story:
            add_log(f"Story generated: {story['title']}", "AI")
            update_progress(25, f"Story '{story['title']}' created")
            
            # Save to database
            add_log(f"Saving story to database...", "Database")
            story_id = self.db.save_story(story)
            self.db.save_generation_history(story_id, optimized_config)
            add_log(f"Story saved with ID: {story_id}", "Database")
            
            # Create shot list (moved to step 2)
            update_progress(30, "Breaking story into shots...")
            add_log("Creating shot list from story content...", "AI")
            
            # Update progress window with render node info
            if self.progress_window and hasattr(self.progress_window, 'update_step_node_info'):
                selected_model = getattr(self.ollama, 'selected_model', {}).get('shots', 'llama3.1')
                node_name = getattr(self.ollama, 'selected_instance', 'localhost')
                self.progress_window.update_step_node_info('shots', node_name, 'ollama', selected_model)
            
            shots = self.create_shot_list(story, optimized_config)
            add_log(f"Created {len(shots)} shots", "AI")
            
            # Update time estimates now that we know shot count
            if self.progress_window and hasattr(self.progress_window, 'update_step_estimates'):
                self.progress_window.update_step_estimates(shot_count=len(shots))
            
            # Analyze characters and locations for consistency (now step 3)
            update_progress(40, "Analyzing characters and locations...")
            add_log("Extracting characters and locations for visual consistency...", "AI")
            
            # Update progress window with render node info
            if self.progress_window and hasattr(self.progress_window, 'update_step_node_info'):
                selected_model = getattr(self.ollama, 'selected_model', {}).get('characters', 'llama3.1')
                node_name = getattr(self.ollama, 'selected_instance', 'localhost')
                self.progress_window.update_step_node_info('characters', node_name, 'ollama', selected_model)
            
            try:
                characters, locations, visual_style = self.analyze_story_characters_and_locations(story)
                add_log(f"Found {len(characters)} characters and {len(locations)} locations", "AI")
                
                # Update time estimates now that we know character count
                if self.progress_window and hasattr(self.progress_window, 'update_step_estimates'):
                    self.progress_window.update_step_estimates(character_count=len(characters))
                
                # Generate ComfyUI prompts for characters (NEW)
                update_progress(42, "Generating character ComfyUI prompts...")
                add_log("Creating ComfyUI prompts for character consistency...", "AI")
                character_prompts = self.generate_character_comfyui_prompts(characters)
                
                # Store character prompts in story data for later use
                story['character_prompts'] = character_prompts
                add_log(f"Generated ComfyUI prompts for {len(character_prompts)} characters", "AI")
                
                # Save characters and locations to database for persistence
                for character in characters:
                    self.db.save_story_character(story['id'], character)
                
                for location in locations:
                    self.db.save_story_location(story['id'], location)
                
                # Update style references display
                if self.progress_window and hasattr(self.progress_window, 'update_style_references'):
                    self.progress_window.update_style_references(characters, locations, visual_style)
                
            except Exception as e:
                add_log(f"Character analysis failed, continuing without character consistency: {str(e)}", "Warning")
                characters, locations, visual_style = [], [], {}
                character_prompts = []
            
            # Style Sheets placeholder (step 4)
            update_progress(45, "Processing style sheets...")
            add_log("Style sheet processing (placeholder for future implementation)", "Info")
            
            # Update progress window with placeholder info
            if self.progress_window and hasattr(self.progress_window, 'update_step_node_info'):
                self.progress_window.update_step_node_info('style', 'Future Implementation', 'placeholder', 'N/A')
            
            # Process each shot
            total_shots = len(shots)
            for idx, shot in enumerate(shots):
                progress = 50 + (idx / total_shots) * 40  # 50% to 90%
                update_progress(progress, f"Processing shot {idx + 1} of {total_shots}...")
                
                # Save shot to database
                add_log(f"Processing shot {shot.shot_number}: {shot.description[:50]}...", "AI")
                shot_id = self.db.save_shot(shot)
                shot.id = shot_id
                
                # Generate prompts
                update_progress(progress + 5, f"Generating prompts for shot {idx + 1}...")
                
                # Update progress window with render node info for prompts
                if idx == 0 and self.progress_window and hasattr(self.progress_window, 'update_step_node_info'):
                    selected_model = getattr(self.ollama, 'selected_model', {}).get('prompts', 'llama3.1')
                    node_name = getattr(self.ollama, 'selected_instance', 'localhost')
                    self.progress_window.update_step_node_info('prompts', node_name, 'ollama', selected_model)
                
                add_log(f"Generating Wan 2.2 prompt for shot {shot.shot_number}...", "AI")
                self.generate_wan_prompt(shot, story_id, optimized_config.visual_style, characters, locations)
                
                # Only generate narration if shot requires dialogue/narration
                if shot.narration and shot.narration.strip() != "":
                    # Update progress window with render node info for narration (first shot only)
                    if idx == 0 and self.progress_window and hasattr(self.progress_window, 'update_step_node_info'):
                        selected_model = getattr(self.ollama, 'selected_model', {}).get('narration', 'llama3.1')
                        node_name = getattr(self.ollama, 'selected_instance', 'localhost')
                        self.progress_window.update_step_node_info('narration', node_name, 'ollama', selected_model)
                    
                    add_log(f"Generating narration for shot {shot.shot_number}...", "AI")
                    self.generate_elevenlabs_script(shot)
                else:
                    add_log(f"Skipping narration for shot {shot.shot_number} (no dialogue required)", "Info")
                
                # Only generate music if shot requires background music
                if shot.music_cue and shot.music_cue.strip() != "":
                    # Update progress window with render node info for music (first shot only)
                    if idx == 0 and self.progress_window and hasattr(self.progress_window, 'update_step_node_info'):
                        selected_model = getattr(self.ollama, 'selected_model', {}).get('music', 'llama3.1')
                        node_name = getattr(self.ollama, 'selected_instance', 'localhost')
                        self.progress_window.update_step_node_info('music', node_name, 'ollama', selected_model)
                    
                    add_log(f"Generating music cue for shot {shot.shot_number}...", "AI")
                    self.generate_suno_prompt(shot)
                else:
                    add_log(f"Skipping music for shot {shot.shot_number} (no music required)", "Info")
                
                # Update shot in database with generated prompts
                cursor = self.db.conn.cursor()
                cursor.execute('''
                    UPDATE shots 
                    SET wan_prompt = ?, narration = ?, music_cue = ?, status = 'ready'
                    WHERE id = ?
                ''', (shot.wan_prompt, shot.narration, shot.music_cue, shot_id))
                self.db.conn.commit()
                add_log(f"Shot {shot.shot_number} saved and ready for rendering", "Database")
                
                # Update shot display with new prompts immediately
                if self.progress_window and hasattr(self.progress_window, 'update_shot_prompts'):
                    self.progress_window.update_shot_prompts(shot.shot_number, shot.wan_prompt)
                
                # Add to render queue
                priority = 10 if shot.shot_number == 1 else 5
                self.db.add_to_render_queue(shot_id, priority)
                add_log(f"Shot {shot.shot_number} added to render queue with priority {priority}", "Database")
            
            # Mark story as ready
            update_progress(95, "Finalizing story...")
            
            # Update progress window with render queue info
            if self.progress_window and hasattr(self.progress_window, 'update_step_node_info'):
                self.progress_window.update_step_node_info('queue', 'Database', 'sqlite', 'Local DB')
            
            self.db.conn.execute("UPDATE stories SET status = 'ready' WHERE id = ?", (story_id,))
            self.db.conn.commit()
            add_log(f"Story '{story['title']}' marked as ready for rendering", "Database")
            
            update_progress(100, "Story generation complete!")
            return story, shots
        else:
            add_log("Failed to generate story", "Error")
            update_progress(0, "Story generation failed")
        
        return None, []
    
    # Updates for story_generator.py - remove simulation fallbacks:

    # Updates for story_generator.py to handle <think> tags properly:

    def clean_ai_response(self, response: str) -> str:
        """Remove <think> tags from AI response and return clean content"""
        # Remove <think>...</think> blocks
        import re
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        return cleaned.strip()

    def generate_story(self, config: StoryConfig) -> Dict:
        """Generate story using Ollama - handles <think> tags"""
        if not self.ollama.available:
            raise Exception("Ollama not available - check connection and model selection")
        
        # Simple user prompt - let the robust system prompt do the heavy lifting
        prompt = f"""Genre: {config.genre}
Length: {config.length}
Concept: {config.prompt}"""
        
        # Log the AI request - show FULL prompt
        if self.progress_window:
            self.progress_window.add_ai_message('request', prompt, 'story')
        
        try:
            # Generate with Ollama using step-specific model - this will raise exception if it fails
            raw_response = self.ollama.generate(
                prompt=prompt,
                system=SYSTEM_PROMPTS['story_writer'],
                step='story'
            )
            
            # Log the FULL raw response (including <think> tags for display)
            if self.progress_window:
                self.progress_window.add_ai_message('response', raw_response, 'story')
            
            # Clean the response for actual use (remove <think> tags)
            response = self.clean_ai_response(raw_response)
            
            if not response or len(response.strip()) < 10:
                raise Exception("AI returned empty or invalid story content")
            
            # Parse response into story structure
            story_id = f"story_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Extract title from response
            lines = response.split('\n')
            title = "Untitled Story"
            for line in lines:
                if 'Title:' in line or 'title:' in line:
                    title = line.split(':', 1)[1].strip()
                    break
            
            # Update popup title
            if self.progress_window:
                self.progress_window.update_story_title(title)
            
            # Determine number of parts based on length
            length_range = GENERATION_SETTINGS['length_to_parts'].get(config.length, (3, 5))
            parts = random.randint(*length_range)
            
            story = {
                'id': story_id,
                'title': title,
                'genre': config.genre,
                'length': config.length,
                'prompt': config.prompt,
                'content': response,  # Use cleaned response without <think> tags
                'parts': parts,
                'created_at': datetime.now().isoformat()
            }
            
            # Update content display if progress window is available
            if self.progress_window:
                # Set current story ID for chat message saving
                self.progress_window.current_story_id = story['id']
                self.progress_window.update_story_content(story)
            
            return story
            
        except Exception as e:
            # Log error and re-raise instead of simulating
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Story generation failed: {str(e)}", 'story')
            raise Exception(f"Failed to generate story: {str(e)}")

    def create_shot_list(self, story: Dict, config: StoryConfig = None) -> List[Shot]:
        """Create shot list from story - handles <think> tags"""
        if not self.ollama.available:
            raise Exception("Ollama not available for shot list generation")
        
        # Simple user prompt with story data - system prompt handles the formatting
        prompt = f"""Story: {story['title']}
Genre: {story['genre']}
Length: {story['length']}

{story['content']}"""

        # Log FULL request
        if self.progress_window:
            self.progress_window.add_ai_message('request', prompt, 'shots')

        try:
            # Generate with Ollama using step-specific model
            raw_response = self.ollama.generate(
                prompt=prompt,
                system=SYSTEM_PROMPTS['shot_list_creator'],
                temperature=0.5,
                step='shots'
            )
            
            # Log FULL raw response (including <think> for display)
            if self.progress_window:
                self.progress_window.add_ai_message('response', raw_response, 'shots')
            
            # Clean response for JSON parsing
            response = self.clean_ai_response(raw_response)
            
            # Parse JSON response
            shots = []
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                try:
                    shot_data = json.loads(json_str)
                    
                    # Get FPS setting for frame calculation
                    fps_key = config.fps if config else RENDER_SETTINGS['defaults']['fps']
                    fps_value = RENDER_SETTINGS['fps_options'][fps_key]['value']
                    
                    for shot_info in shot_data.get('shots', []):
                        duration = shot_info.get('duration', 5.0)
                        frames = shot_info.get('frames', int(duration * fps_value))
                        
                        shot = Shot(
                            shot_number=shot_info.get('shot_number', len(shots) + 1),
                            story_id=story['id'],
                            description=shot_info.get('description', ''),
                            duration=duration,
                            frames=frames,
                            wan_prompt="",
                            narration=shot_info.get('narration', ''),
                            music_cue=shot_info.get('music_cue', None)
                        )
                        shots.append(shot)
                        
                    if shots:
                        # Save shots to database immediately for persistence
                        for shot in shots:
                            shot_id = self.db.save_shot(shot)
                            shot.id = shot_id
                        
                        # Update storyboard display if progress window is available
                        if self.progress_window:
                            self.progress_window.update_shot_list(shots)
                        
                        return shots
                    else:
                        raise Exception("No shots found in AI response")
                        
                except json.JSONDecodeError as e:
                    if self.progress_window:
                        self.progress_window.add_ai_message('error', f"JSON parsing failed: {str(e)}\nCleaned response: {response}", 'shots')
                    raise Exception(f"Invalid JSON from AI: {str(e)}")
            else:
                if self.progress_window:
                    self.progress_window.add_ai_message('error', f"No JSON found in cleaned AI response: {response[:200]}...", 'shots')
                raise Exception("AI did not return valid JSON format")
                
        except Exception as e:
            # Re-raise instead of falling back to simulation
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Shot list creation failed: {str(e)}", 'shots')
            raise Exception(f"Failed to create shot list: {str(e)}")

    def generate_wan_prompt(self, shot: Shot, story_id: str = None, visual_style: str = None, characters: List[Dict] = None, locations: List[Dict] = None):
        """Generate Wan 2.2 prompt with character consistency and visual style - handles <think> tags"""
        if not self.ollama.available:
            raise Exception("Ollama not available for prompt generation")
        
        # Build enhanced user prompt with character and location data
        prompt = f"""Shot: {shot.description}
Duration: {shot.duration}s
Shot #{shot.shot_number}"""

        # Add character descriptions if available
        if characters:
            relevant_characters = []
            for char in characters:
                # Check if this character might appear in this shot (simple text matching)
                char_name_lower = char['name'].lower()
                shot_desc_lower = shot.description.lower()
                
                # Look for character name or role references in shot description
                if (char_name_lower in shot_desc_lower or 
                    any(word in shot_desc_lower for word in char_name_lower.split()) or
                    char['role'].lower() in shot_desc_lower):
                    relevant_characters.append(char)
            
            if relevant_characters:
                prompt += "\n\nCharacter Descriptions:"
                for char in relevant_characters:
                    prompt += f"\n- {char['name']} ({char['role']}): {char['physical_description']}, {char['age_range']}, {char['clothing_style']}"

        # Add location descriptions if available  
        if locations:
            relevant_locations = []
            for loc in locations:
                loc_name_lower = loc['name'].lower()
                shot_desc_lower = shot.description.lower()
                
                # Look for location references in shot description
                if (loc_name_lower in shot_desc_lower or
                    any(word in shot_desc_lower for word in loc_name_lower.split()) or
                    loc['environment_type'].lower() in shot_desc_lower):
                    relevant_locations.append(loc)
            
            if relevant_locations:
                prompt += "\n\nLocation Descriptions:"
                for loc in relevant_locations:
                    prompt += f"\n- {loc['name']}: {loc['description']}, {loc['lighting_style']} lighting, {loc['time_of_day']}"

        # Log FULL request
        if self.progress_window:
            self.progress_window.add_ai_message('request', prompt, 'prompts')

        try:
            raw_response = self.ollama.generate(
                prompt=prompt,
                system=SYSTEM_PROMPTS['prompt_engineer'],
                temperature=0.3,
                step='prompts'
            )
            
            # Log FULL raw response (including <think> for display)
            if self.progress_window:
                self.progress_window.add_ai_message('response', raw_response, 'prompts')
            
            # Clean response for actual use
            response = self.clean_ai_response(raw_response)
            
            # Extract positive prompt
            if "Positive prompt:" in response:
                base_prompt = response.split("Positive prompt:")[1].split("Negative prompt:")[0].strip()
            else:
                base_prompt = response.split('\n')[0].strip()
            
            if not base_prompt:
                raise Exception("No prompt generated from AI response")
            
            # Enhance with visual style
            enhanced_prompt = base_prompt
            if visual_style:
                style_enhanced_prompt, style_negative = self.enhance_prompt_with_style(base_prompt, visual_style)
                enhanced_prompt = style_enhanced_prompt
                
                if self.progress_window:
                    self.progress_window.add_ai_message('success', 
                        f"Enhanced shot {shot.shot_number} with {visual_style} style", 'prompts')
            
            # Enhance with character consistency if available
            if story_id and self.comfyui:
                try:
                    consistency_prompts = self.comfyui.get_shot_consistency_prompts(story_id, shot.description)
                    final_prompt = self.comfyui.enhance_shot_prompt_with_consistency(enhanced_prompt, consistency_prompts)
                    shot.wan_prompt = final_prompt
                    
                    # Update progress window with new prompt
                    if self.progress_window and hasattr(self.progress_window, 'update_shot_prompts'):
                        self.progress_window.update_shot_prompts(shot.shot_number, shot.wan_prompt)
                    
                    if consistency_prompts.get('combined_consistency'):
                        if self.progress_window:
                            self.progress_window.add_ai_message('success', 
                                f"Enhanced shot {shot.shot_number} with character consistency", 'prompts')
                except Exception as consistency_error:
                    # If consistency enhancement fails, use style-enhanced prompt
                    shot.wan_prompt = enhanced_prompt
                    
                    # Update progress window with new prompt
                    if self.progress_window and hasattr(self.progress_window, 'update_shot_prompts'):
                        self.progress_window.update_shot_prompts(shot.shot_number, shot.wan_prompt)
                    
                    if self.progress_window:
                        self.progress_window.add_ai_message('error', 
                            f"Consistency enhancement failed for shot {shot.shot_number}: {str(consistency_error)}", 'prompts')
            else:
                shot.wan_prompt = enhanced_prompt
                
                # Update progress window with new prompt
                if self.progress_window and hasattr(self.progress_window, 'update_shot_prompts'):
                    self.progress_window.update_shot_prompts(shot.shot_number, shot.wan_prompt)
                
        except Exception as e:
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Prompt generation failed: {str(e)}", 'prompts')
            raise Exception(f"Failed to generate visual prompt: {str(e)}")

    def generate_elevenlabs_script(self, shot: Shot):
        """Generate ElevenLabs narration - handles <think> tags"""
        if not self.ollama.available:
            raise Exception("Ollama not available for narration generation")
        
        # Only enhance narration if shot already has dialogue/narration content
        if shot.narration and shot.narration.strip():
            # Simple user prompt with shot and existing narration data
            prompt = f"""Shot: {shot.description}
Duration: {shot.duration}s
Existing narration: {shot.narration}
Shot #{shot.shot_number}"""

            # Log FULL request
            if self.progress_window:
                self.progress_window.add_ai_message('request', prompt, 'narration')

            try:
                raw_response = self.ollama.generate(
                    prompt=prompt,
                    system=SYSTEM_PROMPTS['narration_writer'],
                    temperature=0.7,
                    step='narration'
                )
                
                # Log FULL raw response
                if self.progress_window:
                    self.progress_window.add_ai_message('response', raw_response, 'narration')
                
                # Clean response for actual use
                response = self.clean_ai_response(raw_response)
                shot.narration = response.strip()
                
                if not shot.narration:
                    raise Exception("No narration generated from AI response")
                    
            except Exception as e:
                if self.progress_window:
                    self.progress_window.add_ai_message('error', f"Narration generation failed: {str(e)}", 'narration')
                raise Exception(f"Failed to generate narration: {str(e)}")
        else:
            # Shot doesn't require narration
            if self.progress_window:
                self.progress_window.add_ai_message('info', f"Shot {shot.shot_number} has no dialogue/narration content to process", 'narration')

    def generate_suno_prompt(self, shot: Shot):
        """Generate Suno music prompt - handles <think> tags"""
        if not self.ollama.available:
            raise Exception("Ollama not available for music generation")
        
        if shot.music_cue:
            # Simple user prompt with shot and music data - system prompt handles specifications
            prompt = f"""Shot: {shot.description}
Music: {shot.music_cue}
Duration: {shot.duration}s
Shot #{shot.shot_number}"""

            # Log FULL request
            if self.progress_window:
                self.progress_window.add_ai_message('request', prompt, 'music')

            try:
                raw_response = self.ollama.generate(
                    prompt=prompt,
                    system=SYSTEM_PROMPTS['music_director'],
                    temperature=0.6,
                    step='music'
                )
                
                # Log FULL raw response
                if self.progress_window:
                    self.progress_window.add_ai_message('response', raw_response, 'music')
                
                # Clean response for actual use
                response = self.clean_ai_response(raw_response)
                shot.music_cue = response.strip()
                
            except Exception as e:
                if self.progress_window:
                    self.progress_window.add_ai_message('error', f"Music generation failed: {str(e)}", 'music')
                raise Exception(f"Failed to generate music cue: {str(e)}")
    
    def generate_optimal_prompt(self) -> str:
        """Generate optimal prompt based on metrics"""
        best_prompts = self.db.get_best_performing_prompts()
        
        if best_prompts:
            # Use variation of best prompt
            base_prompt = random.choice(best_prompts[:3]) if len(best_prompts) >= 3 else best_prompts[0]
            return base_prompt
        
        # Fallback prompts
        prompts = [
            "A mysterious stranger arrives in a small town...",
            "Two unlikely friends embark on an adventure...",
            "A secret from the past threatens everything...",
            "In a world where technology has gone too far...",
            "The last day before everything changes...",
            "A message from the future changes everything...",
            "Two rivals must work together to survive...",
            "An ordinary person discovers extraordinary powers..."
        ]
        return random.choice(prompts)
    
    def select_optimal_genre(self) -> str:
        """Select optimal genre based on metrics"""
        genre_performance = self.db.get_genre_performance()
        
        if genre_performance:
            # Weight selection by performance
            genres = list(genre_performance.keys())
            weights = [genre_performance[g]['avg_engagement'] for g in genres]
            
            # Normalize weights
            total = sum(weights)
            if total > 0:
                weights = [w/total for w in weights]
                selected = random.choices(genres, weights=weights)[0]
                return selected
        
        # Fallback
        return random.choice(GENERATION_SETTINGS['genres'])
    
    def select_optimal_length(self) -> str:
        """Select optimal length based on metrics"""
        length_performance = self.db.get_length_performance()
        
        if length_performance:
            # Select based on completion rate
            best_length = max(length_performance.items(), 
                            key=lambda x: x[1]['avg_completion'])[0]
            return best_length
        
        # Fallback
        lengths = GENERATION_SETTINGS['lengths']
        weights = [0.1, 0.4, 0.35, 0.15]
        return random.choices(lengths, weights=weights)[0]
