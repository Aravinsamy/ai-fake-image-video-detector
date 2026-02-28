# pyright: reportMissingImports=false
import os
from detector import AIDetector

detector = AIDetector()

BASE_PATH = "dataset"
REAL_PATH = os.path.join(BASE_PATH, "real")
FAKE_PATH = os.path.join(BASE_PATH, "fake")

y_true = []  # ground truth
y_pred = []  # model prediction


def evaluate_folder(folder_path, label):
    for file in os.listdir(folder_path):
        if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        full_path = os.path.join(folder_path, file)
        print(f"Testing: {full_path}")

        result = detector.analyze_image(full_path)

        prediction = 1 if result['isAI'] else 0
        y_true.append(label)
        y_pred.append(prediction)


# 0 = Real, 1 = Fake
evaluate_folder(REAL_PATH, 0)
evaluate_folder(FAKE_PATH, 1)

# ---- Metrics ----
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
cm = confusion_matrix(y_true, y_pred)

print("\n===== EVALUATION RESULTS =====")
print(f"Accuracy  : {accuracy * 100:.2f}%")
print(f"Precision : {precision * 100:.2f}%")
print(f"Recall    : {recall * 100:.2f}%")
print("\nConfusion Matrix:")
print(cm)
