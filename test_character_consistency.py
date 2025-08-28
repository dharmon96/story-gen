"""
Test script for character consistency pipeline
"""

import json
from database import DatabaseManager
from comfyui_manager import ComfyUIManager

def test_character_consistency_pipeline():
    """Test the complete character consistency pipeline"""
    print("Testing Character Consistency Pipeline...")
    
    # Initialize components
    db = DatabaseManager()
    comfyui = ComfyUIManager(db)
    
    # Test story ID
    test_story_id = "test_story_123"
    
    # Sample character data (as would be returned by character analyzer)
    characters = [
        {
            "name": "Sarah",
            "role": "protagonist", 
            "physical_description": "young woman with curly brown hair, wearing casual jeans and blue sweater",
            "age_range": "young adult",
            "clothing_style": "casual modern",
            "importance_level": 3,
            "personality_traits": "determined, optimistic"
        },
        {
            "name": "Marcus",
            "role": "supporting",
            "physical_description": "middle-aged man with gray beard, formal business attire",
            "age_range": "middle-aged", 
            "clothing_style": "formal business",
            "importance_level": 2
        }
    ]
    
    # Sample location data
    locations = [
        {
            "name": "Coffee Shop",
            "description": "cozy neighborhood coffee shop with warm lighting and vintage decor",
            "environment_type": "indoor",
            "time_of_day": "morning",
            "lighting_style": "warm natural",
            "weather_mood": "bright",
            "importance_level": 2
        }
    ]
    
    # Sample visual style
    visual_style = {
        "overall_mood": "warm and optimistic",
        "color_palette": "warm tones",
        "cinematography": "realistic",
        "era_setting": "modern"
    }
    
    print(f"Testing with {len(characters)} characters and {len(locations)} locations")
    
    # Test style card generation
    print("\n1. Testing style card generation...")
    try:
        style_results = comfyui.generate_style_cards(test_story_id, characters, locations, visual_style)
        print(f"[OK] Generated {style_results['total_generated']} style reference cards")
        print(f"   - Character cards: {len(style_results['character_cards'])}")
        print(f"   - Location cards: {len(style_results['location_cards'])}")
        print(f"   - Style cards: {len(style_results['style_cards'])}")
        
        if style_results['errors']:
            print(f"   [WARNING] Errors: {style_results['errors']}")
    except Exception as e:
        print(f"[ERROR] Style card generation failed: {e}")
        return False
    
    # Test shot consistency prompts
    print("\n2. Testing shot consistency prompts...")
    try:
        test_shot_descriptions = [
            "Sarah walks into the coffee shop looking worried",
            "Marcus looks up from his laptop as Sarah approaches",
            "Close-up of coffee cups on the wooden table"
        ]
        
        for i, shot_desc in enumerate(test_shot_descriptions, 1):
            consistency_prompts = comfyui.get_shot_consistency_prompts(test_story_id, shot_desc)
            print(f"   Shot {i}: '{shot_desc}'")
            print(f"   Character consistency: {consistency_prompts['character_consistency'][:50]}...")
            print(f"   Location consistency: {consistency_prompts['location_consistency'][:50]}...")
            
            # Test prompt enhancement
            base_prompt = "cinematic shot, professional lighting, 8k resolution"
            enhanced = comfyui.enhance_shot_prompt_with_consistency(base_prompt, consistency_prompts)
            print(f"   Enhanced prompt: {enhanced[:80]}...")
            print()
            
    except Exception as e:
        print(f"[ERROR] Shot consistency test failed: {e}")
        return False
    
    # Test database retrieval
    print("3. Testing database retrieval...")
    try:
        stored_characters = db.get_story_characters(test_story_id)
        stored_locations = db.get_story_locations(test_story_id)
        stored_references = db.get_style_references(test_story_id)
        
        print(f"[OK] Retrieved from database:")
        print(f"   - Characters: {len(stored_characters)}")
        print(f"   - Locations: {len(stored_locations)}")
        print(f"   - Style references: {len(stored_references)}")
        
        if stored_characters:
            print(f"   First character: {stored_characters[0]['name']} ({stored_characters[0]['role']})")
        
    except Exception as e:
        print(f"[ERROR] Database retrieval failed: {e}")
        return False
    
    # Test ComfyUI workflow data generation
    print("\n4. Testing ComfyUI workflow data...")
    try:
        workflow_data = comfyui.get_comfyui_workflow_data(test_story_id)
        print(f"[OK] Workflow data generated:")
        print(f"   - Workflow ready: {workflow_data['workflow_ready']}")
        print(f"   - Total references: {workflow_data['total_references']}")
        print(f"   - Characters: {len(workflow_data['characters'])}")
        print(f"   - Locations: {len(workflow_data['locations'])}")
        
    except Exception as e:
        print(f"[ERROR] Workflow data generation failed: {e}")
        return False
    
    print("\n[OK] Character consistency pipeline test completed successfully!")
    print("\nNext steps:")
    print("- Run a full story generation to test the complete integration")
    print("- Verify that the progress popup displays style references correctly")
    print("- Test character consistency in actual shot prompts")
    
    return True

if __name__ == "__main__":
    try:
        success = test_character_consistency_pipeline()
        if success:
            print("\n[SUCCESS] All tests passed! Character consistency system is ready.")
        else:
            print("\n[FAILED] Some tests failed. Check the output above for details.")
    except Exception as e:
        print(f"\n[CRASH] Test script failed with error: {e}")
        import traceback
        traceback.print_exc()