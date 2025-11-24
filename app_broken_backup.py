import streamlit as st
import json
import time
import os
from modules.pipeline_manager import PipelineManager
from utils.logger import logger
from models import Project

# Page Config
st.set_page_config(
    page_title="Storyteller v2.0",
    page_icon="🎬",
    layout="wide"
)

# Initialize Pipeline
if "pipeline" not in st.session_state:
    st.session_state.pipeline = PipelineManager()

st.title("🎬 Storyteller v2.0")

# Tabs
tab_creator, tab_library, tab_debugger, tab_settings = st.tabs(["✨ Creator", "📚 Library", "🐛 Live Debugger", "⚙️ Settings"])

import pandas as pd

# --- REAL-TIME LOGGING SINK ---
class StreamlitSink:
    def __init__(self, container):
        self.container = container
        self.logs = []
        
    def write(self, message):
        # Message is already formatted string from Loguru
        self.logs.append(message)
        # Keep last 15 lines to avoid UI clutter
        if len(self.logs) > 15:
            self.logs = self.logs[-15:]
            
        # Update the container
        log_content = "".join(self.logs)
        self.container.code(log_content, language="text")

# --- TAB 1: CREATOR ---
with tab_creator:
    st.header("Create New Story")
    
    with st.form("story_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            topic = st.text_input("Topic", placeholder="e.g. The History of Coffee")
            voice = st.selectbox("Voice", ["am_michael", "Heart", "Bella", "Adam"])
            duration = st.number_input("Target Duration (minutes)", min_value=1, max_value=90, value=3, step=1)
            image_provider = st.selectbox("Image Provider", ["ComfyUI", "DALL-E 3"])
        
        with col2:
            st.subheader("Style Configuration")
            lora1_name = None
            lora1_strength = 1.0
            
            if image_provider == "ComfyUI":
                lora1_name = st.text_input("LoRA 1 Name", placeholder="e.g. cinematic_v2")
                lora1_strength = st.slider("LoRA 1 Strength", 0.0, 2.0, 1.0)
                
                # Expandable for more advanced settings
                with st.expander("Advanced ComfyUI Settings"):
                    lora2_name = st.text_input("LoRA 2 Name", placeholder="Optional")
                    lora2_strength = st.slider("LoRA 2 Strength", 0.0, 2.0, 1.0)
        
        submitted = st.form_submit_button("🚀 Start Production")
        
    # Real-time logs container
    logs_container = st.empty()
        
    if submitted and topic:
        st.info(f"Starting production for: {topic}")
        
        # Initialize Sink
        sink = StreamlitSink(logs_container)
        handler_id = logger.add(sink.write, format="{time:HH:mm:ss} | {level} | {message}")
        
        # Create Project Object
        project_data = Project(
            topic=topic,
            target_duration=duration,
            voice_id=voice,
            image_provider=image_provider,
            lora1_name=lora1_name,
            lora1_strength=lora1_strength
        )
        
        try:
            # Run Pipeline
            project = st.session_state.pipeline.run_full_production(project_data)
            st.success("Production Completed!")
            st.json(project.model_dump())
        except Exception as e:
            st.error(f"Production failed: {e}")
            logger.exception("Production failed")
        finally:
            # Remove handler to clean up
            logger.remove(handler_id)

# --- TAB 2: LIBRARY ---
with tab_library:
    st.header("Project Library")
    
    col_tools, col_refresh = st.columns([4, 1])
    with col_refresh:
        if st.button("🔄 Refresh"):
            st.rerun()
            
    from services import get_all_stories
    stories = get_all_stories()
    
    if not stories:
        st.info("No stories found. Create one in the Creator tab!")
    else:
        # Convert to DataFrame for better visualization
        df = pd.DataFrame(stories)
        
        # Select columns to display
        display_cols = ['id', 'topic', 'status', 'created_at', 'audio_duration']
        # Filter to only existing columns
        display_cols = [c for c in display_cols if c in df.columns]
        
        # Main Data Editor
        st.subheader("All Projects")
        selected_project_id = None
        
        # Use a selection event if possible, or just show the table
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        
        # Project Details Selector
        project_options = {f"{s['id']}: {s['topic']}": s['id'] for s in stories}
        selected_option = st.selectbox("Select Project to View Details", options=list(project_options.keys()))
        
        if selected_option:
            selected_id = project_options[selected_option]
            story = next((s for s in stories if s['id'] == selected_id), None)
            
            if story:
                st.divider()
                st.subheader(f"Details: {story['topic']}")
                
                tab_details, tab_script, tab_tech, tab_actions = st.tabs(["Media & Info", "Script", "Technical Data", "⚙️ Actions"])
                
                with tab_details:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.markdown(f"**Status:** {story['status']}")
                        st.markdown(f"**Created:** {story['created_at']}")
                        st.markdown(f"**Duration:** {story.get('audio_duration', 0)}s")
                        
                        # Audio Player
                        audio_path = story.get('full_audio_path')
                        if audio_path and os.path.exists(audio_path):
                            st.audio(audio_path)
                            st.caption(f"Path: `{audio_path}`")
                        elif audio_path:
                            st.warning(f"Audio file missing: {audio_path}")
                        else:
                            st.info("No audio generated yet.")
                            
                        if st.button("🗑️ Delete Project", key=f"del_{story['id']}", type="primary"):
                            from services import delete_story
                            if delete_story(story['id']):
                                st.success("Deleted!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to delete.")
                                
                    with col2:
                        # Fetch Chapters
                        from utils.database import db
                        chapters = db.get_chapters(story['id'])
                        if chapters:
                            st.write(f"**Chapters ({len(chapters)}):**")
                            chapters_df = pd.DataFrame(chapters)
                            st.dataframe(
                                chapters_df[['title', 'start_time', 'end_time', 'visual_desc']], 
                                use_container_width=True, 
                                hide_index=True
                            )
                        else:
                            st.info("No chapters found.")

                with tab_script:
                    st.text_area("Full Script", story.get('script_content', ''), height=400)
                    
                with tab_tech:
                    st.json(story)
                    
                with tab_actions:
                    st.warning("⚠️ Regeneration will overwrite existing data for that phase!")
                    
                    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                    
                    # Helper to reconstruct Project object
                    def get_project_obj(story_dict):
                        # We need to reconstruct the Project object for the pipeline
                        # This is a bit of a hack, ideally we'd load it fully from DB
                        # For now, we populate what we can
                        p = Project(
                            topic=story_dict['topic'],
                            target_duration=1, # Default or fetch if stored
                            voice_id=story_dict.get('voice_id', 'am_michael'),
                            image_provider=story_dict.get('image_provider', 'ComfyUI')
                        )
                        p.id = str(story_dict['id'])
                        p.research_content = story_dict.get('research_content')
                        p.research_sources = story_dict.get('research_sources')
                        
                        # Load chapters if needed
                        chapters_data = db.get_chapters(story_dict['id'])
                        if chapters_data:
                            from models import Chapter
                            p.chapters = [Chapter(**c) for c in chapters_data]
                            
                        return p

                    with col_a1:
                        if st.button("1️⃣ Research", key=f"run_res_{story['id']}", help="Run or Re-run Research Phase"):
                            with st.spinner("Running Research..."):
                                try:
                                    proj = get_project_obj(story)
                                    st.session_state.pipeline.run_research_phase(proj)
                                    st.success("Research Complete!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                                    logger.exception("Research failed")

                    with col_a2:
                        if st.button("2️⃣ Script", key=f"run_scr_{story['id']}", help="Generate Script from Research"):
                            with st.spinner("Generating Script..."):
                                try:
                                    proj = get_project_obj(story)
                                    st.session_state.pipeline.run_script_phase(proj)
                                    st.success("Script Generated!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                                    logger.exception("Script generation failed")

                    with col_a3:
                        if st.button("3️⃣ Audio (Kokoro)", key=f"run_aud_{story['id']}", help="Generate Audio from Script"):
                            with st.spinner("Generating Audio..."):
                                try:
                                    proj = get_project_obj(story)
                                    st.session_state.pipeline.run_audio_phase(proj)
                                    st.success("Audio Generated!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                                    logger.exception("Audio generation failed")
                                    
                    with col_a4:
                        if st.button("4️⃣ Visuals", key=f"run_vis_{story['id']}", help="Generate Visuals from Script"):
                            with st.spinner("Generating Visuals..."):
                                try:
                                    proj = get_project_obj(story)
                                    st.session_state.pipeline.run_visuals_phase(proj)
                                    st.success("Visuals Generated!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                                    logger.exception("Visuals generation failed")
                                    
                    # --- INTERACTIVE RESEARCH ---
                    st.markdown("---")
                    st.subheader("🕵️ Interactive Research")
                    
                    # Session State for Interactive Research
                    if f"research_draft_{story['id']}" not in st.session_state:
                         st.session_state[f"research_draft_{story['id']}"] = story.get('research_content', "")

                    col_ir1, col_ir2 = st.columns([1, 3])
                    
                    with col_ir1:
                        if st.button("Generate Research Draft", key=f"gen_res_draft_{story['id']}"):
                            with st.spinner("Researching..."):
                                try:
                                    proj = get_project_obj(story)
                                    # Call engine directly
                                    res_data = st.session_state.pipeline.research_engine.run_research(proj.topic)
                                    st.session_state[f"research_draft_{story['id']}"] = res_data['content']
                                    st.success("Draft Generated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                    
                    with col_ir2:
                        # Editable Text Area
                        new_research_content = st.text_area(
                            "Research Content (Editable)", 
                            value=st.session_state[f"research_draft_{story['id']}"],
                            height=300,
                            key=f"res_area_{story['id']}"
                        )
                        
                        if st.button("💾 Save Research", key=f"save_res_{story['id']}"):
                            try:
                                from services import update_story
                                update_story(story['id'], research_content=new_research_content)
                                st.success("Research Saved to Database!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Save failed: {e}")

                    # --- INTERACTIVE SCRIPTING ---
                    st.markdown("---")
                    st.subheader("✍️ Interactive Scripting")
                    
                    # Session State for Interactive Scripting
                    if f"outline_{story['id']}" not in st.session_state:
                        st.session_state[f"outline_{story['id']}"] = []
                    
                    # Step 1: Research Context
                    with st.expander("Step 1: Review Research", expanded=False):
                        st.text_area("Research Content", story.get('research_content', 'No research found.'), height=200, disabled=True)
                        
                    # Step 2: Outline Generation
                    st.markdown("#### Step 2: Outline")
                    if st.button("Generate Outline", key=f"gen_outline_{story['id']}"):
                        with st.spinner("Generating Outline..."):
                            try:
                                proj = get_project_obj(story)
                                # Use the exposed method directly
                                outline = st.session_state.pipeline.script_engine.generate_outline(
                                    proj.research_content, 
                                    proj.target_duration
                                )
                                st.session_state[f"outline_{story['id']}"] = [{"title": t} for t in outline]
                                st.success("Outline Generated!")
                            except Exception as e:
                                st.error(f"Failed: {e}")
                    
                    # Editable Outline
                    if st.session_state[f"outline_{story['id']}"]:
                        edited_outline = st.data_editor(
                            st.session_state[f"outline_{story['id']}"],
                            num_rows="dynamic",
                            key=f"editor_{story['id']}",
                            column_config={
                                "title": st.column_config.TextColumn("Chapter Title", width="large")
                            }
                        )
                        st.session_state[f"outline_{story['id']}"] = edited_outline
                        
                    # Step 3: Chapter Generation
                    st.markdown("#### Step 3: Content Generation")
                    
                    # Check for existing chapters
                    existing_chapters = db.get_chapters(story['id'])
                    if existing_chapters:
                        st.info(f"Found {len(existing_chapters)} existing chapters.")
                        with st.expander("View Existing Chapters", expanded=False):
                            for c in existing_chapters:


                    if st.button(gen_btn_label, key=gen_btn_key, disabled=not st.session_state[f"outline_{story['id']}"]):
                        with st.spinner("Writing Chapters..."):
                            # Create a container for logs
                            script_log_container = st.empty()
                            sink = StreamlitSink(script_log_container)
                            handler_id = logger.add(sink.write, format="{time:HH:mm:ss} | {level} | {message}")
                            
                            try:
                                proj = get_project_obj(story)
                                outline_titles = [item["title"] for item in st.session_state[f"outline_{story['id']}"]]
                                
                                # Manual generation loop to show progress
                                total_words = proj.target_duration * 150
                                chapter_words = int(total_words / len(outline_titles))
                                context_buffer = ""
                                new_chapters = []
                                current_time = 0.0
                                
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for i, title in enumerate(outline_titles):
                                    status_text.text(f"Writing chapter {i+1}/{len(outline_titles)}: {title}...")
                                    
                                    content = st.session_state.pipeline.script_engine.generate_chapter_content(
                                        title=title,
                                        research_data=proj.research_content,
                                        context=context_buffer,
                                        target_words=chapter_words
                                    )
                                    
                                    # Estimate duration
                                    actual_words = len(content.split())
                                    duration = actual_words / 2.5
                                    
                                    from models import Chapter
                                    chapter = Chapter(
                                        title=title,
                                        content=content,
                                        start_time=current_time,
                                        end_time=current_time + duration
                                    )
                                    new_chapters.append(chapter)
                                    
                                    context_buffer += f"\nChapter {i+1} ({title}): {content[:200]}..."
                                    current_time += duration
                                    progress_bar.progress((i + 1) / len(outline_titles))
                                    
                                # Save to DB
                                status_text.text("Saving to database...")
                                chapters_data = [c.dict() for c in new_chapters]
                                db.save_chapters(story['id'], chapters_data)
                                
                                # Update project script content (NO markdown headers)
                                full_script = "\n\n".join([c.content for c in new_chapters])
                                from services import update_story
                                update_story(story['id'], script_content=full_script)
                                
                                st.success("Script Generated & Saved!")
                                
                                # Show Result
                                st.subheader("Generated Script Preview")
                                for c in new_chapters:
                                    with st.expander(f"Chapter: {c.title} ({c.duration:.1f}s)", expanded=False):
                                        st.write(c.content)
                                        
                            except Exception as e:
                                st.error(f"Failed: {e}")
                                logger.exception("Interactive script generation failed")
                            finally:
                                # Remove the sink handler
                                logger.remove(handler_id)
                    
                    # --- Full Script Editor ---
                    if story.get('script_content'):
                        st.markdown("#### 📝 Full Script Editor (Pre-Audio)")
                        st.caption("This is the text that will be sent to Kokoro TTS. You can make final edits here.")
                        # Session state for script editing
                        if f"full_script_{story['id']}" not in st.session_state:
                            st.session_state[f"full_script_{story['id']}"] = story['script_content']
                            
                        edited_script = st.text_area(
                            "Full Script",
                    col_aud1, col_aud2 = st.columns([1, 2])
                    
                    with col_aud1:
                        if st.button("🎵 Start Kokoro Audio Generation", key=f"start_kokoro_{story['id']}"):
                            with st.spinner("Generating Audio with Kokoro..."):
                                # Log container
                                audio_log_container = st.empty()
                                sink = StreamlitSink(audio_log_container)
                                handler_id = logger.add(sink.write, format="{time:HH:mm:ss} | {level} | {message}")
                                
                                try:
                                    proj = get_project_obj(story)
                                    
                                    # Ensure we use the LATEST script content from DB/Session
                                    # (get_project_obj pulls from story dict which might be stale if not re-fetched)
                                    # But st.rerun() in previous steps should have refreshed 'story' via get_all_stories()
                                    
                                    updated_proj = st.session_state.pipeline.run_audio_phase(proj)
                                    
                                    st.success("Audio Generation Complete!")
                                    
                                    # Validation & Display
                                    st.markdown("#### Validation Results")
                                    
                                    # 1. Check Path
                                    if updated_proj.full_audio_path and os.path.exists(updated_proj.full_audio_path):
                                        st.success(f"✅ Audio File Created: `{updated_proj.full_audio_path}`")
                                        st.audio(updated_proj.full_audio_path)
                                    else:
                                        st.error("❌ Audio File Missing!")
                                        
                                    # 2. Check Duration (fetch from DB to be sure or use returned obj)
                                    # The pipeline updates DB, so let's fetch fresh data to verify persistence
                                    from services import get_story
                                    fresh_story = get_story(story['id'])
                                    duration = fresh_story.get('audio_duration', 0.0)
                                    
                                    if duration > 0:
                                        st.success(f"✅ Duration Valid: {duration:.2f}s")
                                    else:
                                        st.warning("⚠️ Duration is 0s (Possible generation issue)")
                                        
                                    # 3. Check Timestamps
                                    timestamps = fresh_story.get('audio_timestamps')
                                    if timestamps and len(timestamps) > 5: # Arbitrary check for non-empty
                                        st.success("✅ Timestamps Generated")
                                    else:
                                        st.warning("⚠️ Timestamps missing or empty")
                                        
                                except Exception as e:
                                    st.error(f"Audio Generation Failed: {e}")
                                    logger.exception("Interactive audio failed")
                                finally:
                                    logger.remove(handler_id)
                    
                    with col_aud2:
                        # Show current audio state if exists (and not just generated)
                        if story.get('full_audio_path') and os.path.exists(story['full_audio_path']):
                            st.info("Current Audio:")
                            st.audio(story['full_audio_path'])
                            st.caption(f"Duration: {story.get('audio_duration', 0)}s")

                    # --- INTERACTIVE VISUALS ---
                    st.markdown("---")
                    st.subheader("🎨 Interactive Visuals")
                    
                    # Helper to flatten shots for editor
                    def get_all_shots_data(chapters):
                        data = []
                        for c_idx, c in enumerate(chapters):
                            for s_idx, s in enumerate(c.shots):
                                data.append({
                                    "chapter_idx": c_idx,
                                    "shot_idx": s_idx,
                                    "chapter_title": c.title,
                                    "visual_desc": s.visual_desc,
                                    "comfy_prompt": s.comfy_prompt,
                                    "image_path": s.image_path
                                })
                        return data

                    # Step 1: Plan Shots
                    if st.button("Plan Visuals (Generate Prompts)", key=f"plan_vis_{story['id']}"):
                        with st.spinner("Planning Shots..."):
                            try:
                                proj = get_project_obj(story)
                                # Call plan_shots directly
                                updated_chapters = st.session_state.pipeline.visual_director.plan_shots(proj.chapters)
                                
                                # Save planned shots to DB immediately
                                chapters_data = [c.dict() for c in updated_chapters]
                                db.save_chapters(story['id'], chapters_data)
                                st.success("Visuals Planned! You can now edit prompts below.")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Planning failed: {e}")
                                logger.exception("Visual planning failed")

                    # Step 2: Edit Prompts & Generate
                    current_chapters = db.get_chapters(story['id'])
                    if current_chapters:
                        # Convert to objects for easier handling
                        from models import Chapter
                        chapters_objs = [Chapter(**c) for c in current_chapters]
                        
                        # Check if we have shots
                        has_shots = any(len(c.shots) > 0 for c in chapters_objs)
                        
                        if has_shots:
                            shots_data = get_all_shots_data(chapters_objs)
                            
                            st.info(f"Planned {len(shots_data)} shots. Edit prompts before generating images.")
                            
                            edited_shots = st.data_editor(
                                shots_data,
                                key=f"editor_vis_{story['id']}",
                                column_config={
                                    "chapter_idx": None, # Hide
                                    "shot_idx": None, # Hide
                                    "chapter_title": st.column_config.TextColumn("Chapter", disabled=True),
                                    "visual_desc": st.column_config.TextColumn("Visual Description", width="medium"),
                                    "comfy_prompt": st.column_config.TextColumn("ComfyUI Prompt", width="large"),
                                    "image_path": st.column_config.ImageColumn("Image", width="small")
                                },
                                hide_index=True,
                                num_rows="fixed"
                            )
                            
                            col_v1, col_v2 = st.columns([1, 3])
                            with col_v1:
                                if st.button("🎨 Generate Images", key=f"gen_imgs_{story['id']}"):
                                    with st.spinner("Generating Images (this may take a while)..."):
                                        # Create log sink
                                        vis_log_container = st.empty()
                                        sink = StreamlitSink(vis_log_container)
                                        handler_id = logger.add(sink.write, format="{time:HH:mm:ss} | {level} | {message}")
                                        
                                        try:
                                            # Update objects with edited data
                                            for row in edited_shots:
                                                c_idx = row['chapter_idx']
                                                s_idx = row['shot_idx']
                                                chapters_objs[c_idx].shots[s_idx].visual_desc = row['visual_desc']
                                                chapters_objs[c_idx].shots[s_idx].comfy_prompt = row['comfy_prompt']
                                            
                                            # Run Generation
                                            st.session_state.pipeline.visual_director.generate_images_for_chapters(chapters_objs, story['id'])
                                            
                                            # Save results
                                            chapters_data = [c.dict() for c in chapters_objs]
                                            db.save_chapters(story['id'], chapters_data)
                                            st.success("Images Generated!")
                                            time.sleep(1)
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"Generation failed: {e}")
                                            logger.exception("Image generation failed")
                                        finally:
                                            logger.remove(handler_id)
                            
                            with col_v2:
                                # Gallery Preview
                                images = [s['image_path'] for s in shots_data if s['image_path']]
                                if images:
                                    st.image(images, width=150, caption=[s['comfy_prompt'][:30]+"..." for s in shots_data if s['image_path']])

with tab_debugger:
    st.header("System Events (Live)")
    
    log_container = st.empty()
    log_file_path = "logs/system_events.json"
    
    # Add a button to manually refresh or toggle auto-refresh
    auto_refresh = st.checkbox("Auto-refresh logs", value=True)
    
    if auto_refresh:
        # Read logs
        logs = []
        if os.path.exists(log_file_path):
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # Display logs (reverse order)
        with log_container.container():
            for log in reversed(logs[-20:]): # Show last 20
                record = log.get("record", {})
                level = record.get("level", {}).get("name", "INFO")
                message = record.get("message", "")
                timestamp = record.get("time", {}).get("repr", "")
                module = record.get("name", "")
                func = record.get("function", "")
                
                color = "blue"
                if level == "ERROR": color = "red"
                if level == "WARNING": color = "orange"
                if level == "SUCCESS": color = "green"
                
                st.markdown(
                    f":{color}[**{level}**] `{timestamp}` | *{module}:{func}* -> {message}"
                )
                
                if "exception" in record and record["exception"]:
                    st.error(f"Exception: {record['exception']}")
                
                st.divider()
# --- TAB 4: SETTINGS ---
with tab_settings:
    st.header("⚙️ System Settings")
    
    from utils.prompt_manager import prompt_manager
    
    # Load current prompts
    current_prompts = prompt_manager.load_prompts()
    
    with st.form("settings_form"):
        st.subheader("Research Phase")
        research_system = st.text_area(
            "Research System Prompt", 
            value=current_prompts.get("research_system", ""),
            height=150,
            help="Instructions for the AI researcher."
        )
        
        st.subheader("Script Phase")
        script_outline = st.text_area(
            "Script Outline Prompt", 
            value=current_prompts.get("script_outline", ""),
            height=200,
            help="Instructions for generating the chapter outline. Use {duration} and {research_data} placeholders."
        )
        
        script_chapter = st.text_area(
            "Script Chapter Prompt", 
            value=current_prompts.get("script_chapter", ""),
            height=200,
            help="Instructions for writing chapter content. Use {title}, {context}, {research_data}, {target_words} placeholders."
        )
        
        st.subheader("Visual Phase")
        visual_template = st.text_area(
            "Visual Prompt Template", 
            value=current_prompts.get("visual_comfy_template", ""),
            height=100,
            help="Template for ComfyUI prompts. Use {title} and {visual_desc} placeholders."
        )
        
        if st.form_submit_button("💾 Save Settings"):
            new_prompts = {
                "research_system": research_system,
                "script_outline": script_outline,
                "script_chapter": script_chapter,
                "visual_comfy_template": visual_template
            }
            prompt_manager.save_prompts(new_prompts)
            st.success("Settings saved successfully! New prompts will be used for next operations.")
            
            # Reload pipeline to ensure fresh state if needed (though engines pull from manager dynamically)
            # st.session_state.pipeline = PipelineManager() 
