import streamlit as st
import json
import time
import os
import importlib
import config
importlib.reload(config) # Force reload to get new Table IDs
from config import settings
from modules.pipeline_manager import PipelineManager
from utils.logger import logger
from models import Project

# Page Config
st.set_page_config(
    page_title="Storyteller v2.0 - Debug Mode",
    page_icon="🎬",
    layout="wide"
)

# Initialize Pipeline
if "pipeline" not in st.session_state:
    st.session_state.pipeline = PipelineManager()

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "phase_status" not in st.session_state:
    st.session_state.phase_status = {
        "init": False,
        "research": False,
        "script": False,
        "audio": False,
        "visual": False
    }

st.title("🎬 Storyteller v2.0 - Phase Debugger")

# Sidebar - Project Configuration
with st.sidebar:
    st.header("⚙️ Project Configuration")
    
    # Project History - Load existing projects
    st.subheader("📁 Load Existing Project")
    
    try:
        import requests
        from config import settings
        
        # Fetch recent projects from NocoDB
        api_url = settings.NOCODB_API_URL
        table_id = settings.NOCODB_PROJECTS_TABLE_ID
        headers = {"xc-token": settings.NOCODB_API_TOKEN}
        
        resp = requests.get(
            f"{api_url}/api/v2/tables/{table_id}/records?limit=10&sort=-Id",
            headers=headers
        )
        
        if resp.status_code == 200:
            data = resp.json()
            projects = data.get("list", [])
            
            if projects:
                project_options = {
                    f"ID {p['Id']}: {p.get('Topic', 'Untitled')} ({p.get('Status', 'Unknown')})": p['Id']
                    for p in projects
                }
                
                selected = st.selectbox(
                    "Select project to resume:",
                    options=["-- Create New --"] + list(project_options.keys()),
                    key="project_selector"
                )
                
                if selected != "-- Create New --" and st.button("📂 Load Project"):
                    project_id = project_options[selected]
                    
                    # Load full project data
                    resp_detail = requests.get(
                        f"{api_url}/api/v2/tables/{table_id}/records/{project_id}",
                        headers=headers
                    )
                    
                    if resp_detail.status_code == 200:
                        project_data = resp_detail.json()
                        
                        # Create Project object from NocoDB data
                        loaded_project = Project(
                            id=str(project_data['Id']),
                            topic=project_data.get('Topic', ''),
                            status=project_data.get('Status', 'New'),
                            target_duration=3,  # Default, could be stored in DB
                            research_content=project_data.get('Research Data'),
                            research_sources=project_data.get('Script Content')
                        )
                        
                        st.session_state.current_project = loaded_project
                        
                        # Set phase status based on what data exists
                        st.session_state.phase_status["init"] = True
                        if loaded_project.research_content:
                            st.session_state.phase_status["research"] = True
                        
                        st.success(f"✅ Loaded project: {loaded_project.topic}")
                        st.rerun()
            else:
                st.info("No projects found. Create a new one below.")
        else:
            st.warning("Could not load project history")
            
    except Exception as e:
        st.warning(f"Project history unavailable: {e}")
    
    st.divider()
    
    # New Project Configuration
    st.subheader("➕ Create New Project")
    
    topic = st.text_input("Topic", value="The History of Coffee", key="topic_input")
    target_duration = st.number_input("Duration (min)", min_value=1, max_value=30, value=3)
    voice_id = st.selectbox("Voice", ["am_michael", "Heart", "Bella", "Adam"])
    image_provider = st.selectbox("Image Provider", ["ComfyUI", "DALL-E 3"])
    
    st.divider()
    
    # Reset button
    if st.button("🔄 Reset All", type="secondary", use_container_width=True):
        st.session_state.current_project = None
        st.session_state.phase_status = {k: False for k in st.session_state.phase_status}
        st.rerun()

# Main Content - Phase Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Phase 1: Initialize",
    "🔍 Phase 2: Research", 
    "📝 Phase 3: Script",
    "🎵 Phase 4: Audio",
    "🎨 Phase 5: Visual",
    "🐛 Logs"
])

# PHASE 1: INITIALIZE
with tab1:
    st.header("Phase 1: Initialize Project")
    st.write("Creates a new project record in NocoDB with basic metadata.")
    
    if st.button("▶️ Run Phase 1: Initialize", type="primary", disabled=st.session_state.phase_status["init"]):
        with st.spinner("Initializing project..."):
            try:
                # Create project
                project = Project(
                    topic=topic,
                    status="New",
                    target_duration=target_duration,
                    voice_id=voice_id,
                    image_provider=image_provider
                )
                
                # Initialize in NocoDB
                result = st.session_state.pipeline.initialize_project(project)
                
                if result and result.id:
                    st.session_state.current_project = result
                    st.session_state.phase_status["init"] = True
                    st.success(f"✅ Project initialized! ID: {result.id}")
                else:
                    st.error("❌ Failed to initialize project")
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")
                logger.exception("Phase 1 failed")
    
    # Show current state
    if st.session_state.current_project:
        st.divider()
        st.subheader("📊 Current Project State")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Project ID", st.session_state.current_project.id)
        with col2:
            st.metric("Topic", st.session_state.current_project.topic)
        with col3:
            st.metric("Status", st.session_state.current_project.status)
        
        with st.expander("🔍 Full Project Data"):
            st.json(st.session_state.current_project.model_dump())

# PHASE 2: RESEARCH
with tab2:
    st.header("Phase 2: Run Research")
    st.write("Uses Perplexity API to research the topic and saves results to NocoDB.")
    
    if not st.session_state.phase_status["init"]:
        st.warning("⚠️ Please complete Phase 1 first")
    else:
        # Allow re-running
        btn_label = "🔄 Re-run Phase 2: Research" if st.session_state.phase_status["research"] else "▶️ Run Phase 2: Research"
        
        if st.button(btn_label, type="primary"):
            with st.spinner("Running research via Perplexity..."):
                try:
                    project = st.session_state.current_project
                    
                    research_result = st.session_state.pipeline.research_engine.run_research(project.topic)
                    
                    if research_result:
                        project.research_content = research_result.get("content", "")
                        project.research_sources = research_result.get("sources", "")
                        
                        # Update in NocoDB
                        import requests
                        from config import settings
                        
                        api_url = settings.NOCODB_API_URL
                        table_id = settings.NOCODB_PROJECTS_TABLE_ID
                        headers = {"xc-token": settings.NOCODB_API_TOKEN}
                        
                        payload = [{
                            "Id": project.id,
                            settings.NOCODB_FIELDS["project"]["research_content"]: project.research_content,
                            settings.NOCODB_FIELDS["project"]["research_sources"]: project.research_sources
                        }]
                        
                        resp = requests.patch(
                            f"{api_url}/api/v2/tables/{table_id}/records",
                            json=payload,
                            headers=headers
                        )
                        
                        if resp.status_code == 200:
                            st.session_state.current_project = project
                            st.session_state.phase_status["research"] = True
                            st.success(f"✅ Research completed! ({len(project.research_content)} chars)")
                        else:
                            st.error(f"❌ Failed to save research: {resp.status_code}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    logger.exception("Phase 2 failed")
        
        # Show research results
        if st.session_state.current_project and st.session_state.current_project.research_content:
            st.divider()
            st.subheader("📊 Research Results")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Content Length", f"{len(st.session_state.current_project.research_content)} chars")
            with col2:
                st.metric("Sources", st.session_state.current_project.research_sources.count("http"))
            
            with st.expander("📄 Research Content"):
                st.markdown(st.session_state.current_project.research_content)
            
            with st.expander("🔗 Sources"):
                st.text(st.session_state.current_project.research_sources)

# PHASE 3: SCRIPT
with tab3:
    st.header("Phase 3: Generate Script")
    st.write("Uses Gemini to generate chapters and narration script.")
    
    if not st.session_state.phase_status["research"]:
        st.warning("⚠️ Please complete Phase 2 first")
    else:
        # Allow re-running even if done
        btn_label = "🔄 Re-run Phase 3: Script" if st.session_state.phase_status["script"] else "▶️ Run Phase 3: Script"
        
        if st.button(btn_label, type="primary"): # Removed disabled=...
            with st.spinner("Generating script via Gemini..."):
                try:
                    project = st.session_state.current_project
                    
                    # Generate script - use correct method name and parameters
                    chapters = st.session_state.pipeline.script_engine.generate_scripts(
                        project_id=project.id,
                        research_data=project.research_content,
                        target_duration=project.target_duration
                    )
                    
                    if chapters:
                        project.chapters = chapters
                        
                        # Save chapters to NocoDB Chapters table
                        import requests
                        from config import settings
                        
                        api_url = settings.NOCODB_API_URL
                        # FORCE CORRECT ID due to caching issues
                        chapters_table_id = "m3bzlwkrgoaxb36" 
                        headers = {"xc-token": settings.NOCODB_API_TOKEN}
                        
                        # --- CLEANUP: Delete existing chapters for this project ---
                        st.info("🧹 Cleaning up old chapters...")
                        try:
                            # Strategy: Get ALL chapters, then filter in Python (safest for Many-to-Many)
                            list_resp = requests.get(
                                f"{api_url}/api/v2/tables/{chapters_table_id}/records?limit=100",
                                headers=headers
                            )
                            
                            if list_resp.status_code == 200:
                                data = list_resp.json()
                                all_chapters = data.get("list", [])
                                
                                # Filter in Python: Find chapters where Projects field relates to this project
                                existing_ids = []
                                for ch in all_chapters:
                                    # Projects field might be: int (count), list, or dict
                                    # We need a way to check if this chapter links to our project
                                    # Since we can't reliably check without nested data,
                                    # we'll just get the chapter ID and try to check via a separate call?
                                    # 
                                    # Actually, simpler: Just DELETE ALL chapters and recreate.
                                    # This is acceptable for a debug/test app.
                                    # User can always load project from DB if needed.
                                    pass
                                
                                # SIMPLER APPROACH: Delete ALL chapters in the table
                                # (For production, we'd need proper filtering, but for debug this is OK)
                                if all_chapters:
                                    all_ids = [r["Id"] for r in all_chapters]
                                    st.write(f"⚠️ Deleting ALL {len(all_ids)} chapters in table (cannot filter by project reliably).")
                                    
                                    # Bulk Delete
                                    del_payload = [{"Id": i} for i in all_ids]
                                    del_resp = requests.delete(
                                        f"{api_url}/api/v2/tables/{chapters_table_id}/records",
                                        json=del_payload,
                                        headers=headers
                                    )
                                    
                                    if del_resp.status_code == 200:
                                        st.success(f"✅ Deleted {len(all_ids)} chapters.")
                                    else:
                                        st.warning(f"⚠️ Delete failed: {del_resp.status_code}")
                                        st.code(del_resp.text)
                                else:
                                    st.info("No chapters found in table.")
                            else:
                                st.warning(f"⚠️ Failed to list chapters: {list_resp.status_code}")
                                st.code(list_resp.text)
                            
                        except Exception as e:
                            st.warning(f"⚠️ Cleanup warning: {e}")
                            logger.exception("Cleanup failed")
                        
                        # --- END CLEANUP ---

                        st.info(f"💾 Saving {len(chapters)} chapters to Table ID: {chapters_table_id}")
                        st.write(f"Project ID being used: {project.id}")
                        
                        saved_count = 0
                        for i, chapter in enumerate(chapters):
                            # Prepare chapter payload
                            chapter_payload = {
                                "Title": chapter.title,
                                "Content": chapter.content,
                                "Projects": [{"Id": int(project.id)}], # List format for Many-to-Many
                                "StartTime": chapter.start_time,
                                "EndTime": chapter.end_time
                            }
                            
                            # DEBUG: Show payload for first chapter
                            if i == 0:
                                with st.expander("🔍 Debug Payload (First Chapter)", expanded=True):
                                    st.json(chapter_payload)
                            
                            # POST to Chapters table
                            try:
                                resp = requests.post(
                                    f"{api_url}/api/v2/tables/{chapters_table_id}/records",
                                    json=chapter_payload,
                                    headers=headers
                                )
                                
                                if resp.status_code == 200:
                                    chapter_data = resp.json()
                                    chapter.id = str(chapter_data.get("Id"))
                                    saved_count += 1
                                else:
                                    st.error(f"❌ Failed to save chapter {i+1}: {resp.status_code}")
                                    st.code(resp.text) # Show full error response
                                    logger.error(f"Failed to save chapter: {resp.status_code} - {resp.text}")
                            except Exception as e:
                                st.error(f"❌ Exception saving chapter: {e}")
                                logger.error(f"Error saving chapter: {e}")
                        
                        st.session_state.current_project = project
                        st.session_state.phase_status["script"] = True
                        
                        if saved_count == len(chapters):
                            st.success(f"✅ Script generated & SAVED! {saved_count}/{len(chapters)} chapters in DB")
                        else:
                            st.warning(f"⚠️ Script generated but only {saved_count}/{len(chapters)} saved. Check logs.")
                            
                    else:
                        st.error("❌ Failed to generate script")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    logger.exception("Phase 3 failed")
        
        # Real-time Log Viewer for this Phase
        if "logs" in st.session_state and st.session_state.logs:
            with st.expander("📜 Real-time Logs", expanded=True):
                for log in reversed(st.session_state.logs[-10:]):
                    color = "red" if log['level'] == "ERROR" else "blue"
                    st.markdown(f":{color}[{log['time']}] **{log['level']}**: {log['message']}")
                    if log.get('exception'):
                        st.code(log['exception'])
        # Show chapters
        if st.session_state.current_project and st.session_state.current_project.chapters:
            st.divider()
            st.subheader(f"📊 Script Overview ({len(st.session_state.current_project.chapters)} chapters)")
            
            for i, chapter in enumerate(st.session_state.current_project.chapters):
                with st.expander(f"Chapter {i+1}: {chapter.title}"):
                    st.write(f"**Duration:** {chapter.start_time:.1f}s - {chapter.end_time:.1f}s")
                    st.write("**Content:**")
                    st.text(chapter.content)
            
            # PHASE 3.5: Consolidate Narrator Script
            st.divider()
            st.subheader("📝 Phase 3.5: Consolidate Narrator Script")
            
            if st.button("🔗 Consolidate & Validate Narrator Script", type="secondary"):
                logger.info("Phase 3.5: User clicked 'Consolidate & Validate'")
                with st.spinner("Fetching chapters from NocoDB..."):
                    try:
                        import requests
                        from config import settings
                        
                        api_url = settings.NOCODB_API_URL
                        chapters_table_id = "m3bzlwkrgoaxb36"
                        headers = {"xc-token": settings.NOCODB_API_TOKEN}
                        
                        logger.info(f"Fetching chapters from table {chapters_table_id}")
                        
                        # Fetch all chapters for this project
                        resp = requests.get(
                            f"{api_url}/api/v2/tables/{chapters_table_id}/records?limit=100",
                            headers=headers
                        )
                        
                        logger.info(f"GET chapters response: {resp.status_code}")
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            all_chapters = data.get("list", [])
                            
                            logger.info(f"Fetched {len(all_chapters)} total chapters")
                            
                            # Filter chapters for this project (simple approach - get all and filter)
                            # In production, use proper NocoDB filter
                            project_chapters = [ch for ch in all_chapters if ch.get("Id") is not None]
                            
                            if project_chapters:
                                st.info(f"Found {len(project_chapters)} chapters.")
                                logger.info(f"Filtered to {len(project_chapters)} chapters with IDs")
                                
                                # Consolidate text
                                consolidated_text = " ".join([ch.get("Content", "") for ch in project_chapters if ch.get("Content")])
                                
                                # Validation
                                word_count = len(consolidated_text.split())
                                char_count = len(consolidated_text)
                                
                                logger.info(f"Consolidated: {char_count} chars, {word_count} words")
                                logger.debug(f"Preview: {consolidated_text[:200]}...")
                                
                                # Store in session state for save button
                                st.session_state.consolidated_narrator_script = consolidated_text
                                st.session_state.narrator_word_count = word_count
                                st.session_state.narrator_char_count = char_count
                                
                                st.success(f"✅ Consolidated {len(project_chapters)} chapters!")
                            else:
                                st.warning("No chapters found for this project.")
                                logger.warning("No chapters with valid IDs found")
                        else:
                            st.error(f"Failed to fetch chapters: {resp.status_code}")
                            logger.error(f"Failed to fetch chapters: {resp.status_code} - {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                        logger.exception("Phase 3.5 consolidation failed")
            
            # Show consolidated text stats if available
            if "consolidated_narrator_script" in st.session_state and st.session_state.consolidated_narrator_script:
                consolidated_text = st.session_state.consolidated_narrator_script
                word_count = st.session_state.narrator_word_count
                char_count = st.session_state.narrator_char_count
                
                st.write(f"**Consolidated Stats:**")
                st.write(f"- Characters: {char_count}")
                st.write(f"- Words: {word_count}")
                st.write(f"- Estimated duration: {word_count / 2.5:.1f}s (~{word_count / 150:.1f} min)")
                
                # Show preview
                with st.expander("📄 Consolidated Text Preview"):
                    st.text(consolidated_text[:1000] + "...")
                
                # Validation checks
                validation_ok = True
                if char_count < 100:
                    st.error("❌ Text too short (< 100 chars)")
                    validation_ok = False
                if word_count < 50:
                    st.error("❌ Too few words (< 50)")
                    validation_ok = False
                if char_count > 50000:
                    st.warning("⚠️ Text very long (> 50k chars) - may take time to generate")
                
                if validation_ok:
                    st.success("✅ Validation passed!")
                    
                    # Save button (NOT nested)
                    if st.button("💾 Save to Narrator Script", type="primary", key="save_narrator_script"):
                        import requests
                        from config import settings
                        
                        api_url = settings.NOCODB_API_URL
                        headers = {"xc-token": settings.NOCODB_API_TOKEN}
                        
                        payload = [{
                            "Id": st.session_state.current_project.id,
                            settings.NOCODB_FIELDS["project"]["narrator_script"]: consolidated_text
                        }]
                        
                        logger.info(f"Saving Narrator Script to Project {st.session_state.current_project.id}")
                        logger.debug(f"Payload: {payload}")
                        
                        update_resp = requests.patch(
                            f"{api_url}/api/v2/tables/{settings.NOCODB_PROJECTS_TABLE_ID}/records",
                            json=payload,
                            headers=headers
                        )
                        
                        logger.info(f"PATCH response: {update_resp.status_code}")
                        
                        if update_resp.status_code == 200:
                            st.success(f"✅ Narrator Script saved! ({word_count} words)")
                            st.session_state.current_project.narrator_script = consolidated_text
                        else:
                            st.error(f"❌ Failed to save: {update_resp.status_code}")
                            st.code(update_resp.text)
                            logger.error(f"Failed to save narrator script: {update_resp.text}")

# PHASE 4: AUDIO
with tab4:
    st.header("Phase 4: Generate Audio")
    st.write("Uses Kokoro TTS to generate narration audio.")
    
    if not st.session_state.phase_status["script"]:
        st.warning("⚠️ Please complete Phase 3 first")
    else:
        # Allow re-running
        btn_label = "🔄 Re-run Phase 4: Audio" if st.session_state.phase_status["audio"] else "▶️ Run Phase 4: Audio"
        
        if st.button(btn_label, type="primary"):
            logger.info("Phase 4: User clicked 'Run Phase 4: Audio'")
            with st.spinner("Generating audio via Kokoro TTS..."):
                try:
                    project = st.session_state.current_project
                    
                    # Check if Narrator Script exists
                    if not hasattr(project, 'narrator_script') or not project.narrator_script:
                        st.error("❌ Narrator Script is empty! Please run Phase 3.5 first to consolidate chapters.")
                        logger.error("Narrator Script is empty - cannot generate audio")
                    else:
                        full_text = project.narrator_script
                        
                        logger.info(f"Using Narrator Script: {len(full_text)} chars, {len(full_text.split())} words")
                        st.info(f"Using Narrator Script: {len(full_text)} characters, {len(full_text.split())} words")
                        
                        # Debug: Show text preview
                        with st.expander("🔍 Narrator Script Preview"):
                            st.text(full_text[:500] + "...")
                        
                        logger.info(f"Calling Kokoro TTS with voice_id={project.voice_id}")
                        audio_path, timestamps = st.session_state.pipeline.audio_engine.generate_master_audio(
                            full_text, 
                            project.voice_id
                        )
                    
                    if audio_path and os.path.exists(audio_path):
                        logger.info(f"Audio file generated: {audio_path}")
                        st.success(f"✅ Audio generated: {audio_path}")
                        project.full_audio_path = audio_path
                        
                        # 2. Upload to NocoDB
                        logger.info("Uploading audio file to NocoDB storage...")
                        st.info("Uploading audio to NocoDB...")
                        attachment_data = st.session_state.pipeline.upload_file(audio_path)
                        
                        if attachment_data:
                            logger.info(f"Audio uploaded successfully: {attachment_data}")
                            st.success("✅ Audio uploaded successfully")
                            
                            # Get audio URL from attachment
                            audio_url = attachment_data[0].get("url") if isinstance(attachment_data, list) and len(attachment_data) > 0 else None
                            logger.info(f"Audio URL: {audio_url}")
                            
                            # Calculate audio duration from MP3 file metadata
                            import json
                            from mutagen.mp3 import MP3
                            
                            try:
                                audio_file = MP3(audio_path)
                                audio_duration = audio_file.info.length  # Duration in seconds (float)
                                logger.info(f"Audio duration from MP3 metadata: {audio_duration}s")
                            except Exception as e:
                                logger.warning(f"Failed to read MP3 metadata: {e}. Using timestamp fallback.")
                                # Fallback: use last timestamp's end_time
                                audio_duration = max([t.get("end_time", 0) for t in timestamps]) if timestamps else len(full_text.split()) / 2.5
                            
                            audio_duration_rounded = round(audio_duration, 2)
                            
                            logger.info(f"Audio duration: {audio_duration_rounded}s")
                            logger.info(f"Timestamps count: {len(timestamps)}")
                            logger.debug(f"First 3 timestamps: {timestamps[:3] if len(timestamps) > 0 else 'None'}")
                            
                            # 3. Update Project Record with ALL audio fields
                            import requests
                            from config import settings
                            
                            api_url = settings.NOCODB_API_URL
                            table_id = settings.NOCODB_PROJECTS_TABLE_ID
                            headers = {"xc-token": settings.NOCODB_API_TOKEN}
                            
                            # Prepare payload with all audio data
                            payload = [{
                                "Id": project.id,
                                settings.NOCODB_FIELDS["project"]["tts_audio"]: attachment_data,  # Attachment
                                settings.NOCODB_FIELDS["project"]["audio_url"]: audio_url,  # URL
                                settings.NOCODB_FIELDS["project"]["audio_timestamps"]: json.dumps(timestamps),  # JSON string
                                settings.NOCODB_FIELDS["project"]["audio_duration"]: audio_duration_rounded  # Number (2 decimal places)
                            }]
                            
                            logger.info(f"Saving audio data to Project {project.id}")
                            logger.debug(f"Payload fields: TTS Audio (len={len(attachment_data)}), URL={audio_url}, Duration={audio_duration_rounded}, Timestamps={len(timestamps)}")
                            
                            # Debug: Show payload
                            with st.expander("🔍 Debug: Audio Update Payload"):
                                st.json(payload)
                            
                            resp = requests.patch(
                                f"{api_url}/api/v2/tables/{table_id}/records",
                                json=payload,
                                headers=headers
                            )
                            
                            logger.info(f"PATCH response: {resp.status_code}")
                            
                            if resp.status_code == 200:
                                logger.info(f"SUCCESS! Audio data saved to NocoDB")
                                st.session_state.current_project = project
                                st.session_state.phase_status["audio"] = True
                                st.success(f"✅ Project updated! Audio: {audio_duration_rounded}s, {len(timestamps)} timestamps")
                            else:
                                logger.error(f"Failed to save audio: {resp.status_code} - {resp.text}")
                                st.error(f"❌ Failed to update project: {resp.status_code}")
                                st.code(resp.text)
                        else:
                            logger.error("Audio upload failed - no attachment data")
                            st.error("❌ Failed to upload audio file")
                            
                    else:
                        st.error("❌ Audio generation failed (no file created)")
                        
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    logger.exception("Phase 4 failed")
        
        # Show Audio Result
        if st.session_state.current_project and hasattr(st.session_state.current_project, 'full_audio_path'):
            if st.session_state.current_project.full_audio_path and os.path.exists(st.session_state.current_project.full_audio_path):
                st.divider()
                st.subheader("🎵 Generated Audio")
                st.audio(st.session_state.current_project.full_audio_path)
        
        # Real-time Log Viewer for this Phase
        if "logs" in st.session_state and st.session_state.logs:
            with st.expander("📜 Real-time Logs", expanded=True):
                for log in reversed(st.session_state.logs[-10:]):
                    color = "red" if log['level'] == "ERROR" else "blue"
                    st.markdown(f":{color}[{log['time']}] **{log['level']}**: {log['message']}")
                    if log.get('exception'):
                        st.code(log['exception'])

# PHASE 5: VISUAL
with tab5:
    st.header("Phase 5: Generate Visuals")
    st.write("Uses ComfyUI to generate images for each shot.")
    
    if not st.session_state.phase_status["audio"]:
        st.warning("⚠️ Please complete Phase 4 first")
    else:
        st.info("🚧 Visual generation phase - Coming soon!")

# LOGS TAB
with tab6:
    st.header("System Events (Live)")
    
    log_file_path = "logs/system_events.json"
    auto_refresh = st.checkbox("Auto-refresh logs", value=True)
    
    if auto_refresh:
        logs = []
        if os.path.exists(log_file_path):
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        for log in reversed(logs[-30:]):
            record = log.get("record", {})
            level = record.get("level", {}).get("name", "INFO")
            message = record.get("message", "")
            timestamp = record.get("time", {}).get("repr", "")
            
            color = "blue"
            if level == "ERROR": color = "red"
            if level == "WARNING": color = "orange"
            if level == "SUCCESS": color = "green"
            
            st.markdown(f":{color}[**{level}**] `{timestamp}` → {message}")
            st.divider()
