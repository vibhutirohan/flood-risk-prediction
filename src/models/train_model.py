import pandas as pd
import joblib
import shap
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

# ------------------------------------
# LOAD DATA
# ------------------------------------
df = pd.read_csv("data/processed/flood_data.csv")

target = "risk_level"
y = df[target]
X = df.drop(columns=[target])

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# ------------------------------------
# PREPROCESSING
# ------------------------------------
numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns
categorical_cols = X.select_dtypes(include=["object"]).columns

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)
    ]
)

# ------------------------------------
# SPLIT DATA
# ------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.25, random_state=42
)

# ------------------------------------
# MODELS
# ------------------------------------
models = {
    "random_forest": RandomForestClassifier(n_estimators=200, random_state=42),
    "xgboost": XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1, subsample=0.9
    ),
    "logistic_regression": LogisticRegression(max_iter=1000)
}

trained_models = {}
model_metrics = {}
shap_values_all = {}

# ------------------------------------
# TRAIN EACH MODEL
# ------------------------------------
for model_name, model in models.items():

    clf = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", model)
    ])

    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)

    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "precision": float(precision_score(y_test, preds, average="weighted")),
        "recall": float(recall_score(y_test, preds, average="weighted")),
        "f1_score": float(f1_score(y_test, preds, average="weighted")),
    }

    model_metrics[model_name] = metrics
    trained_models[model_name] = clf

    # CREATE SHAP EXPLAINER (Tree models use TreeExplainer)
    if model_name in ["random_forest", "xgboost"]:
        explainer = shap.TreeExplainer(clf.named_steps["model"])
    else:
        explainer = shap.Explainer(clf.predict, X_train[:50])

    shap_values = explainer.shap_values(X_train[:50])
    shap_values_all[model_name] = shap_values.tolist()


# ------------------------------------
# SAVE EVERYTHING
# ------------------------------------
save_bundle = {
    "models": trained_models,
    "label_encoder": label_encoder,
    "metrics": model_metrics,
    "shap_values": shap_values_all,
    "feature_names": list(X.columns)
}

joblib.dump(save_bundle, "models/flood_risk_multimodel.joblib")

print("Training complete! Models + SHAP saved successfully.")
