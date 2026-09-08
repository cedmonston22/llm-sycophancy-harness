import sqlite3

connection = sqlite3.connect("evals.db")
connection.execute("""CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT,
                    finish_reason TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    latency_ms REAL NOT NULL
    
    
                    ) STRICT
                    """)
connection.commit()
print(connection.execute("PRAGMA table_info(results)").fetchall())
connection.close()
