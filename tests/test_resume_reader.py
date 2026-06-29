import pytest
from pathlib import Path
from src.resume_reader import read_resume

def test_read_txt_resume(tmp_path):
    # Create a temporary txt resume
    resume_file = tmp_path / "test_resume.txt"
    resume_content = "John Doe\nQA Engineer\nSkills: Selenium, Python"
    resume_file.write_text(resume_content, encoding="utf-8")
    
    loaded_content = read_resume(resume_file)
    assert "John Doe" in loaded_content
    assert "Selenium" in loaded_content

def test_read_resume_not_found():
    with pytest.raises(FileNotFoundError):
        read_resume("non_existent_resume_file_xyz.txt")

def test_unsupported_format(tmp_path):
    bad_file = tmp_path / "test_resume.pdf"
    bad_file.write_text("dummy pdf contents", encoding="utf-8")
    with pytest.raises(ValueError):
        read_resume(bad_file)
