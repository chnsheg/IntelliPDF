from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/intellipdf.db')
with engine.connect() as conn:
    conn.execute(
        text("UPDATE alembic_version SET version_num = '001_initial'"))
    conn.commit()
    print("Updated alembic version to 001_initial")
