"""
ComfyUI Manager for Style Card Generation and Character Consistency
Handles style reference creation and ComfyUI workflow integration
"""

import json
import time
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config import SYSTEM_PROMPTS
from database import DatabaseManager


class ComfyUIManager:
    """Manages ComfyUI style card generation and character consistency"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.progress_window = None
        
        # Style card templates for different reference types
        self.style_templates = {
            'character': {
                'base_prompt': "{character_description}, {clothing_style}, {age_range}, professional character reference sheet, multiple angles, clean background, high detail, photorealistic style",
                'negative_prompt': "text, watermark, blurry, distorted, extra limbs, low quality, bad anatomy, multiple people, crowd",
                'settings': {
                    'width': 1024,
                    'height': 1024,
                    'steps': 30,
                    'cfg_scale': 7.0,
                    'seed': -1
                }
            },
            'location': {
                'base_prompt': "{location_description}, {lighting_style}, {time_of_day}, {weather_mood}, establishing shot, cinematic composition, high detail, photorealistic style",
                'negative_prompt': "text, watermark, blurry, distorted, low quality, people, characters, faces",
                'settings': {
                    'width': 1920,
                    'height': 1080,
                    'steps': 25,
                    'cfg_scale': 6.5,
                    'seed': -1
                }
            },
            'style_reference': {
                'base_prompt': "{visual_style_description}, {color_palette}, {cinematography}, reference sheet, style guide, mood board, high detail",
                'negative_prompt': "text, watermark, blurry, distorted, low quality, random objects",
                'settings': {
                    'width': 1024,
                    'height': 768,
                    'steps': 20,
                    'cfg_scale': 6.0,
                    'seed': -1
                }
            }
        }
    
    def set_progress_window(self, progress_window):
        """Set reference to progress popup window"""
        self.progress_window = progress_window
    
    def generate_style_cards(self, story_id: str, characters: List[Dict], locations: List[Dict], visual_style: Dict) -> Dict:
        """Generate style reference cards for all story elements"""
        
        if self.progress_window:
            self.progress_window.add_ai_message('info', f"Generating style cards for story {story_id}", 'style')
        
        results = {
            'character_cards': [],
            'location_cards': [],
            'style_cards': [],
            'total_generated': 0,
            'errors': []
        }
        
        try:
            # Generate character style cards
            for character in characters:
                if self.progress_window:
                    self.progress_window.add_ai_message('info', f"Creating style card for character: {character['name']}", 'style')
                
                character_card = self._generate_character_style_card(story_id, character, visual_style)
                if character_card:
                    results['character_cards'].append(character_card)
                    results['total_generated'] += 1
            
            # Generate location style cards
            for location in locations:
                if self.progress_window:
                    self.progress_window.add_ai_message('info', f"Creating style card for location: {location['name']}", 'style')
                
                location_card = self._generate_location_style_card(story_id, location, visual_style)
                if location_card:
                    results['location_cards'].append(location_card)
                    results['total_generated'] += 1
            
            # Generate overall style reference card
            if self.progress_window:
                self.progress_window.add_ai_message('info', "Creating overall style reference card", 'style')
            
            style_card = self._generate_overall_style_card(story_id, visual_style)
            if style_card:
                results['style_cards'].append(style_card)
                results['total_generated'] += 1
            
            if self.progress_window:
                self.progress_window.add_ai_message('success', f"Generated {results['total_generated']} style cards successfully", 'style')
            
        except Exception as e:
            error_msg = f"Error generating style cards: {str(e)}"
            results['errors'].append(error_msg)
            if self.progress_window:
                self.progress_window.add_ai_message('error', error_msg, 'style')
        
        return results
    
    def _generate_character_style_card(self, story_id: str, character: Dict, visual_style: Dict) -> Optional[Dict]:
        """Generate style card for a specific character"""
        try:
            # Build character prompt from template
            template = self.style_templates['character']
            
            prompt = template['base_prompt'].format(
                character_description=character['physical_description'],
                clothing_style=character.get('clothing_style', 'casual modern'),
                age_range=character.get('age_range', 'adult')
            )
            
            # Add visual style elements
            if visual_style.get('overall_mood'):
                prompt += f", {visual_style['overall_mood']} mood"
            if visual_style.get('era_setting'):
                prompt += f", {visual_style['era_setting']} era"
            
            # Create style reference data
            reference_data = {
                'reference_type': 'character',
                'reference_name': character['name'],
                'comfyui_prompt': prompt,
                'negative_prompt': template['negative_prompt'],
                'style_settings': {
                    **template['settings'],
                    'character_name': character['name'],
                    'importance_level': character.get('importance_level', 1),
                    'visual_style': visual_style
                }
            }
            
            # Save to database
            reference_id = self.db.save_style_reference(story_id, reference_data)
            
            # Create character reference prompt for shot consistency
            character_reference_prompt = self._create_character_reference_prompt(character, visual_style)
            
            # Update character with reference prompt
            character_data = {
                **character,
                'reference_prompt': character_reference_prompt
            }
            self.db.save_story_character(story_id, character_data)
            
            return {
                'id': reference_id,
                'type': 'character',
                'name': character['name'],
                'prompt': prompt,
                'reference_prompt': character_reference_prompt
            }
            
        except Exception as e:
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Failed to generate character style card for {character.get('name', 'Unknown')}: {str(e)}", 'style')
            return None
    
    def _generate_location_style_card(self, story_id: str, location: Dict, visual_style: Dict) -> Optional[Dict]:
        """Generate style card for a specific location"""
        try:
            # Build location prompt from template
            template = self.style_templates['location']
            
            prompt = template['base_prompt'].format(
                location_description=location['description'],
                lighting_style=location.get('lighting_style', 'natural lighting'),
                time_of_day=location.get('time_of_day', 'day'),
                weather_mood=location.get('weather_mood', 'clear')
            )
            
            # Add visual style elements
            if visual_style.get('color_palette'):
                prompt += f", {visual_style['color_palette']} color palette"
            if visual_style.get('cinematography'):
                prompt += f", {visual_style['cinematography']} style"
            
            # Create style reference data
            reference_data = {
                'reference_type': 'location',
                'reference_name': location['name'],
                'comfyui_prompt': prompt,
                'negative_prompt': template['negative_prompt'],
                'style_settings': {
                    **template['settings'],
                    'location_name': location['name'],
                    'importance_level': location.get('importance_level', 1),
                    'visual_style': visual_style
                }
            }
            
            # Save to database
            reference_id = self.db.save_style_reference(story_id, reference_data)
            
            # Create location reference prompt for shot consistency
            location_reference_prompt = self._create_location_reference_prompt(location, visual_style)
            
            # Update location with reference prompt
            location_data = {
                **location,
                'reference_prompt': location_reference_prompt
            }
            self.db.save_story_location(story_id, location_data)
            
            return {
                'id': reference_id,
                'type': 'location',
                'name': location['name'],
                'prompt': prompt,
                'reference_prompt': location_reference_prompt
            }
            
        except Exception as e:
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Failed to generate location style card for {location.get('name', 'Unknown')}: {str(e)}", 'style')
            return None
    
    def _generate_overall_style_card(self, story_id: str, visual_style: Dict) -> Optional[Dict]:
        """Generate overall style reference card for the story"""
        try:
            template = self.style_templates['style_reference']
            
            # Build style description
            style_description = f"{visual_style.get('overall_mood', 'cinematic')} {visual_style.get('cinematography', 'realistic')} style"
            
            prompt = template['base_prompt'].format(
                visual_style_description=style_description,
                color_palette=visual_style.get('color_palette', 'balanced'),
                cinematography=visual_style.get('cinematography', 'cinematic')
            )
            
            if visual_style.get('era_setting'):
                prompt += f", {visual_style['era_setting']} era aesthetic"
            
            # Create style reference data
            reference_data = {
                'reference_type': 'style_reference',
                'reference_name': f"Overall Style - {visual_style.get('overall_mood', 'Main')}",
                'comfyui_prompt': prompt,
                'negative_prompt': template['negative_prompt'],
                'style_settings': {
                    **template['settings'],
                    'visual_style': visual_style
                }
            }
            
            # Save to database
            reference_id = self.db.save_style_reference(story_id, reference_data)
            
            return {
                'id': reference_id,
                'type': 'style_reference',
                'name': 'Overall Style',
                'prompt': prompt
            }
            
        except Exception as e:
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Failed to generate overall style card: {str(e)}", 'style')
            return None
    
    def _create_character_reference_prompt(self, character: Dict, visual_style: Dict) -> str:
        """Create a concise character reference prompt for shot consistency"""
        reference_parts = []
        
        # Core character description
        if character.get('physical_description'):
            reference_parts.append(character['physical_description'])
        
        # Age and clothing
        if character.get('age_range'):
            reference_parts.append(f"{character['age_range']} person")
        if character.get('clothing_style'):
            reference_parts.append(f"wearing {character['clothing_style']}")
        
        # Visual style consistency
        if visual_style.get('overall_mood'):
            reference_parts.append(f"{visual_style['overall_mood']} mood")
        
        return ", ".join(reference_parts)
    
    def _create_location_reference_prompt(self, location: Dict, visual_style: Dict) -> str:
        """Create a concise location reference prompt for shot consistency"""
        reference_parts = []
        
        # Core location description
        if location.get('description'):
            reference_parts.append(location['description'])
        
        # Environmental details
        if location.get('time_of_day'):
            reference_parts.append(f"{location['time_of_day']} time")
        if location.get('lighting_style'):
            reference_parts.append(f"{location['lighting_style']}")
        if location.get('weather_mood'):
            reference_parts.append(f"{location['weather_mood']} atmosphere")
        
        # Visual style consistency
        if visual_style.get('color_palette'):
            reference_parts.append(f"{visual_style['color_palette']} colors")
        
        return ", ".join(reference_parts)
    
    def get_shot_consistency_prompts(self, story_id: str, shot_description: str) -> Dict[str, str]:
        """Get character and location consistency prompts for a specific shot"""
        try:
            # Analyze shot description to find relevant characters and locations
            character_prompts = []
            location_prompts = []
            
            # Get all characters and locations for this story
            characters = self.db.get_story_characters(story_id)
            locations = self.db.get_story_locations(story_id)
            
            # Find matching characters in shot description
            for character in characters:
                if any(name_part.lower() in shot_description.lower() 
                      for name_part in character['name'].split()):
                    if character.get('reference_prompt'):
                        character_prompts.append(character['reference_prompt'])
            
            # Find matching locations in shot description
            for location in locations:
                if any(location_part.lower() in shot_description.lower() 
                      for location_part in location['name'].split()) or \
                   any(desc_part.lower() in shot_description.lower() 
                      for desc_part in location['description'].split()[:5]):
                    if location.get('reference_prompt'):
                        location_prompts.append(location['reference_prompt'])
            
            # If no specific matches, use most important character/location
            if not character_prompts:
                main_character = self.db.get_character_for_shot_consistency(story_id)
                if main_character and main_character.get('reference_prompt'):
                    character_prompts.append(main_character['reference_prompt'])
            
            if not location_prompts:
                main_location = self.db.get_location_for_shot_consistency(story_id)
                if main_location and main_location.get('reference_prompt'):
                    location_prompts.append(main_location['reference_prompt'])
            
            return {
                'character_consistency': ", ".join(character_prompts) if character_prompts else "",
                'location_consistency': ", ".join(location_prompts) if location_prompts else "",
                'combined_consistency': ", ".join(character_prompts + location_prompts) if character_prompts or location_prompts else ""
            }
            
        except Exception as e:
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Failed to get shot consistency prompts: {str(e)}", 'style')
            return {'character_consistency': '', 'location_consistency': '', 'combined_consistency': ''}
    
    def enhance_shot_prompt_with_consistency(self, original_prompt: str, consistency_prompts: Dict[str, str]) -> str:
        """Enhance a shot prompt with character and location consistency"""
        if not consistency_prompts.get('combined_consistency'):
            return original_prompt
        
        # Add consistency elements at the beginning for higher priority
        enhanced_prompt = f"{consistency_prompts['combined_consistency']}, {original_prompt}"
        
        # Ensure we don't exceed typical prompt limits
        if len(enhanced_prompt) > 500:
            # Prioritize character consistency over location if we need to truncate
            character_part = consistency_prompts.get('character_consistency', '')
            if character_part:
                enhanced_prompt = f"{character_part}, {original_prompt}"
        
        return enhanced_prompt
    
    def get_comfyui_workflow_data(self, story_id: str) -> Dict:
        """Get all ComfyUI workflow data for a story"""
        try:
            characters = self.db.get_story_characters(story_id)
            locations = self.db.get_story_locations(story_id)
            style_references = self.db.get_style_references(story_id)
            
            return {
                'story_id': story_id,
                'characters': characters,
                'locations': locations,
                'style_references': style_references,
                'workflow_ready': len(style_references) > 0,
                'total_references': len(style_references),
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            if self.progress_window:
                self.progress_window.add_ai_message('error', f"Failed to get ComfyUI workflow data: {str(e)}", 'style')
            return {'story_id': story_id, 'workflow_ready': False, 'error': str(e)}