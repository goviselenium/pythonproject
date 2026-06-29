import os
from pathlib import Path
from dotenv import load_dotenv

# Find the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(PROJECT_ROOT / ".env")

# Directory Configurations
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
DB_PATH = PROJECT_ROOT / "jobs.db"

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API Keys and tokens
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Gemini Config
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Apify Config
APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "johnvc/google-jobs-scraper")
DEFAULT_JOB_LIMIT = int(os.getenv("DEFAULT_JOB_LIMIT", "10"))

# Target Roles
TARGET_ROLES = [
    "Test Automation Lead",
    "Senior QA Automation Engineer",
    "SDET",
    "Playwright Automation Lead",
    "Selenium Automation Lead",
    "Azure DevOps Test Automation Lead",
    "QA Automation Architect",
    "AI Testing Engineer",
    "LLM Testing QA Engineer"
]

# Master Resume default path
DEFAULT_RESUME_DOCX = INPUT_DIR / "master_resume.docx"
DEFAULT_RESUME_TXT = INPUT_DIR / "master_resume.txt"
