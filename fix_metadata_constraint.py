"""
修复 metadata 列的 NOT NULL 约束
"""

import sqlite3
from pathlib import Path

db_path = Path("backend/data/intellipdf.db")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("修复 annotations 表的 metadata 列...")

try:
    # SQLite 不支持直接修改列约束，需要重建表
    # 1. 创建新表
    print("1. 创建临时表...")
    cursor.execute("""
        CREATE TABLE annotations_new (
            id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36) NOT NULL,
            annotation_type VARCHAR(32) NOT NULL,
            page_number INTEGER NOT NULL,
            position JSON,
            color VARCHAR(20),
            content TEXT,
            tags JSON NOT NULL DEFAULT '[]',
            metadata JSON,  -- 改为可空
            data TEXT,
            user_name VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)

    # 2. 复制数据
    print("2. 复制现有数据...")
    cursor.execute("""
        INSERT INTO annotations_new 
        SELECT * FROM annotations
    """)

    # 3. 删除旧表
    print("3. 删除旧表...")
    cursor.execute("DROP TABLE annotations")

    # 4. 重命名新表
    print("4. 重命名新表...")
    cursor.execute("ALTER TABLE annotations_new RENAME TO annotations")

    # 5. 创建索引
    print("5. 重建索引...")
    cursor.execute(
        "CREATE INDEX idx_annotations_document ON annotations(document_id)")
    cursor.execute("CREATE INDEX idx_annotations_user ON annotations(user_id)")
    cursor.execute(
        "CREATE INDEX idx_annotations_type ON annotations(annotation_type)")
    cursor.execute(
        "CREATE INDEX idx_annotations_page ON annotations(page_number)")

    conn.commit()
    print("\n✅ 修复完成！metadata 列现在可以为 NULL")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    conn.rollback()
finally:
    conn.close()
