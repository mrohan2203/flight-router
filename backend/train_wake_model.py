import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. Generate Synthetic Airspace Data
np.random.seed(42)
n_samples = 5000

# Features: altitude_diff (ft), lateral_dist (NM), is_lead_heavy (1/0), is_trail_heavy (1/0)
alt_diff = np.random.uniform(0, 2000, n_samples)
lat_dist = np.random.uniform(0, 10, n_samples)
is_lead_heavy = np.random.choice([0, 1], n_samples)
is_trail_heavy = np.random.choice([0, 1], n_samples)

# Labels: 1 = Unsafe (Conflict/Wake Turbulence), 0 = Safe
unsafe = np.zeros(n_samples)

for i in range(n_samples):
    # Base collision risk: less than 1000ft vertical AND less than 3NM lateral
    if alt_diff[i] < 1000 and lat_dist[i] < 3.0:
        unsafe[i] = 1
    # Wake turbulence: Lead is Heavy, Trail is Medium, within 5NM lateral and 1000ft vertical
    elif is_lead_heavy[i] == 1 and is_trail_heavy[i] == 0:
        if alt_diff[i] < 1000 and lat_dist[i] < 5.0:
            unsafe[i] = 1

df = pd.DataFrame({
    'alt_diff': alt_diff,
    'lat_dist': lat_dist,
    'is_lead_heavy': is_lead_heavy,
    'is_trail_heavy': is_trail_heavy,
    'unsafe': unsafe
})

# 2. Train the XGBoost Classifier
X = df[['alt_diff', 'lat_dist', 'is_lead_heavy', 'is_trail_heavy']]
y = df['unsafe']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1)
model.fit(X_train, y_train)

predictions = model.predict(X_test)
print(f"Model Accuracy: {accuracy_score(y_test, predictions) * 100:.2f}%")

# 3. Save the serialized model
model.save_model("wake_safety_model.ubj")
print("Saved wake_safety_model.ubj")
