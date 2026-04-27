import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

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
    "tuz_g"
]

# Giriş ve hedef
X = df[features]
y = df["nutriscore_notu"]

# Boş kalanları sil
X = X.dropna()
y = y.loc[X.index]

# Eğitim / test böl
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Model oluştur
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

# Eğit
model.fit(X_train, y_train)

# Tahmin
y_pred = model.predict(X_test)

# Sonuçlar
print("Accuracy:", accuracy_score(y_test, y_pred))
print()
print(classification_report(y_test, y_pred))