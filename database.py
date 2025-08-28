"""
Database management for Film Generator App
Handles all SQLite operations
"""

import sqlite3
import json
from typing import List, Dict, Optional, Any
from dataclasses import asdict
from config import DB_PATH
from data_models import StoryConfig, Shot

def init_database():
    """Initialize database with required tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"Database created/opened successfully at: {DB_PATH}")
        cursor = conn.cursor()
        
        # Stories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                length TEXT NOT NULL,
                prompt TEXT NOT NULL,
                content TEXT NOT NULL,
                parts INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        # Shots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT NOT NULL,
                shot_number INTEGER NOT NULL,
                description TEXT NOT NULL,
                duration REAL NOT NULL,
                frames INTEGER DEFAULT 120,
                wan_prompt TEXT,
                narration TEXT,
                music_cue TEXT,
                status TEXT DEFAULT 'pending',
                render_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rendered_at TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
        ''')
        
        # Videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                story_id TEXT NOT NULL,
                part_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                upload_url TEXT,
                duration REAL,
                status TEXT DEFAULT 'pending',
                uploaded_at TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
        ''')
        
        # Metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                story_id TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                completion_rate REAL DEFAULT 0.0,
                engagement_rate REAL DEFAULT 0.0,
                avg_watch_time REAL DEFAULT 0.0,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (id),
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
        ''')
        
        # Render queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS render_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_id INTEGER NOT NULL,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'queued',
                attempts INTEGER DEFAULT 0,
                error_message TEXT,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (shot_id) REFERENCES shots (id)
            )
        ''')
        
        # Generation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT NOT NULL,
                config_json TEXT NOT NULL,
                performance_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
        ''')
        
        # Research sessions table - Daily research data snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_sessions (
                id TEXT PRIMARY KEY,
                date DATE UNIQUE,
                platforms_scraped TEXT NOT NULL,
                total_content_found INTEGER DEFAULT 0,
                ai_content_found INTEGER DEFAULT 0,
                trending_keywords TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        # Trending content discoveries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trending_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                content_url TEXT,
                title TEXT,
                description TEXT,
                hashtags TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                engagement_rate REAL DEFAULT 0.0,
                ai_keywords TEXT,
                content_type TEXT,
                genre TEXT,
                duration INTEGER,
                created_date DATE,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES research_sessions (id)
            )
        ''')
        
        # Master trends analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                trend_score REAL DEFAULT 0.0,
                growth_rate REAL DEFAULT 0.0,
                peak_date DATE,
                platforms TEXT,
                sample_content_ids TEXT,
                generated_prompts TEXT,
                total_occurrences INTEGER DEFAULT 0,
                avg_engagement REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Research-based story prompts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                source_keyword TEXT,
                source_trend_id INTEGER,
                genre TEXT,
                expected_performance REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (source_trend_id) REFERENCES trend_analysis (id)
            )
        ''')
        
        # Story characters table - Character consistency for ComfyUI
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                physical_description TEXT NOT NULL,
                personality_traits TEXT,
                age_range TEXT,
                clothing_style TEXT,
                importance_level INTEGER DEFAULT 1,
                reference_prompt TEXT,
                style_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
        ''')
        
        # Story locations table - Background consistency for ComfyUI
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                environment_type TEXT,
                time_of_day TEXT,
                weather_mood TEXT,
                lighting_style TEXT,
                importance_level INTEGER DEFAULT 1,
                reference_prompt TEXT,
                style_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
        ''')
        
        # Style reference cards table - Generated style cards for ComfyUI workflows
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS style_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT NOT NULL,
                reference_type TEXT NOT NULL,
                reference_name TEXT NOT NULL,
                comfyui_prompt TEXT NOT NULL,
                negative_prompt TEXT,
                style_settings JSON,
                reference_image_path TEXT,
                usage_count INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
        ''')

        # User settings table - API keys, preferences, etc.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # System prompt presets table - Custom user presets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preset_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                preset_data JSON NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Performance summary view
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS story_performance AS
            SELECT 
                s.id as story_id,
                s.title,
                s.genre,
                s.length,
                s.status,
                COUNT(DISTINCT v.id) as total_parts,
                COALESCE(SUM(m.views), 0) as total_views,
                COALESCE(AVG(m.engagement_rate), 0) as avg_engagement,
                COALESCE(AVG(m.completion_rate), 0) as avg_completion,
                MAX(m.recorded_at) as last_updated
            FROM stories s
            LEFT JOIN videos v ON s.id = v.story_id
            LEFT JOIN metrics m ON v.id = m.video_id
            GROUP BY s.id
        ''')
        
        # Research trends summary view
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS trending_summary AS
            SELECT 
                ta.keyword,
                ta.category,
                ta.trend_score,
                ta.growth_rate,
                ta.platforms,
                COUNT(tc.id) as content_count,
                AVG(tc.engagement_rate) as avg_engagement,
                MAX(tc.discovered_at) as last_seen
            FROM trend_analysis ta
            LEFT JOIN trending_content tc ON json_extract(tc.ai_keywords, '$') LIKE '%' || ta.keyword || '%'
            GROUP BY ta.id
            ORDER BY ta.trend_score DESC
        ''')
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self):
        self.conn = None
        self.connect()
        self._run_migrations()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.OperationalError as e:
            print(f"Error connecting to database: {e}")
            raise
    
    def _run_migrations(self):
        """Run database schema migrations for existing databases"""
        if not self.conn:
            return
            
        cursor = self.conn.cursor()
        
        # Migration: Add frames column to shots table if it doesn't exist
        try:
            cursor.execute("PRAGMA table_info(shots)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'frames' not in columns:
                cursor.execute("ALTER TABLE shots ADD COLUMN frames INTEGER DEFAULT 120")
                self.conn.commit()
                print("Migration: Added frames column to shots table")
        except Exception as e:
            print(f"Migration warning: Could not add frames column: {e}")
        
        cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def save_story(self, story: Dict) -> str:
        """Save story to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO stories (id, title, genre, length, prompt, content, parts, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (story['id'], story['title'], story['genre'], story['length'],
              story['prompt'], story['content'], story['parts'], 'processing'))
        self.conn.commit()
        return story['id']
    
    def save_shot(self, shot: Shot) -> int:
        """Save shot to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO shots (story_id, shot_number, description, duration, frames,
                             wan_prompt, narration, music_cue, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (shot.story_id, shot.shot_number, shot.description, shot.duration, shot.frames,
              shot.wan_prompt, shot.narration, shot.music_cue, shot.status))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_shot_status(self, shot_id: int, status: str, render_path: str = None):
        """Update shot rendering status"""
        cursor = self.conn.cursor()
        if render_path:
            cursor.execute('''
                UPDATE shots 
                SET status = ?, render_path = ?, rendered_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, render_path, shot_id))
        else:
            cursor.execute('UPDATE shots SET status = ? WHERE id = ?', (status, shot_id))
        self.conn.commit()
    
    def add_to_render_queue(self, shot_id: int, priority: int = 5):
        """Add shot to render queue"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO render_queue (shot_id, priority, status)
            VALUES (?, ?, 'queued')
        ''', (shot_id, priority))
        self.conn.commit()
    
    def get_next_render_item(self) -> Optional[Dict]:
        """Get next item from render queue"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT rq.*, s.* 
            FROM render_queue rq
            JOIN shots s ON rq.shot_id = s.id
            WHERE rq.status = 'queued'
            ORDER BY rq.priority DESC, rq.queued_at ASC
            LIMIT 1
        ''')
        return cursor.fetchone()
    
    def update_render_queue_status(self, queue_id: int, status: str, error: str = None):
        """Update render queue item status"""
        cursor = self.conn.cursor()
        if status == 'processing':
            cursor.execute('''
                UPDATE render_queue 
                SET status = ?, started_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, queue_id))
        elif status == 'completed':
            cursor.execute('''
                UPDATE render_queue 
                SET status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, queue_id))
        elif status == 'failed':
            cursor.execute('''
                UPDATE render_queue 
                SET status = ?, error_message = ?, attempts = attempts + 1
                WHERE id = ?
            ''', (status, error, queue_id))
        self.conn.commit()
    
    def save_video(self, video_data: Dict):
        """Save uploaded video information"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO videos (id, story_id, part_number, title, upload_url, 
                              duration, status, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (video_data['id'], video_data['story_id'], video_data['part_number'],
              video_data['title'], video_data.get('upload_url'), video_data.get('duration'),
              'uploaded'))
        self.conn.commit()
    
    def save_metrics(self, metrics: Dict):
        """Save video metrics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO metrics (video_id, story_id, views, likes, comments, 
                               shares, completion_rate, engagement_rate, avg_watch_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (metrics['video_id'], metrics['story_id'], metrics['views'],
              metrics['likes'], metrics['comments'], metrics['shares'],
              metrics['completion_rate'], metrics['engagement_rate'],
              metrics['avg_watch_time']))
        self.conn.commit()
    
    def get_story_performance(self) -> List[Dict]:
        """Get performance data for all stories"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM story_performance ORDER BY total_views DESC')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_genre_performance(self) -> Dict:
        """Get performance by genre"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT genre, 
                   AVG(avg_engagement) as avg_engagement,
                   AVG(avg_completion) as avg_completion,
                   SUM(total_views) as total_views
            FROM story_performance
            GROUP BY genre
            ORDER BY avg_engagement DESC
        ''')
        return {row['genre']: dict(row) for row in cursor.fetchall()}
    
    def get_length_performance(self) -> Dict:
        """Get performance by length"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT length,
                   AVG(avg_engagement) as avg_engagement,
                   AVG(avg_completion) as avg_completion,
                   COUNT(*) as story_count
            FROM story_performance
            GROUP BY length
            ORDER BY avg_completion DESC
        ''')
        return {row['length']: dict(row) for row in cursor.fetchall()}
    
    def get_recent_stories(self, limit: int = 10) -> List[Dict]:
        """Get recent stories"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM stories 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_render_queue_status(self) -> Dict:
        """Get render queue statistics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued,
                COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM render_queue
            WHERE DATE(queued_at) = DATE('now')
        ''')
        return dict(cursor.fetchone())
    
    def save_generation_history(self, story_id: str, config: StoryConfig, score: float = None):
        """Save generation configuration for ML training"""
        cursor = self.conn.cursor()
        config_json = json.dumps(asdict(config))
        cursor.execute('''
            INSERT INTO generation_history (story_id, config_json, performance_score)
            VALUES (?, ?, ?)
        ''', (story_id, config_json, score))
        self.conn.commit()
    
    def delete_story(self, story_id: str):
        """Delete a story and all related data"""
        cursor = self.conn.cursor()
        
        # Delete in order of dependencies
        cursor.execute('DELETE FROM metrics WHERE story_id = ?', (story_id,))
        cursor.execute('DELETE FROM videos WHERE story_id = ?', (story_id,))
        cursor.execute('DELETE FROM render_queue WHERE shot_id IN (SELECT id FROM shots WHERE story_id = ?)', (story_id,))
        cursor.execute('DELETE FROM shots WHERE story_id = ?', (story_id,))
        cursor.execute('DELETE FROM generation_history WHERE story_id = ?', (story_id,))
        cursor.execute('DELETE FROM stories WHERE id = ?', (story_id,))
        
        self.conn.commit()
        return True
    
    def clear_render_queue(self):
        """Clear all items from render queue"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM render_queue')
        self.conn.commit()
    
    def get_best_performing_prompts(self, limit: int = 5) -> List[str]:
        """Get best performing prompts for auto-generation"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.prompt, AVG(sp.avg_engagement) as avg_performance
            FROM stories s
            JOIN story_performance sp ON s.id = sp.story_id
            WHERE sp.total_views > 100
            GROUP BY s.prompt
            ORDER BY avg_performance DESC
            LIMIT ?
        ''', (limit,))
        return [row['prompt'] for row in cursor.fetchall()]
    
    # Research System Methods
    
    def create_research_session(self, platforms: List[str]) -> str:
        """Create a new research session for today"""
        from datetime import date
        import uuid
        
        session_id = str(uuid.uuid4())
        today = date.today()
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO research_sessions (id, date, platforms_scraped, status)
                VALUES (?, ?, ?, 'running')
            ''', (session_id, today, json.dumps(platforms)))
            self.conn.commit()
            return session_id
        except sqlite3.IntegrityError:
            # Session for today already exists
            cursor.execute('SELECT id FROM research_sessions WHERE date = ?', (today,))
            return cursor.fetchone()['id']
    
    def save_trending_content(self, session_id: str, content_data: Dict):
        """Save discovered trending content"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trending_content (
                session_id, platform, content_url, title, description, hashtags,
                view_count, like_count, comment_count, share_count, engagement_rate,
                ai_keywords, content_type, genre, duration, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, content_data['platform'], content_data.get('content_url'),
            content_data.get('title'), content_data.get('description'),
            json.dumps(content_data.get('hashtags', [])),
            content_data.get('view_count', 0), content_data.get('like_count', 0),
            content_data.get('comment_count', 0), content_data.get('share_count', 0),
            content_data.get('engagement_rate', 0.0),
            json.dumps(content_data.get('ai_keywords', [])),
            content_data.get('content_type'), content_data.get('genre'),
            content_data.get('duration'), content_data.get('created_date')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_research_session(self, session_id: str, status: str, stats: Dict = None):
        """Update research session with completion stats"""
        cursor = self.conn.cursor()
        if stats:
            cursor.execute('''
                UPDATE research_sessions 
                SET status = ?, total_content_found = ?, ai_content_found = ?,
                    trending_keywords = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, stats.get('total_found', 0), stats.get('ai_found', 0),
                  json.dumps(stats.get('keywords', [])), session_id))
        else:
            cursor.execute('''
                UPDATE research_sessions SET status = ? WHERE id = ?
            ''', (status, session_id))
        self.conn.commit()
    
    def save_trend_analysis(self, keyword: str, analysis_data: Dict):
        """Save or update trend analysis"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO trend_analysis (
                keyword, category, trend_score, growth_rate, peak_date,
                platforms, sample_content_ids, generated_prompts,
                total_occurrences, avg_engagement, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            keyword, analysis_data['category'], analysis_data['trend_score'],
            analysis_data.get('growth_rate', 0.0), analysis_data.get('peak_date'),
            json.dumps(analysis_data.get('platforms', [])),
            json.dumps(analysis_data.get('sample_content_ids', [])),
            json.dumps(analysis_data.get('generated_prompts', [])),
            analysis_data.get('total_occurrences', 0),
            analysis_data.get('avg_engagement', 0.0)
        ))
        self.conn.commit()
    
    def save_research_prompt(self, prompt: str, source_data: Dict):
        """Save research-generated prompt"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO research_prompts (
                prompt, source_keyword, source_trend_id, genre, expected_performance
            ) VALUES (?, ?, ?, ?, ?)
        ''', (prompt, source_data.get('keyword'), source_data.get('trend_id'),
              source_data.get('genre'), source_data.get('expected_performance', 0.0)))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_trending_summary(self, limit: int = 20) -> List[Dict]:
        """Get current trending summary"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM trending_summary LIMIT ?', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_research_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent research sessions"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM research_sessions 
            ORDER BY date DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_trending_content_by_session(self, session_id: str) -> List[Dict]:
        """Get trending content for a specific session"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM trending_content 
            WHERE session_id = ?
            ORDER BY engagement_rate DESC
        ''', (session_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_research_prompts(self, genre: str = None, limit: int = 10) -> List[Dict]:
        """Get research-based prompts, optionally filtered by genre"""
        cursor = self.conn.cursor()
        if genre:
            cursor.execute('''
                SELECT * FROM research_prompts 
                WHERE genre = ? 
                ORDER BY expected_performance DESC, created_at DESC
                LIMIT ?
            ''', (genre, limit))
        else:
            cursor.execute('''
                SELECT * FROM research_prompts 
                ORDER BY expected_performance DESC, created_at DESC
                LIMIT ?
            ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_prompt_usage(self, prompt_id: int, success: bool = True):
        """Update prompt usage statistics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE research_prompts 
            SET usage_count = usage_count + 1,
                success_rate = (success_rate * usage_count + ?) / (usage_count + 1),
                last_used = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (1.0 if success else 0.0, prompt_id))
        self.conn.commit()
    
    def cleanup_old_research_data(self, days_to_keep: int = 30):
        """Clean up old research data"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM trending_content 
            WHERE session_id IN (
                SELECT id FROM research_sessions 
                WHERE date < date('now', '-{} days')
            )
        '''.format(days_to_keep))
        
        cursor.execute('''
            DELETE FROM research_sessions 
            WHERE date < date('now', '-{} days')
        '''.format(days_to_keep))
        
        self.conn.commit()
    
    # Character and Style Consistency Methods
    
    def save_story_character(self, story_id: str, character_data: Dict) -> int:
        """Save character data for story consistency"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO story_characters (
                story_id, name, role, physical_description, personality_traits,
                age_range, clothing_style, importance_level, reference_prompt, style_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            story_id, character_data['name'], character_data['role'],
            character_data['physical_description'], character_data.get('personality_traits'),
            character_data.get('age_range'), character_data.get('clothing_style'),
            character_data.get('importance_level', 1), character_data.get('reference_prompt'),
            character_data.get('style_notes')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def save_story_location(self, story_id: str, location_data: Dict) -> int:
        """Save location data for story consistency"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO story_locations (
                story_id, name, description, environment_type, time_of_day,
                weather_mood, lighting_style, importance_level, reference_prompt, style_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            story_id, location_data['name'], location_data['description'],
            location_data.get('environment_type'), location_data.get('time_of_day'),
            location_data.get('weather_mood'), location_data.get('lighting_style'),
            location_data.get('importance_level', 1), location_data.get('reference_prompt'),
            location_data.get('style_notes')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def save_style_reference(self, story_id: str, reference_data: Dict) -> int:
        """Save style reference card data"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO style_references (
                story_id, reference_type, reference_name, comfyui_prompt,
                negative_prompt, style_settings, reference_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            story_id, reference_data['reference_type'], reference_data['reference_name'],
            reference_data['comfyui_prompt'], reference_data.get('negative_prompt'),
            json.dumps(reference_data.get('style_settings', {})),
            reference_data.get('reference_image_path')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_story_characters(self, story_id: str) -> List[Dict]:
        """Get all characters for a story"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM story_characters 
            WHERE story_id = ?
            ORDER BY importance_level DESC, created_at ASC
        ''', (story_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_story_locations(self, story_id: str) -> List[Dict]:
        """Get all locations for a story"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM story_locations 
            WHERE story_id = ?
            ORDER BY importance_level DESC, created_at ASC
        ''', (story_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_style_references(self, story_id: str, reference_type: str = None) -> List[Dict]:
        """Get style references for a story, optionally filtered by type"""
        cursor = self.conn.cursor()
        if reference_type:
            cursor.execute('''
                SELECT * FROM style_references 
                WHERE story_id = ? AND reference_type = ?
                ORDER BY quality_score DESC, created_at DESC
            ''', (story_id, reference_type))
        else:
            cursor.execute('''
                SELECT * FROM style_references 
                WHERE story_id = ?
                ORDER BY reference_type, quality_score DESC, created_at DESC
            ''', (story_id,))
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('style_settings'):
                result['style_settings'] = json.loads(result['style_settings'])
            results.append(result)
        return results
    
    def update_style_reference_usage(self, reference_id: int, quality_score: float = None):
        """Update style reference usage statistics"""
        cursor = self.conn.cursor()
        if quality_score is not None:
            cursor.execute('''
                UPDATE style_references 
                SET usage_count = usage_count + 1,
                    quality_score = ?,
                    last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (quality_score, reference_id))
        else:
            cursor.execute('''
                UPDATE style_references 
                SET usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (reference_id,))
        self.conn.commit()
    
    def get_character_for_shot_consistency(self, story_id: str, character_name: str = None) -> Optional[Dict]:
        """Get character data for shot consistency, returns most important character if name not specified"""
        cursor = self.conn.cursor()
        if character_name:
            cursor.execute('''
                SELECT * FROM story_characters 
                WHERE story_id = ? AND name LIKE ?
                ORDER BY importance_level DESC
                LIMIT 1
            ''', (story_id, f'%{character_name}%'))
        else:
            cursor.execute('''
                SELECT * FROM story_characters 
                WHERE story_id = ?
                ORDER BY importance_level DESC
                LIMIT 1
            ''', (story_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def get_location_for_shot_consistency(self, story_id: str, location_name: str = None) -> Optional[Dict]:
        """Get location data for shot consistency"""
        cursor = self.conn.cursor()
        if location_name:
            cursor.execute('''
                SELECT * FROM story_locations 
                WHERE story_id = ? AND (name LIKE ? OR description LIKE ?)
                ORDER BY importance_level DESC
                LIMIT 1
            ''', (story_id, f'%{location_name}%', f'%{location_name}%'))
        else:
            cursor.execute('''
                SELECT * FROM story_locations 
                WHERE story_id = ?
                ORDER BY importance_level DESC
                LIMIT 1
            ''', (story_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    
    # Settings and Presets Management Methods
    
    def save_setting(self, key: str, value: Any, setting_type: str = 'string'):
        """Save or update a user setting"""
        cursor = self.conn.cursor()
        
        # Convert value to string for storage
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
            setting_type = 'json'
        elif isinstance(value, bool):
            value_str = '1' if value else '0'
            setting_type = 'boolean'
        else:
            value_str = str(value)
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_settings 
            (setting_key, setting_value, setting_type, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (key, value_str, setting_type))
        self.conn.commit()
    
    def get_setting(self, key: str, default=None):
        """Get a user setting with optional default"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT setting_value, setting_type FROM user_settings 
            WHERE setting_key = ?
        ''', (key,))
        result = cursor.fetchone()
        
        if not result:
            return default
        
        value_str, setting_type = result['setting_value'], result['setting_type']
        
        # Convert back to appropriate type
        if setting_type == 'json':
            return json.loads(value_str)
        elif setting_type == 'boolean':
            return value_str == '1'
        elif setting_type == 'integer':
            return int(value_str)
        elif setting_type == 'float':
            return float(value_str)
        else:
            return value_str
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all user settings"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT setting_key, setting_value, setting_type FROM user_settings')
        
        settings = {}
        for row in cursor.fetchall():
            key, value_str, setting_type = row['setting_key'], row['setting_value'], row['setting_type']
            
            if setting_type == 'json':
                settings[key] = json.loads(value_str)
            elif setting_type == 'boolean':
                settings[key] = value_str == '1'
            elif setting_type == 'integer':
                settings[key] = int(value_str)
            elif setting_type == 'float':
                settings[key] = float(value_str)
            else:
                settings[key] = value_str
        
        return settings
    
    def save_preset(self, preset_name: str, display_name: str, description: str, preset_data: Dict, is_default: bool = False) -> int:
        """Save or update a system prompt preset"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO prompt_presets 
            (preset_name, display_name, description, preset_data, is_default, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (preset_name, display_name, description, json.dumps(preset_data), is_default))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_preset(self, preset_name: str) -> Optional[Dict]:
        """Get a specific preset"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM prompt_presets WHERE preset_name = ?
        ''', (preset_name,))
        result = cursor.fetchone()
        
        if result:
            preset = dict(result)
            preset['preset_data'] = json.loads(preset['preset_data'])
            return preset
        return None
    
    def get_all_presets(self) -> List[Dict]:
        """Get all presets"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM prompt_presets ORDER BY is_default DESC, display_name ASC
        ''')
        
        presets = []
        for row in cursor.fetchall():
            preset = dict(row)
            preset['preset_data'] = json.loads(preset['preset_data'])
            presets.append(preset)
        return presets
    
    def delete_preset(self, preset_name: str) -> bool:
        """Delete a preset"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM prompt_presets WHERE preset_name = ?', (preset_name,))
        deleted = cursor.rowcount > 0
        self.conn.commit()
        return deleted
    
    def set_default_preset(self, preset_name: str):
        """Set a preset as default (and unset others)"""
        cursor = self.conn.cursor()
        # Unset all defaults
        cursor.execute('UPDATE prompt_presets SET is_default = 0')
        # Set new default
        cursor.execute('UPDATE prompt_presets SET is_default = 1 WHERE preset_name = ?', (preset_name,))
        self.conn.commit()
    
    def get_default_preset(self) -> Optional[Dict]:
        """Get the default preset"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM prompt_presets WHERE is_default = 1 LIMIT 1
        ''')
        result = cursor.fetchone()
        
        if result:
            preset = dict(result)
            preset['preset_data'] = json.loads(preset['preset_data'])
            return preset
        return None
