import asyncio
from qdrant_client import models
from app.core.qdrant import qdrant_client

async def switch_aliases():
    print("--- 1. Switching Aliases ---")
    
    # In Qdrant, to overwrite an alias we can use update_aliases, which takes a list of operations
    # If the alias does not exist or was a collection, we might need to handle that.
    # Qdrant default behavior for create_alias doesn't replace an existing collection with the same name.
    # But earlier, we confirmed `jobs` and `candidates` are collections, not aliases yet.
    # If they are collections, we cannot create an alias with the same name without deleting the collection first.
    # We must delete the old collections `jobs` and `candidates` and create them as aliases pointing to `jobs_v2` and `candidates_v2`.
    
    collections_response = await qdrant_client.get_collections()
    collection_names = [c.name for c in collections_response.collections]
    
    if "jobs" in collection_names:
        print("Deleting old 'jobs' collection to create alias...")
        await qdrant_client.delete_collection("jobs")
    
    if "candidates" in collection_names:
        print("Deleting old 'candidates' collection to create alias...")
        await qdrant_client.delete_collection("candidates")
        
    print("Creating aliases...")
    await qdrant_client.update_collection_aliases(
        change_aliases_operations=[
            models.CreateAliasOperation(
                create_alias=models.CreateAlias(
                    collection_name="jobs_v2",
                    alias_name="jobs"
                )
            ),
            models.CreateAliasOperation(
                create_alias=models.CreateAlias(
                    collection_name="candidates_v2",
                    alias_name="candidates"
                )
            )
        ]
    )
    
    print("\n--- 2. Verifying Aliases ---")
    j_count = (await qdrant_client.count(collection_name="jobs")).count
    c_count = (await qdrant_client.count(collection_name="candidates")).count
    
    print(f"Jobs Alias Count: {j_count}")
    print(f"Candidates Alias Count: {c_count}")
    
    print("\nJobs Alias Spot Check:")
    j_points, _ = await qdrant_client.scroll(collection_name="jobs", limit=2, with_vectors=True)
    for p in j_points:
        vecs = p.vector.keys() if hasattr(p.vector, "keys") else p.vector
        print(f"  Point {p.id}: {vecs}")
        
    print("\nCandidates Alias Spot Check:")
    c_points, _ = await qdrant_client.scroll(collection_name="candidates", limit=2, with_vectors=True)
    for p in c_points:
        vecs = p.vector.keys() if hasattr(p.vector, "keys") else p.vector
        print(f"  Point {p.id}: {vecs}")

if __name__ == "__main__":
    asyncio.run(switch_aliases())
