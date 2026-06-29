# 💼 AI Resume-Job Search Agent

An automated career agent designed to scrape remote QA Automation, SDET, and Test Automation Lead jobs using Apify, match and score them against your master resume using the Gemini API, and generate customized resume summaries, bullets, cover letters, and recruiter outreach messages. All managed through an interactive Streamlit dashboard.

---

## 🌟 Key Features
1. **Master Resume Extraction**: Automatically reads and extracts content from `.txt` and `.docx` master resumes.
2. **Apify Job Scraping**: Queries remote job postings using the Apify actor (default: `johnvc/google-jobs-scraper`).
3. **Structured Gemini Matching**: Uses Google's official `google-genai` Python SDK to perform a detailed comparison.
4. **Smart Scoring**: Automatically rates job fit from 0 to 100 and classifies listings into *Apply*, *Customize Resume*, or *Skip*.
5. **Tailored Material Generation**: Instantly produces:
   - Customized resume professional summaries.
   - Tailored achievement-oriented resume bullet points.
   - High-quality cover letters.
   - Snappy LinkedIn recruiter outreach messages (strictly under 300 characters).
6. **Robust SQLite Caching**: Saves scraped jobs locally to prevent duplicate processing, preserve API credits, and support progress recovery.
7. **Reports Export**: Generates professional, styled Excel spreadsheets and clean CSV reports of matched roles.
8. **Interactive Streamlit Dashboard**: Search, filter, view details, copy tailored contents, and manage keys/scraping parameters in a premium UI.

---

## 🛠️ Project Structure
```
resume-job-search-agent/
│
├── .env                  # Local secrets configuration (APIFY & GEMINI keys)
├── .env.example          # Template environment config
├── .gitignore            # Git ignore file (excludes virtualenvs, DBs, and keys)
├── README.md             # This instructions file
├── requirements.txt      # Python dependencies list
├── jobs.db               # SQLite database cache (auto-created)
│
├── input/                # Folder for master resumes
│   └── master_resume.txt # Example/your master resume
│
├── output/               # Exports destination (Excel / CSV)
│
├── src/                  # Source package code
│   ├── __init__.py
│   ├── app.py            # Streamlit Dashboard UI
│   ├── config.py         # App configurations
│   ├── resume_reader.py  # Parses TXT/DOCX files
│   ├── apify_scraper.py  # Apify actor integration
│   ├── gemini_matcher.py # Gemini Structured API matcher
│   ├── database.py       # Cache and SQLite storage operations
│   └── exporter.py       # Excel and CSV export helpers
│
└── tests/                # Test suite
    ├── __init__.py
    ├── test_resume_reader.py
    ├── test_apify_scraper.py
    └── test_gemini_matcher.py
```

---

## 🚀 Setup & Installation (Windows)

Follow these step-by-step instructions to get the application running on Windows:

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system. You can check this by running:
```powershell
python --version
```

### 2. Create a Virtual Environment
Navigate to the project root directory and create a virtual environment:
```powershell
cd d:\JobSearchPortal\JobSearch\resume-job-search-agent
python -m venv venv
```

### 3. Activate the Virtual Environment
Activate the environment in your shell:
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
Install all required libraries:
```powershell
pip install -r requirements.txt
```

### 5. Setup Environment Variables
1. Copy the `.env.example` file to create a `.env` file:
   ```powershell
   copy .env.example .env
   ```
2. Open `.env` in a text editor and fill in your API keys:
   - **APIFY_API_TOKEN**: Get your token from the [Apify Console](https://console.apify.com/account#/integrations).
   - **GEMINI_API_KEY**: Get your free/paid API key from [Google AI Studio](https://aistudio.google.com/).

---

## 🏃 Running the Application

### 1. Prepare your Resume
Ensure your master resume is placed inside the `input/` folder:
- Filename: `master_resume.txt` or `master_resume.docx`
- A pre-filled template has already been created for you at `input/master_resume.txt`.

### 2. Start the Streamlit Dashboard
From the project root (with the virtual environment activated), launch Streamlit:
```powershell
streamlit run src/app.py
```

Streamlit will compile and launch the dashboard in your default browser at `http://localhost:8501`.

---

## 🤖 How to Use the Dashboard

1. **Configure API Keys**: If you didn't define keys in `.env`, you can type them directly into the sidebar text fields.
2. **Select Master Resume**: Pick your resume from the list of files in the `input` directory. You can preview it inside the sidebar expander.
3. **Set Scraping Parameters**: Choose your target role (e.g. `Test Automation Lead`), enable remote search, set the maximum number of jobs, and customize the Apify Actor ID if desired.
4. **Trigger Scraping**: Click **1. Scrape Jobs**. This triggers the Apify scraper to find matching listings and saves them into your local SQLite cache.
5. **Run Fit Analysis**: Click **2. Analyze Fit**. This matches each scraped job against your resume using Gemini, scores the fit (0-100), extracts skills, and generates customized content.
6. **Filter & Browse**: Browse jobs in the interactive table. Search by keywords or filter by score and recommendation (Apply, Customize Resume, Skip).
7. **Review Tailored Outputs**: Select any job to view detailed match explanations, side-by-side skill comparisons, and tabs containing your tailored Summary, Bullets, Cover Letter, and LinkedIn Outreach messages.
8. **Export**: Click the download buttons to save your results to Excel or CSV.

---

## 🧪 Running Unit Tests

Run the test suite using `pytest` to verify the components function correctly:
```powershell
pytest
```
This runs the unit tests for the resume parser, SQLite database schema, Apify scraper formats, and Gemini mock calls.
