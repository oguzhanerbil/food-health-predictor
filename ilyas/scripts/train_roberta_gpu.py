import pandas as pd
from datasets import Dataset
from sklearn.preprocessing import LabelEncoder
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
import evaluate
import numpy as np
import torch

print("GPU:", torch.cuda.get_device_name(0))

# Veri oku
df = pd.read_csv("ilyas/data/roberta_data.csv")

# Boş label varsa sil
df = df[df["label"].notna()].copy()

# Label encode
label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df["label"])

print("Sınıflar:", label_encoder.classes_)
print("Veri Boyutu:", df.shape)

# Dataset
dataset = Dataset.from_pandas(df)

dataset = dataset.train_test_split(
    test_size=0.2,
    seed=42
)

train_dataset = dataset["train"]
test_dataset = dataset["test"]

# Tokenizer
MODEL_NAME = "roberta-base"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=512
    )

train_dataset = train_dataset.map(
    tokenize_function,
    batched=True
)

test_dataset = test_dataset.map(
    tokenize_function,
    batched=True
)

# Format
train_dataset.set_format(
    type="torch",
    columns=["input_ids", "attention_mask", "label"]
)

test_dataset.set_format(
    type="torch",
    columns=["input_ids", "attention_mask", "label"]
)

# Model
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(label_encoder.classes_)
)

# Accuracy
accuracy = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred

    predictions = np.argmax(
        logits,
        axis=-1
    )

    return accuracy.compute(
        predictions=predictions,
        references=labels
    )

# Eğitim ayarları
training_args = TrainingArguments(
    output_dir="./models/roberta_nutriscore",

    num_train_epochs=5,

    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,

    learning_rate=2e-5,

    weight_decay=0.01,

    fp16=True,

    seed=42,
    data_seed=42,

    save_strategy="epoch",

    eval_strategy="epoch",

    logging_steps=100,

    load_best_model_at_end=True,

    metric_for_best_model="accuracy",

    greater_is_better=True,

    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics
)

print("Eğitim başlıyor...")

trainer.train()

results = trainer.evaluate()

print("\nSonuçlar:")
print(results)

print("\nModel kaydediliyor...")

trainer.save_model(
    "./models/roberta_nutriscore"
)

tokenizer.save_pretrained(
    "./models/roberta_nutriscore"
)

print("Tamamlandı.")