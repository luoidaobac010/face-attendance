import os
import time
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

# Fix in tiếng Việt
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Import các hàm xử lý dữ liệu chuẩn từ chính file main.py của dự án
from main import load_dataset, PCA

def run_comparison():
    print("="*70)
    print("   THỰC NGHIỆM DEMO: SO SÁNH SVM VÀ KNN TRÊN CÙNG PIPELINE PCA")
    print("="*70)

    # 1. Load dữ liệu
    print("[1] Đang tải tập dữ liệu...")
    X, y, label_map = load_dataset()
    if len(X) == 0 or len(label_map) < 2:
        print("❌ Lỗi: Cần ít nhất 2 người trong dataset để so sánh mô hình phân loại.")
        return

    print(f"📊 Tổng số ảnh: {len(X)} | Số người: {len(label_map)}")

    # Chia dữ liệu theo tỷ lệ chuẩn 80% Train, 20% Test, phân bổ đều (stratify=y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"   -> Tập huấn luyện (Train): {len(X_train)} ảnh")
    print(f"   -> Tập kiểm thử (Test)   : {len(X_test)} ảnh\n")

    # 2. Xử lý giảm chiều (Dimension Reduction) với PCA
    print("[2] Đang trích xuất đặc trưng với PCA (Giảm từ 10000 chiều -> 50 chiều)...")
    W, mean = PCA(X_train)
    
    # Cùng một ma trận chiếu (W, mean) áp dụng cho cả Train và Test
    X_train_pca = np.dot(X_train - mean, W)
    X_test_pca = np.dot(X_test - mean, W)
    print("✔ Trích xuất PCA hoàn tất! Bắt đầu đưa vào các bộ phân loại...\n")

    # 3. Khởi tạo và so sánh 2 mô hình
    print("[3] KẾT QUẢ ĐÁNH GIÁ (SVM vs KNN):")
    models = {
        "SVM (Linear Kernel)": SVC(kernel='linear', probability=True),
        "KNN (K=5)": KNeighborsClassifier(n_neighbors=5, metric='euclidean')
    }

    results = {}

    for name, model in models.items():
        print(f"▶ Đang chạy: {name} ...")
        
        # Huấn luyện
        start_train = time.time()
        model.fit(X_train_pca, y_train)
        train_time = time.time() - start_train

        # Dự đoán
        start_predict = time.time()
        y_pred = model.predict(X_test_pca)
        predict_time = time.time() - start_predict

        # Đánh giá
        acc = accuracy_score(y_test, y_pred) * 100
        results[name] = {"accuracy": acc, "train_time": train_time, "predict_time": predict_time}

        print(f"   - Độ chính xác (Accuracy): {acc:.2f}%")
        print(f"   - Thời gian huấn luyện   : {train_time:.5f} giây")
        print(f"   - Thời gian nhận diện    : {predict_time:.5f} giây\n")

    # 4. Vẽ biểu đồ xuất ra ảnh để báo cáo
    print("[4] Đang khởi tạo biểu đồ so sánh trực quan...")
    names = ["SVM (Hệ thống đang dùng)", "KNN (Đối chứng)"]
    keys = list(models.keys())
    accuracies = [results[keys[0]]["accuracy"], results[keys[1]]["accuracy"]]
    predict_times = [results[keys[0]]["predict_time"], results[keys[1]]["predict_time"]]

    fig, ax1 = plt.subplots(figsize=(9, 6))

    # Trục 1: Độ chính xác
    color1 = '#2E86C1'
    ax1.set_xlabel('Thuật toán (Đã qua xử lý chung PCA)', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Độ chính xác - Accuracy (%)', color=color1, fontweight='bold', fontsize=11)
    bars1 = ax1.bar([0.8, 1.8], accuracies, width=0.25, label='Độ chính xác (%)', color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim([0, 115])
    ax1.set_xticks([0.925, 1.925])
    ax1.set_xticklabels(names, fontweight='bold', fontsize=12)

    # Trục 2: Thời gian dự đoán
    ax2 = ax1.twinx()  
    color2 = '#E67E22'
    ax2.set_ylabel('Thời gian nhận diện (giây) - CÀNG THẤP CÀNG TỐT', color=color2, fontweight='bold', fontsize=11)  
    bars2 = ax2.bar([1.05, 2.05], predict_times, width=0.25, label='Thời gian nhận diện', color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Hiển thị số liệu
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f'{yval:.1f}%', ha='center', va='bottom', color=color1, fontweight='bold')
        
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.4f}s', ha='center', va='bottom', color=color2, fontweight='bold')

    plt.title("BIỂU ĐỒ THỰC NGHIỆM: SO SÁNH SVM VÀ KNN", fontweight='bold', pad=20, fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.tight_layout()
    
    output_img = "compare_chart.png"
    plt.savefig(output_img, dpi=300)
    print(f"✔ Đã xuất biểu đồ so sánh thành công: '{output_img}'")
    print("="*70)

if __name__ == "__main__":
    run_comparison()
