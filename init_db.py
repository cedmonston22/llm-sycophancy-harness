import sqlite3

connection = sqlite3.connect("evals.db")
connection.execute("PRAGMA foreign_keys = ON")

connection.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY,
        suite TEXT NOT NULL,
        models TEXT NOT NULL,
        intended_count INTEGER NOT NULL,
        git_sha TEXT,
        started_at TEXT NOT NULL,
        finished_at TEXT
    ) STRICT
""")

connection.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY,
        fingerprint TEXT NOT NULL UNIQUE,
        suite TEXT NOT NULL,
        key TEXT NOT NULL,
        prompt TEXT NOT NULL,
        expected_answer TEXT NOT NULL,
        scorer TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
""")

connection.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY,
        run_id INTEGER NOT NULL REFERENCES runs(id),
        case_id INTEGER NOT NULL REFERENCES cases(id),
        model TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        response TEXT,
        finish_reason TEXT,
        input_tokens INTEGER,
        output_tokens INTEGER,
        latency_ms REAL NOT NULL,
        error TEXT,
        UNIQUE (run_id, case_id, model)
    ) STRICT
""")

connection.execute("CREATE INDEX IF NOT EXISTS idx_cases_suite_key ON cases (suite, key)")

connection.commit()

for table in ("runs", "cases", "results"):
    print(table)
    for column in connection.execute(f"PRAGMA table_info({table})").fetchall():
        print("   ", column)

connection.close()
