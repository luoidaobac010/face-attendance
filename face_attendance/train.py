import cv2
import os
import numpy as np
import pickle

# Đường dẫn folder chứa các ảnh khuôn mặt dùng để học
DATASET = "dataset"
MODEL_FILE = "model.pkl"      # File lưu model LBPH đã train
FEATURES_FILE = "features.npz" # File lưu đặc trưng (thay vì giữ ảnh gốc)

def load_dataset():
    """
    Đọc tất cả ảnh từ thư mục dataset và trả về:
    - faces: danh sách các ma trận ảnh (đã resize 100x100)
    - labels: danh sách ID tương ứng
    - label_map: từ điển ánh xạ ID → Tên người
    """
    faces = []
    labels = []
    label_map = {}
    label_id = 0

    # Kiểm tra thư mục dataset có tồn tại không
    if not os.path.exists(DATASET):
        print("❌ Thư mục 'dataset' không tồn tại! Hãy chạy collect.py trước.")
        return [], [], {}

    # Bước 1: Quét qua từng thư mục con (mỗi folder đại diện một người)
    for person in os.listdir(DATASET):
        person_path = os.path.join(DATASET, person)

        # Bỏ qua nếu không phải thư mục
        if not os.path.isdir(person_path):
            continue

        # Đưa Tên người đó ứng với biến ID hiện tại vào từ điển
        label_map[label_id] = person

        # Bước 2: Quét toàn bộ ảnh bên trong folder của người đó
        for img_name in os.listdir(person_path):
            img_path = os.path.join(person_path, img_name)

            # Đọc ảnh ở chế độ Trắng/Đen (GrayScale) bằng tham số 0
            img = cv2.imread(img_path, 0)

            # Bỏ qua nếu ảnh bị lỗi không đọc được
            if img is None:
                continue

            # Resize chuẩn hóa về 100x100 để đồng nhất kích thước
            img = cv2.resize(img, (100, 100))

            # Lưu ảnh và ID tương ứng vào danh sách
            faces.append(img)
            labels.append(label_id)

        # Cộng ID lên 1 để chuẩn bị cho người tiếp theo
        label_id += 1

    return faces, labels, label_map


def train():
    """
    Huấn luyện model LBPH và lưu kết quả ra file.
    Sau khi train xong, có thể xóa folder dataset để tiết kiệm dung lượng.
    """
    faces, labels, label_map = load_dataset()

    if len(faces) == 0:
        print("❌ Không có dữ liệu để train!")
        return False

    print(f"📊 Tìm thấy {len(faces)} ảnh của {len(label_map)} người")

    # Bước 3: Lưu đặc trưng vào file .npz (thay vì giữ hàng nghìn file ảnh)
    # File .npz nén tất cả ảnh + nhãn vào MỘT file duy nhất
    # VD: 1000 người x 50 ảnh = 50,000 file JPG → 1 file features.npz (~50MB)
    faces_array = np.array(faces)
    labels_array = np.array(labels)
    np.savez(FEATURES_FILE, faces=faces_array, labels=labels_array)
    print(f"💾 Đã lưu đặc trưng vào '{FEATURES_FILE}'")

    # Bước 4: Khởi tạo và huấn luyện Thuật toán LBPH Face Recognizer
    # LBPH (Local Binary Patterns Histograms) trích xuất đặc trưng khuôn mặt
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    # Bắt đầu quá trình Huấn Luyện (Phân loại ảnh thuộc vào ID nào)
    recognizer.train(faces, labels_array)

    # Bước 5: Lưu model và từ điển tên vào file pickle
    # Lần sau chỉ cần load file này, không cần train lại → tiết kiệm thời gian
    recognizer.save("trainer.yml")

    with open(MODEL_FILE, "wb") as f:
        pickle.dump(label_map, f)

    print(f"✔ Training xong! Model đã lưu vào '{MODEL_FILE}' và 'trainer.yml'")
    print("💡 Tip: Bạn có thể xóa folder 'dataset/' để giải phóng dung lượng.")
    print("   Model đã học xong và không cần ảnh gốc nữa.")
    return True


if __name__ == "__main__":
    train()