# Train and Score a Model in SQL — MySQL HeatWave AutoML

*Predict churn with two SQL calls. No data export, no notebook, no separate model server.*

---

**📋 At a glance**

- **Tech stack:** MySQL HeatWave AutoML (ML_TRAIN, ML_PREDICT_TABLE) · SQL · Python
- **Database:** MySQL HeatWave 9.7 (9.7.0-cloud)
- **Best for:** Training and scoring an ML model (e.g. churn) in pure SQL, with no data export.
- **Level:** Beginner–Intermediate


The usual ML loop exports features to a notebook, trains elsewhere, and stands up a model service. MySQL HeatWave keeps it all in the database: `ML_TRAIN` builds the model, `ML_PREDICT_TABLE` scores your rows. The data, the model, and the predictions never leave MySQL.

## 1) Train — one call
```sql
CALL sys.ML_TRAIN('heatwave_ai.churn_train', 'churned',
                  JSON_OBJECT('task','classification'), @churn_model);
CALL sys.ML_MODEL_LOAD(@churn_model, NULL);
```

## 2) Score — one call
```sql
CALL sys.ML_PREDICT_TABLE('heatwave_ai.customers', @churn_model,
                          'heatwave_ai.customers_scored', NULL);
SELECT name, ml_results->>'$.predictions.churned' AS churn,
       ml_results->'$.probabilities."1"'          AS churn_prob
FROM customers_scored ORDER BY churn_prob DESC;
```

## It works — verified live

![Churn scoreboard: Aurora Labs 0.993 and Delta Foods 0.974 predicted to churn, down to Brightpath Co 0.002 predicted to stay](result.png)
*Trained and scored entirely inside MySQL HeatWave — the model flags the high-ticket, late-paying BASIC customers.*

## Run it
```
pip install -r requirements.txt
copy .env.example .env
python automl.py
```

## Why it matters
- **No data movement.** Training data, model, and predictions stay in MySQL.
- **Scoring is just SQL.** Join predictions to any query or dashboard.
- **AutoML.** HeatWave selects and tunes the model for you.

📦 **Full code on GitHub:** [github.com/khadayatepa/heatwave-automl](https://github.com/khadayatepa/heatwave-automl)

---

*About the author: **Prashant Khadayate** is an **Oracle ACE** focused on Oracle AI Database (26ai), MySQL HeatWave, and AI in the database. Connect on [LinkedIn](https://www.linkedin.com/in/prashant-khadayate-1a8b0b97/).*

> A learning demo on synthetic data.
