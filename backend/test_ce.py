from sentence_transformers import CrossEncoder
import math

jd = "Lead a team of engineers to build scalable backend systems using Python and AWS."
resume = "Architected and deployed scalable backend microservices using Python, FastAPI, and Docker on AWS. Led a team of 5 engineers to migrate legacy monolithic systems to a modern distributed architecture."

for model_name in ['cross-encoder/ms-marco-MiniLM-L-6-v2', 'cross-encoder/stsb-MiniLM-L6-v2']:
    ce = CrossEncoder(model_name)
    score = ce.predict([jd, resume])
    
    if 'ms-marco' in model_name:
        sig_score = 1 / (1 + math.exp(-score))
        pct = sig_score * 100.0
    else:
        # STSB outputs 0-1
        pct = score * 100.0
        
    print(f"{model_name}: score={score:.4f}, pct={pct:.2f}%")
