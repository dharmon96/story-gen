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

## 🚀 Planned Updates (Next Sprint)

### Story Queue Management System
**Priority: HIGH** - Enable batch story generation and queue management
- **Story Queue Tab**: New GUI tab for managing multiple story generation requests
- **Batch Processing**: Queue multiple stories with different configurations
- **Priority System**: High/Normal/Low priority queue management
- **Queue Persistence**: Save queue state across application restarts
- **Progress Tracking**: Individual progress bars for each queued story
- **Queue Statistics**: ETA calculations and throughput metrics

### Additional Render Nodes & Distributed Processing
**Priority: HIGH** - Scale video generation across multiple machines
- **Render Node Discovery**: Auto-discover ComfyUI instances on network
- **Load Balancing**: Distribute render jobs across available nodes
- **Node Health Monitoring**: Real-time status and performance tracking
- **Failover System**: Automatic job redistribution on node failures
- **Resource Management**: Memory and GPU utilization monitoring
- **Render Farm Dashboard**: Centralized node management interface

### UI/UX Cleanup & Modernization
**Priority: MEDIUM** - Improve user experience and visual design
- **Modern Theme System**: Dark/Light mode with accent color options
- **Responsive Layout**: Better window resizing and component scaling
- **Enhanced Progress Indicators**: More detailed generation progress
- **Improved Error Handling**: User-friendly error messages and recovery
- **Keyboard Shortcuts**: Hotkeys for common actions
- **Drag & Drop**: File operations and queue reordering
- **Status Bar**: Real-time system status and connection indicators

### ComfyUI Integration Phase 1
**Priority: HIGH** - Begin video generation automation
- **ComfyUI Node Manager**: Discover and manage ComfyUI instances
- **Workflow Templates**: Pre-built workflows for different video styles
- **Automatic Workflow Execution**: Send prompts directly to ComfyUI
- **Progress Monitoring**: Real-time render progress from ComfyUI
- **Output Management**: Automatic video file collection and organization
- **Quality Control**: Automated video validation and retry logic

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

**Future Components** (PLANNED):

**Story Queue System**: `story_queue.py` (PLANNED)
- Batch story generation queue with priority management
- Queue persistence and state recovery
- ETA calculations and throughput metrics
- Individual story progress tracking

**Render Farm Manager**: `render_farm.py` (PLANNED)
- Multi-node ComfyUI discovery and management
- Load balancing and job distribution
- Node health monitoring and failover systems
- Resource utilization tracking

**ComfyUI Integration**: `comfyui_manager.py` (PLANNED)
- ComfyUI node discovery and workflow management
- Automatic prompt-to-video pipeline execution
- Progress monitoring and output collection
- Quality control and retry mechanisms

**UI Modernization**: Enhanced GUI components (PLANNED)
- Modern theme system with dark/light modes
- Responsive layouts and improved UX
- Keyboard shortcuts and drag-drop functionality
- Enhanced error handling and user feedback

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

6. **Story Queue Management** (PLANNED):
   - Batch story generation with configurable parameters
   - Priority-based queue processing with ETA calculations
   - Queue persistence and recovery across application sessions
   - Individual story progress tracking and management

7. **Distributed Render Farm** (PLANNED):
   - Multi-node ComfyUI discovery and load balancing
   - Automatic job distribution and failover handling
   - Real-time node health monitoring and resource tracking
   - Centralized render farm management interface

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

**Phase 1: Queue Management** (Next 2-3 weeks)
1. Implement story queue database tables and models
2. Create story queue GUI tab with queue management
3. Add batch processing and priority system
4. Implement queue persistence and recovery

**Phase 2: Render Farm Setup** (Weeks 3-5)
1. Develop ComfyUI node discovery system
2. Implement render job distribution and load balancing
3. Add node health monitoring and failover
4. Create render farm dashboard

**Phase 3: ComfyUI Integration** (Weeks 4-7)
1. Build ComfyUI API integration layer
2. Create workflow templates for different video styles
3. Implement automatic prompt-to-video pipeline
4. Add progress monitoring and output management

**Phase 4: UI/UX Polish** (Weeks 6-8)
1. Implement modern theme system
2. Improve responsive layouts and components
3. Add keyboard shortcuts and drag-drop
4. Enhanced error handling and user feedback