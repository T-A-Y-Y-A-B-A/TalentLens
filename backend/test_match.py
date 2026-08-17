import sys
import os
sys.path.insert(0, os.getcwd())

from app.workers.tasks.keyword_matching import compute_keyword_match

cand_skills = ['C++', 'Python', 'JavaScript (ES6+)', 'SQL', 'MySQL', 'PostgreSQL', 'React', 'React Native', 'Next.js', 'Node.js', 'Express.js', 'FastAPI', 'Tailwind CSS', 'PyTorch', 'TensorFlow', 'OpenAI API', 'RAG Pipelines', 'BERT / GPT', 'YOLOv8', 'ResNet50', 'MediaPipe', 'MongoDB', 'Neon', 'Vercel', 'Git']
job_reqs = {
    "required_skills": ["Python", "React", "SQL", "FastAPI", "PostgreSQL"]
}

res = compute_keyword_match(cand_skills, job_reqs)
print(f"Match result: {res}")
