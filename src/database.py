import sqlite3
import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_key TEXT UNIQUE,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        description TEXT,
        url TEXT,
        posted_at TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Analysis fields
        score INTEGER,
        matched_skills TEXT,   -- JSON array
        missing_skills TEXT,   -- JSON array
        recommendation TEXT,  -- 'Apply', 'Customize Resume', 'Skip'
        explanation TEXT,
        
        -- Tailored Outputs
        tailored_summary TEXT,
        tailored_bullets TEXT, -- JSON array
        cover_letter TEXT,
        linkedin_message TEXT,
        
        -- Pipeline Status
        status TEXT DEFAULT 'scraped' -- 'scraped', 'analyzed', 'error'
    )
    """)
    conn.commit()
    conn.close()

def generate_job_key(title: str, company: str, url: str) -> str:
    """Generates a unique stable hash key for a job posting."""
    # Use title + company + url to uniquely identify a posting
    unique_str = f"{title.lower().strip()}_{company.lower().strip()}_{url.strip()}"
    return hashlib.md5(unique_str.encode("utf-8")).hexdigest()

def insert_scraped_jobs(jobs: List[Dict[str, Any]]) -> int:
    """
    Inserts a list of scraped jobs into the database.
    Ignores duplicates using INSERT OR IGNORE.
    Returns the number of newly added jobs.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    new_jobs_count = 0
    
    for job in jobs:
        title = job.get("title", "Unknown Title")
        company = job.get("company", "Unknown Company")
        url = job.get("url", "")
        job_key = generate_job_key(title, company, url)
        
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO jobs (
                    job_key, title, company, location, description, url, posted_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'scraped')
                """,
                (
                    job_key,
                    title,
                    company,
                    job.get("location", "Remote"),
                    job.get("description", ""),
                    url,
                    job.get("posted_at", ""),
                )
            )
            if cursor.rowcount > 0:
                new_jobs_count += 1
        except Exception as e:
            print(f"Error inserting job {title} at {company}: {e}")
            
    conn.commit()
    conn.close()
    return new_jobs_count

def get_jobs_by_status(status: str) -> List[Dict[str, Any]]:
    """Retrieves all jobs with a specific pipeline status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE status = ?", (status,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_jobs() -> List[Dict[str, Any]]:
    """Retrieves all jobs from the database, ordered by score descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY score DESC, scraped_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_job_analysis(job_id: int, analysis: Dict[str, Any], status: str = 'analyzed'):
    """Updates a job record with LLM matching and tailored application content."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    matched_skills_json = json.dumps(analysis.get("matched_skills", []))
    missing_skills_json = json.dumps(analysis.get("missing_skills", []))
    tailored_bullets_json = json.dumps(analysis.get("tailored_bullets", []))
    
    cursor.execute(
        """
        UPDATE jobs
        SET score = ?,
            matched_skills = ?,
            missing_skills = ?,
            recommendation = ?,
            explanation = ?,
            tailored_summary = ?,
            tailored_bullets = ?,
            cover_letter = ?,
            linkedin_message = ?,
            status = ?
        WHERE id = ?
        """,
        (
            analysis.get("score"),
            matched_skills_json,
            missing_skills_json,
            analysis.get("recommendation"),
            analysis.get("explanation"),
            analysis.get("tailored_summary"),
            tailored_bullets_json,
            analysis.get("cover_letter"),
            analysis.get("linkedin_message"),
            status,
            job_id
        )
    )
    conn.commit()
    conn.close()

def update_job_status(job_id: int, status: str):
    """Updates only the status of a job (e.g., to 'error')."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()

def get_db_stats() -> Dict[str, Any]:
    """Computes summary statistics of the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total
    cursor.execute("SELECT COUNT(*) FROM jobs")
    stats["total"] = cursor.fetchone()[0]
    
    # Scraped (Pending)
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'scraped'")
    stats["scraped"] = cursor.fetchone()[0]
    
    # Analyzed
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'analyzed'")
    stats["analyzed"] = cursor.fetchone()[0]
    
    # Error
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'error'")
    stats["error"] = cursor.fetchone()[0]
    
    # Recommendations counts
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'analyzed' AND recommendation = 'Apply'")
    stats["apply"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'analyzed' AND recommendation = 'Customize Resume'")
    stats["customize"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'analyzed' AND recommendation = 'Skip'")
    stats["skip"] = cursor.fetchone()[0]
    
    # Average Score
    cursor.execute("SELECT AVG(score) FROM jobs WHERE status = 'analyzed'")
    avg_score = cursor.fetchone()[0]
    stats["avg_score"] = round(avg_score, 1) if avg_score is not None else 0.0
    
    conn.close()
    return stats

def clear_database():
    """Drops all entries from the jobs table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()
