"""
Simple Test Script for Research System Integration
Tests all components with plain ASCII output
"""

import sys
import os
import traceback
from datetime import date

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_extensions():
    """Test research database schema"""
    print("Testing database schema extensions...")
    
    try:
        from database import init_database, DatabaseManager
        
        # Initialize database with new tables
        init_database()
        print("  [OK] Database initialized successfully")
        
        # Test database manager research methods
        db = DatabaseManager()
        
        # Test create research session
        session_id = db.create_research_session(['tiktok', 'instagram', 'youtube'])
        print(f"  [OK] Created research session: {session_id}")
        
        # Test save trending content
        sample_content = {
            'platform': 'tiktok',
            'content_url': 'https://test.com/video1',
            'title': 'Test AI Comedy Video',
            'description': 'Funny AI-generated comedy sketch',
            'hashtags': ['#ai', '#comedy', '#funny'],
            'view_count': 50000,
            'like_count': 5000,
            'comment_count': 500,
            'share_count': 200,
            'engagement_rate': 0.08,
            'ai_keywords': ['ai', 'comedy', 'generated'],
            'content_type': 'comedy',
            'genre': 'Comedy',
            'duration': 30,
            'created_date': date.today()
        }
        
        content_id = db.save_trending_content(session_id, sample_content)
        print(f"  [OK] Saved trending content: {content_id}")
        
        # Test trend analysis
        trend_data = {
            'category': 'ai-comedy',
            'trend_score': 0.85,
            'growth_rate': 15.5,
            'platforms': ['tiktok', 'youtube'],
            'total_occurrences': 10,
            'avg_engagement': 0.08
        }
        
        db.save_trend_analysis('ai comedy', trend_data)
        print("  [OK] Saved trend analysis")
        
        # Test research prompt
        prompt_data = {
            'keyword': 'ai comedy',
            'genre': 'Comedy',
            'expected_performance': 0.85
        }
        
        prompt_id = db.save_research_prompt('An AI comedian tells jokes but gets everything wrong', prompt_data)
        print(f"  [OK] Saved research prompt: {prompt_id}")
        
        # Update session
        stats = {
            'total_found': 1,
            'ai_found': 1,
            'keywords': ['ai comedy']
        }
        db.update_research_session(session_id, 'completed', stats)
        print("  [OK] Updated research session")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] Database test failed: {e}")
        return False

def test_api_modules():
    """Test that API modules can be imported"""
    print("Testing API module imports...")
    
    try:
        from social_media_apis import SocialMediaManager
        print("  [OK] Social media APIs imported")
        
        from research_engine import ResearchEngine
        print("  [OK] Research engine imported")
        
        from research_tab import ResearchTab
        print("  [OK] Research tab imported")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Module import failed: {e}")
        return False

def test_story_integration():
    """Test story generator integration"""
    print("Testing story generator integration...")
    
    try:
        from database import DatabaseManager
        from story_generator import StoryGenerator
        from ollama_manager import OllamaManager
        
        db = DatabaseManager()
        ollama = OllamaManager()
        generator = StoryGenerator(ollama, db)
        
        # Test method existence
        assert hasattr(generator, 'get_trending_prompt'), "Missing get_trending_prompt method"
        assert hasattr(generator, 'enhance_prompt_with_trends'), "Missing enhance_prompt_with_trends method"
        assert hasattr(generator, 'select_optimal_prompt'), "Missing select_optimal_prompt method"
        
        print("  [OK] All research methods exist in StoryGenerator")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] Story integration test failed: {e}")
        return False

def test_gui_integration():
    """Test GUI integration"""
    print("Testing GUI integration...")
    
    try:
        # Test import of main GUI with research tab
        from gui import FilmGeneratorApp
        print("  [OK] Main GUI imports research components")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] GUI integration failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("Research System Integration Test")
    print("=" * 50)
    
    tests = [
        ("Database Extensions", test_database_extensions),
        ("API Modules", test_api_modules), 
        ("Story Integration", test_story_integration),
        ("GUI Integration", test_gui_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 30)
        
        try:
            success = test_func()
            if success:
                passed += 1
                print(f"  Result: PASS")
            else:
                print(f"  Result: FAIL")
        except Exception as e:
            print(f"  Result: CRASH - {e}")
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("All tests passed! Research system is integrated.")
        print("\nNext steps:")
        print("1. Run the main application: python main.py")
        print("2. Go to the Research tab")
        print("3. Configure API keys (optional)")
        print("4. Click 'Start Research Now' to test")
        print("5. Generate stories with trending prompts")
    else:
        print(f"Some tests failed. Fix issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    run_tests()