import pytest
from unittest.mock import MagicMock, patch
from src.gemini_matcher import GeminiMatcher, JobAnalysis

def test_api_token_configured():
    # Empty token should fail checks
    matcher = GeminiMatcher(api_key="")
    assert matcher.api_token_configured() is False
    
    with pytest.raises(ValueError):
        matcher.analyze_job("Resume", "Title", "Company", "Description")

@patch('src.gemini_matcher.genai.Client')
def test_analyze_job_success(mock_client_class):
    # Setup mock client and return values
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_job_analysis = JobAnalysis(
        score=85,
        matched_skills=["Selenium", "Java"],
        missing_skills=["Docker"],
        recommendation="Apply",
        explanation="Candidate matches core criteria.",
        tailored_summary="Experienced Automation Engineer specializing in Selenium and Java.",
        tailored_bullets=["- Led automation test design.", "- Integrated Playwright tests."],
        cover_letter="Dear Hiring Team, I am writing to apply...",
        linkedin_message="Hi recruiter, let's connect!"
    )
    mock_response.parsed = mock_job_analysis
    mock_client.models.generate_content.return_value = mock_response
    
    matcher = GeminiMatcher(api_key="valid_mock_key")
    analysis = matcher.analyze_job(
        resume_text="Resume details",
        job_title="Automation Engineer",
        company="TechCorp",
        job_description="We need Selenium and Java"
    )
    
    # Assertions
    assert analysis["score"] == 85
    assert "Selenium" in analysis["matched_skills"]
    assert "Docker" in analysis["missing_skills"]
    assert analysis["recommendation"] == "Apply"
    assert "TechCorp" not in analysis["linkedin_message"] # check that mock values are fetched
    mock_client.models.generate_content.assert_called_once()
