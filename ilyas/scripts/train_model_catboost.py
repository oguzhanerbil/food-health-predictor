import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from catboost import CatBoostClassifier

# Veriyi oku
df = pd.read_csv("ilyas/data/model_veri.csv")

# Kullanılacak sütunlar
features = [
    "enerji_kcal",
    "yag_g",
    "doymus_yag_g",
    "karbonhidrat_g",
    "seker_g",
    "protein_g",
    "tuz_g",
    "lif_g",
    "sodyum_g",
    "nova_grubu",
    "seker_orani",
    "protein_orani",
    "doymus_yag_orani"
]

X = df[features]
y = df["nutriscore_notu"]

# Hedefi sayıya çevir
le = LabelEncoder()
y = le.fit_transform(y)

# Eğitim / test böl
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Model
model = CatBoostClassifier(
    iterations=500,
    depth=8,
    learning_rate=0.03,
    loss_function="MultiClass",
    eval_metric="Accuracy",
    random_state=42,
    verbose=0
)

# Eğit
model.fit(X_train, y_train)

# Tahmin
y_pred = model.predict(X_test)

# Sonuç
print("Accuracy:", accuracy_score(y_test, y_pred))
print()
print(classification_report(y_test, y_pred, target_names=le.classes_))