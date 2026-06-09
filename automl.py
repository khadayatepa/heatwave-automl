"""
HeatWave AutoML — train and score a churn model in pure SQL, no data export.

ML_TRAIN builds the model inside MySQL HeatWave; ML_PREDICT_TABLE scores customers.
The data, the model, and the predictions all stay in the database.

Run:  python automl.py
"""
from __future__ import annotations

import os
import random
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

import mysql.connector
from dotenv import load_dotenv

load_dotenv()
random.seed(42)
PLANS = ["BASIC", "PRO", "ENTERPRISE"]


def _row(i):
    tenure = random.randint(1, 60); tickets = random.randint(0, 12)
    late = random.randint(0, 6); spend = random.randint(20, 220)
    plan = random.choice(PLANS)
    score = (12 - min(tenure, 24) / 2) + tickets * 0.6 + late * 1.1 - spend * 0.02 + (2 if plan == "BASIC" else 0)
    churned = 1 if score + random.gauss(0, 1.4) > 8 else 0
    return (tenure, spend, tickets, late, plan, churned)


TRAIN = [_row(i) for i in range(120)]
CUSTOMERS = [  # name, tenure, spend, tickets, late, plan
    ("Aurora Labs", 4, 39, 9, 4, "BASIC"),
    ("Brightpath Co", 48, 180, 1, 0, "ENTERPRISE"),
    ("Cobalt Retail", 11, 70, 5, 2, "PRO"),
    ("Delta Foods", 7, 30, 7, 3, "BASIC"),
    ("Everest Media", 30, 140, 2, 0, "PRO"),
    ("Finch Analytics", 9, 55, 6, 1, "PRO"),
]


def conn():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"), port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "ADMIN"), password=os.getenv("MYSQL_PASSWORD", ""),
        connection_timeout=20)


def run(cur, sql, params=None):
    cur.execute(sql, params or ())
    try:
        cur.fetchall()
    except Exception:
        pass


def main() -> None:
    print("\n=== HeatWave AutoML — churn scoring in SQL ===\n")
    c = conn(); cur = c.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS heatwave_ai"); cur.execute("USE heatwave_ai")

    print("1) Loading labelled training data ...")
    run(cur, "DROP TABLE IF EXISTS churn_train")
    run(cur, "CREATE TABLE churn_train (tenure_months INT, monthly_spend INT, support_tickets INT, "
             "late_payments INT, plan VARCHAR(20), churned INT)")
    cur.executemany("INSERT INTO churn_train (tenure_months,monthly_spend,support_tickets,late_payments,plan,churned) "
                    "VALUES (%s,%s,%s,%s,%s,%s)", TRAIN)
    c.commit()
    print(f"   {len(TRAIN)} rows\n")

    print("2) Training the model INSIDE HeatWave (sys.ML_TRAIN) — this can take a minute ...")
    run(cur, "CALL sys.ML_TRAIN('heatwave_ai.churn_train', 'churned', "
             "JSON_OBJECT('task','classification'), @churn_model)")
    cur.execute("SELECT @churn_model"); handle = cur.fetchone()[0]
    print(f"   model: {handle}")
    run(cur, "CALL sys.ML_MODEL_LOAD(@churn_model, NULL)")

    print("\n3) Scoring current customers (sys.ML_PREDICT_TABLE) ...")
    run(cur, "DROP TABLE IF EXISTS customers")
    run(cur, "CREATE TABLE customers (name VARCHAR(40), tenure_months INT, monthly_spend INT, "
             "support_tickets INT, late_payments INT, plan VARCHAR(20))")
    cur.executemany("INSERT INTO customers VALUES (%s,%s,%s,%s,%s,%s)", CUSTOMERS)
    c.commit()
    run(cur, "DROP TABLE IF EXISTS customers_scored")
    run(cur, "CALL sys.ML_PREDICT_TABLE('heatwave_ai.customers', @churn_model, "
             "'heatwave_ai.customers_scored', NULL)")

    cur.execute("SELECT name, plan, support_tickets, late_payments, "
                "ml_results->>'$.predictions.churned' AS churn_pred, "
                "ROUND(JSON_EXTRACT(ml_results, '$.probabilities.\"1\"'), 3) AS churn_prob "
                "FROM customers_scored ORDER BY churn_prob DESC")
    print(f"   {'Customer':<18}{'plan':<12}{'churn?':<8}{'prob':<7}signals")
    for name, plan, tk, late, pred, prob in cur.fetchall():
        print(f"   {name:<18}{plan:<12}{str(pred):<8}{str(prob):<7}{tk}t / {late}late")

    print("\n✅ Done. Model trained and customers scored entirely inside MySQL HeatWave.")
    cur.close(); c.close()


if __name__ == "__main__":
    main()
