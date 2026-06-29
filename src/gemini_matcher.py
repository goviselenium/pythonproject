import time
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import APIError
from src.config import GEMINI_API_KEY, GEMINI_MODEL

# Define the Pydantic schema for structured output validation
class JobAnalysis(BaseModel):
    score: int = Field(
        ..., 
        description="Match score from 0 to 100 representing how well the candidate's resume fits the job requirements."
    )
    matched_skills: List[str] = Field(
        ..., 
        description="Core skills required by the job that are present in the candidate's resume."
    )
    missing_skills: List[str] = Field(
        ..., 
        description="Required or preferred skills mentioned in the job description that are missing or weak in the candidate's resume."
    )
    recommendation: str = Field(
        ..., 
        description="Decision recommendation: must be exactly one of 'Apply', 'Customize Resume', or 'Skip'."
    )
    explanation: str = Field(
        ..., 
        description="A concise 2-3 sentence justification explaining the score and recommendation based on the comparison."
    )
    tailored_summary: str = Field(
        ..., 
        description="A tailored 3-4 sentence professional summary for the resume, highlighting matching experience for this specific job."
    )
    tailored_bullets: List[str] = Field(
        ..., 
        description="3 to 5 tailored achievement-oriented resume bullets (in past tense, starting with action verbs) aligning the candidate's background with the job duties."
    )
    cover_letter: str = Field(
        ..., 
        description="A complete, professional, and tailored 3-4 paragraph cover letter addressed to the hiring manager or company."
    )
    linkedin_message: str = Field(
        ..., 
        description="A short, compelling outreach message to send to a recruiter or hiring manager (strict maximum of 300 characters for LinkedIn connection requests)."
    )

class GeminiMatcher:
    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        # Initialize client if key is available
        self.client = genai.Client(api_key=api_key) if api_key else None

    def analyze_job(self, resume_text: str, job_title: str, company: str, job_description: str, retries: int = 3) -> Dict[str, Any]:
        """
        Compares the candidate's resume with a job description using Gemini API.
        Returns a dictionary validated against the JobAnalysis Pydantic schema.
        """
        if not self.api_token_configured():
            raise ValueError(
                "Gemini API key is not set. Please configure GEMINI_API_KEY in your .env "
                "or provide it in the Streamlit interface."
            )

        prompt = f"""
You are an expert career consultant, recruiter, and professional resume writer.
Analyze the following Job Posting against the Candidate's Master Resume.

Candidate's Core Skillset:
Selenium, Playwright, Java, .NET, C#, NUnit, TestNG, Maven, Azure DevOps, Jenkins, CI/CD, API Testing, Manual Testing, Automation Testing, SQL, Security Testing basics, Test Leadership, Agile, LLM Testing beginner.

Master Resume Content:
---
{resume_text}
---

Job Details:
- Title: {job_title}
- Company: {company}
- Job Description:
---
{job_description}
---

Evaluation Rules:
1. **Match Score (0-100)**:
   - 80-100: Excellent fit. The candidate meets almost all required skills and has corresponding leadership/automation experience.
   - 50-79: Good potential fit. Foundational skills (Selenium, Playwright, automation concepts) are present, but there are some missing toolsets or domain requirements. Requires minor customization.
   - 0-49: Poor fit. High mismatch in stack, seniority, or remote expectations.
2. **Recommendation**:
   - 'Apply' (for score >= 80)
   - 'Customize Resume' (for score 50-79)
   - 'Skip' (for score < 50)
3. **Matched Skills**: List exact technical skills matching between the job description and the candidate's resume (e.g. "Selenium", "Java", "CI/CD").
4. **Missing Skills**: List technical skills or frameworks requested in the job description that are NOT in the candidate's resume (e.g. "Python", "Docker", "AWS", etc.).
5. **Tailored Summary**: Write a powerful 3-4 sentence professional summary for the resume, focusing heavily on matching skills.
6. **Tailored Bullets**: Write 3-5 achievement-oriented bullets mapping the candidate's achievements from the master resume to this job's responsibilities.
7. **Cover Letter**: Write a complete 3-4 paragraph professional cover letter targeted to the company and role. Use placeholders like [Hiring Manager] if the name is not known, but make it ready to send.
8. **LinkedIn Message**: Write a short outreach message (MAXIMUM 300 characters, including spaces) to send to a recruiter. Ensure it is highly professional and fits within LinkedIn's connection request limit.

You must return a valid JSON object matching the requested schema.
"""

        backoff = 2
        for attempt in range(retries):
            try:
                # Use GenAI Client call with response_schema
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': JobAnalysis,
                        'temperature': 0.2
                    }
                )
                
                # Check parsed result
                if response.parsed:
                    # Return as dict
                    return response.parsed.model_dump()
                else:
                    raise ValueError("Gemini returned empty or invalid response that could not be parsed.")
                    
            except APIError as e:
                print(f"Gemini API Error on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(backoff)
                backoff *= 2
            except Exception as e:
                print(f"Unexpected error matching job on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(backoff)
                backoff *= 2

        raise RuntimeError("Failed to match job after multiple retries.")

    def api_token_configured(self) -> bool:
        """Returns True if the client is initialized, False otherwise."""
        if not self.client and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        return self.client is not None
