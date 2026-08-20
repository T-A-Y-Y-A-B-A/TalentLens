from app.workers.tasks.keyword_matching import match_candidate_to_all_jobs
import asyncio

def verify():
    cand_padded = "d6cc9904-5167-4f26-8b77-378ac1ba7233"
    cand_strong = "b2ff0918-2c6d-4995-af0f-7afbbcc0bf86"
    
    print("\n--- Testing match_candidate_to_all_jobs (Padded) ---")
    match_candidate_to_all_jobs(cand_padded)
    print("match_candidate_to_all_jobs (Padded) completed successfully.")
    
    print("\n--- Testing match_candidate_to_all_jobs (Strong) ---")
    match_candidate_to_all_jobs(cand_strong)
    print("match_candidate_to_all_jobs (Strong) completed successfully.")

if __name__ == "__main__":
    verify()
