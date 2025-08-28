"""
Footage Assembly Manager
Handles the reassembly of rendered shots into final video sequence
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class SequenceSettings:
    """Settings for video sequence assembly"""
    resolution: str = "1920x1080"
    framerate: int = 30
    audio_sample_rate: int = 44100
    video_codec: str = "h264"
    audio_codec: str = "aac"
    quality: str = "high"  # low, medium, high, ultra

@dataclass
class RenderedShot:
    """Information about a rendered shot file"""
    shot_id: int
    shot_number: int
    duration: float
    video_path: str
    audio_path: Optional[str] = None
    narration_path: Optional[str] = None
    music_path: Optional[str] = None
    status: str = "rendered"
    render_timestamp: Optional[str] = None

class FootageAssembler:
    """Manages the assembly of rendered shots into final video sequences"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.output_dir = "rendered_videos"
        self.shots_dir = "rendered_shots"
        self.temp_dir = "temp_assembly"
        
        # Create directories if they don't exist
        for directory in [self.output_dir, self.shots_dir, self.temp_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def get_story_sequence_plan(self, story_id: str) -> Dict:
        """Generate a complete sequence plan for a story"""
        # Get story information
        story = self.db.get_story(story_id)
        if not story:
            raise Exception(f"Story {story_id} not found")
        
        # Get all shots for the story, ordered by shot number
        shots = self.db.get_shots_by_story(story_id)
        if not shots:
            raise Exception(f"No shots found for story {story_id}")
        
        # Sort shots by shot number to ensure correct sequence
        shots.sort(key=lambda x: x.shot_number)
        
        # Create sequence plan
        sequence_plan = {
            'story_id': story_id,
            'story_title': story.get('title', 'Untitled'),
            'total_shots': len(shots),
            'total_estimated_duration': sum(shot.duration for shot in shots),
            'created_at': datetime.now().isoformat(),
            'sequence_settings': SequenceSettings().__dict__,
            'shots': [],
            'audio_layers': {
                'narration': [],  # Voice-over tracks
                'music': [],      # Background music tracks
                'sfx': []         # Sound effects tracks
            },
            'transitions': [],    # Transition effects between shots
            'assembly_status': 'planned'
        }
        
        # Process each shot
        for shot in shots:
            shot_info = {
                'shot_id': shot.id,
                'shot_number': shot.shot_number,
                'description': shot.description,
                'duration': shot.duration,
                'start_time': sum(s.duration for s in shots[:shots.index(shot)]),  # Cumulative start time
                'end_time': sum(s.duration for s in shots[:shots.index(shot) + 1]),
                'video_file': f"{self.shots_dir}/shot_{shot.shot_number:03d}_{story_id}.mp4",
                'render_status': 'pending',
                'has_narration': bool(shot.narration and shot.narration.strip()),
                'has_music': bool(shot.music_cue and shot.music_cue.strip()),
                'audio_files': {}
            }
            
            # Add audio file paths if they exist
            if shot_info['has_narration']:
                shot_info['audio_files']['narration'] = f"{self.shots_dir}/shot_{shot.shot_number:03d}_{story_id}_narration.wav"
                sequence_plan['audio_layers']['narration'].append({
                    'shot_number': shot.shot_number,
                    'start_time': shot_info['start_time'],
                    'duration': shot.duration,
                    'file_path': shot_info['audio_files']['narration'],
                    'text': shot.narration
                })
            
            if shot_info['has_music']:
                shot_info['audio_files']['music'] = f"{self.shots_dir}/shot_{shot.shot_number:03d}_{story_id}_music.wav"
                sequence_plan['audio_layers']['music'].append({
                    'shot_number': shot.shot_number,
                    'start_time': shot_info['start_time'],
                    'duration': shot.duration,
                    'file_path': shot_info['audio_files']['music'],
                    'music_description': shot.music_cue
                })
            
            sequence_plan['shots'].append(shot_info)
        
        # Add transition information (simple cuts by default)
        for i in range(len(shots) - 1):
            sequence_plan['transitions'].append({
                'between_shots': [shots[i].shot_number, shots[i + 1].shot_number],
                'type': 'cut',  # cut, fade, dissolve, wipe, etc.
                'duration': 0.0,
                'at_time': sum(s.duration for s in shots[:i + 1])
            })
        
        return sequence_plan
    
    def save_sequence_plan(self, sequence_plan: Dict) -> str:
        """Save sequence plan to file for reference"""
        story_id = sequence_plan['story_id']
        plan_file = f"{self.temp_dir}/sequence_plan_{story_id}.json"
        
        with open(plan_file, 'w') as f:
            json.dump(sequence_plan, f, indent=2)
        
        return plan_file
    
    def check_render_readiness(self, story_id: str) -> Dict:
        """Check if all shots are rendered and ready for assembly"""
        sequence_plan = self.get_story_sequence_plan(story_id)
        readiness_report = {
            'story_id': story_id,
            'story_title': sequence_plan['story_title'],
            'total_shots': sequence_plan['total_shots'],
            'shots_ready': 0,
            'shots_missing': 0,
            'audio_tracks_ready': 0,
            'audio_tracks_missing': 0,
            'ready_for_assembly': False,
            'missing_files': [],
            'ready_files': [],
            'estimated_final_duration': sequence_plan['total_estimated_duration']
        }
        
        # Check each shot's render status
        for shot_info in sequence_plan['shots']:
            video_file = shot_info['video_file']
            
            if os.path.exists(video_file):
                readiness_report['shots_ready'] += 1
                readiness_report['ready_files'].append(video_file)
            else:
                readiness_report['shots_missing'] += 1
                readiness_report['missing_files'].append(video_file)
            
            # Check audio files
            for audio_type, audio_file in shot_info.get('audio_files', {}).items():
                if os.path.exists(audio_file):
                    readiness_report['audio_tracks_ready'] += 1
                    readiness_report['ready_files'].append(audio_file)
                else:
                    readiness_report['audio_tracks_missing'] += 1
                    readiness_report['missing_files'].append(audio_file)
        
        # Determine if ready for assembly (all video files must exist, audio is optional)
        readiness_report['ready_for_assembly'] = readiness_report['shots_missing'] == 0
        
        return readiness_report
    
    def generate_ffmpeg_command(self, sequence_plan: Dict, output_path: str) -> str:
        """Generate FFmpeg command for video assembly"""
        shots = sequence_plan['shots']
        audio_layers = sequence_plan['audio_layers']
        settings = sequence_plan['sequence_settings']
        
        # Start building FFmpeg command
        cmd_parts = ['ffmpeg']
        
        # Input video files
        for shot in shots:
            if os.path.exists(shot['video_file']):
                cmd_parts.extend(['-i', f'"{shot["video_file"]}"'])
        
        # Input audio files (narration)
        narration_inputs = []
        for audio_track in audio_layers['narration']:
            if os.path.exists(audio_track['file_path']):
                cmd_parts.extend(['-i', f'"{audio_track["file_path"]}"'])
                narration_inputs.append(len(cmd_parts) // 2 - 1)  # Track input index
        
        # Input audio files (music)
        music_inputs = []
        for audio_track in audio_layers['music']:
            if os.path.exists(audio_track['file_path']):
                cmd_parts.extend(['-i', f'"{audio_track["file_path"]}"'])
                music_inputs.append(len(cmd_parts) // 2 - 1)  # Track input index
        
        # Filter complex for concatenating videos
        video_inputs = len([s for s in shots if os.path.exists(s['video_file'])])
        if video_inputs > 1:
            concat_filter = f"concat=n={video_inputs}:v=1:a=0[outv]"
            
            # Add audio mixing if needed
            if narration_inputs or music_inputs:
                audio_filters = []
                
                # Mix narration tracks
                if narration_inputs:
                    narration_mix = '+'.join([f'[{i}:a]' for i in narration_inputs])
                    audio_filters.append(f"{narration_mix}amix=inputs={len(narration_inputs)}[narration]")
                
                # Mix music tracks
                if music_inputs:
                    music_mix = '+'.join([f'[{i}:a]' for i in music_inputs])
                    audio_filters.append(f"{music_mix}amix=inputs={len(music_inputs)}[music]")
                
                # Final audio mix
                if len(audio_filters) == 2:  # Both narration and music
                    audio_filters.append("[narration][music]amix=inputs=2[outa]")
                    filter_complex = f"{concat_filter};{';'.join(audio_filters)}"
                elif narration_inputs:
                    filter_complex = f"{concat_filter};{audio_filters[0].replace('[narration]', '[outa]')}"
                elif music_inputs:
                    filter_complex = f"{concat_filter};{audio_filters[0].replace('[music]', '[outa]')}"
                else:
                    filter_complex = concat_filter
                
                cmd_parts.extend(['-filter_complex', f'"{filter_complex}"'])
                cmd_parts.extend(['-map', '[outv]', '-map', '[outa]'])
            else:
                cmd_parts.extend(['-filter_complex', f'"{concat_filter}"'])
                cmd_parts.extend(['-map', '[outv]'])
        
        # Output settings
        cmd_parts.extend([
            '-c:v', settings['video_codec'],
            '-c:a', settings['audio_codec'],
            '-r', str(settings['framerate']),
            '-ar', str(settings['audio_sample_rate'])
        ])
        
        # Quality settings
        if settings['quality'] == 'ultra':
            cmd_parts.extend(['-crf', '18', '-preset', 'slow'])
        elif settings['quality'] == 'high':
            cmd_parts.extend(['-crf', '20', '-preset', 'medium'])
        elif settings['quality'] == 'medium':
            cmd_parts.extend(['-crf', '23', '-preset', 'fast'])
        else:  # low
            cmd_parts.extend(['-crf', '28', '-preset', 'veryfast'])
        
        # Output file
        cmd_parts.extend(['-y', f'"{output_path}"'])
        
        return ' '.join(cmd_parts)
    
    def create_assembly_script(self, story_id: str) -> str:
        """Create a batch/shell script for video assembly"""
        sequence_plan = self.get_story_sequence_plan(story_id)
        readiness = self.check_render_readiness(story_id)
        
        story_title = sequence_plan['story_title'].replace(' ', '_').replace('"', '')
        output_filename = f"{story_title}_{story_id}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create script content
        script_lines = [
            "# Video Assembly Script",
            f"# Story: {sequence_plan['story_title']}",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Total Duration: {sequence_plan['total_estimated_duration']:.1f} seconds",
            "",
            "# Readiness Check:",
            f"# Shots Ready: {readiness['shots_ready']}/{readiness['total_shots']}",
            f"# Audio Tracks Ready: {readiness['audio_tracks_ready']}",
            f"# Ready for Assembly: {'YES' if readiness['ready_for_assembly'] else 'NO'}",
            ""
        ]
        
        if not readiness['ready_for_assembly']:
            script_lines.extend([
                "# MISSING FILES:",
                *[f"# - {file}" for file in readiness['missing_files']],
                "",
                "echo 'ERROR: Not all required files are ready for assembly'",
                "echo 'Please ensure all shots are rendered before running this script'",
                "exit 1",
                ""
            ])
        
        # Generate FFmpeg command
        ffmpeg_cmd = self.generate_ffmpeg_command(sequence_plan, output_path)
        
        script_lines.extend([
            "# FFmpeg Assembly Command:",
            ffmpeg_cmd,
            "",
            f"echo 'Video assembly complete: {output_path}'"
        ])
        
        # Save script
        script_filename = f"assemble_{story_id}.bat" if os.name == 'nt' else f"assemble_{story_id}.sh"
        script_path = os.path.join(self.temp_dir, script_filename)
        
        with open(script_path, 'w') as f:
            if os.name != 'nt':  # Unix-like systems
                f.write("#!/bin/bash\n")
            f.write('\n'.join(script_lines))
        
        # Make script executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(script_path, 0o755)
        
        return script_path
    
    def get_assembly_status(self, story_id: str) -> Dict:
        """Get current assembly status for a story"""
        try:
            sequence_plan = self.get_story_sequence_plan(story_id)
            readiness = self.check_render_readiness(story_id)
            
            # Check if final video exists
            story_title = sequence_plan['story_title'].replace(' ', '_').replace('"', '')
            output_filename = f"{story_title}_{story_id}.mp4"
            final_video_path = os.path.join(self.output_dir, output_filename)
            
            status = {
                'story_id': story_id,
                'story_title': sequence_plan['story_title'],
                'sequence_ready': readiness['ready_for_assembly'],
                'shots_status': f"{readiness['shots_ready']}/{readiness['total_shots']}",
                'audio_status': f"{readiness['audio_tracks_ready']} tracks ready",
                'final_video_exists': os.path.exists(final_video_path),
                'final_video_path': final_video_path if os.path.exists(final_video_path) else None,
                'estimated_duration': sequence_plan['total_estimated_duration'],
                'assembly_script_ready': True,
                'next_steps': []
            }
            
            # Generate next steps recommendations
            if not readiness['ready_for_assembly']:
                status['next_steps'].append(f"Render {readiness['shots_missing']} missing shots")
            elif not status['final_video_exists']:
                status['next_steps'].append("Run assembly script to create final video")
            else:
                status['next_steps'].append("Story assembly complete!")
            
            return status
            
        except Exception as e:
            return {
                'story_id': story_id,
                'error': str(e),
                'sequence_ready': False,
                'assembly_script_ready': False
            }