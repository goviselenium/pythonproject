import sys
from pathlib import Path

# Add project root to python path to prevent ModuleNotFoundError when running streamlit
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
import json
from src import config

from src.resume_reader import read_resume
from src.database import (
    init_db,
    insert_scraped_jobs,
    get_all_jobs,
    get_jobs_by_status,
    update_job_analysis,
    update_job_status,
    get_db_stats,
    clear_database
)
from src.apify_scraper import ApifyJobScraper
from src.gemini_matcher import GeminiMatcher
from src.exporter import export_to_csv, export_to_excel

# Initialize database schema
init_db()

st.set_page_config(
    page_title="AI Resume-Job Search Agent",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# CSS Styling for Premium Aesthetics
# ----------------------------------------------------
st.markdown("""
<style>
    /* Main Layout Styling */
    .main {
        background-color: #fafbfc;
        padding-top: 1rem;
    }
    
    /* Title styling */
    .title-container {
        padding: 1.5rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    .title-container h1 {
        margin: 0;
        font-family: 'Outfit', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .title-container p {
        margin: 5px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Metrics panel */
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 5px solid #1e3c72;
        text-align: center;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1e3c72;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Custom Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-apply {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .badge-customize {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
    }
    .badge-skip {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    /* Section dividers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2a5298;
        border-bottom: 2px solid #e9ecef;
        padding-bottom: 5px;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Form controls styling */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Main Header
# ----------------------------------------------------
st.markdown("""
<div class="title-container">
    <h1>💼 AI Resume-Job Search Agent</h1>
    <p>Automate remote QA Automation & SDET job scraping, analyze fit using Gemini, and tailor application materials instantly.</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Sidebar Inputs
# ----------------------------------------------------
st.sidebar.image("https://img.icons8.com/clouds/100/job.png", width=80)
st.sidebar.markdown("### ⚙️ Setup & Credentials")

# Secrets inputs
apify_token = st.sidebar.text_input(
    "Apify API Token",
    value=config.APIFY_API_TOKEN,
    type="password",
    help="Get from https://console.apify.com/account#/integrations"
)

gemini_key = st.sidebar.text_input(
    "Gemini API Key",
    value=config.GEMINI_API_KEY,
    type="password",
    help="Get from https://aistudio.google.com/"
)

gemini_model = st.sidebar.selectbox(
    "Gemini Model",
    options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📄 Master Resume Selection")

# Scan input folder for resumes
available_resumes = []
for file in config.INPUT_DIR.glob("*"):
    if file.suffix.lower() in [".txt", ".docx"] and not file.name.startswith("."):
        available_resumes.append(file.name)

uploaded_file = st.sidebar.file_uploader("Upload new resume (.txt or .docx)", type=["txt", "docx"])
if uploaded_file is not None:
    # Save uploaded file to input folder
    save_path = config.INPUT_DIR / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"Saved: {uploaded_file.name}")
    # Refresh resume list
    if uploaded_file.name not in available_resumes:
        available_resumes.append(uploaded_file.name)

# Select resume
selected_resume_file = None
if available_resumes:
    # Try to default to master_resume.txt or .docx
    default_idx = 0
    if "master_resume.txt" in available_resumes:
        default_idx = available_resumes.index("master_resume.txt")
    elif "master_resume.docx" in available_resumes:
        default_idx = available_resumes.index("master_resume.docx")
        
    selected_resume_file = st.sidebar.selectbox(
        "Choose master resume",
        options=available_resumes,
        index=default_idx
    )
else:
    st.sidebar.warning("No resumes found. Please upload a .txt or .docx resume.")

# Preview Resume content
resume_text = ""
if selected_resume_file:
    try:
        resume_text = read_resume(config.INPUT_DIR / selected_resume_file)
        with st.sidebar.expander("🔍 Preview Selected Resume"):
            st.text(resume_text[:1000] + ("..." if len(resume_text) > 1000 else ""))
    except Exception as e:
        st.sidebar.error(f"Error reading resume: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Scraping Controls")

# Scraping settings
search_role = st.sidebar.selectbox(
    "Target Job Role",
    options=config.TARGET_ROLES,
    index=0
)

remote_only = st.sidebar.checkbox("Limit search to Remote", value=True)

job_limit = st.sidebar.slider(
    "Max Jobs to Scrape",
    min_value=1,
    max_value=50,
    value=config.DEFAULT_JOB_LIMIT
)

apify_actor = st.sidebar.text_input(
    "Apify Actor ID",
    value=config.APIFY_ACTOR_ID,
    help="Defaults to johnvc/google-jobs-scraper"
)

# ----------------------------------------------------
# Dashboard Actions (Trigger buttons)
# ----------------------------------------------------
st.sidebar.markdown("### 🚀 Operations")

col_scrape, col_match = st.sidebar.columns(2)

# Trigger job scraping
if col_scrape.button("1. Scrape Jobs", use_container_width=True):
    if not apify_token:
        st.sidebar.error("Apify API Token is required.")
    else:
        scraper = ApifyJobScraper(api_token=apify_token)
        query = f"{search_role} remote" if remote_only else search_role
        
        with st.status(f"Scraping '{query}' jobs from Apify...", expanded=True) as status:
            try:
                scraped_data = scraper.scrape_jobs(query, limit=job_limit, actor_id=apify_actor)
                if scraped_data:
                    new_count = insert_scraped_jobs(scraped_data)
                    status.update(label="Scraping completed!", state="complete", expanded=False)
                    st.toast(f"Scraped {len(scraped_data)} jobs. {new_count} new entries added to database!", icon="🎉")
                else:
                    status.update(label="No jobs found or error occurred.", state="error", expanded=False)
                    st.warning("Apify returned 0 results. Check your Actor configuration or search query.")
            except Exception as e:
                status.update(label=f"Scraping failed: {e}", state="error")
                st.exception(e)

# Trigger Gemini Matching
if col_match.button("2. Analyze Fit", use_container_width=True):
    if not gemini_key:
        st.sidebar.error("Gemini API Key is required.")
    elif not resume_text:
        st.sidebar.error("Please provide a valid resume first.")
    else:
        pending_jobs = get_jobs_by_status("scraped")
        if not pending_jobs:
            st.sidebar.warning("No pending scraped jobs to analyze. Click 'Scrape Jobs' first.")
        else:
            matcher = GeminiMatcher(api_key=gemini_key, model_name=gemini_model)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            analyzed_count = 0
            error_count = 0
            
            for idx, job in enumerate(pending_jobs):
                status_text.markdown(f"**Analyzing {idx+1}/{len(pending_jobs)}**: {job['title']} at *{job['company']}*")
                progress_bar.progress((idx) / len(pending_jobs))
                
                try:
                    analysis = matcher.analyze_job(
                        resume_text=resume_text,
                        job_title=job['title'],
                        company=job['company'],
                        job_description=job['description']
                    )
                    update_job_analysis(job['id'], analysis)
                    analyzed_count += 1
                except Exception as e:
                    print(f"Failed to analyze job {job['id']}: {e}")
                    update_job_status(job['id'], "error")
                    error_count += 1
                    
            progress_bar.progress(1.0)
            status_text.empty()
            st.toast(f"Analysis completed: {analyzed_count} succeeded, {error_count} failed.", icon="🤖")

# Clear Database
if st.sidebar.button("🧹 Clear All Stored Data", use_container_width=True):
    clear_database()
    st.sidebar.success("Database cleared successfully!")
    st.rerun()

# ----------------------------------------------------
# Main Content Area
# ----------------------------------------------------
stats = get_db_stats()

# KPI Metrics Panel
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{stats.get("total", 0)}</div>
        <div class="metric-label">Total Jobs Stored</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid #28a745;">
        <div class="metric-val">{stats.get("avg_score", 0.0)}%</div>
        <div class="metric-label">Avg Match Score</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid #28a745;">
        <div class="metric-val">
            <span style="color:#28a745">{stats.get("apply", 0)}</span> / 
            <span style="color:#ffc107">{stats.get("customize", 0)}</span> / 
            <span style="color:#dc3545">{stats.get("skip", 0)}</span>
        </div>
        <div class="metric-label">Apply / Customize / Skip</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid #ffc107;">
        <div class="metric-val">{stats.get("scraped", 0)}</div>
        <div class="metric-label">Pending Analysis</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# Interactive Jobs Table & Filters
# ----------------------------------------------------
st.markdown("<div class='section-header'>📋 Scraped & Analyzed Jobs</div>", unsafe_allow_html=True)

all_jobs = get_all_jobs()

if not all_jobs:
    st.info("The database is currently empty. Use the sidebar settings to scrape and analyze jobs!")
else:
    # Convert DB rows to Pandas DataFrame for filtering
    df_raw = pd.DataFrame(all_jobs)
    
    # Quick filter sidebar/header widgets
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    
    with col_f1:
        rec_filter = st.selectbox(
            "Filter by Recommendation",
            options=["All", "Apply", "Customize Resume", "Skip", "Pending Analysis"]
        )
        
    with col_f2:
        score_filter = st.slider("Filter by Minimum Score", 0, 100, 0)
        
    with col_f3:
        search_query = st.text_input("Search Job Title or Company", value="")

    # Apply Filters
    df = df_raw.copy()
    
    # Filter by Recommendation status
    if rec_filter == "Pending Analysis":
        df = df[df["status"] == "scraped"]
    elif rec_filter != "All":
        df = df[(df["status"] == "analyzed") & (df["recommendation"] == rec_filter)]
    else:
        # Don't show jobs that failed with errors unless requested
        df = df[df["status"] != "error"]
        
    # Filter by Score
    if "score" in df.columns:
        # Replace NaN with 0 for sorting/filtering
        df["score"] = df["score"].fillna(0).astype(int)
        df = df[df["score"] >= score_filter]
        
    # Search Query
    if search_query:
        df = df[
            df["title"].str.contains(search_query, case=False, na=False) |
            df["company"].str.contains(search_query, case=False, na=False)
        ]
        
    # Render table
    if df.empty:
        st.warning("No jobs match the active filters.")
    else:
        # Select columns to display
        display_cols = ["id", "score", "recommendation", "title", "company", "location", "url", "posted_at"]
        df_display = df[[c for c in display_cols if c in df.columns]].copy()
        df_display.columns = [c.capitalize() for c in df_display.columns]
        
        st.dataframe(
            df_display, 
            column_config={
                "Url": st.column_config.LinkColumn("Job Posting Link"),
                "Id": st.column_config.NumberColumn("DB ID", width="small")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # ----------------------------------------------------
        # Exports
        # ----------------------------------------------------
        st.markdown("##### 📥 Export Reports")
        col_csv, col_xlsx = st.columns(2)
        
        # Generate export files
        analyzed_list = [j for j in all_jobs if j.get("status") == "analyzed"]
        
        if analyzed_list:
            # Generate exports on the fly
            csv_path = export_to_csv(analyzed_list)
            xlsx_path = export_to_excel(analyzed_list)
            
            with open(csv_path, "r", encoding="utf-8") as f:
                csv_data = f.read()
                
            with open(xlsx_path, "rb") as f:
                xlsx_data = f.read()
                
            col_csv.download_button(
                label="📥 Download CSV Report",
                data=csv_data,
                file_name="job_matches_report.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            col_xlsx.download_button(
                label="📥 Download Excel Report (Styled)",
                data=xlsx_data,
                file_name="job_matches_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.caption("No analyzed jobs available yet to export. Complete fit analysis first.")

        # ----------------------------------------------------
        # Job Detail Viewer
        # ----------------------------------------------------
        st.markdown("<div class='section-header'>🔍 Job Match Details & Tailored Content</div>", unsafe_allow_html=True)
        
        # Select job for detailed view
        analyzed_jobs = df[df["status"] == "analyzed"]
        
        if analyzed_jobs.empty:
            st.info("Select a recommendation filter and run analysis to populate details.")
        else:
            job_options = {
                f"{row['title']} at {row['company']} (Score: {row['score']}%)": row['id']
                for _, row in analyzed_jobs.iterrows()
            }
            
            selected_job_label = st.selectbox(
                "Select a job to view analysis & tailored content:",
                options=list(job_options.keys())
            )
            
            selected_job_id = job_options[selected_job_label]
            job_detail = df_raw[df_raw["id"] == selected_job_id].iloc[0].to_dict()
            
            # Match badge colors
            rec_val = job_detail.get("recommendation", "Skip")
            badge_class = "badge-skip"
            if rec_val == "Apply":
                badge_class = "badge-apply"
            elif rec_val == "Customize Resume":
                badge_class = "badge-customize"
                
            # Score and status banner
            st.markdown(f"""
            <div style="padding:15px; background-color:#f1f3f5; border-radius:8px; margin-bottom:20px;">
                <h3>{job_detail.get('title')} at <strong>{job_detail.get('company')}</strong></h3>
                <p style="font-size:1.1rem; margin:0;">
                    Match Score: <strong style="font-size:1.3rem; color:#1e3c72;">{job_detail.get('score')}%</strong> | 
                    Recommendation: <span class="badge {badge_class}">{rec_val}</span>
                </p>
                <p style="font-size:0.95rem; color:#6c757d; margin:5px 0 0 0;">
                    Location: 📍 {job_detail.get('location')} | URL: <a href="{job_detail.get('url')}" target="_blank">{job_detail.get('url')}</a>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Skills side by side
            try:
                matched_skills = json.loads(job_detail.get("matched_skills", "[]"))
                missing_skills = json.loads(job_detail.get("missing_skills", "[]"))
            except Exception:
                matched_skills = [job_detail.get("matched_skills")]
                missing_skills = [job_detail.get("missing_skills")]
                
            col_sk1, col_sk2 = st.columns(2)
            
            with col_sk1:
                st.markdown("##### ✅ Matched Skills")
                if matched_skills:
                    for skill in matched_skills:
                        st.markdown(f"- `{skill}`")
                else:
                    st.caption("No matching skills identified.")
                    
            with col_sk2:
                st.markdown("##### ❌ Missing / Weak Skills")
                if missing_skills:
                    for skill in missing_skills:
                        st.markdown(f"- `{skill}`")
                else:
                    st.caption("No missing skills identified! Great match.")
                    
            st.markdown("##### 📝 Match Explanation")
            st.write(job_detail.get("explanation", "N/A"))
            
            # Tabs for Tailored Content
            tab_sum, tab_bul, tab_cov, tab_lin, tab_desc = st.tabs([
                "✨ Tailored Resume Summary", 
                "✍️ Tailored Resume Bullets", 
                "✉️ Customized Cover Letter", 
                "💬 LinkedIn Outreach", 
                "📄 Raw Job Description"
            ])
            
            with tab_sum:
                st.markdown("##### Tailored Professional Summary")
                summary_text = job_detail.get("tailored_summary", "")
                st.write(summary_text)
                st.button(
                    "Copy Summary to Clipboard", 
                    key="btn_copy_sum", 
                    on_click=lambda: st.toast("Summary copied! (Use Ctrl+C to copy selected text)")
                )
                
            with tab_bul:
                st.markdown("##### Tailored Resume Bullets")
                try:
                    bullets = json.loads(job_detail.get("tailored_bullets", "[]"))
                except Exception:
                    bullets = [job_detail.get("tailored_bullets", "")]
                    
                if bullets:
                    bullet_text = ""
                    for bullet in bullets:
                        st.markdown(f"- {bullet}")
                        bullet_text += f"- {bullet}\n"
                else:
                    st.caption("No tailored bullets generated.")
                st.button(
                    "Copy Bullets to Clipboard", 
                    key="btn_copy_bul", 
                    on_click=lambda: st.toast("Bullets copied! (Use Ctrl+C to copy selected text)")
                )
                
            with tab_cov:
                st.markdown("##### Tailored Cover Letter")
                cover_letter = job_detail.get("cover_letter", "")
                st.text_area("Cover Letter Text", value=cover_letter, height=350, key="txt_cov")
                
            with tab_lin:
                st.markdown("##### LinkedIn Recruiter outreach message")
                ln_msg = job_detail.get("linkedin_message", "")
                st.text_area("LinkedIn Message", value=ln_msg, height=150, key="txt_lin")
                st.caption(f"Character Count: {len(ln_msg)} / 300 characters limit")
                if len(ln_msg) > 300:
                    st.warning("This message exceeds 300 characters and may not fit in a LinkedIn connection request note.")
                    
            with tab_desc:
                st.markdown("##### Raw Job Description Text")
                st.text_area("Job Description", value=job_detail.get("description", ""), height=350, key="txt_desc")
