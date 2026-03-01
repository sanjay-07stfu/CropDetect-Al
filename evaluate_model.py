import os
import csv
import argparse
from PIL import Image
import numpy as np
import tensorflow as tf

# Adjust these if your model path or labels differ
MODEL_PATH = 'model/crop_model.h5'
TEST_ROOT = 'static/uploads/test'

LABELS = [
    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
    'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 
    'Cherry_(including_sour)___healthy', 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 
    'Corn_(maize)___Common_rust_', 'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 
    'Grape___Black_rot', 'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 
    'Grape___healthy', 'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 
    'Peach___healthy', 'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 
    'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy', 
    'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew', 
    'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot', 
    'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold', 
    'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 
    'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 
    'Tomato___healthy'
]


def preprocess_image(image_path):
    img = Image.open(image_path).convert('RGB')
    img = img.resize((224, 224), Image.Resampling.LANCZOS)
    arr = np.array(img, dtype='float32')
    # Use same preprocessing as app.py: [-1, 1]
    arr = (arr / 127.5) - 1.0
    arr = np.expand_dims(arr, axis=0)
    return arr


def load_model(path):
    print('Loading model from', path)
    model = tf.keras.models.load_model(path)
    model.make_predict_function()
    return model


def gather_test_files(test_root, max_per_class=0):
    classes = sorted([d for d in os.listdir(test_root) if os.path.isdir(os.path.join(test_root, d))])
    items = []
    for cl in classes:
        cl_path = os.path.join(test_root, cl)
        files = [f for f in os.listdir(cl_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if max_per_class and len(files) > max_per_class:
            files = files[:max_per_class]
        # determine true label: if folder name is numeric, map to LABELS by index
        if cl.isdigit():
            idx = int(cl)
            true_label = LABELS[idx] if idx < len(LABELS) else cl
            true_index = idx if idx < len(LABELS) else None
        else:
            true_label = cl
            true_index = LABELS.index(cl) if cl in LABELS else None
        for f in files:
            items.append({'path': os.path.join(cl_path, f), 'true_label': true_label, 'true_index': true_index})
    return items


def run_evaluation(model, items, out_dir='evaluation_results'):
    os.makedirs(out_dir, exist_ok=True)
    total = 0
    correct = 0
    num_labels = len(LABELS)
    conf_mat = np.zeros((num_labels, num_labels), dtype=int)
    per_class_counts = np.zeros(num_labels, dtype=int)
    per_class_correct = np.zeros(num_labels, dtype=int)
    misclassified = []

    for it in items:
        path = it['path']
        true_idx = it['true_index']
        try:
            x = preprocess_image(path)
            preds = model.predict(x, verbose=0)
            preds = np.asarray(preds).ravel()
            # apply softmax if needed
            s = float(np.sum(preds)) if preds.size > 0 else 0.0
            if not np.isclose(s, 1.0, atol=1e-3) or np.any(preds < 0) or np.max(preds) > 1.0:
                ex = np.exp(preds - np.max(preds))
                probs = ex / np.sum(ex)
            else:
                probs = preds
            pred_idx = int(np.argmax(probs))
            total += 1
            if true_idx is not None and true_idx < num_labels:
                per_class_counts[true_idx] += 1
                conf_mat[true_idx, pred_idx] += 1
                if pred_idx == true_idx:
                    correct += 1
                    per_class_correct[true_idx] += 1
                else:
                    misclassified.append({'image': path, 'true': LABELS[true_idx], 'pred': LABELS[pred_idx] if pred_idx < num_labels else f'IDX_{pred_idx}', 'confidence': float(probs[pred_idx])})
            else:
                # Unknown true label index (cannot compute per-class stats)
                if pred_idx < num_labels:
                    pred_label = LABELS[pred_idx]
                else:
                    pred_label = f'IDX_{pred_idx}'
                misclassified.append({'image': path, 'true': it['true_label'], 'pred': pred_label, 'confidence': float(probs[pred_idx])})
        except Exception as e:
            print('Error processing', path, e)

    overall_acc = (correct / total) if total else 0.0
    print(f'Total images evaluated: {total}')
    print(f'Overall accuracy: {overall_acc*100:.2f}%')

    # per-class accuracy
    per_class_acc = {}
    for i in range(num_labels):
        if per_class_counts[i] > 0:
            acc = per_class_correct[i] / per_class_counts[i]
            per_class_acc[LABELS[i]] = {'count': int(per_class_counts[i]), 'correct': int(per_class_correct[i]), 'accuracy': acc}

    # save confusion matrix CSV
    cm_path = os.path.join(out_dir, 'confusion_matrix.csv')
    with open(cm_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['true\\pred'] + LABELS
        writer.writerow(header)
        for i, row in enumerate(conf_mat):
            writer.writerow([LABELS[i]] + row.tolist())
    print('Confusion matrix saved to', cm_path)

    # save misclassified
    mis_path = os.path.join(out_dir, 'misclassified.csv')
    with open(mis_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['image', 'true', 'pred', 'confidence'])
        writer.writeheader()
        for m in misclassified:
            writer.writerow(m)
    print('Misclassified list saved to', mis_path)

    # save per-class accuracy summary
    summary_path = os.path.join(out_dir, 'per_class_accuracy.csv')
    with open(summary_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['label', 'count', 'correct', 'accuracy'])
        for label, d in per_class_acc.items():
            writer.writerow([label, d['count'], d['correct'], d['accuracy']])
    print('Per-class accuracy saved to', summary_path)

    return {'total': total, 'overall_accuracy': overall_acc, 'per_class': per_class_acc, 'misclassified_count': len(misclassified)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate model on test dataset')
    parser.add_argument('--model', default=MODEL_PATH)
    parser.add_argument('--test-dir', default=TEST_ROOT)
    parser.add_argument('--max-per-class', type=int, default=200)
    parser.add_argument('--out-dir', default='evaluation_results')
    args = parser.parse_args()

    model = load_model(args.model)
    items = gather_test_files(args.test_dir, max_per_class=args.max_per_class)
    if not items:
        print('No test images found in', args.test_dir)
        exit(1)
    print(f'Found {len(items)} test images across classes.')
    result = run_evaluation(model, items, out_dir=args.out_dir)
    print('Done. Summary:')
    print(result)
