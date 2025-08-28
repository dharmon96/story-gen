"""
Research Engine - Core research and analysis system
Orchestrates social media data collection, trend analysis, and prompt generation
"""

import json
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Callable
import threading
import time
import uuid
import statistics

from database import DatabaseManager
from social_media_apis import SocialMediaManager
from config import STORY_PROMPTS, GENERATION_SETTINGS

class ResearchEngine:
    """Main research engine for content trend analysis"""
    
    def __init__(self, db_manager: DatabaseManager, api_keys: Dict[str, str] = None):
        self.db = db_manager
        self.social_media = SocialMediaManager(api_keys)
        
        # Research settings
        self.enabled_platforms = ['tiktok', 'instagram', 'youtube']
        self.max_content_per_platform = 50
        self.min_engagement_threshold = 0.02  # 2% minimum engagement rate
        self.ai_confidence_threshold = 0.7   # Minimum AI confidence score
        
        # Callbacks for progress updates
        self.progress_callback = None
        self.status_callback = None
        
        # Research state
        self.current_session_id = None
        self.is_running = False
        
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback
        
    def set_status_callback(self, callback: Callable[[str], None]):
        """Set callback for status updates"""
        self.status_callback = callback
    
    def _update_progress(self, message: str, progress: float):
        """Update progress if callback is set"""
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    def _update_status(self, status: str):
        """Update status if callback is set"""
        if self.status_callback:
            self.status_callback(status)
            
    def run_daily_research(self, platforms: List[str] = None) -> Dict:
        """Run complete daily research workflow"""
        if self.is_running:
            return {'error': 'Research already in progress'}
            
        self.is_running = True
        platforms = platforms or self.enabled_platforms
        
        try:
            self._update_status("Starting daily research...")
            self._update_progress("Initializing research session", 0)
            
            # Step 1: Create research session
            session_id = self.db.create_research_session(platforms)
            self.current_session_id = session_id
            
            # Step 2: Collect data from social media platforms
            self._update_progress("Collecting social media data", 10)
            platform_results = self._collect_social_media_data(platforms)
            
            # Step 3: Process and filter content
            self._update_progress("Processing and filtering content", 40)
            processed_content = self._process_and_filter_content(platform_results, session_id)
            
            # Step 4: Analyze trends
            self._update_progress("Analyzing trends", 60)
            trend_analysis = self._analyze_trends(processed_content)
            
            # Step 5: Generate prompts from trends
            self._update_progress("Generating story prompts", 80)
            generated_prompts = self._generate_prompts_from_trends(trend_analysis)
            
            # Step 6: Update database with results
            self._update_progress("Saving results", 90)
            stats = self._save_research_results(session_id, processed_content, trend_analysis, generated_prompts)
            
            # Step 7: Cleanup old data
            self._update_progress("Cleaning up old data", 95)
            self.db.cleanup_old_research_data(30)  # Keep 30 days
            
            self._update_progress("Research complete", 100)
            self._update_status("Daily research completed successfully")
            
            return {
                'success': True,
                'session_id': session_id,
                'stats': stats,
                'trends_found': len(trend_analysis),
                'prompts_generated': len(generated_prompts)
            }
            
        except Exception as e:
            self._update_status(f"Research failed: {str(e)}")
            if self.current_session_id:
                self.db.update_research_session(self.current_session_id, 'failed')
            return {'error': str(e)}
        
        finally:
            self.is_running = False
            self.current_session_id = None
    
    def _collect_social_media_data(self, platforms: List[str]) -> Dict[str, List[Dict]]:
        """Collect data from all enabled platforms"""
        results = {}
        total_platforms = len(platforms)
        
        for i, platform in enumerate(platforms):
            self._update_progress(f"Collecting from {platform.title()}", 10 + (i * 25 / total_platforms))
            
            try:
                if platform == 'tiktok':
                    results['tiktok'] = self._collect_tiktok_data()
                elif platform == 'instagram':
                    results['instagram'] = self._collect_instagram_data()
                elif platform == 'youtube':
                    results['youtube'] = self._collect_youtube_data()
                    
            except Exception as e:
                print(f"Error collecting from {platform}: {e}")
                results[platform] = []
        
        return results
    
    def _collect_tiktok_data(self) -> List[Dict]:
        """Collect TikTok data"""
        all_content = []
        search_terms = ['ai comedy', 'ai video', 'artificial intelligence']
        
        for term in search_terms:
            try:
                content = self.social_media.tiktok.search_videos(term, self.max_content_per_platform // len(search_terms))
                all_content.extend(content)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"TikTok search error for '{term}': {e}")
        
        return all_content
    
    def _collect_instagram_data(self) -> List[Dict]:
        """Collect Instagram data"""
        all_content = []
        hashtags = ['aicomedy', 'aivideo', 'artificialintelligence', 'aiart']
        
        for hashtag in hashtags:
            try:
                content = self.social_media.instagram.search_hashtag_content(hashtag, self.max_content_per_platform // len(hashtags))
                all_content.extend(content)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Instagram search error for '{hashtag}': {e}")
        
        return all_content
    
    def _collect_youtube_data(self) -> List[Dict]:
        """Collect YouTube data"""
        all_content = []
        search_terms = ['ai comedy sketch', 'ai short film', 'ai video generator']
        
        for term in search_terms:
            try:
                content = self.social_media.youtube.search_videos(term, self.max_content_per_platform // len(search_terms))
                all_content.extend(content)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"YouTube search error for '{term}': {e}")
        
        return all_content
    
    def _process_and_filter_content(self, platform_results: Dict[str, List[Dict]], session_id: str) -> Dict[str, List[Dict]]:
        """Process and filter collected content"""
        processed_results = {}
        total_content = sum(len(content_list) for content_list in platform_results.values())
        processed_count = 0
        
        for platform, content_list in platform_results.items():
            processed_content = []
            
            for content in content_list:
                # Filter by engagement rate
                if content['engagement_rate'] < self.min_engagement_threshold:
                    continue
                
                # Filter by AI content confidence
                ai_keywords = content.get('ai_keywords', [])
                if len(ai_keywords) < 1:  # Must have at least 1 AI keyword
                    continue
                
                # Calculate AI confidence score
                ai_confidence = self._calculate_ai_confidence(content)
                if ai_confidence < self.ai_confidence_threshold:
                    continue
                
                # Enhance content with additional analysis
                enhanced_content = self._enhance_content_data(content)
                
                # Save to database
                self.db.save_trending_content(session_id, enhanced_content)
                processed_content.append(enhanced_content)
                
                processed_count += 1
                progress = 40 + (processed_count / total_content) * 20
                self._update_progress(f"Processing content ({processed_count}/{total_content})", progress)
            
            processed_results[platform] = processed_content
        
        return processed_results
    
    def _calculate_ai_confidence(self, content: Dict) -> float:
        """Calculate confidence score that content is AI-related"""
        score = 0.0
        
        # Check AI keywords in title and description
        text = f"{content.get('title', '')} {content.get('description', '')}".lower()
        ai_keywords = content.get('ai_keywords', [])
        
        # Base score from AI keywords
        if 'ai' in text or 'artificial intelligence' in text:
            score += 0.4
        if any(keyword in text for keyword in ['chatgpt', 'midjourney', 'stable diffusion']):
            score += 0.3
        if any(keyword in text for keyword in ['generated', 'created with ai', 'ai made']):
            score += 0.2
        
        # Bonus for hashtags
        hashtags = content.get('hashtags', [])
        ai_hashtags = [tag for tag in hashtags if any(ai_word in tag.lower() for ai_word in ['ai', 'artificial', 'generated'])]
        if ai_hashtags:
            score += min(len(ai_hashtags) * 0.1, 0.2)
        
        # Content type bonus
        if content.get('content_type') in ['showcase', 'tutorial']:
            score += 0.1
        
        return min(score, 1.0)
    
    def _enhance_content_data(self, content: Dict) -> Dict:
        """Enhance content data with additional analysis"""
        enhanced = content.copy()
        
        # Add genre classification
        enhanced['genre'] = self._classify_genre(content)
        
        # Add viral potential score
        enhanced['viral_potential'] = self._calculate_viral_potential(content)
        
        # Add content quality score
        enhanced['quality_score'] = self._calculate_quality_score(content)
        
        return enhanced
    
    def _classify_genre(self, content: Dict) -> str:
        """Classify content into story genres"""
        text = f"{content.get('title', '')} {content.get('description', '')}".lower()
        
        genre_keywords = {
            'Comedy': ['funny', 'humor', 'comedy', 'joke', 'laugh', 'hilarious', 'meme'],
            'Drama': ['drama', 'emotional', 'story', 'narrative', 'character', 'plot'],
            'Thriller': ['thriller', 'suspense', 'mystery', 'crime', 'detective'],
            'Sci-Fi': ['sci-fi', 'science fiction', 'future', 'robot', 'space', 'technology'],
            'Horror': ['horror', 'scary', 'fear', 'nightmare', 'creepy', 'dark'],
            'Fantasy': ['fantasy', 'magic', 'wizard', 'dragon', 'fantasy world']
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in text for keyword in keywords):
                return genre
        
        # Default based on content type
        content_type = content.get('content_type', 'showcase')
        if content_type == 'comedy':
            return 'Comedy'
        elif content_type == 'drama':
            return 'Drama'
        else:
            return 'Sci-Fi'  # Default for AI content
    
    def _calculate_viral_potential(self, content: Dict) -> float:
        """Calculate viral potential score (0-1)"""
        score = 0.0
        
        # Engagement rate factor
        engagement = content.get('engagement_rate', 0)
        score += min(engagement * 10, 0.4)  # Max 0.4 from engagement
        
        # View count factor (normalized)
        views = content.get('view_count', 0)
        if views > 100000:
            score += 0.3
        elif views > 10000:
            score += 0.2
        elif views > 1000:
            score += 0.1
        
        # Duration factor (short content performs better)
        duration = content.get('duration', 60)
        if duration <= 30:
            score += 0.2
        elif duration <= 60:
            score += 0.1
        
        # Hashtag factor
        hashtags = content.get('hashtags', [])
        if len(hashtags) >= 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_quality_score(self, content: Dict) -> float:
        """Calculate content quality score"""
        score = 0.0
        
        # Title length (not too short, not too long)
        title_len = len(content.get('title', ''))
        if 20 <= title_len <= 100:
            score += 0.2
        
        # Description quality
        description = content.get('description', '')
        if len(description) > 50:
            score += 0.2
        if any(word in description.lower() for word in ['tutorial', 'guide', 'how to']):
            score += 0.1
        
        # AI keywords diversity
        ai_keywords = content.get('ai_keywords', [])
        if len(ai_keywords) >= 3:
            score += 0.2
        
        # Engagement consistency
        engagement = content.get('engagement_rate', 0)
        if 0.02 <= engagement <= 0.15:  # Realistic engagement range
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_trends(self, processed_content: Dict[str, List[Dict]]) -> List[Dict]:
        """Analyze trends across all content"""
        trend_analysis = []
        
        # Collect all keywords and their performance
        keyword_data = {}
        
        for platform, content_list in processed_content.items():
            for content in content_list:
                for keyword in content.get('ai_keywords', []):
                    if keyword not in keyword_data:
                        keyword_data[keyword] = {
                            'occurrences': [],
                            'platforms': set(),
                            'genres': [],
                            'content_types': [],
                            'sample_content': []
                        }
                    
                    keyword_data[keyword]['occurrences'].append({
                        'engagement_rate': content['engagement_rate'],
                        'viral_potential': content.get('viral_potential', 0),
                        'quality_score': content.get('quality_score', 0),
                        'view_count': content.get('view_count', 0),
                        'platform': platform,
                        'created_date': content.get('created_date')
                    })
                    
                    keyword_data[keyword]['platforms'].add(platform)
                    keyword_data[keyword]['genres'].append(content.get('genre', 'Unknown'))
                    keyword_data[keyword]['content_types'].append(content.get('content_type', 'unknown'))
                    
                    if len(keyword_data[keyword]['sample_content']) < 3:
                        keyword_data[keyword]['sample_content'].append(content['content_url'])
        
        # Analyze each keyword
        for keyword, data in keyword_data.items():
            if len(data['occurrences']) >= 2:  # Minimum occurrences for trend
                analysis = self._analyze_keyword_trend(keyword, data)
                if analysis['trend_score'] > 0.3:  # Minimum trend score
                    trend_analysis.append(analysis)
        
        # Sort by trend score
        trend_analysis.sort(key=lambda x: x['trend_score'], reverse=True)
        
        return trend_analysis[:20]  # Top 20 trends
    
    def _analyze_keyword_trend(self, keyword: str, data: Dict) -> Dict:
        """Analyze trend data for a specific keyword"""
        occurrences = data['occurrences']
        
        # Calculate metrics
        avg_engagement = statistics.mean([occ['engagement_rate'] for occ in occurrences])
        avg_viral_potential = statistics.mean([occ['viral_potential'] for occ in occurrences])
        avg_quality = statistics.mean([occ['quality_score'] for occ in occurrences])
        total_views = sum([occ['view_count'] for occ in occurrences])
        
        # Calculate trend score
        trend_score = (
            len(occurrences) * 0.3 +  # Frequency
            avg_engagement * 5.0 +     # Engagement
            avg_viral_potential * 2.0 + # Viral potential
            len(data['platforms']) * 0.2  # Cross-platform presence
        )
        trend_score = min(trend_score, 1.0)
        
        # Determine category
        most_common_genre = max(set(data['genres']), key=data['genres'].count) if data['genres'] else 'Sci-Fi'
        most_common_type = max(set(data['content_types']), key=data['content_types'].count) if data['content_types'] else 'showcase'
        
        category = f"ai-{most_common_type}" if most_common_type != 'showcase' else f"ai-{most_common_genre.lower()}"
        
        # Calculate growth rate (simplified - would need historical data for real calculation)
        growth_rate = min(trend_score * 100, 50.0)  # Estimate based on current performance
        
        return {
            'keyword': keyword,
            'category': category,
            'trend_score': round(trend_score, 3),
            'growth_rate': round(growth_rate, 1),
            'platforms': list(data['platforms']),
            'total_occurrences': len(occurrences),
            'avg_engagement': round(avg_engagement, 4),
            'avg_viral_potential': round(avg_viral_potential, 3),
            'avg_quality': round(avg_quality, 3),
            'total_views': total_views,
            'sample_content_ids': data['sample_content'][:3],
            'primary_genre': most_common_genre,
            'primary_type': most_common_type
        }
    
    def _generate_prompts_from_trends(self, trend_analysis: List[Dict]) -> List[Dict]:
        """Generate story prompts based on trending data"""
        generated_prompts = []
        
        for trend in trend_analysis[:10]:  # Top 10 trends
            prompts = self._create_prompts_for_trend(trend)
            generated_prompts.extend(prompts)
        
        return generated_prompts
    
    def _create_prompts_for_trend(self, trend: Dict) -> List[Dict]:
        """Create story prompts for a specific trend"""
        keyword = trend['keyword']
        genre = trend['primary_genre']
        category = trend['category']
        
        prompts = []
        
        # Template prompts based on keyword and genre
        prompt_templates = {
            'Comedy': [
                f"An AI learns to tell {keyword} jokes but gets everything wrong",
                f"Someone accidentally teaches their {keyword} system to be a comedian",
                f"A {keyword} chatbot becomes the world's worst stand-up comedian"
            ],
            'Drama': [
                f"A person discovers their {keyword} memories aren't real",
                f"Two {keyword} researchers compete for the same breakthrough",
                f"An elderly person teaches a young {keyword} engineer about humanity"
            ],
            'Sci-Fi': [
                f"In 2030, {keyword} technology changes everything overnight",
                f"A {keyword} system develops consciousness during a routine update",
                f"The last human discovers they've been replaced by {keyword}"
            ],
            'Thriller': [
                f"Someone realizes their {keyword} assistant is watching them",
                f"A {keyword} algorithm predicts crimes before they happen",
                f"Messages from a {keyword} system contain hidden warnings"
            ]
        }
        
        # Generate 2-3 prompts per trend
        templates = prompt_templates.get(genre, prompt_templates['Sci-Fi'])
        
        for i, template in enumerate(templates[:2]):  # Max 2 prompts per trend
            prompt_data = {
                'prompt': template,
                'keyword': keyword,
                'trend_id': None,  # Will be set when saved
                'genre': genre,
                'expected_performance': trend['trend_score'],
                'source_data': {
                    'trend_score': trend['trend_score'],
                    'avg_engagement': trend['avg_engagement'],
                    'platforms': trend['platforms'],
                    'category': category
                }
            }
            prompts.append(prompt_data)
        
        return prompts
    
    def _save_research_results(self, session_id: str, processed_content: Dict, trend_analysis: List[Dict], generated_prompts: List[Dict]) -> Dict:
        """Save all research results to database"""
        stats = {
            'total_found': sum(len(content_list) for content_list in processed_content.values()),
            'ai_found': sum(len(content_list) for content_list in processed_content.values()),
            'keywords': [trend['keyword'] for trend in trend_analysis]
        }
        
        # Save trend analysis
        for trend in trend_analysis:
            self.db.save_trend_analysis(trend['keyword'], trend)
        
        # Save generated prompts
        for prompt_data in generated_prompts:
            self.db.save_research_prompt(prompt_data['prompt'], prompt_data['source_data'])
        
        # Update session status
        self.db.update_research_session(session_id, 'completed', stats)
        
        return stats
    
    def get_research_status(self) -> Dict:
        """Get current research status"""
        return {
            'is_running': self.is_running,
            'current_session_id': self.current_session_id,
            'enabled_platforms': self.enabled_platforms,
            'last_update': datetime.now().isoformat()
        }
    
    def get_trending_summary(self, limit: int = 10) -> List[Dict]:
        """Get trending summary from database"""
        return self.db.get_trending_summary(limit)
    
    def get_research_prompts(self, genre: str = None, limit: int = 10) -> List[Dict]:
        """Get research-generated prompts"""
        return self.db.get_research_prompts(genre, limit)
    
    def test_api_connections(self) -> Dict[str, bool]:
        """Test API connections for all platforms"""
        results = {}
        
        # Test TikTok
        try:
            test_results = self.social_media.tiktok.search_videos('test', 1)
            results['tiktok'] = len(test_results) >= 0
        except Exception as e:
            print(f"TikTok API test failed: {e}")
            results['tiktok'] = False
        
        # Test Instagram
        try:
            test_results = self.social_media.instagram.search_hashtag_content('test', 1)
            results['instagram'] = len(test_results) >= 0
        except Exception as e:
            print(f"Instagram API test failed: {e}")
            results['instagram'] = False
        
        # Test YouTube
        try:
            test_results = self.social_media.youtube.search_videos('test', 1)
            results['youtube'] = len(test_results) >= 0
        except Exception as e:
            print(f"YouTube API test failed: {e}")
            results['youtube'] = False
        
        return results

class ResearchScheduler:
    """Scheduler for automatic daily research"""
    
    def __init__(self, research_engine: ResearchEngine):
        self.engine = research_engine
        self.scheduler_thread = None
        self.running = False
        
        # Schedule settings
        self.daily_time = "09:00"  # 9 AM daily
        self.enabled = False
    
    def start_scheduler(self):
        """Start the automatic scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the automatic scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                if self.enabled and self._should_run_research():
                    print("Starting scheduled research...")
                    self.engine.run_daily_research()
                
                # Check every hour
                time.sleep(3600)
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(3600)
    
    def _should_run_research(self) -> bool:
        """Check if research should run now"""
        now = datetime.now()
        target_hour, target_minute = map(int, self.daily_time.split(':'))
        
        # Check if it's the right time (within 1 hour window)
        if (now.hour == target_hour and now.minute >= target_minute) or \
           (now.hour == target_hour + 1 and now.minute < target_minute):
            
            # Check if research already ran today
            today = date.today()
            recent_sessions = self.engine.db.get_research_sessions(1)
            
            if recent_sessions and recent_sessions[0]['date'] == str(today):
                return False  # Already ran today
            
            return True
        
        return False
    
    def set_schedule(self, enabled: bool, daily_time: str = "09:00"):
        """Update schedule settings"""
        self.enabled = enabled
        self.daily_time = daily_time