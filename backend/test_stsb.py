from sentence_transformers import CrossEncoder

jd = "Lead a team of engineers to build scalable backend systems using Python and AWS."
resume = "Architected and deployed scalable backend microservices using Python, FastAPI, and Docker on AWS. Led a team of 5 engineers to migrate legacy monolithic systems to a modern distributed architecture."

ce = CrossEncoder('cross-encoder/stsb-distilroberta-base')
score = ce.predict([jd, resume])
print(f"STSB output: {score}")
