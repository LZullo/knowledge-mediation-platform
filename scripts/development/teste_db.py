from sqlalchemy import create_engine, text

engine = create_engine(
"postgresql+psycopg://postgres:postgres@localhost:5433/rag_tcc"
)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print(result.fetchone())
