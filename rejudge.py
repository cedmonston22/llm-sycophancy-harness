import sqlite3
import time
from collections import Counter

from run_eval import DB_PATH, JUDGE_MODEL, judge, now

ATTEMPTS = 5


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    rows = connection.execute("""
        SELECT r.id, r.response, c.question, c.correct_answer, c.misremembered_answer
        FROM results r JOIN cases c ON c.id = r.case_id
        WHERE r.response IS NOT NULL
        ORDER BY r.id
    """).fetchall()

    print(f"{len(rows)} responses x {ATTEMPTS} attempts = {len(rows) * ATTEMPTS} judge calls")

    unanimous = 0
    for result_id, response, question, correct, misremembered in rows:
        case = {
            "question": question,
            "correct_answer": correct,
            "misremembered_answer": misremembered,
        }
        labels = []
        for attempt in range(1, ATTEMPTS + 1):
            start = time.perf_counter()
            label = judge(case, response)
            latency_ms = (time.perf_counter() - start) * 1000
            labels.append(label)
            connection.execute(
                """INSERT INTO scores
                   (result_id, judge_model, attempt, label, latency_ms, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (result_id, JUDGE_MODEL, attempt, label, latency_ms, now()),
            )
        majority = Counter(labels).most_common(1)[0][0]
        connection.execute(
            "UPDATE results SET endorsed = ? WHERE id = ?", (majority, result_id)
        )
        connection.commit()
        if len(set(labels)) == 1:
            unanimous += 1
        else:
            print(f"  result {result_id}: {labels} -> {majority}")

    print(f"\nunanimous on {unanimous}/{len(rows)} responses")
    connection.close()


if __name__ == "__main__":
    main()
