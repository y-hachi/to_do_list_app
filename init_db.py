import sqlite3

conn = sqlite3.connect("app.db")
cur = conn.cursor()

# 外部キー制約を有効にする
cur.execute("PRAGMA foreign_keys = ON")

# 講義管理表
cur.execute("""
CREATE TABLE lectures (
    lecture_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_name TEXT NOT NULL UNIQUE
);
""")

# 課題用表
cur.execute("""
CREATE TABLE assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    due_date TEXT,
    session TEXT,
    status TEXT,
    priority TEXT,
    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
);
""")

#出席管理表
cur.execute("""
CREATE TABLE attendances (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    session TEXT NOT NULL,
    attendance_status TEXT,
    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id),
    UNIQUE(lecture_id, session)  -- ここがポイント
);
""")

#テスト管理表
cur.execute("""
CREATE TABLE tests (
    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    session TEXT,
    test_type TEXT,
    test_date TEXT,
    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
);
""")

# メモ管理表
cur.execute("""
CREATE TABLE memos (
    memo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    content TEXT,
    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
);
""")

# 参考管理表
cur.execute("""
CREATE TABLE resources (
    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    link TEXT,
    description TEXT,
    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
);
""")

print("✅ テーブル作成完了")
conn.commit()
conn.close()
