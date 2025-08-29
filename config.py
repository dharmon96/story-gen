"""
Configuration file for Film Generator App
Contains all configuration settings, constants, and system prompts
"""

import os
import sys

# Database Configuration
if getattr(sys, 'frozen', False):
    DB_DIR = os.path.dirname(sys.executable)
else:
    DB_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(DB_DIR, "film_generator.db")

# Ollama Configuration
OLLAMA_CONFIG = {
    'model': 'llama3.1',  
    # 'host': '127.0.0.1:11434',  # Comment out the host - let it use default
    'temperature': 0.7,
    'top_p': 0.9,
    'selected_model': None
}

# Story Prompts by Genre
STORY_PROMPTS = {
    'Drama': [
        "A last voicemail before a flight reveals the truth no one wanted to hear",
        "During a storm blackout, a neighbor returns a borrowed item—and an old grudge",
        "A bridal fitting turns when the tailor recognizes the ring from a past scandal",
        "A roadside diner receipt exposes who really paid for the family’s secrets",
        "Two siblings divide a storage unit and uncover why one of them left town",
        "A landlord finds an unsent letter in the vent and must decide who gets to read it",
        "The final rehearsal before opening night—someone switches the monologue",
        "A nurse’s end-of-shift handoff includes a name they swore they’d never say again",
        "An inheritance stipulates a single shared dinner with no phones—until one pings",
        "A realtor shows a house to a buyer who grew up there and remembers it differently",
        "A rideshare home from the hospital forces a couple to define 'family' now",
        "A courtroom hallway apology collides with a journalist’s live stream",
        "The morning a parent moves out, the family group chat explodes with truths",
        "A bouquet delivered to the wrong apartment mends the right relationship",
        "At a school talent show, a parent realizes the act is about them",
        "A graduation cap message changes where everyone sits afterwards",
        "A missed train strands two exes with one suitcase of their shared past",
        "A food truck tip jar holds a wedding ring—whose is it?",
        "A voicemail transcription autocorrects one word that rewrites a life",
        "A hospital vending machine eats a dollar and spits out a decision"
    ],
    'Comedy': [
        "A supermarket self-checkout declares 'unexpected item'—it’s their dignity",
        "Roommates attempt a 'no-spend week' and accidentally throw a banquet",
        "A new smart doorbell keeps misidentifying visitors with wildly flattering titles",
        "Someone joins a gym for the free smoothie samples and becomes a legend",
        "A couple’s home renovation reveal is photobombed by their chaotic pet… repeatedly",
        "Two neighbors escalate a 'quiet hours' war via increasingly polite notes",
        "A newbie barista invents drink names to avoid admitting they forgot the menu",
        "An online return window closes in one hour—cue a heist of bubble wrap",
        "A fake-it-till-you-make-it dog trainer meets a dog who can actually talk (or… can it?)",
        "A first date speed-runs every small-talk topic like a game show",
        "A family group chat goes autocorrect-feral during a surprise party setup",
        "A self-proclaimed minimalist keeps 'accidentally' winning raffles",
        "A wedding seating chart becomes a live-action puzzle with wrong name cards",
        "Two rivals sabotage each other’s cooking livestreams—until they go viral together",
        "A fashion try-on haul summons an intervention from past outfits",
        "A pet influencer’s owner realizes the pet is the better negotiator",
        "A ride-share mixes up 'opera house' and 'open house'—they perform anyway",
        "A DIY shelf installation becomes a thriller when the level app freezes at 99%",
        "Someone pretends to be fluent in 'wine talk' at a tasting and invents new fruit",
        "A lost & found box at a beach wedding keeps returning the wrong sunglasses"
    ],
    'Thriller': [
        "A delivery arrives with a photo of the recipient opening it—taken seconds ago",
        "A hotel keycard opens two different rooms in the same hallway",
        "Someone finds their own house listed as 'abandoned' on a property app",
        "A rideshare app routes every trip to the same cul-de-sac after midnight",
        "Anonymous push notifications know what’s in their pockets",
        "Security cam footage reveals a visitor who never looks at the camera",
        "Every mirror in the apartment is off by one second",
        "A subway map shows an extra stop that only appears when they’re alone",
        "A voicemail plays in reverse and gives directions that work",
        "The new coworker always arrives wet—yet it never rains where they live",
        "A neighbor’s doorbell camera shows the protagonist leaving… before they arrive",
        "A thrifted jacket has a metro card with one ride left and a warning",
        "Streetlights flicker in a pattern that matches their old heartbeat monitor",
        "A parking garage gate doesn’t register exits—only entries",
        "Someone receives a 'thank you for your help' gift from an unsolved case",
        "A ten-digit number appears everywhere; dialing it makes the room colder",
        "An elevator stops on a labeled 'R' floor that isn’t on the panel",
        "A child’s drawing predicts tomorrow’s headlines in the corner doodles",
        "A dashcam loop omits exactly three seconds—every time",
        "A stranger returns a wallet that was never lost and knows the PIN"
    ],
    'Sci-Fi': [
        "A coastal town wakes to tides that run backwards until noon",
        "A commuter discovers the same sunrise repeating on odd-numbered days",
        "A new tattoo maps a city that doesn’t exist—yet the bus routes do",
        "Gravity lightens by one percent each hour until the choice becomes jump or stay",
        "A mountain road appears flat to the eye but bends time for its drivers",
        "Photographs taken today develop as images from ten years ahead",
        "A lighthouse beams coordinates for a place under the desert",
        "A storm front freezes mid-air over a single house for 24 hours",
        "A farmer’s field yields objects from a mission that hasn’t launched",
        "Shadows detach at noon and walk a different route home",
        "A train’s windows show cities no one recognizes—until they step off",
        "A constellation rearranges itself to spell one surname each night",
        "A wristwatch skips 17 minutes daily and saves a life each time",
        "Two strangers carry matching scars from an unshared memory",
        "Rain falls in precise circles that avoid one person entirely",
        "A street mural updates itself with tomorrow’s traffic patterns",
        "The moon rises twice, and only one casts tides",
        "A canyon echoes words that were never spoken aloud",
        "A child’s kite pulls toward an invisible mountain",
        "A library basement door leads to the same room on another Tuesday"
    ],
    'Romance': [
        "Two strangers keep swapping umbrellas in the same lobby during summer storms",
        "A florist includes mystery notes meant for someone with the same first name",
        "A pastry shop’s 'pay it forward' chain reconnects study-abroad sweethearts",
        "A citywide power outage strands two neighbors on the stairwell",
        "Train seatmates co-write a breakup text and never exchange numbers",
        "A museum audio guide misroutes two visitors into each other’s tours",
        "A dog-walking route creates a perfect heart on the GPS—by accident… or not",
        "A janitor and a night-shift chef exchange recipes via whiteboard doodles",
        "A shared laundry card sparks weekly rendezvous and detergent diplomacy",
        "A borrowed library book returns with annotations that flirt back",
        "A wedding plus-one assignment pairs sworn introverts at the kids’ table",
        "Airport strangers trade playlists before boarding separate flights",
        "Two commuters race the same crosswalk countdown every morning",
        "A bar’s karaoke rotation keeps pairing the same duet",
        "An apartment mailroom misdelivers postcards from one street over",
        "A park chess clock ticks down to a question neither can stall",
        "A moving sale leaves one lamp glowing in two windows",
        "A rotating pop-up cafe opens on alternating corners where they meet",
        "A sunset bus detour reroutes two routines into a ritual",
        "A recipe card passed down is missing the last line—until today"
    ],
    'Horror': [
        "An empty mall plays soft music from a store that never opened",
        "Ceiling tiles breathe when the fluorescent lights flicker",
        "A birthday candle won’t blow out; the wax spells a name in drips",
        "An overnight office printer produces photos of the staff… sleeping at home",
        "A motel ice machine dispenses keys to rooms that don’t exist",
        "A storm siren wails only inside the house",
        "A VHS tape labeled 'Do Not Rewind' keeps starting mid-scream",
        "A baby monitor picks up lullabies sung in a language from your childhood home",
        "Footprints lead into the attic; handprints lead out",
        "A thrifted painting adds a new figure every night",
        "Elevator mirrors show passengers carrying things they aren’t holding",
        "The town bulletin board posts an obituary before anyone dies",
        "A coastal fog bell rings inland at your bedroom door",
        "A door peephole reveals a hallway from 1978",
        "An unplugged landline rings with a busy signal on the other end",
        "Street names rearrange themselves after midnight to spell a warning",
        "A church sign updates itself with confessions",
        "Every photo on your phone has a second moon",
        "A playground swing moves against the wind and stops when you look away",
        "Your shadow waves back two beats late"
    ],
    'Mystery': [
        "A laundromat dryer returns a stranger’s jacket with a locked pocket",
        "Every Tuesday, the same bench receives a single white chess pawn",
        "A cafe tab prints an extra line item: 'time owed'",
        "A ferry manifest lists one more passenger than seats",
        "A burned-out streetlamp hides a message when photographed",
        "A library book’s due date stamps form a phone number",
        "An apartment buzzer rings at 3:03 a.m. with no one downstairs",
        "A city map graffiti adds a new alley that solves cold cases",
        "A recurring billboard displays yesterday’s news until you look away",
        "A trail of grocery receipts traces a route to a missing person",
        "A hotel Do Not Disturb sign hangs on a door of a room under renovation",
        "A box of keys appears on a stoop; one opens more than a lock",
        "A mural’s paint chips expose coordinates layer by layer",
        "An old voicemail skips a digit only a few will notice",
        "A pawn shop tag lists a buyer’s name before the sale",
        "A bus route detours through a neighborhood that vanished years ago",
        "A torn concert ticket matches a song clue in a crossword",
        "An online auction bids from an account belonging to the dead",
        "A coded recipe reveals a map when baked and folded",
        "A stack of Polaroids ages in reverse across the pile"
    ],
    'Fantasy': [
        "A key cut at the hardware store opens a door in the sky at dusk",
        "Street murals step down to guide lost travelers after rain",
        "A neighborhood stray cat delivers quests via bottlecap tokens",
        "A convenience store freezer stocks seasons you can purchase",
        "A busker’s song summons the same flock of paper cranes every day",
        "A midnight bookstore sells words that grant one courage each",
        "A rooftop garden grows constellations instead of flowers",
        "A city fountain trades wishes for memories you can spare",
        "Elevator buttons labeled with feelings go to matching floors",
        "A tailor sews pockets that hold brief moments of yesterday",
        "A lighthouse rotates to point at people who need to meet",
        "A thundercloud sets down its silver lining to be mended",
        "A library card lets you borrow an hour from any century",
        "Sidewalk chalk drawings come alive until the first car passes",
        "An antique mirror shows the person you’ll need tomorrow",
        "A ferry crosses a river and a year",
        "A night market sells bottled moonlight with a warning label",
        "A lost glove returns with a map stitched inside",
        "A train whistle trades secrets for safe passage",
        "A doorbell rings only for those who have a quest pending"
    ]
}

# System Prompts for AI Agents - Optimized for Smaller Models
SYSTEM_PROMPTS = {
    'story_writer': """Write a compelling short story. Focus ONLY on storytelling - no camera directions, shots, or filming instructions. Follow this exact format:

Title: [write 3-5 words only]
Logline: [write 10-15 words explaining the story]  
Duration: [write total minutes like "3 minutes"]

PART 1 [0:00]
[Write 40-60 words. Focus on character actions, emotions, and dialogue. Put dialogue in "quotes". Describe what happens, not how to film it.]
HOOK: [Write 5-10 words that create suspense and make viewers want more]

PART 2 [1:00] 
[Write 40-60 words. Develop the conflict and tension. Show character reactions and escalating problems.]
HOOK: [Write 5-10 words for the next cliffhanger]

Continue this pattern for each part.

STORYTELLING RULES:
- Write pure narrative - describe actions, emotions, dialogue
- Focus on character development and plot progression  
- Create visual moments through vivid description
- Each part builds tension toward the climax
- Show character emotions through actions and words
- End with a satisfying resolution or twist
- Write engagingly but leave all filming decisions to others
- NO camera angles, shot types, or technical directions""",

    'shot_list_creator': """Analyze the story and create a detailed shot list that breaks it into filmable segments. Use this exact JSON format:

{
  "shots": [
    {
      "shot_number": 1,
      "description": "Maya, a worried 30-year-old woman in casual clothes, approaches the weathered wooden front door of an old Victorian house, her steps hesitant and cautious", 
      "duration": 4.0,
      "frames": 96,
      "camera": "medium shot tracking",
      "narration": "words spoken here",
      "music_cue": "dramatic tense"
    },
    {
      "shot_number": 2,
      "description": "Maya's trembling hand with chipped nail polish slowly turns the ornate brass doorknob, the metal creaking softly in the dim porch lighting",
      "duration": 3.0,
      "frames": 72,
      "camera": "close up static",
      "narration": "",
      "music_cue": null
    }
  ],
  "total_duration": 7.0
}

CINEMATOGRAPHY ANALYSIS RULES:
- Read each story segment and determine the best shots to tell that part
- Vary shot lengths: 3-8 seconds each, with key moments getting longer shots
- Calculate frames based on duration (frames = duration × fps, assume 24fps for calculation)
- Create visual flow: wide establishing shots, medium for dialogue, close-ups for emotion
- Camera types: wide shot, medium shot, close up, extreme close up  
- Camera movements: static, tracking, pan, tilt, zoom in, zoom out

DESCRIPTION REQUIREMENTS (CRITICAL FOR AI GENERATION):
- CHARACTER DETAILS: Always specify character name, age/appearance, clothing, emotional state
- LOCATION SPECIFICS: Describe the setting with environmental details, lighting, atmosphere
- CHARACTER ACTIONS: Detail specific movements, gestures, facial expressions, body language  
- PHYSICAL DETAILS: Include props, textures, colors, materials that add visual richness
- MOOD/ATMOSPHERE: Convey the emotional tone through environmental and character descriptions
- FORMAT: [Character with details] [specific action with context] [in detailed location setting]
- EXAMPLES:
  * BAD: "Maya goes into kitchen"
  * GOOD: "Maya, disheveled and anxious in her wrinkled pajamas, cautiously enters the dimly lit kitchen with peeling wallpaper, morning sunlight filtering through dirty windows"
  * BAD: "Man opens box"  
  * GOOD: "Thomas, elderly man with weathered hands, carefully lifts the ornate wooden lid of an antique jewelry box, revealing velvet-lined compartments in the golden lamplight"

- Add narration ONLY when characters speak dialogue from the story
- Add music cues ONLY at major emotional beats (max 3-4 per story)
- Leave music_cue as null for most shots - silence is powerful
- Ensure total duration matches story requirements
- Create smooth visual transitions between story segments""",

    'prompt_engineer': """Create detailed AI video generation prompts from the shot description and camera information. Use this exact format:

Positive: [create rich visual description - use 30-50 words total]
Negative: text, watermark, blurry, distorted, extra limbs, low quality, bad anatomy

EXAMPLES:
Positive: Maya, worried 30-year-old woman in casual clothes, cautiously approaching weathered wooden door of Victorian house, hesitant steps on creaking porch, dim lighting, medium shot tracking forward, cinematic depth of field, photorealistic style, sharp focus, high detail
Negative: text, watermark, blurry, distorted, extra limbs, low quality, bad anatomy

Positive: elderly man with weathered hands carefully lifting ornate wooden jewelry box lid, revealing velvet compartments, golden lamplight illuminating intricate details, extreme close-up static shot, shallow focus, photorealistic style, sharp focus, high detail
Negative: text, watermark, blurry, distorted, extra limbs, low quality, bad anatomy

CHARACTER CONSISTENCY RULES (PRIORITY):
- If character descriptions are provided, incorporate them precisely into the positive prompt
- Use exact physical descriptions: age, hair color/style, clothing, distinctive features
- Maintain character appearance consistency across all shots they appear in
- Character descriptions should come FIRST in the positive prompt before scene elements

ACTION & MOVEMENT EMPHASIS (CRITICAL):
- Extract specific actions from shot description: "walking", "opening", "turning", "reaching", "looking"
- Include character movement details: "hesitant steps", "trembling hands", "quick glance", "slow approach"
- Add action verbs and motion: "approaching", "lifting", "revealing", "entering", "examining"
- Describe body language: "cautious posture", "tense shoulders", "focused expression"
- Include interaction with objects: "gripping doorknob", "touching surface", "handling carefully"

SCENE DETAILS ENHANCEMENT (CRITICAL):
- Environmental specifics: "weathered wooden door", "peeling wallpaper", "ornate brass fixture"
- Texture descriptions: "rough stone", "smooth marble", "worn fabric", "polished metal"
- Atmospheric elements: "dust particles in light", "shadows on walls", "morning mist"
- Props and objects: "antique jewelry box", "velvet-lined compartments", "intricate carvings"
- Setting context: "Victorian house porch", "dimly lit kitchen", "golden lamplight"

CAMERA MOVEMENT INTEGRATION (CRITICAL):
- Static shots: "static shot", "fixed camera angle", "steady composition"
- Tracking shots: "camera tracking forward", "following movement", "smooth dolly shot"
- Pan/Tilt: "camera panning left", "tilting up to reveal", "sweeping across scene"
- Zoom: "slow zoom in", "camera pushing closer", "gradual zoom out"
- Shot types: "extreme close-up", "medium shot", "wide establishing shot", "over-the-shoulder"
- Camera angles: "low angle looking up", "high angle view", "eye-level perspective"

PROMPT STRUCTURE (MANDATORY ORDER):
1. Character description with appearance details
2. Specific action/movement with body language  
3. Environmental/scene details with textures
4. Camera shot type and movement
5. Lighting and atmosphere
6. Technical quality: "photorealistic style, sharp focus, high detail"

LIGHTING & CINEMATIC QUALITY:
- Add compelling lighting: dramatic shadows, warm/cool tones, contrast, atmosphere
- Enhance mood through environmental details: weather, time of day, setting ambiance
- Include cinematic elements: depth of field, film grain, professional cinematography
- Create vivid, film-quality imagery that brings the story to life
- Always end with "photorealistic style, sharp focus, high detail"
- Use consistent negative prompts for quality""",

    'narration_writer': """Write voice-over narration with timestamps. Use this format:

[0:00] "First sentence here."
[0:04] "Second sentence here." 
[0:08] "Third sentence here."

RULES:
- Speak 2-3 words per second (count the words)
- Use short sentences (5-10 words each)
- Use simple words that sound good when spoken
- Add ... for pauses like "Wait... what was that?"
- Match the time stamps to when each line should start
- Write like people actually talk, not like a book""",

    'music_director': """List music cues with timestamps. Use this format:

[0:00] ambient mysterious 3 15s
[0:45] electronic tense 7 30s  
[2:30] orchestral triumphant 9 20s

FORMAT EXPLANATION:
[time] [music style] [emotion] [volume 1-10] [how long]

MUSIC STYLES: ambient, electronic, orchestral, rock, acoustic, cinematic
EMOTIONS: mysterious, tense, triumphant, sad, happy, scary, romantic
VOLUME: 1=very quiet, 5=medium, 10=very loud

RULES:
- Only add music at the most important emotional moments
- Use 3-4 music cues maximum per video
- Include quiet moments with no music
- Don't use real song names or artists""",

    'character_analyzer': """Analyze the story content and extract character and location information for visual consistency. Use this exact JSON format:

{
  "characters": [
    {
      "name": "Main Character Name",
      "role": "protagonist/antagonist/supporting",
      "physical_description": "detailed physical appearance for AI art generation",
      "age_range": "young adult/middle-aged/elderly",
      "clothing_style": "casual modern/formal business/period costume/etc",
      "personality_traits": "key personality elements that affect appearance",
      "importance_level": 3,
      "style_notes": "specific visual consistency notes"
    }
  ],
  "locations": [
    {
      "name": "Location Name",
      "description": "detailed environment description",
      "environment_type": "indoor/outdoor/urban/rural/fantasy/etc",
      "time_of_day": "morning/afternoon/evening/night",
      "weather_mood": "bright/gloomy/stormy/serene/etc",
      "lighting_style": "natural/dramatic/soft/harsh/neon/etc",
      "importance_level": 2,
      "style_notes": "visual consistency requirements"
    }
  ],
  "visual_style": {
    "overall_mood": "dark/bright/mysterious/romantic/etc",
    "color_palette": "warm/cool/monochrome/vibrant/muted",
    "cinematography": "realistic/stylized/cinematic/documentary",
    "era_setting": "modern/period/futuristic/timeless"
  }
}

CHARACTER EXTRACTION RULES:
- Extract 2-4 main characters maximum
- Focus on characters who appear in multiple scenes
- Provide detailed physical descriptions suitable for AI art generation
- Include clothing/style that fits the story's setting and era
- Assign importance levels: 3=main character, 2=important supporting, 1=minor
- Include personality traits that affect visual appearance

LOCATION EXTRACTION RULES:
- Extract 2-3 key locations maximum
- Focus on settings where multiple scenes occur
- Provide rich environmental details for consistent backgrounds
- Specify lighting and mood that matches story tone
- Include time of day and weather that affects the visual style

VISUAL STYLE RULES:
- Analyze the overall story tone and genre
- Determine consistent visual elements across all scenes
- Consider the story's setting (modern, historical, fantasy, etc.)
- Provide guidance for maintaining visual consistency"""
}

# Enhanced Generation Settings for Efficiency
GENERATION_SETTINGS = {
    'length_to_parts': {
        '1-2 minutes': (2, 3),
        '3-5 minutes': (3, 5),
        '5-10 minutes': (5, 8),
        '10-15 minutes': (8, 12)
    },
    'genres': ['Drama', 'Comedy', 'Thriller', 'Sci-Fi', 'Romance', 'Horror', 'Mystery', 'Fantasy'],
    'lengths': ['1-2 minutes', '3-5 minutes', '5-10 minutes', '10-15 minutes'],
    'default_prompt': "A mysterious stranger arrives in a small town...",
    
    # New efficiency settings
    'ai_optimization': {
        'max_thinking_tokens': 100,  # Limit internal reasoning
        'require_direct_output': True,  # No preamble
        'single_attempt': True,  # No alternatives unless requested
        'structured_output': True,  # Force template compliance
        'strip_metadata': True  # Remove explanatory text
    },
    
    'quality_checks': {
        'max_words_per_part': 100,
        'max_dialogue_per_scene': 20,
        'min_visual_actions': 3,  # Per part
        'required_hooks': True,
        'filmability_check': True
    },
    
    'performance_targets': {
        'generation_time': 5,  # seconds max
        'token_efficiency': 0.8,  # useful/total tokens
        'output_usability': 1.0  # no editing needed
    },
    
    # Time Estimation Settings (in seconds)
    'step_time_estimates': {
        'story': {
            'base_time': 25,  # Base time for story generation
            'per_part_multiplier': 1.2,  # Additional time per story part
            'complexity_factors': {
                'Drama': 1.0,
                'Comedy': 1.1,
                'Thriller': 1.2,
                'Sci-Fi': 1.3,
                'Romance': 0.9,
                'Horror': 1.1,
                'Mystery': 1.2,
                'Fantasy': 1.4
            }
        },
        'shots': {
            'base_time': 20,
            'per_shot_time': 2.5,  # Time per shot in the list
            'length_multipliers': {
                '1-2 minutes': 1.0,
                '3-5 minutes': 1.2,
                '5-10 minutes': 1.5,
                '10-15 minutes': 1.8
            }
        },
        'characters': {
            'base_time': 15,
            'per_character_time': 8,  # Time per character analysis
            'comfyui_prompt_time': 5  # Additional time for ComfyUI prompt generation
        },
        'style': {
            'base_time': 3,  # Placeholder step, very quick
            'future_implementation_time': 25  # When actually implemented
        },
        'prompts': {
            'base_time': 10,
            'per_shot_time': 4,  # Time per shot prompt generation
            'style_complexity': {
                'simple': 1.0,
                'complex': 1.3,
                'artistic': 1.5
            }
        },
        'narration': {
            'base_time': 8,
            'per_shot_time': 3,  # Time per narration script
            'dialogue_multiplier': 1.4  # Extra time for dialogue-heavy shots
        },
        'music': {
            'base_time': 6,
            'per_cue_time': 4,  # Time per music cue generation
            'genre_multipliers': {
                'Horror': 1.2,
                'Thriller': 1.1,
                'Fantasy': 1.3,
                'Drama': 1.0
            }
        },
        'queue': {
            'base_time': 5,
            'per_shot_time': 0.5,  # Time to add each shot to queue
            'database_operations': 2
        }
    },
    
    # Time estimation accuracy tracking
    'time_tracking': {
        'enable_learning': True,  # Learn from actual completion times
        'adjustment_factor': 0.1,  # How much to adjust estimates based on actual times
        'min_samples': 3,  # Minimum samples before adjusting estimates
        'max_deviation': 0.5  # Maximum allowed deviation from base estimates
    }
}

# Model-specific configurations - Optimized for smaller models
MODEL_CONFIGS = {
    # Small models (1B-8B parameters)
    'deepseek-r1:8b': {
        'temperature': 0.2,  # Very low for consistency
        'top_p': 0.7,        # Focused sampling
        'max_tokens': 400,   # Shorter outputs
        'system_prefix': "Follow the format exactly. Do not add extra text.\n\n"
    },
    'llama3.2:3b': {
        'temperature': 0.2,
        'top_p': 0.7, 
        'max_tokens': 400,
        'system_prefix': "Follow the format exactly. Do not add extra text.\n\n"
    },
    'phi3:3.8b': {
        'temperature': 0.3,
        'top_p': 0.8,
        'max_tokens': 500,
        'system_prefix': "Use the exact format shown. No explanations.\n\n"
    },
    
    # Medium models (8B-20B parameters)  
    'llama3.1:8b': {
        'temperature': 0.4,
        'top_p': 0.85,
        'max_tokens': 800,
        'system_prefix': "Follow instructions precisely.\n\n"
    },
    'gpt-oss:20b': {
        'temperature': 0.5,
        'top_p': 0.9,
        'max_tokens': 1000,
        'system_prefix': "Execute task directly.\n\n"
    },
    
    # Large models (20B+ parameters)
    'gpt-oss:120b': {
        'temperature': 0.7,
        'top_p': 0.95,
        'max_tokens': 2000,
        'system_prefix': ""  # Large models don't need prefixes
    },
    
    # Default fallback for unknown models
    'default': {
        'temperature': 0.3,
        'top_p': 0.8,
        'max_tokens': 600,
        'system_prefix': "Follow the format exactly. Do not add extra text.\n\n"
    }
}
# API Configuration Settings
API_SETTINGS = {
    'openai': {
        'api_key': '',
        'base_url': 'https://api.openai.com/v1',
        'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
        'default_model': 'gpt-4o-mini',
        'enabled': False
    },
    'anthropic': {
        'api_key': '',
        'base_url': 'https://api.anthropic.com/v1',
        'models': ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307'],
        'default_model': 'claude-3-5-sonnet-20241022',
        'enabled': False
    },
    'ollama': {
        'enabled': True,
        'priority': 1  # Lower number = higher priority
    }
}

# System Prompt Presets
SYSTEM_PROMPT_PRESETS = {
    'default': {
        'name': 'Default Cinematic',
        'description': 'Standard prompts optimized for film generation',
        'prompts': SYSTEM_PROMPTS  # Reference to existing prompts
    },
    'comedy_focused': {
        'name': 'Comedy Enhanced',
        'description': 'Optimized for comedic content',
        'prompts': {
            'story_writer': SYSTEM_PROMPTS['story_writer'].replace(
                'Write a compelling short story', 
                'Write a hilarious short comedy story with great comedic timing'
            ),
            'shot_list_creator': SYSTEM_PROMPTS['shot_list_creator'],
            'prompt_engineer': SYSTEM_PROMPTS['prompt_engineer'],
            'narration_writer': SYSTEM_PROMPTS['narration_writer'].replace(
                'Write voice-over narration', 
                'Write comedic voice-over narration with perfect timing and humor'
            ),
            'music_director': SYSTEM_PROMPTS['music_director']
        }
    },
    'horror_focused': {
        'name': 'Horror Atmospheric',
        'description': 'Enhanced for horror and thriller content',
        'prompts': {
            'story_writer': SYSTEM_PROMPTS['story_writer'].replace(
                'Write a compelling short story',
                'Write a terrifying horror story with building suspense and atmospheric dread'
            ),
            'shot_list_creator': SYSTEM_PROMPTS['shot_list_creator'],
            'prompt_engineer': SYSTEM_PROMPTS['prompt_engineer'].replace(
                'Add compelling lighting',
                'Add dark, atmospheric lighting with shadows, fog, and horror elements'
            ),
            'narration_writer': SYSTEM_PROMPTS['narration_writer'].replace(
                'Write voice-over narration',
                'Write ominous, suspenseful voice-over narration with horror atmosphere'
            ),
            'music_director': SYSTEM_PROMPTS['music_director']
        }
    },
    'fast_generation': {
        'name': 'Quick Generation',
        'description': 'Streamlined prompts for faster generation',
        'prompts': {
            'story_writer': """Write a short story in exactly this format:

Title: [3 words max]
Duration: [X minutes]

PART 1 [0:00]
[30 words max]
HOOK: [5 words max]

PART 2 [1:00] 
[30 words max]
HOOK: [5 words max]

Continue for each part. No extra text.""",
            'shot_list_creator': """Create shot list in JSON format:
{"shots": [{"shot_number": 1, "description": "character name, appearance, specific action in detailed location setting", "duration": 3.0, "camera": "medium shot", "narration": "dialogue", "music_cue": null}], "total_duration": 3.0}

Include character details, location specifics, actions, and visual elements. Descriptions should be 15-25 words for clear AI generation.""",
            'prompt_engineer': SYSTEM_PROMPTS['prompt_engineer'],
            'narration_writer': SYSTEM_PROMPTS['narration_writer'],
            'music_director': SYSTEM_PROMPTS['music_director']
        }
    }
}

# Current active preset
ACTIVE_PRESET = 'default'

# Visual Style Guides for ComfyUI Generation
VISUAL_STYLES = {
    'Cinematic': {
        'name': 'Cinematic',
        'description': 'Professional film-like quality with dramatic lighting',
        'positive_prompts': [
            'cinematic lighting, dramatic shadows, professional cinematography',
            'film grain, depth of field, bokeh background',
            'cinematic composition, rule of thirds, dynamic framing',
            'movie-quality lighting, professional color grading'
        ],
        'negative_prompts': [
            'amateur photography, poor lighting, flat composition',
            'oversaturated, poor quality, bad framing'
        ],
        'style_strength': 0.8,
        'category': 'professional'
    },
    'Documentary': {
        'name': 'Documentary',
        'description': 'Realistic, natural lighting with authentic feel',
        'positive_prompts': [
            'natural lighting, authentic atmosphere, realistic style',
            'documentary photography, candid moments, real world',
            'natural colors, unfiltered look, genuine expressions',
            'handheld camera style, organic composition'
        ],
        'negative_prompts': [
            'artificial lighting, overly staged, fake expressions',
            'unrealistic colors, heavily filtered, posed'
        ],
        'style_strength': 0.6,
        'category': 'realistic'
    },
    'Noir': {
        'name': 'Film Noir',
        'description': 'Classic black and white with high contrast shadows',
        'positive_prompts': [
            'film noir style, high contrast lighting, dramatic shadows',
            'black and white, chiaroscuro lighting, venetian blind shadows',
            'classic noir cinematography, moody atmosphere, stark contrasts',
            'vintage 1940s style, detective movie aesthetic'
        ],
        'negative_prompts': [
            'bright colors, flat lighting, modern style',
            'low contrast, oversaturated, cheerful mood'
        ],
        'style_strength': 0.9,
        'category': 'stylized'
    },
    'Neon Cyberpunk': {
        'name': 'Neon Cyberpunk',
        'description': 'Futuristic with vibrant neon colors and urban tech',
        'positive_prompts': [
            'cyberpunk style, neon lighting, futuristic atmosphere',
            'vibrant neon colors, urban dystopia, tech noir',
            'blade runner aesthetic, holographic displays, rain-soaked streets',
            'electric blue and pink lighting, chrome reflections'
        ],
        'negative_prompts': [
            'natural lighting, rural settings, warm colors',
            'vintage style, low-tech, pastoral scenes'
        ],
        'style_strength': 0.85,
        'category': 'stylized'
    },
    'Golden Hour': {
        'name': 'Golden Hour',
        'description': 'Warm, soft lighting with golden tones',
        'positive_prompts': [
            'golden hour lighting, warm sunset glow, soft natural light',
            'golden tones, warm color palette, backlighting',
            'magical hour photography, lens flares, warm atmosphere',
            'honey-colored light, romantic lighting, dreamy quality'
        ],
        'negative_prompts': [
            'harsh lighting, cool colors, artificial light',
            'overcast, flat lighting, cold atmosphere'
        ],
        'style_strength': 0.7,
        'category': 'atmospheric'
    },
    'Horror Dark': {
        'name': 'Horror Dark',
        'description': 'Dark, ominous atmosphere with unsettling shadows',
        'positive_prompts': [
            'horror atmosphere, dark shadows, ominous lighting',
            'eerie mood, unsettling atmosphere, dramatic darkness',
            'horror movie cinematography, creepy shadows, fog effects',
            'sinister lighting, gothic atmosphere, spine-chilling mood'
        ],
        'negative_prompts': [
            'bright lighting, cheerful mood, warm colors',
            'safe atmosphere, friendly lighting, cozy feeling'
        ],
        'style_strength': 0.8,
        'category': 'atmospheric'
    },
    'Vintage Film': {
        'name': 'Vintage Film',
        'description': 'Classic film look with grain and muted colors',
        'positive_prompts': [
            'vintage film stock, analog photography, film grain',
            'retro cinematography, muted color palette, classic film look',
            '35mm film aesthetic, nostalgic atmosphere, period cinematography',
            'vintage color grading, old school film style'
        ],
        'negative_prompts': [
            'digital perfection, oversaturated colors, modern look',
            'crisp digital, high definition, contemporary style'
        ],
        'style_strength': 0.75,
        'category': 'stylized'
    },
    'Minimalist': {
        'name': 'Minimalist',
        'description': 'Clean, simple composition with subtle lighting',
        'positive_prompts': [
            'minimalist composition, clean lines, simple design',
            'subtle lighting, neutral colors, uncluttered frame',
            'geometric composition, negative space, elegant simplicity',
            'refined aesthetic, understated style, architectural lighting'
        ],
        'negative_prompts': [
            'cluttered composition, busy background, chaotic elements',
            'over-decorated, excessive details, messy frame'
        ],
        'style_strength': 0.6,
        'category': 'professional'
    },
    'Fantasy Epic': {
        'name': 'Fantasy Epic',
        'description': 'Grand, magical atmosphere with epic scale',
        'positive_prompts': [
            'epic fantasy atmosphere, magical lighting, grand scale',
            'mythical ambiance, ethereal glow, otherworldly beauty',
            'fantasy cinematography, epic scope, legendary atmosphere',
            'magical realism, enchanted lighting, heroic composition'
        ],
        'negative_prompts': [
            'mundane setting, realistic lighting, ordinary scale',
            'modern technology, contemporary style, earthbound'
        ],
        'style_strength': 0.8,
        'category': 'atmospheric'
    },
    'Pastel Dream': {
        'name': 'Pastel Dream',
        'description': 'Soft, dreamy colors with ethereal quality',
        'positive_prompts': [
            'pastel color palette, soft dreamy lighting, ethereal atmosphere',
            'cotton candy colors, whimsical mood, fairy-tale lighting',
            'soft focus, dreamy quality, romantic pastels',
            'gentle lighting, peaceful atmosphere, serene mood'
        ],
        'negative_prompts': [
            'harsh colors, dramatic lighting, dark atmosphere',
            'high contrast, aggressive tones, intense mood'
        ],
        'style_strength': 0.7,
        'category': 'atmospheric'
    },
    'Anime Style': {
        'name': 'Anime Style',
        'description': 'Japanese animation inspired with vibrant colors',
        'positive_prompts': [
            'anime style, vibrant colors, cel-shaded lighting',
            'japanese animation aesthetic, clean lines, expressive characters',
            'manga-inspired visuals, dynamic composition, colorful palette',
            'studio ghibli style, detailed backgrounds, whimsical atmosphere'
        ],
        'negative_prompts': [
            'photorealistic, live action, muted colors',
            'western animation, 3D rendering, realistic proportions'
        ],
        'style_strength': 0.9,
        'category': 'stylized'
    },
    'Painterly': {
        'name': 'Painterly',
        'description': 'Hand-painted artistic style with brush strokes',
        'positive_prompts': [
            'painterly style, visible brush strokes, artistic rendering',
            'oil painting aesthetic, impressionist style, textured canvas',
            'fine art quality, masterpiece painting, artistic composition',
            'traditional art style, painted illustration, rich textures'
        ],
        'negative_prompts': [
            'photographic, digital perfection, sharp edges',
            'mechanical precision, computer generated, sterile look'
        ],
        'style_strength': 0.8,
        'category': 'artistic'
    },
    'Gritty Realistic': {
        'name': 'Gritty Realistic',
        'description': 'Raw, unfiltered realism with urban edge',
        'positive_prompts': [
            'gritty realistic style, raw photography, urban atmosphere',
            'street photography aesthetic, unfiltered reality, harsh lighting',
            'documentary realism, authentic textures, weathered surfaces',
            'industrial atmosphere, concrete textures, urban decay'
        ],
        'negative_prompts': [
            'polished, glamorous, fantasy elements',
            'clean aesthetics, perfect lighting, idealized beauty'
        ],
        'style_strength': 0.7,
        'category': 'realistic'
    },
    'Romantic Soft': {
        'name': 'Romantic Soft',
        'description': 'Gentle, romantic atmosphere with warm tones',
        'positive_prompts': [
            'romantic lighting, soft focus, warm golden tones',
            'gentle atmosphere, dreamy quality, tender moments',
            'rose-colored lighting, intimate setting, cozy ambiance',
            'valentine aesthetic, soft shadows, loving atmosphere'
        ],
        'negative_prompts': [
            'harsh lighting, cold colors, aggressive mood',
            'dramatic shadows, intense atmosphere, stark contrasts'
        ],
        'style_strength': 0.7,
        'category': 'atmospheric'
    },
    'Comic Book': {
        'name': 'Comic Book',
        'description': 'Bold comic book style with dynamic action',
        'positive_prompts': [
            'comic book style, bold colors, dynamic action poses',
            'graphic novel aesthetic, sharp contrasts, dramatic angles',
            'superhero comic style, pop art colors, halftone patterns',
            'sequential art style, action lines, vibrant palette'
        ],
        'negative_prompts': [
            'photorealistic, muted colors, static composition',
            'documentary style, natural lighting, subtle tones'
        ],
        'style_strength': 0.85,
        'category': 'stylized'
    },
    'Steampunk': {
        'name': 'Steampunk',
        'description': 'Victorian-era industrial with brass and steam',
        'positive_prompts': [
            'steampunk aesthetic, brass machinery, victorian industrial',
            'copper pipes, steam effects, clockwork mechanisms',
            'retro-futuristic style, goggles and gears, sepia tones',
            'mechanical details, vintage technology, ornate metalwork'
        ],
        'negative_prompts': [
            'modern technology, clean lines, minimalist design',
            'digital aesthetics, sleek surfaces, contemporary style'
        ],
        'style_strength': 0.8,
        'category': 'stylized'
    }
}

# Genre-Specific Style Mappings
# Each genre has preferred styles that auto-populate when selected
GENRE_STYLE_MAPPINGS = {
    'Fantasy': [
        'Anime Style',      # Vibrant, fantastical
        'Painterly',        # Artistic, magical
        'Fantasy Epic',     # Grand, mythical
        'Pastel Dream',     # Ethereal, dreamy
        'Golden Hour'       # Magical lighting
    ],
    'Horror': [
        'Horror Dark',      # Primary horror aesthetic
        'Noir',            # Dark, shadowy
        'Gritty Realistic', # Raw, unsettling
        'Vintage Film',     # Classic horror feel
        'Minimalist'        # Stark, unsettling
    ],
    'Sci-Fi': [
        'Neon Cyberpunk',   # Futuristic primary
        'Minimalist',       # Clean, sterile
        'Cinematic',        # Epic sci-fi
        'Steampunk',        # Retro-futuristic
        'Comic Book'        # Dynamic action
    ],
    'Romance': [
        'Romantic Soft',    # Primary romantic
        'Golden Hour',      # Warm, dreamy
        'Pastel Dream',     # Soft, gentle
        'Vintage Film',     # Classic romance
        'Cinematic'         # Beautiful moments
    ],
    'Comedy': [
        'Comic Book',       # Bright, energetic
        'Anime Style',      # Exaggerated, fun
        'Documentary',      # Natural, authentic
        'Vintage Film',     # Classic comedy
        'Cinematic'         # Professional quality
    ],
    'Thriller': [
        'Noir',            # Dark, suspenseful
        'Gritty Realistic', # Tense, raw
        'Cinematic',        # Professional thriller
        'Horror Dark',      # Atmospheric tension
        'Documentary'       # Realistic edge
    ],
    'Drama': [
        'Cinematic',        # Primary dramatic
        'Documentary',      # Real, authentic
        'Gritty Realistic', # Raw emotion
        'Golden Hour',      # Beautiful, emotional
        'Vintage Film'      # Classic drama
    ],
    'Mystery': [
        'Noir',            # Classic mystery
        'Gritty Realistic', # Urban detective
        'Cinematic',        # Sophisticated
        'Vintage Film',     # Period mystery
        'Minimalist'        # Clean, focused
    ]
}

# Render Settings Configuration
RENDER_SETTINGS = {
    'aspect_ratios': {
        'Vertical': {
            'name': 'Vertical (9:16)',
            'ratio': '9:16',
            'width': 1080,
            'height': 1920,
            'comfyui_params': {'width': 1080, 'height': 1920, 'aspect_ratio': '9:16'}
        },
        'Square': {
            'name': 'Square (1:1)', 
            'ratio': '1:1',
            'width': 1080,
            'height': 1080,
            'comfyui_params': {'width': 1080, 'height': 1080, 'aspect_ratio': '1:1'}
        },
        'Horizontal': {
            'name': 'Horizontal (16:9)',
            'ratio': '16:9', 
            'width': 1920,
            'height': 1080,
            'comfyui_params': {'width': 1920, 'height': 1080, 'aspect_ratio': '16:9'}
        },
        'Portrait': {
            'name': 'Portrait (4:5)',
            'ratio': '4:5',
            'width': 864,
            'height': 1080, 
            'comfyui_params': {'width': 864, 'height': 1080, 'aspect_ratio': '4:5'}
        }
    },
    'fps_options': {
        '12fps': {
            'name': '12 FPS (Cinematic)',
            'value': 12,
            'comfyui_params': {'fps': 12, 'frame_rate': 12}
        },
        '15fps': {
            'name': '15 FPS (Smooth)',
            'value': 15,
            'comfyui_params': {'fps': 15, 'frame_rate': 15}
        },
        '24fps': {
            'name': '24 FPS (Film Standard)',
            'value': 24,
            'comfyui_params': {'fps': 24, 'frame_rate': 24}
        },
        '30fps': {
            'name': '30 FPS (High Quality)',
            'value': 30,
            'comfyui_params': {'fps': 30, 'frame_rate': 30}
        }
    },
    'defaults': {
        'aspect_ratio': 'Vertical',
        'fps': '24fps'
    }
}

# Application Settings
APP_SETTINGS = {
    'window_title': 'Short-Form Film Generator',
    'window_size': '1200x800',
    'log_refresh_rate': 100,  # milliseconds
    'metrics_refresh_rate': 30000,  # milliseconds
    'generation_wait_time': 5,  # seconds between continuous generations
}



# Time estimation utility functions
def estimate_step_time(step_key: str, config_data: dict = None, shot_count: int = 0, character_count: int = 0) -> int:
    """Estimate time for a specific generation step in seconds"""
    estimates = GENERATION_SETTINGS["step_time_estimates"]
    
    if step_key not in estimates:
        return 30  # Default fallback
    
    step_config = estimates[step_key]
    base_time = step_config["base_time"]
    
    if step_key == "story":
        if config_data:
            genre_multiplier = step_config["complexity_factors"].get(config_data.get("genre", "Drama"), 1.0)
            parts = GENERATION_SETTINGS["length_to_parts"].get(config_data.get("length", "3-5 minutes"), (3, 5))[1]
            return int(base_time * genre_multiplier * (1 + parts * step_config["per_part_multiplier"] * 0.1))
        return base_time
    
    elif step_key == "shots":
        if config_data and shot_count > 0:
            length_multiplier = step_config["length_multipliers"].get(config_data.get("length", "3-5 minutes"), 1.2)
            return int(base_time + (shot_count * step_config["per_shot_time"]) * length_multiplier)
        return base_time + int(shot_count * step_config["per_shot_time"]) if shot_count > 0 else base_time
    
    elif step_key == "characters":
        char_time = base_time + (character_count * step_config["per_character_time"])
        if character_count > 0:
            char_time += character_count * step_config["comfyui_prompt_time"]
        return int(char_time)
    
    elif step_key in ["prompts", "narration"]:
        return int(base_time + (shot_count * step_config["per_shot_time"]))
    
    elif step_key == "music":
        # Estimate music cues as roughly 30% of shots
        music_cues = max(1, int(shot_count * 0.3))
        genre_multiplier = step_config["genre_multipliers"].get(config_data.get("genre", "Drama") if config_data else "Drama", 1.0)
        return int((base_time + (music_cues * step_config["per_cue_time"])) * genre_multiplier)
    
    elif step_key == "queue":
        return int(base_time + (shot_count * step_config["per_shot_time"]) + step_config["database_operations"])
    
    return base_time

def estimate_total_time(config_data: dict = None, shot_count: int = None, character_count: int = None) -> int:
    """Estimate total generation time in seconds"""
    # Estimate shot count if not provided
    if shot_count is None and config_data:
        length_range = GENERATION_SETTINGS["length_to_parts"].get(config_data.get("length", "3-5 minutes"), (3, 5))
        shot_count = int((length_range[0] + length_range[1]) / 2 * 2)  # Rough estimate: 2 shots per part
    elif shot_count is None:
        shot_count = 6  # Default estimate
    
    # Estimate character count if not provided
    if character_count is None:
        character_count = 2  # Default estimate
    
    total_time = 0
    steps = ["story", "shots", "characters", "style", "prompts", "narration", "music", "queue"]
    
    for step in steps:
        step_time = estimate_step_time(step, config_data, shot_count, character_count)
        total_time += step_time
    
    return total_time

def format_time_estimate(seconds: int) -> str:
    """Format time estimate in a user-friendly way"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

