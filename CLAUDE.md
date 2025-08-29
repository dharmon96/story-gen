# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
python main.py
```

### Testing Research System
```bash
python test_research_simple.py
```

### Character Consistency Testing
```bash
python test_character_consistency.py
```

### Development Dependencies
This project uses:
- `tkinter` for GUI (built into Python)
- `ollama` for AI integration (`pip install ollama`)
- `requests` for HTTP API calls (`pip install requests`)
- `sqlite3` for database (built into Python)

Install dependencies manually: `pip install ollama requests`

## Recent Updates (Latest Version)

### ✨ Research System Integration (COMPLETED)
A comprehensive research system has been added to analyze trending AI video content from social media platforms:

**New Components:**
- **Research Dashboard**: Full-featured GUI tab with real-time trending analysis
- **Social Media APIs**: TikTok, Instagram, YouTube integration with fallback systems
- **Trend Analysis Engine**: Statistical scoring and cross-platform trend detection  
- **Research-Driven Story Generation**: Automatic trending prompt integration
- **Daily Automation**: Scheduled research with data persistence and cleanup

**New Files:**
- `social_media_apis.py` - Multi-platform API integration
- `research_engine.py` - Core research and analysis logic
- `research_tab.py` - GUI dashboard for research management
- `test_research_simple.py` - Integration testing

**Enhanced Files:**
- `database.py` - 4 new tables for research data storage
- `story_generator.py` - Trending prompt selection and optimization
- `gui.py` - Research tab integration
- `data_models.py` - Fixed StoryConfig with parts field

**Bug Fixes & Improvements:**
- Fixed missing `parts` field in StoryConfig dataclass causing runtime errors
- Improved error handling by replacing bare except clauses with specific exceptions
- Enhanced error logging with detailed messages for debugging
- Cleaned up redundant test files for better project organization

## ✅ Completed Features (Current Version)

### Story Queue Management System
**Status: COMPLETED** - Full batch story generation and queue management system
- **Story Queue Tab**: Complete GUI tab with comprehensive queue management
- **Batch Processing**: Queue multiple stories with different configurations and priorities
- **Priority System**: 1-10 priority levels with automatic queue ordering
- **Queue Persistence**: Full queue state persistence across application restarts
- **Progress Tracking**: Real-time individual progress bars for each queued story
- **Queue Statistics**: Live statistics, ETA calculations, and throughput metrics
- **Continuous Generation**: Automated story generation when render queue is low
- **Progress Windows**: Individual progress windows for each queue item
- **Queue Controls**: Pause/resume, retry failed items, clear completed items
- **Auto-randomization**: Automatic input randomization after queue completion

**New Files:**
- `story_queue.py` - Core queue management system with threading and continuous generation
- `story_queue_tab.py` - Complete GUI interface for queue management and monitoring

### Multi-Node Processing Architecture  
**Status: COMPLETED** - Distributed processing across multiple machines
- **Node Manager**: `node_manager.py` - Complete multi-PC processing coordination
- **Node Types**: TEXT_LLM, COMFYUI, and HYBRID processing capabilities
- **Load Balancing**: Automatic task distribution based on node performance
- **Heartbeat Monitoring**: Real-time node health monitoring and failover
- **Task Queue**: Priority-based task distribution with retry mechanisms
- **Node Discovery**: Auto-discovery of Ollama and ComfyUI services
- **Performance Tracking**: Processing time analytics and load scoring

### ComfyUI Style Card System
**Status: COMPLETED** - Character and style consistency management
- **ComfyUI Manager**: `comfyui_manager.py` - Style reference card generation
- **Character Consistency**: Multi-angle character reference sheets
- **Location Cards**: Establishing shot style references
- **Style Templates**: Configurable templates for different content types
- **Consistency Prompts**: Automatic character/location consistency in shots
- **Database Integration**: Style reference storage and retrieval system
- **Progress Integration**: Real-time style card generation progress tracking

## 🚀 Current Development Focus

### UI/UX Improvements & Bug Fixes
**Priority: HIGH** - Address user experience issues identified in NEEDS FIXING.txt
- **Settings Integration**: Move model configuration to settings tab (NEEDS FIXING.txt:1)
- **Multi-Node Configuration**: Add multiple nodes per generation step (NEEDS FIXING.txt:3)
- **Modern Theme System**: Dark/Light mode with Windows theme integration (NEEDS FIXING.txt:5)
- **Progress Window Fixes**: Fix content loading mid-generation, disable auto-close (NEEDS FIXING.txt:9,11)
- **Music & Narration Tab**: Add timeline view for music cues and narration (NEEDS FIXING.txt:13)
- **Network Discovery**: Fix initial network instance discovery (NEEDS FIXING.txt:15)
- **Queue Improvements**: Fix ETA calculations, clear completed button (NEEDS FIXING.txt:7,21)
- **Shot Descriptions**: Enhance shot list detail for better ComfyUI prompts (NEEDS FIXING.txt:28)
- **TikTok API Integration**: Update research system with official TikTok API (NEEDS FIXING.txt:25)
- **OpenAI Config**: Fix permission errors saving custom presets (NEEDS FIXING.txt:23)

### ComfyUI Video Generation Pipeline
**Priority: HIGH** - Complete video generation automation
- **Workflow Integration**: Direct ComfyUI workflow execution from shots
- **Progress Monitoring**: Real-time render progress from ComfyUI nodes
- **Output Management**: Automatic video file collection and organization
- **Quality Control**: Automated video validation and retry logic
- **Character Consistency**: Integration with style card system for consistent characters
- **Batch Rendering**: Queue-based video generation across multiple ComfyUI nodes

### Advanced Features
**Priority: MEDIUM** - Enhanced functionality and integrations
- **Audio Generation**: Suno API integration for music generation
- **Voice Synthesis**: ElevenLabs integration for narration
- **Footage Assembly**: Complete video assembly pipeline
- **Advanced Analytics**: Performance metrics and optimization insights

## Architecture

### Core Components

**Main Entry Point**: `main.py`
- Initializes database and launches GUI
- Handles application lifecycle and error catching

**GUI Layer**: `gui.py`
- Main `FilmGeneratorApp` class using Tkinter
- Multi-tab interface: Story Generator, Research, Logs, Metrics, Render Queue
- Threaded generation with progress tracking
- Real-time log display and metrics
- Integration with progress popup window

**Story Generation**: `story_generator.py`
- `StoryGenerator` class handles complete story creation pipeline
- Generates story → shot list → video prompts → narration → music cues
- Uses specialized AI system prompts for each generation phase
- **NEW**: Research-aware prompt selection and trending topic integration

**AI Integration**: `ollama_manager.py`
- `OllamaManager` handles multiple Ollama API connections
- Multi-network instance discovery and management
- Per-step model selection and assignment
- Support for both library and HTTP API connections

**Fast Network Discovery**: `network_discovery.py`
- `FastNetworkDiscovery` with optimized scanning algorithms
- Session caching for instant UI responsiveness  
- Background refresh with ARP table optimization
- Sub-second network discovery using active IP detection

**Model Selection UI**: `model_selection_dialog.py`
- Advanced dialog for configuring AI models per generation step
- Network instance selection and management
- Future AI service placeholders (ComfyUI, ElevenLabs, Suno)

**Database**: `database.py`
- SQLite-based storage with `DatabaseManager` class
- Core tables: stories, shots, video_metrics, render_queue, generation_history
- **Research tables**: research_sessions, trending_content, trend_analysis, research_prompts
- Story/shot relationship management with research data integration

**Configuration**: `config.py`
- Centralized settings and prompts
- Genre-specific story prompts (140+ predefined prompts across 8 genres)
- AI system prompts for each generation phase
- Model-specific configurations and performance settings

**Data Models**: `data_models.py`
- Dataclasses: `StoryConfig`, `Shot`, `VideoMetrics`
- Type definitions for story generation pipeline

**Enhanced Progress UI**: `generation_progress_popup.py`
- Tabbed content display with real-time updates
- **Story Tab**: Formatted story content viewer with styling
- **Storyboard Tab**: Grid-based shot list with ComfyUI placeholders
- **AI Chat Tab**: Debug view for AI responses and requests
- **Prompts Tab**: Future integration ready for visual prompts
- Individual shot cards with render progress tracking

**Multi-Node Processing**: `node_manager.py` 
- Complete distributed processing system for TEXT_LLM and COMFYUI tasks
- Node discovery, load balancing, and health monitoring
- Task queue with priority management and automatic failover
- Performance tracking and resource utilization monitoring

**Style Card Generation**: `comfyui_manager.py`
- Character and location consistency management
- Style reference card generation with configurable templates
- Shot-level consistency prompt integration
- Database storage for reference data and retrieval

**Story Queue System**: `story_queue.py` 
- Complete batch story generation with priority management
- Queue persistence, state recovery, and continuous generation
- ETA calculations, throughput metrics, and retry mechanisms
- Real-time progress tracking and callback integration

**Future Components** (PLANNED):

**Footage Assembly**: `footage_assembler.py` (PLANNED)
- Complete video assembly from individual shot renders
- Timeline synchronization with narration and music
- Transition effects and post-processing integration
- Final video export and quality optimization

**Advanced Analytics**: Enhanced monitoring and metrics (PLANNED)
- Performance analytics across all generation steps  
- Resource utilization tracking and optimization recommendations
- Quality metrics and automated improvement suggestions
- Historical data analysis and trend identification

**Research System** (NEW):

**Social Media APIs**: `social_media_apis.py`
- Multi-platform content discovery (TikTok, Instagram, YouTube)
- AI content detection and filtering algorithms
- Engagement rate calculation and viral potential scoring
- Rate limiting and fallback systems for reliability

**Research Engine**: `research_engine.py`
- Automated daily research workflow coordination
- Cross-platform trend analysis with statistical scoring
- Research-based story prompt generation
- Background scheduling with data persistence

**Research Dashboard**: `research_tab.py`
- Comprehensive GUI for research management and monitoring
- Real-time trending topics visualization
- API configuration and connection testing
- Research session history and data export

**Test Suite**: `test_research_simple.py`
- Integration testing for all research system components
- Database schema validation
- API connection verification

### Key Workflows

1. **Multi-Network AI Generation Pipeline**:
   - Network discovery → Instance selection → Per-step model assignment
   - Each AI step can use different models on different network instances
   - Story generation → Shot list → Visual prompts → Narration → Music cues

2. **Model Configuration Flow**:
   - Automatic network scanning for Ollama instances
   - Manual model assignment per generation step
   - Load balancing across multiple AI instances
   - Fallback to localhost if network instances unavailable

3. **Database Management**:
   - Stories and shots with comprehensive metadata
   - Database deletion with automatic backup creation
   - Backup storage in timestamped files
   - Fresh database initialization after deletion

4. **AI System Prompts** (per-step model support):
   - `story_writer`: Generates structured stories with timing and hooks
   - `shot_list_creator`: Converts stories to filmable shot sequences  
   - `prompt_engineer`: Creates AI video generation prompts
   - `narration_writer`: Produces voice-over scripts
   - `music_director`: Specifies music cues and timing

5. **Research-Driven Content Pipeline**:
   - Daily social media content discovery and analysis
   - Trend scoring and cross-platform correlation
   - Automatic story prompt generation from trending topics
   - Research data integration with story generation
   - Performance tracking and prompt optimization

6. **Story Queue Management** (IMPLEMENTED):
   - Batch story generation with full configuration options
   - 1-10 priority system with automatic queue ordering
   - Complete queue persistence and recovery across application sessions
   - Individual story progress tracking with real-time windows
   - Continuous generation when render queue is low
   - Retry mechanisms and comprehensive error handling

7. **Multi-Node Processing** (IMPLEMENTED):
   - TEXT_LLM and COMFYUI node discovery and management
   - Automatic load balancing based on node performance
   - Real-time node health monitoring with heartbeat system
   - Task queue with priority-based distribution and failover
   - Performance analytics and resource utilization tracking

8. **Character Consistency System** (IMPLEMENTED):
   - Style reference card generation for characters and locations
   - Shot-level consistency prompt integration
   - ComfyUI workflow templates for different content types
   - Database storage and retrieval of style references

### Genre System
Eight supported genres with 20 unique prompts each:
- Drama, Comedy, Thriller, Sci-Fi, Romance, Horror, Mystery, Fantasy
- Auto-prompt selection available for random generation

### Performance Optimizations
- **Fast Network Discovery**: Sub-second scanning using ARP tables
- **Session Caching**: Instant UI updates with 5-minute cache
- **Background Refresh**: Non-blocking updates for responsive GUI
- **Optimized Timeouts**: 0.3s socket + 0.5s HTTP for fast detection
- **No AI Generation Timeouts**: Unlimited time for AI model responses
- **Multi-fallback System**: Environment variables → Custom client → Direct HTTP
- **Research System Optimizations**:
  - Async social media API calls with proper rate limiting
  - Database indexing for trend analysis queries
  - Automatic data cleanup (30-day retention)
  - Mock data fallbacks when APIs unavailable
  - Background research scheduling
- **Planned Performance Improvements**:
  - Story queue batch processing optimization
  - Render farm load balancing algorithms
  - ComfyUI workflow caching and reuse
  - UI responsiveness improvements
  - Database query optimization for large datasets
- Structured output enforcement to prevent hallucination
- Model-specific temperature and token settings
- Quality checks for filmability and word limits

### File Structure Notes
- Database file: `film_generator.db` (created in app directory)
- Ollama models stored in `llama3.1/blobs/` directory
- No external config files or requirements.txt
- Future queue data stored in `story_queue/` subdirectory (PLANNED)
- ComfyUI workflows stored in `workflows/` subdirectory (PLANNED)
- Render output organized in `renders/[story_id]/` structure (PLANNED)

### Development Roadmap

**Phase 1: UI/UX Improvements** (Current - Next 2-3 weeks) 
1. ✅ Complete story queue management system
2. ✅ Multi-node processing architecture  
3. ✅ ComfyUI style card generation system
4. 🔄 Address issues identified in NEEDS FIXING.txt:
   - Move model configuration to settings tab
   - Fix progress window content loading
   - Add music & narration timeline tab
   - Implement dark/light theme system
   - Fix queue ETA calculations and clearing
   - Enhance shot descriptions for better ComfyUI prompts

**Phase 2: Video Generation Pipeline** (Weeks 3-6)
1. Complete ComfyUI workflow execution integration
2. Implement real-time render progress monitoring
3. Add automatic video file collection and organization
4. Develop quality control and retry mechanisms
5. Integrate character consistency system with video generation

**Phase 3: Audio Integration** (Weeks 5-8)
1. Suno API integration for music generation
2. ElevenLabs API for voice synthesis and narration
3. Timeline synchronization between audio and video
4. Music transition and fade system implementation

**Phase 4: Final Assembly** (Weeks 7-10)
1. Complete footage assembly pipeline
2. Advanced video editing and transition effects
3. Quality optimization and export system
4. Performance analytics and monitoring dashboard