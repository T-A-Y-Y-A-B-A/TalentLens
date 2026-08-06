RESUME_EXTRACTION_PROMPT = """
You are an expert HR assistant. Your task is to extract structured information from the following resume text.
Extract the candidate's name, email, phone number, a list of skills, work experience, education history, certifications, and notable projects.

CRITICAL SCHEMA INSTRUCTIONS:
- For 'experience', you MUST return a list of objects with the exact keys: 'title' (for role/position), 'company' (for organization), 'start_date', 'end_date', and 'description'. Do NOT use 'role' or 'organization'.
- For 'education', use the exact keys: 'degree', 'institution', and 'graduation_year'.
- For 'projects', return a list of objects with the exact keys: 'name' and 'description'.

If a piece of information is not found in the resume, leave it empty or omit it. Do not invent information.

Resume Text:
{text}
"""
