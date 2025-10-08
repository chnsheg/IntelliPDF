"""
快速修复数据库：添加 data 列到 annotations 表

这个脚本用于修复现有数据库，添加新的 data 列（JSON类型）
"""

import sqlite3
from pathlib import Path

db_path = Path("backend/data/intellipdf.db")

if not db_path.exists():
    print(f"❌ 数据库文件不存在: {db_path}")
    exit(1)

print(f"📁 数据库路径: {db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # 检查表结构
    print("\n1. 检查 annotations 表结构...")
    cursor.execute("PRAGMA table_info(annotations)")
    columns = cursor.fetchall()

    print(f"   当前列: {len(columns)} 个")
    for col in columns:
        print(f"      - {col[1]} ({col[2]})")

    # 检查并添加缺失的列
    column_names = [col[1] for col in columns]

    # 需要的列及其类型
    required_columns = {
        'data': 'TEXT',
        'user_name': 'VARCHAR(100)'
    }

    added_count = 0
    for col_name, col_type in required_columns.items():
        if col_name not in column_names:
            print(f"\n2. 添加 {col_name} 列 ({col_type})...")
            cursor.execute(
                f"ALTER TABLE annotations ADD COLUMN {col_name} {col_type}")
            conn.commit()
            print(f"   ✅ {col_name} 列添加成功")
            added_count += 1
        else:
            print(f"\n   ✅ {col_name} 列已存在")

    if added_count == 0:
        print("\n   ℹ️  所有必需的列都已存在")

    # 迁移旧数据：将现有的标注数据转换为新格式
    print("\n3. 检查需要迁移的数据...")
    cursor.execute(
        "SELECT COUNT(*) FROM annotations WHERE data IS NULL OR data = ''")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"   发现 {count} 条需要迁移的标注")
        print("   ⚠️  注意：这些旧标注需要手动迁移或重新创建")
    else:
        print("   ✅ 所有标注数据已完整")

    print("\n" + "=" * 60)
    print("✅ 数据库修复完成！")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ 错误: {e}")
    conn.rollback()
finally:
    conn.close()
