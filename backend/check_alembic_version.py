from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/intellipdf.db')
with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM alembic_version'))
    for row in result:
        print(row)
