"""
Data models and structures for Film Generator App
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class StoryConfig:
    """Configuration for story generation"""
    prompt: str
    genre: str
    length: str
    visual_style: str = "Cinematic"  # Default visual style
    aspect_ratio: str = "Vertical"  # Aspect ratio setting
    fps: str = "24fps"  # Frame rate setting
    auto_prompt: bool = False
    auto_genre: bool = False
    auto_length: bool = False
    auto_style: bool = False
    parts: int = 0  # Number of story parts - calculated from length

@dataclass
class Shot:
    """Represents a single shot in a story"""
    shot_number: int
    story_id: str
    description: str
    duration: float
    frames: int
    wan_prompt: str
    narration: str
    music_cue: Optional[str] = None
    status: str = 'pending'
    id: Optional[int] = None

@dataclass
class VideoMetrics:
    """Metrics for uploaded videos"""
    video_id: str
    story_id: str
    title: str
    part_number: int
    views: int = 0
    likes: int = 0
    completion_rate: float = 0.0
    engagement_rate: float = 0.0
    upload_time: str = ""

@dataclass
class StoryCharacter:
    """Character information for visual consistency"""
    name: str
    role: str
    physical_description: str
    age_range: Optional[str] = None
    clothing_style: Optional[str] = None
    personality_traits: Optional[str] = None
    importance_level: int = 1
    reference_prompt: Optional[str] = None
    style_notes: Optional[str] = None
    id: Optional[int] = None

@dataclass
class StoryLocation:
    """Location information for visual consistency"""
    name: str
    description: str
    environment_type: Optional[str] = None
    time_of_day: Optional[str] = None
    weather_mood: Optional[str] = None
    lighting_style: Optional[str] = None
    importance_level: int = 1
    reference_prompt: Optional[str] = None
    style_notes: Optional[str] = None
    id: Optional[int] = None

@dataclass
class StyleReference:
    """Style reference card for ComfyUI workflows"""
    reference_type: str
    reference_name: str
    comfyui_prompt: str
    negative_prompt: Optional[str] = None
    style_settings: Optional[dict] = None
    reference_image_path: Optional[str] = None
    usage_count: int = 0
    quality_score: float = 0.0
    id: Optional[int] = None

@dataclass
class VisualStyle:
    """Overall visual style for the story"""
    overall_mood: str
    color_palette: str
    cinematography: str
    era_setting: str

@dataclass
class QueueItem:
    """Story queue item"""
    id: Optional[int]
    queue_position: int
    story_config: StoryConfig
    priority: int = 5
    status: str = 'queued'
    current_step: str = 'pending'
    progress_data: Optional[dict] = None
    story_id: Optional[str] = None
    continuous_generation: bool = False
    error_message: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_completion: Optional[str] = None

@dataclass
class QueueConfig:
    """Queue configuration settings"""
    continuous_enabled: bool = False
    render_queue_high_threshold: int = 50
    render_queue_low_threshold: int = 10
    max_concurrent_generations: int = 1
    auto_priority_boost: bool = True
    retry_failed_items: bool = True
