# HeatWave AutoML — train and score a churn model in SQL

Train and predict entirely inside MySQL HeatWave: `sys.ML_TRAIN` builds the model,
`sys.ML_PREDICT_TABLE` scores your rows. No data export, no notebook, no model server.

## Run
```powershell
pip install -r requirements.txt
copy .env.example .env     # MySQL HeatWave connection
python automl.py
```

## How it works
```sql
CALL sys.ML_TRAIN('heatwave_ai.churn_train','churned', JSON_OBJECT('task','classification'), @m);
CALL sys.ML_MODEL_LOAD(@m, NULL);
CALL sys.ML_PREDICT_TABLE('heatwave_ai.customers', @m, 'heatwave_ai.customers_scored', NULL);
SELECT name, ml_results->>'$.predictions.churned', ml_results->'$.probabilities."1"' FROM customers_scored;
```

> ⚠️ Learning demo on synthetic data. `.env` is git-ignored.
