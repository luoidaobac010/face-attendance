import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# Khắc phục lỗi in Emoji/Unicode trên Windows Terminal
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Định nghĩa các đường dẫn
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(BASE_DIR, "dataset")
FACE_SIZE = (100, 100)

def load_dataset():
    """
    Đọc toàn bộ ảnh từ thư mục dataset, chuẩn hóa kích thước 100x100 và làm phẳng thành vector 10,000 chiều.
    """
    faces = []
    labels = []
    label_map = {}
    label_id = 0

    if not os.path.exists(DATASET):
        print("❌ Thư mục 'dataset' không tồn tại!")
        return np.array([]), np.array([]), {}

    people = [p for p in os.listdir(DATASET) if os.path.isdir(os.path.join(DATASET, p))]
    if not people:
        print("❌ Không tìm thấy thư mục con nào trong 'dataset'!")
        return np.array([]), np.array([]), {}

    for person in people:
        path = os.path.join(DATASET, person)
        label_map[label_id] = person
        
        img_count = 0
        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)
            # Đọc ảnh ở dạng grayscale
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            img = cv2.resize(img, FACE_SIZE)
            faces.append(img.flatten())  # 100x100 -> 10000 chiều
            labels.append(label_id)
            img_count += 1
            
        print(f"📂 Đọc thành công {img_count} ảnh của nhân sự: '{person}'")
        label_id += 1

    return np.array(faces, dtype=np.float32), np.array(labels), label_map

def find_optimal_k():
    print("=" * 60)
    print("🔍 PHÂN TÍCH CHỌN SỐ CHIỀU OPTIMAL K CHO PCA (SCREE PLOT)")
    print("=" * 60)

    # 1. Load dữ liệu
    X, y, label_map = load_dataset()
    n_samples = len(X)
    
    if n_samples == 0:
        print("❌ Không có dữ liệu để phân tích PCA. Vui lòng chạy chụp ảnh đăng ký trước!")
        return

    n_features = X.shape[1]
    print(f"\n📊 Tổng số mẫu dữ liệu (ảnh): {n_samples}")
    print(f"📊 Số chiều gốc của mỗi ảnh : {n_features} (100x100 px)")

    # Số lượng thành phần tối đa có thể phân tích
    max_components = min(n_samples - 1, 100) # Thường tối đa bằng N-1 hoặc giới hạn 100 để vẽ biểu đồ trực quan
    if max_components <= 1:
        print("⚠ Số lượng mẫu ảnh quá ít để phân tích Scree Plot! Hãy chụp thêm ảnh.")
        return

    # 2. Chạy PCA toàn phần
    print(f"⚙ Đang tính toán PCA với tối đa {max_components} thành phần chính...")
    pca = PCA(n_components=max_components)
    pca.fit(X)

    # Tỷ lệ phương sai giải thích bởi mỗi thành phần chính
    explained_variance_ratio = pca.explained_variance_ratio_
    # Phương sai tích lũy
    cumulative_variance = np.cumsum(explained_variance_ratio)

    # 3. Tìm các ngưỡng phương sai tích lũy quan trọng
    thresholds = [0.80, 0.90, 0.95, 0.99]
    k_targets = {}
    for t in thresholds:
        # Tìm chỉ số đầu tiên vượt ngưỡng t
        idx = np.where(cumulative_variance >= t)[0]
        if len(idx) > 0:
            k_targets[t] = idx[0] + 1
        else:
            k_targets[t] = max_components

    # 4. In bảng phân tích ra console
    print("\n📋 BẢNG THỐNG KÊ PHƯƠNG SAI TÍCH LŨY (CUMULATIVE EXPLAINED VARIANCE):")
    print("-" * 65)
    print(f"{'Component (k)':<15} | {'Variance Ratio':<18} | {'Cumulative Variance':<25}")
    print("-" * 65)
    
    # Hiển thị 15 thành phần đầu hoặc tất cả nếu ít hơn 15
    show_limit = min(15, max_components)
    for i in range(show_limit):
        print(f"PC {i+1:<12} | {explained_variance_ratio[i]:>16.4f} | {cumulative_variance[i]:>23.2%}")
    
    if max_components > show_limit:
        print("...")
        # In dòng cuối cùng
        print(f"PC {max_components:<12} | {explained_variance_ratio[-1]:>16.4f} | {cumulative_variance[-1]:>23.2%}")
    print("-" * 65)

    print("\n💡 ĐỀ XUẤT CHỌN SỐ CHIỀU K DỰA TRÊN PHƯƠNG SAI TÍCH LŨY:")
    for t, k_val in k_targets.items():
        tag = ""
        if t == 0.95:
            tag = "🌟 (Khuyên dùng cho Nhận diện khuôn mặt)"
        elif t == 0.90:
            tag = "⚡ (Cân bằng tốt giữa tốc độ và độ chính xác)"
        print(f"   👉 Để giữ lại {t*100:.0f}% lượng thông tin: Chọn k = {k_val} {tag}")

    # Tìm điểm khuỷu tay (Elbow method) đơn giản qua sự thay đổi độ dốc
    diffs = np.diff(explained_variance_ratio)
    elbow_k = np.argmin(diffs) + 2  # +2 vì diff giảm độ dài đi 1 và index bắt đầu từ 0
    print(f"   👉 Điểm khuỷu tay (Elbow Point): k ≈ {elbow_k} (Nơi độ dốc thay đổi mạnh nhất)")

    # 5. Vẽ biểu đồ Scree Plot
    print("\n📈 Đang vẽ Scree Plot và lưu thành file ảnh...")
    
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Trục 1: Tỷ lệ phương sai của từng thành phần (Bar chart)
    color = '#1f77b4'
    ax1.set_xlabel('Số lượng thành phần chính (Principal Components - k)', fontweight='bold')
    ax1.set_ylabel('Tỷ lệ phương sai giải thích riêng lẻ', color=color, fontweight='bold')
    bars = ax1.bar(range(1, max_components + 1), explained_variance_ratio, alpha=0.6, color=color, label='Phương sai riêng lẻ')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.3)

    # Trục 2: Phương sai tích lũy (Line chart)
    ax2 = ax1.twinx()  
    color = '#ff7f0e'
    ax2.set_ylabel('Phương sai tích lũy (Cumulative Variance)', color=color, fontweight='bold')
    line = ax2.plot(range(1, max_components + 1), cumulative_variance, color=color, marker='o', linewidth=2, label='Phương sai tích lũy')
    ax2.tick_params(axis='y', labelcolor=color)

    # Vẽ các đường tham chiếu cho ngưỡng 95%
    k_95 = k_targets.get(0.95, max_components)
    ax2.axhline(y=0.95, color='r', linestyle='--', alpha=0.7, label='Ngưỡng 95% thông tin')
    ax2.axvline(x=k_95, color='g', linestyle='-.', alpha=0.7, label=f'k = {k_95} (95% Variance)')

    # Thêm tiêu đề và chú thích
    plt.title('SCREE PLOT & PHƯƠNG SAI TÍCH LŨY CỦA MÔ HÌNH PCA', fontsize=14, fontweight='bold', pad=15)
    
    # Kết hợp chú thích của cả 2 trục
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')

    plt.tight_layout()
    
    # Lưu biểu đồ
    output_img = os.path.join(BASE_DIR, "pca_scree_plot.png")
    plt.savefig(output_img, dpi=300, bbox_inches='tight')
    print(f"✅ Đã vẽ và lưu biểu đồ Scree Plot thành công tại: '{output_img}'")
    print("=" * 60)

if __name__ == "__main__":
    find_optimal_k()
