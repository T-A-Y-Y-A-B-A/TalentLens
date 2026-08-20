from sqlalchemy import create_engine, MetaData
from app.core.config import settings

def print_schema(table_name):
    # settings.SQLALCHEMY_DATABASE_URI uses asyncpg, replace with psycopg2 for sync
    sync_uri = settings.SQLALCHEMY_DATABASE_URI.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(sync_uri)
    metadata = MetaData()
    metadata.reflect(bind=engine, only=[table_name])
    table = metadata.tables[table_name]
    
    print(f"\\d {table_name}")
    print(f"{'Column':<30} | {'Type':<20} | {'Nullable'}")
    print("-" * 65)
    for c in table.columns:
        print(f"{c.name:<30} | {str(c.type):<20} | {c.nullable}")
    print("")

if __name__ == "__main__":
    print_schema("job_matches")
    print_schema("job_embeddings")
