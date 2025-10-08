from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/intellipdf.db')

with engine.connect() as conn:
    # Create tags table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS tags (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            name VARCHAR(50) NOT NULL,
            color VARCHAR(7) NOT NULL DEFAULT '#3B82F6',
            description TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE (user_id, name)
        )
    """))

    conn.execute(
        text("CREATE INDEX IF NOT EXISTS idx_tags_user ON tags (user_id)"))

    # Create ai_questions table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_questions (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            document_id VARCHAR(36) NOT NULL,
            chunk_id VARCHAR(36),
            selected_text TEXT NOT NULL,
            context_text TEXT,
            user_question TEXT NOT NULL,
            ai_answer TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            position_x FLOAT NOT NULL,
            position_y FLOAT NOT NULL,
            model_used VARCHAR(100) NOT NULL DEFAULT 'gemini-1.5-flash',
            response_metadata JSON,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE,
            FOREIGN KEY(chunk_id) REFERENCES chunks (id) ON DELETE SET NULL
        )
    """))

    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_ai_questions_user_document ON ai_questions (user_id, document_id)"))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_ai_questions_page ON ai_questions (document_id, page_number)"))

    # Add tag_id foreign key to annotations table
    # First check if annotations table exists and has tag_id column
    result = conn.execute(text("PRAGMA table_info(annotations)"))
    columns = [row[1] for row in result]

    if 'tag_id' not in columns:
        # SQLite doesn't support ALTER TABLE ADD FOREIGN KEY, need to recreate table
        print("Note: tag_id column missing in annotations table. You may need to recreate the table.")
    else:
        print("tag_id column already exists in annotations table")

    conn.commit()
    print("Successfully created tags and ai_questions tables")
