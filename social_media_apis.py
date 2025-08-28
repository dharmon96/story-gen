"""
Social Media APIs Integration for Research System
Handles TikTok, Instagram, and YouTube data collection
"""

import requests
import json
import re
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from urllib.parse import urlparse, parse_qs
import hashlib

class SocialMediaAPIs:
    """Unified interface for social media API access"""
    
    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FilmGenerator-Research/1.0',
            'Accept': 'application/json'
        })
        
        # Rate limiting tracking
        self.rate_limits = {
            'tiktok': {'requests': 0, 'reset_time': 0, 'limit': 1000},
            'instagram': {'requests': 0, 'reset_time': 0, 'limit': 200},
            'youtube': {'requests': 0, 'reset_time': 0, 'limit': 10000}
        }
        
        # AI-related keywords to filter content
        self.ai_keywords = [
            'ai', 'artificial intelligence', 'chatgpt', 'midjourney', 'stable diffusion',
            'ai generated', 'ai created', 'ai video', 'machine learning', 'deepfake',
            'text to video', 'ai animation', 'generated content', 'ai art', 'neural network',
            'ai comedian', 'ai storytelling', 'ai filmmaker', 'automated video'
        ]
        
        # Content type patterns
        self.content_patterns = {
            'comedy': ['funny', 'comedy', 'humor', 'joke', 'laugh', 'hilarious', 'meme'],
            'drama': ['drama', 'emotional', 'story', 'narrative', 'character', 'plot'],
            'tutorial': ['how to', 'tutorial', 'guide', 'learn', 'step by step'],
            'showcase': ['showcase', 'demo', 'example', 'test', 'result', 'before after']
        }

class TikTokAPI:
    """TikTok Research API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://open.tiktokapis.com/v2/research/"
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
    
    def search_videos(self, query: str, max_count: int = 100) -> List[Dict]:
        """Search for videos using TikTok Research API"""
        if not self.api_key:
            return self._fallback_search(query, max_count)
        
        url = f"{self.base_url}video/query/"
        
        # Build query for AI-related content
        search_query = {
            "query": {
                "and": [
                    {"operation": "IN", "field_name": "keyword", "field_values": [query]},
                    {"operation": "IN", "field_name": "region_code", "field_values": ["US", "GB", "CA"]}
                ]
            },
            "max_count": min(max_count, 1000),
            "cursor": 0,
            "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
            "end_date": datetime.now().strftime("%Y%m%d")
        }
        
        try:
            response = self.session.post(url, json=search_query, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for video in data.get('data', {}).get('videos', []):
                processed_video = self._process_tiktok_video(video)
                if processed_video:
                    videos.append(processed_video)
            
            return videos
            
        except Exception as e:
            print(f"TikTok API error: {e}")
            return self._fallback_search(query, max_count)
    
    def _process_tiktok_video(self, video_data: Dict) -> Optional[Dict]:
        """Process TikTok video data into standardized format"""
        try:
            # Extract hashtags from video description
            hashtags = self._extract_hashtags(video_data.get('video_description', ''))
            
            # Check if content is AI-related
            ai_keywords = self._find_ai_keywords(video_data.get('video_description', ''))
            if not ai_keywords:
                return None
            
            # Classify content type
            content_type = self._classify_content_type(video_data.get('video_description', ''))
            
            return {
                'platform': 'tiktok',
                'content_url': f"https://www.tiktok.com/@{video_data.get('username', '')}/video/{video_data.get('id', '')}",
                'title': video_data.get('video_description', '')[:100],
                'description': video_data.get('video_description', ''),
                'hashtags': hashtags,
                'view_count': video_data.get('view_count', 0),
                'like_count': video_data.get('like_count', 0),
                'comment_count': video_data.get('comment_count', 0),
                'share_count': video_data.get('share_count', 0),
                'engagement_rate': self._calculate_engagement_rate(video_data),
                'ai_keywords': ai_keywords,
                'content_type': content_type,
                'duration': video_data.get('duration', 0),
                'created_date': self._parse_tiktok_date(video_data.get('create_time'))
            }
        except Exception as e:
            print(f"Error processing TikTok video: {e}")
            return None
    
    def _fallback_search(self, query: str, max_count: int) -> List[Dict]:
        """Fallback method when API is unavailable - simulated data for testing"""
        print(f"Using fallback TikTok search for: {query}")
        
        # Generate sample trending content for testing
        sample_content = []
        base_hashtags = ["#ai", "#artificialintelligence", "#aicomedy", "#aivideo", "#comedy"]
        
        for i in range(min(max_count, 10)):  # Limit to 10 for testing
            sample_content.append({
                'platform': 'tiktok',
                'content_url': f'https://www.tiktok.com/@aicomedian{i}/video/{1234567890 + i}',
                'title': f'AI Comedy Sketch #{i + 1}',
                'description': f'Hilarious AI-generated comedy sketch about {query}. Watch till the end! #ai #comedy #funny',
                'hashtags': base_hashtags + [f"#{query.lower().replace(' ', '')}"],
                'view_count': 50000 + (i * 10000),
                'like_count': 5000 + (i * 1000),
                'comment_count': 500 + (i * 100),
                'share_count': 200 + (i * 50),
                'engagement_rate': 0.08 + (i * 0.01),
                'ai_keywords': ['ai', 'comedy', 'generated'],
                'content_type': 'comedy',
                'duration': 30,
                'created_date': (datetime.now() - timedelta(days=i)).date()
            })
        
        return sample_content
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        return re.findall(r'#\w+', text.lower())
    
    def _find_ai_keywords(self, text: str) -> List[str]:
        """Find AI-related keywords in text"""
        text_lower = text.lower()
        found_keywords = []
        
        ai_keywords = [
            'ai', 'artificial intelligence', 'chatgpt', 'midjourney', 'stable diffusion',
            'ai generated', 'ai created', 'ai video', 'machine learning', 'deepfake',
            'text to video', 'ai animation', 'generated content', 'ai art'
        ]
        
        for keyword in ai_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _classify_content_type(self, text: str) -> str:
        """Classify content type based on description"""
        text_lower = text.lower()
        
        comedy_words = ['funny', 'comedy', 'humor', 'joke', 'laugh', 'hilarious', 'meme']
        drama_words = ['drama', 'emotional', 'story', 'narrative', 'character', 'plot']
        tutorial_words = ['how to', 'tutorial', 'guide', 'learn', 'step by step']
        
        if any(word in text_lower for word in comedy_words):
            return 'comedy'
        elif any(word in text_lower for word in drama_words):
            return 'drama'
        elif any(word in text_lower for word in tutorial_words):
            return 'tutorial'
        else:
            return 'showcase'
    
    def _calculate_engagement_rate(self, video_data: Dict) -> float:
        """Calculate engagement rate for video"""
        views = video_data.get('view_count', 0)
        if views == 0:
            return 0.0
        
        likes = video_data.get('like_count', 0)
        comments = video_data.get('comment_count', 0)
        shares = video_data.get('share_count', 0)
        
        engagement = likes + comments + shares
        return round(engagement / views, 4)
    
    def _parse_tiktok_date(self, timestamp) -> date:
        """Parse TikTok timestamp to date"""
        try:
            if isinstance(timestamp, int):
                return datetime.fromtimestamp(timestamp).date()
        except (ValueError, OSError) as e:
            print(f"Error parsing TikTok timestamp: {e}")
        return date.today()

class InstagramAPI:
    """Instagram Basic Display API integration"""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.base_url = "https://graph.instagram.com"
        self.session = requests.Session()
    
    def search_hashtag_content(self, hashtag: str, max_count: int = 50) -> List[Dict]:
        """Search for content by hashtag"""
        if not self.access_token:
            return self._fallback_instagram_search(hashtag, max_count)
        
        try:
            # Note: Instagram's hashtag search requires business accounts and specific permissions
            # This is a simplified implementation
            url = f"{self.base_url}/me/media"
            params = {
                'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
                'access_token': self.access_token,
                'limit': min(max_count, 50)
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            content = []
            
            for media in data.get('data', []):
                processed_media = self._process_instagram_media(media, hashtag)
                if processed_media:
                    content.append(processed_media)
            
            return content
            
        except Exception as e:
            print(f"Instagram API error: {e}")
            return self._fallback_instagram_search(hashtag, max_count)
    
    def _process_instagram_media(self, media_data: Dict, hashtag: str) -> Optional[Dict]:
        """Process Instagram media data"""
        try:
            caption = media_data.get('caption', '')
            
            # Check for AI keywords
            ai_keywords = self._find_ai_keywords(caption)
            if not ai_keywords:
                return None
            
            hashtags = self._extract_hashtags(caption)
            content_type = self._classify_content_type(caption)
            
            return {
                'platform': 'instagram',
                'content_url': media_data.get('permalink', ''),
                'title': caption[:100] if caption else 'Instagram Post',
                'description': caption,
                'hashtags': hashtags,
                'view_count': 0,  # Not available in basic API
                'like_count': media_data.get('like_count', 0),
                'comment_count': media_data.get('comments_count', 0),
                'share_count': 0,  # Not available
                'engagement_rate': self._calculate_engagement_rate_instagram(media_data),
                'ai_keywords': ai_keywords,
                'content_type': content_type,
                'duration': 30,  # Estimate for videos
                'created_date': self._parse_instagram_date(media_data.get('timestamp'))
            }
        except Exception as e:
            print(f"Error processing Instagram media: {e}")
            return None
    
    def _fallback_instagram_search(self, hashtag: str, max_count: int) -> List[Dict]:
        """Fallback method for Instagram search"""
        print(f"Using fallback Instagram search for: #{hashtag}")
        
        sample_content = []
        for i in range(min(max_count, 8)):  # Limit for testing
            sample_content.append({
                'platform': 'instagram',
                'content_url': f'https://www.instagram.com/p/{hashtag.upper()}{i}ABC/',
                'title': f'AI Short Film #{i + 1}',
                'description': f'Amazing AI-generated short film featuring {hashtag}! Created with cutting-edge AI technology. #ai #shortfilm #{hashtag}',
                'hashtags': [f'#{hashtag}', '#ai', '#shortfilm', '#aivideo'],
                'view_count': 0,
                'like_count': 2000 + (i * 500),
                'comment_count': 150 + (i * 25),
                'share_count': 0,
                'engagement_rate': 0.06 + (i * 0.01),
                'ai_keywords': ['ai', 'generated', 'technology'],
                'content_type': 'showcase',
                'duration': 60,
                'created_date': (datetime.now() - timedelta(days=i)).date()
            })
        
        return sample_content
    
    def _find_ai_keywords(self, text: str) -> List[str]:
        """Find AI keywords in Instagram content"""
        return TikTokAPI._find_ai_keywords(None, text)
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from Instagram caption"""
        return TikTokAPI._extract_hashtags(None, text)
    
    def _classify_content_type(self, text: str) -> str:
        """Classify Instagram content type"""
        return TikTokAPI._classify_content_type(None, text)
    
    def _calculate_engagement_rate_instagram(self, media_data: Dict) -> float:
        """Calculate engagement rate for Instagram (simplified)"""
        likes = media_data.get('like_count', 0)
        comments = media_data.get('comments_count', 0)
        
        # Estimate followers based on engagement (rough approximation)
        estimated_reach = max(likes * 10, 1000)  # Rough estimate
        engagement = likes + comments
        
        return round(engagement / estimated_reach, 4)
    
    def _parse_instagram_date(self, timestamp_str: str) -> date:
        """Parse Instagram timestamp"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.date()
        except:
            return date.today()

class YouTubeAPI:
    """YouTube Data API v3 integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.session = requests.Session()
    
    def search_videos(self, query: str, max_count: int = 50) -> List[Dict]:
        """Search for YouTube videos"""
        if not self.api_key:
            return self._fallback_youtube_search(query, max_count)
        
        try:
            # Search for videos
            search_url = f"{self.base_url}/search"
            search_params = {
                'part': 'snippet',
                'q': f"{query} ai artificial intelligence",
                'type': 'video',
                'maxResults': min(max_count, 50),
                'order': 'relevance',
                'publishedAfter': (datetime.now() - timedelta(days=7)).isoformat() + 'Z',
                'key': self.api_key
            }
            
            search_response = self.session.get(search_url, params=search_params, timeout=30)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]
            
            if not video_ids:
                return []
            
            # Get video statistics
            stats_url = f"{self.base_url}/videos"
            stats_params = {
                'part': 'statistics,contentDetails',
                'id': ','.join(video_ids),
                'key': self.api_key
            }
            
            stats_response = self.session.get(stats_url, params=stats_params, timeout=30)
            stats_response.raise_for_status()
            stats_data = stats_response.json()
            
            # Combine search and stats data
            videos = []
            stats_dict = {video['id']: video for video in stats_data.get('items', [])}
            
            for item in search_data.get('items', []):
                video_id = item['id']['videoId']
                stats = stats_dict.get(video_id, {})
                
                processed_video = self._process_youtube_video(item, stats)
                if processed_video:
                    videos.append(processed_video)
            
            return videos
            
        except Exception as e:
            print(f"YouTube API error: {e}")
            return self._fallback_youtube_search(query, max_count)
    
    def _process_youtube_video(self, video_item: Dict, stats_data: Dict) -> Optional[Dict]:
        """Process YouTube video data"""
        try:
            snippet = video_item['snippet']
            statistics = stats_data.get('statistics', {})
            content_details = stats_data.get('contentDetails', {})
            
            title = snippet.get('title', '')
            description = snippet.get('description', '')
            
            # Check for AI keywords
            full_text = f"{title} {description}"
            ai_keywords = self._find_ai_keywords(full_text)
            if not ai_keywords:
                return None
            
            # Extract hashtags from description
            hashtags = self._extract_hashtags(description)
            content_type = self._classify_content_type(full_text)
            
            view_count = int(statistics.get('viewCount', 0))
            like_count = int(statistics.get('likeCount', 0))
            comment_count = int(statistics.get('commentCount', 0))
            
            return {
                'platform': 'youtube',
                'content_url': f"https://www.youtube.com/watch?v={video_item['id']['videoId']}",
                'title': title,
                'description': description,
                'hashtags': hashtags,
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'share_count': 0,  # Not available in API
                'engagement_rate': self._calculate_engagement_rate_youtube(statistics),
                'ai_keywords': ai_keywords,
                'content_type': content_type,
                'duration': self._parse_youtube_duration(content_details.get('duration', 'PT0S')),
                'created_date': self._parse_youtube_date(snippet.get('publishedAt'))
            }
            
        except Exception as e:
            print(f"Error processing YouTube video: {e}")
            return None
    
    def _fallback_youtube_search(self, query: str, max_count: int) -> List[Dict]:
        """Fallback YouTube search method"""
        print(f"Using fallback YouTube search for: {query}")
        
        sample_content = []
        for i in range(min(max_count, 6)):  # Limit for testing
            sample_content.append({
                'platform': 'youtube',
                'content_url': f'https://www.youtube.com/watch?v={query.upper()}{i}ABC123',
                'title': f'AI {query} Tutorial - Amazing Results!',
                'description': f'Complete guide to creating {query} using AI tools. Learn how to make viral content with artificial intelligence. Subscribe for more AI tutorials!',
                'hashtags': [f'#{query.lower()}', '#ai', '#tutorial', '#artificialintelligence'],
                'view_count': 25000 + (i * 5000),
                'like_count': 800 + (i * 200),
                'comment_count': 120 + (i * 30),
                'share_count': 0,
                'engagement_rate': 0.04 + (i * 0.005),
                'ai_keywords': ['ai', 'artificial intelligence', 'tutorial'],
                'content_type': 'tutorial',
                'duration': 300 + (i * 60),  # 5-10 minutes
                'created_date': (datetime.now() - timedelta(days=i)).date()
            })
        
        return sample_content
    
    def _find_ai_keywords(self, text: str) -> List[str]:
        """Find AI keywords in YouTube content"""
        return TikTokAPI._find_ai_keywords(None, text)
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from YouTube description"""
        return TikTokAPI._extract_hashtags(None, text)
    
    def _classify_content_type(self, text: str) -> str:
        """Classify YouTube content type"""
        return TikTokAPI._classify_content_type(None, text)
    
    def _calculate_engagement_rate_youtube(self, statistics: Dict) -> float:
        """Calculate engagement rate for YouTube"""
        views = int(statistics.get('viewCount', 0))
        if views == 0:
            return 0.0
        
        likes = int(statistics.get('likeCount', 0))
        comments = int(statistics.get('commentCount', 0))
        
        engagement = likes + comments
        return round(engagement / views, 4)
    
    def _parse_youtube_duration(self, duration_str: str) -> int:
        """Parse YouTube duration (ISO 8601) to seconds"""
        try:
            # Simple parser for PT#M#S format
            import re
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration_str)
            
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
            
            return 0
        except (ValueError, AttributeError, TypeError) as e:
            print(f"Error parsing YouTube duration '{duration_str}': {e}")
            return 0
    
    def _parse_youtube_date(self, date_str: str) -> date:
        """Parse YouTube published date"""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.date()
        except (ValueError, AttributeError) as e:
            print(f"Error parsing YouTube date '{date_str}': {e}")
            return date.today()

class SocialMediaManager:
    """Unified manager for all social media APIs"""
    
    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        
        # Initialize API clients
        self.tiktok = TikTokAPI(self.api_keys.get('tiktok'))
        self.instagram = InstagramAPI(self.api_keys.get('instagram'))
        self.youtube = YouTubeAPI(self.api_keys.get('youtube'))
        
        # Research topics for AI content
        self.research_topics = [
            'ai comedy', 'ai animation', 'ai storytelling', 'ai video generator',
            'chatgpt comedy', 'ai short film', 'artificial intelligence humor',
            'ai generated content', 'machine learning video', 'ai memes'
        ]
    
    def research_all_platforms(self, max_per_platform: int = 20) -> Dict[str, List[Dict]]:
        """Research trending AI content across all platforms"""
        results = {
            'tiktok': [],
            'instagram': [],
            'youtube': []
        }
        
        for topic in self.research_topics[:3]:  # Limit topics for testing
            print(f"Researching topic: {topic}")
            
            # TikTok search
            try:
                tiktok_results = self.tiktok.search_videos(topic, max_per_platform // len(self.research_topics[:3]))
                results['tiktok'].extend(tiktok_results)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"TikTok research error for {topic}: {e}")
            
            # Instagram search
            try:
                instagram_results = self.instagram.search_hashtag_content(topic.replace(' ', ''), max_per_platform // len(self.research_topics[:3]))
                results['instagram'].extend(instagram_results)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Instagram research error for {topic}: {e}")
            
            # YouTube search
            try:
                youtube_results = self.youtube.search_videos(topic, max_per_platform // len(self.research_topics[:3]))
                results['youtube'].extend(youtube_results)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"YouTube research error for {topic}: {e}")
        
        # Remove duplicates and sort by engagement
        for platform in results:
            results[platform] = sorted(
                list({item['content_url']: item for item in results[platform]}.values()),
                key=lambda x: x['engagement_rate'],
                reverse=True
            )[:max_per_platform]
        
        return results
    
    def get_trending_keywords(self, platform_results: Dict[str, List[Dict]]) -> List[Tuple[str, int, float]]:
        """Extract trending keywords from research results"""
        keyword_stats = {}
        
        for platform, content_list in platform_results.items():
            for content in content_list:
                for keyword in content.get('ai_keywords', []):
                    if keyword not in keyword_stats:
                        keyword_stats[keyword] = {'count': 0, 'total_engagement': 0.0, 'platforms': set()}
                    
                    keyword_stats[keyword]['count'] += 1
                    keyword_stats[keyword]['total_engagement'] += content['engagement_rate']
                    keyword_stats[keyword]['platforms'].add(platform)
        
        # Convert to list of (keyword, count, avg_engagement)
        trending_keywords = []
        for keyword, stats in keyword_stats.items():
            avg_engagement = stats['total_engagement'] / stats['count'] if stats['count'] > 0 else 0
            trending_keywords.append((keyword, stats['count'], avg_engagement))
        
        # Sort by count * engagement score
        trending_keywords.sort(key=lambda x: x[1] * x[2], reverse=True)
        
        return trending_keywords[:20]  # Top 20 trending keywords