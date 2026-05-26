import cv2
import os
import numpy as np
import time
import sys

# Khắc phục lỗi in Emoji/Unicode trên Windows Terminal
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Trỏ tự động đến thư mục dataset cùng cấp với file script này
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(BASE_DIR, "dataset")

def load_all_data():
    faces = []
    labels = []
    label_map = {}
    label_id = 0

    if not os.path.exists(DATASET):
        print("❌ Thư mục 'dataset' không tồn tại!")
        return [], [], {}

    for person in os.listdir(DATASET):
        person_path = os.path.join(DATASET, person)
        if not os.path.isdir(person_path):
            continue

        label_map[label_id] = person
        for img_name in os.listdir(person_path):
            img_path = os.path.join(person_path, img_name)
            img = cv2.imread(img_path, 0)
            if img is None:
                continue
            img = cv2.resize(img, (100, 100))
            faces.append(img)
            labels.append(label_id)

        label_id += 1

    return np.array(faces), np.array(labels), label_map

def run_evaluation():
    faces, labels, label_map = load_all_data()
    if len(faces) == 0:
        return

    # Chia dữ liệu theo tỉ lệ 80% Train, 20% Test (đơn giản hóa)
    # Trong thực tế có thể dùng sklearn.model_selection.train_test_split
    np.random.seed(42)
    indices = np.random.permutation(len(faces))
    split_point = int(0.8 * len(faces))
    
    train_idx, test_idx = indices[:split_point], indices[split_point:]
    x_train, y_train = faces[train_idx], labels[train_idx]
    x_test, y_test = faces[test_idx], labels[test_idx]

    print(f"📊 Tổng số ảnh: {len(faces)}")
    print(f"   -> Dùng để Train: {len(x_train)} ảnh")
    print(f"   -> Dùng để Test: {len(x_test)} ảnh\n")

    # Danh sách các thông số muốn test (Grid Search)
    # LBPHFaceRecognizer_create(radius, neighbors, grid_x, grid_y)
    param_grid = [
        {"radius": 1, "neighbors": 8, "grid_x": 8, "grid_y": 8},   # Default
        {"radius": 1, "neighbors": 8, "grid_x": 10, "grid_y": 10}, # Lưới mịn hơn
        {"radius": 2, "neighbors": 8, "grid_x": 8, "grid_y": 8},   # Bán kính lớn hơn
    ]

    results = []

    print(f"{'Radius':<8} | {'Neighbors':<10} | {'Grid':<10} | {'Accuracy':<10} | {'Avg. Confidence':<15} | {'Train Time (s)':<15}")
    print("-" * 80)

    for params in param_grid:
        r, n, gx, gy = params["radius"], params["neighbors"], params["grid_x"], params["grid_y"]
        
        # 1. Khởi tạo thuật toán với thông số hiện tại
        recognizer = cv2.face.LBPHFaceRecognizer_create(radius=r, neighbors=n, grid_x=gx, grid_y=gy)
        
        # 2. Bắt đầu đo thời gian Train
        start_time = time.time()
        recognizer.train(list(x_train), y_train)
        train_time = time.time() - start_time
        
        # 3. Tiến hành Test (Dự đoán)
        correct_predictions = 0
        total_confidence = 0
        
        for i in range(len(x_test)):
            test_img = x_test[i]
            true_label = y_test[i]
            
            # Dự đoán
            pred_label, confidence = recognizer.predict(test_img)
            
            total_confidence += confidence
            if pred_label == true_label:
                correct_predictions += 1
                
        # 4. Tính toán kết quả
        accuracy = (correct_predictions / len(x_test)) * 100
        avg_conf = total_confidence / len(x_test)
        
        # In ra bảng
        grid_str = f"{gx}x{gy}"
        print(f"{r:<8} | {n:<10} | {grid_str:<10} | {accuracy:>6.2f}%    | {avg_conf:>15.2f} | {train_time:>15.4f}")
        
        # Lưu kết quả
        results.append({
            "radius": r, "neighbors": n, "grid_x": gx, "grid_y": gy,
            "accuracy": accuracy, "avg_confidence": avg_conf, "train_time": train_time
        })

    print("-" * 80)
    print("\n💡 Tip: Accuracy (Độ chính xác) càng cao càng tốt.")
    print("💡 Tip: Confidence (Độ sai số) càng thấp càng tốt.\n")
    
    if results:
        # Tìm cấu hình tốt nhất (Accuracy cao nhất, sau đó Avg Confidence thấp nhất)
        best_config = sorted(results, key=lambda x: (-x['accuracy'], x['avg_confidence']))[0]
        
        print("🌟" * 20)
        print("🏆 CẤU HÌNH LBPH TỐI ƯU NHẤT DÀNH CHO THUYẾT TRÌNH:")
        print(f"   👉 Radius       : {best_config['radius']}")
        print(f"   👉 Neighbors    : {best_config['neighbors']}")
        print(f"   👉 Grid         : {best_config['grid_x']}x{best_config['grid_y']}")
        print(f"   👉 Độ chính xác : {best_config['accuracy']:.2f}%")
        print(f"   👉 Sai số TB    : {best_config['avg_confidence']:.2f}")
        print("🌟" * 20)
    
    # Bạn có thể xuất kết quả ra file CSV ở đây
    with open("evaluation_results.csv", "w") as f:
        f.write("Radius,Neighbors,GridX,GridY,Accuracy_%,Avg_Confidence,Train_Time_s\n")
        for r in results:
            f.write(f"{r['radius']},{r['neighbors']},{r['grid_x']},{r['grid_y']},{r['accuracy']:.2f},{r['avg_confidence']:.2f},{r['train_time']:.4f}\n")
    print("\n✅ Đã xuất chi tiết ra file 'evaluation_results.csv'.")

if __name__ == "__main__":
    run_evaluation()
