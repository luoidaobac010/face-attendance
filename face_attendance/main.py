import cv2
import os
import numpy as np
import pandas as pd
import pickle
from datetime import datetime
from sklearn.svm import SVC

# ===================== CẤU HÌNH =====================
DATASET = "dataset"
EXCEL = "attendance.xlsx"
MODEL_FILE = "model_svm.pkl"  # Lưu model PCA+SVM đã train
FACE_SIZE = (100, 100)        # Kích thước chuẩn hóa ảnh khuôn mặt
PCA_COMPONENTS = 50           # Số thành phần PCA (giảm từ 10000 chiều → 50)
MAX_COLLECT_IMAGES = 50       # Số ảnh chụp mỗi người (giảm từ 200 → 50)

# Load Haar Cascade để detect mặt
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ===================== EXCEL =====================
if not os.path.exists(EXCEL):
    pd.DataFrame(columns=["Tên", "Ngày", "Thời gian"]).to_excel(EXCEL, index=False)

def mark_once(name):
    """
    Ghi tên vào Excel nếu chưa điểm danh HÔM NAY.
    Mỗi ngày mới cho phép điểm danh lại (không bị block vĩnh viễn).
    """
    try:
        df = pd.read_excel(EXCEL)
    except Exception:
        df = pd.DataFrame(columns=["Tên", "Ngày", "Thời gian"])

    today = datetime.now().strftime("%Y-%m-%d")

    # Kiểm tra: đã điểm danh HÔM NAY chưa (thay vì kiểm tra tên tồn tại vĩnh viễn)
    if "Ngày" in df.columns:
        already = ((df["Tên"] == name) & (df["Ngày"] == today)).any()
        if already:
            return False

    now_time = datetime.now().strftime("%H:%M:%S")
    df.loc[len(df)] = [name, today, now_time]
    df.to_excel(EXCEL, index=False)

    print(f"✅ Chấm công: {name} lúc {today} {now_time}")
    return True

# ===================== COLLECT =====================
def collect(name):
    """
    Chụp ảnh khuôn mặt sử dụng Haar Cascade để cắt đúng vùng mặt.
    Chỉ chụp 50 ảnh (đủ cho PCA+SVM, tiết kiệm bộ nhớ).
    """
    path = f"{DATASET}/{name}"
    os.makedirs(path, exist_ok=True)

    cap = cv2.VideoCapture(0)

    # Kiểm tra camera có mở được không
    if not cap.isOpened():
        print("❌ Không mở được camera!")
        return

    count = 0
    print(f"📸 Đang chụp {MAX_COLLECT_IMAGES} ảnh cho '{name}'...")
    print("💡 Hãy xoay mặt nhiều góc khác nhau!")
    print("🛑 Nhấn ESC để dừng sớm.")

    while count < MAX_COLLECT_IMAGES:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect face bằng Haar Cascade (chỉ lưu vùng mặt, không lưu nền)
        detected_faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in detected_faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, FACE_SIZE)

            cv2.imwrite(f"{path}/{count}.jpg", face)
            count += 1

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"{count}/{MAX_COLLECT_IMAGES}", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Collect", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"✔ Collect xong: {count} ảnh")

# ===================== LOAD DATA =====================
def load_dataset():
    """
    Đọc ảnh từ dataset, trả về mảng vector đã flatten và nhãn.
    Mỗi ảnh 100x100 được chuyển thành vector 10,000 chiều.
    """
    faces, labels = [], []
    label_map = {}
    label_id = 0

    if not os.path.exists(DATASET):
        print("❌ Thư mục 'dataset' không tồn tại!")
        return np.array([]), np.array([]), {}

    for person in os.listdir(DATASET):
        path = os.path.join(DATASET, person)

        if not os.path.isdir(path):
            continue

        label_map[label_id] = person

        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)

            img = cv2.imread(img_path, 0)
            if img is None:
                continue

            img = cv2.resize(img, FACE_SIZE)
            faces.append(img.flatten())  # chuyển 100x100 → vector 10000
            labels.append(label_id)

        label_id += 1

    return np.array(faces, dtype=np.float32), np.array(labels), label_map

# ===================== PCA (SVD) =====================
def PCA(X, k=PCA_COMPONENTS):
    """
    PCA dùng SVD (Singular Value Decomposition) — cách nhanh và chuẩn.

    Bước:
    1. Chuẩn hoá dữ liệu (trừ trung bình)
    2. SVD decomposition: phân rã ma trận thành U × S × Vt
    3. Lấy k hàng đầu tiên của Vt làm k thành phần chính

    Ý nghĩa:
    - Giảm chiều từ 10,000 → 50 (nén 200 lần)
    - Giữ lại thông tin quan trọng nhất (các Eigenfaces)
    - Loại bỏ nhiễu và chi tiết không cần thiết
    """
    mean = np.mean(X, axis=0)
    X_centered = X - mean

    # SVD: U chứa hệ số, S chứa giá trị riêng, Vt chứa vector riêng
    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

    W = Vt[:k].T  # ma trận chiếu: lấy k vector riêng quan trọng nhất

    return W, mean

# ===================== TRAIN =====================
def train():
    """
    Train PCA + SVM và lưu model vào file pickle.
    Lần sau load model từ file → không cần train lại.
    """
    # Kiểm tra model đã có sẵn chưa
    if os.path.exists(MODEL_FILE):
        print("📂 Đã có model sẵn. Load từ file...")
        with open(MODEL_FILE, "rb") as f:
            return pickle.load(f)

    X, y, label_map = load_dataset()

    if len(X) == 0:
        print("❌ Không có dữ liệu để train!")
        return None

    print(f"📊 Số ảnh: {len(X)} | Số người: {len(label_map)}")

    # PCA: giảm chiều dữ liệu
    W, mean = PCA(X)
    X_pca = np.dot(X - mean, W)

    # SVM: huấn luyện mô hình phân loại
    model = SVC(kernel='linear', probability=True)
    model.fit(X_pca, y)

    print("✔ Training xong!")

    # Lưu toàn bộ model ra file (lần sau không cần train lại)
    model_data = (model, W, mean, label_map)
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model_data, f)
    print(f"💾 Model đã lưu vào '{MODEL_FILE}'")

    # Lưu đặc trưng vào file .npz (thay vì giữ hàng nghìn file ảnh)
    np.savez("features.npz", faces=X, labels=y)
    print("💾 Đặc trưng đã lưu vào 'features.npz'")
    print("💡 Tip: Có thể xóa folder 'dataset/' để giải phóng dung lượng.")

    return model_data

def retrain():
    """
    Xóa model cũ và train lại từ đầu (dùng khi thêm người mới).
    """
    if os.path.exists(MODEL_FILE):
        os.remove(MODEL_FILE)
        print("🗑️ Đã xóa model cũ.")
    return train()

# ===================== RECOGNIZE =====================
def recognize():
    """
    Mở camera, nhận diện khuôn mặt và tự động điểm danh.
    """
    model_data = train()
    if model_data is None:
        return

    model, W, mean, label_map = model_data

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Không mở được camera!")
        return

    print("🎥 Camera đang chạy... Nhấn ESC để thoát.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect khuôn mặt bằng Haar Cascade
        detected_faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in detected_faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, FACE_SIZE).flatten()

            # PCA transform: chiếu khuôn mặt vào không gian giảm chiều
            face_pca = np.dot(face - mean, W)

            # SVM predict: dự đoán khuôn mặt thuộc về ai
            pred = model.predict([face_pca])[0]
            prob = model.predict_proba([face_pca])[0]
            confidence = max(prob) * 100  # Xác suất cao nhất (%)

            name = label_map.get(pred, "Unknown")

            if confidence > 60:
                # Nhận diện thành công
                mark_once(name)
                color = (0, 255, 0)  # Xanh lá
                text = f"{name} ({confidence:.0f}%)"
            else:
                # Không đủ độ tin cậy
                color = (0, 0, 255)  # Đỏ
                text = "Unknown"

            cv2.putText(frame, text, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

        cv2.imshow("Recognize", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("👋 Đã tắt camera.")

# ===================== MAIN =====================
def main():
    print("═" * 40)
    print("  HỆ THỐNG ĐIỂM DANH KHUÔN MẶT")
    print("═" * 40)
    print("  C: Chấm công (nhận diện)")
    print("  R: Đăng ký người mới")
    print("  T: Train lại model")
    print("═" * 40)

    choice = input("Chọn: ").strip().lower()

    if choice == "r":
        name = input("Nhập tên: ").strip()
        if not name:
            print("❌ Tên không được để trống!")
            return
        collect(name)
        retrain()  # Train lại vì có người mới
        recognize()

    elif choice == "c":
        recognize()

    elif choice == "t":
        retrain()

    else:
        print("❌ Lựa chọn không hợp lệ!")

main()