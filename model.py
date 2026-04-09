import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier

X = np.array([
    [100, 800, 90, 95],
    [150, 1200, 140, 145],
    [200, 1500, 190, 195],
    [50, 300, 55, 60],
    [300, 1000, 100, 120],
    [400, 1200, 150, 180],
    [250, 2000, 120, 140],
])

y = np.array([0, 0, 0, 0, 1, 1, 1])

model = RandomForestClassifier()
model.fit(X, y)

pickle.dump(model, open("model.pkl", "wb"))

print("✅ ML Model Ready")