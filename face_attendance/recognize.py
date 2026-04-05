import cv2
import numpy as np
import datetime
import pickle
import os

# ===================== CẤU HÌNH =====================
MODEL_FILE = "model.pkl"    # Từ điển ánh xạ ID → Tên
TRAINER_FILE = "trainer.yml" # Bộ trọng số model LBPH
ATTENDANCE_FILE = "attendance.csv"

# Load bộ phát hiện khuôn mặt Haar Cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ===================== KIỂM TRA FILE =====================
# Kiểm tra model đã được train chưa
if not os.path.exists(TRAINER_FILE):
    print("❌ Chưa có model! Hãy chạy 'python train.py' trước.")
    exit()

if not os.path.exists(MODEL_FILE):
    print("❌ Chưa có file label! Hãy chạy 'python train.py' trước.")
    exit()

# ===================== LOAD MODEL =====================
# Khởi tạo và đọc bộ trọng số model đã huấn luyện
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(TRAINER_FILE)

# Đọc từ điển ánh xạ nhãn (ID → Tên)
with open(MODEL_FILE, "rb") as f:
    labels = pickle.load(f)

# ===================== ĐIỂM DANH =====================
# Set lưu danh sách đã điểm danh HÔM NAY (tránh ghi trùng trong 1 phiên)
marked_today = set()

def mark(name):
    """
    Ghi tên vào file CSV nếu người đó chưa điểm danh HÔM NAY.
    Mỗi ngày mới sẽ được điểm danh lại (không bị block vĩnh viễn).
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    key = f"{name}_{today}"  # Tạo key duy nhất: "Nguyen_2026-04-05"

    if key in marked_today:
        return  # Đã điểm danh hôm nay rồi

    # Kiểm tra trong file CSV xem đã có record hôm nay chưa
    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "r") as f:
            for line in f:
                if name in line and today in line:
                    marked_today.add(key)
                    return  # Đã có trong file rồi

    # Ghi vào file CSV
    marked_today.add(key)
    with open(ATTENDANCE_FILE, "a") as f:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{name},{now}\n")

    print(f"✅ Đã điểm danh: {name} lúc {now}")

# ===================== MỞ CAMERA =====================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Không mở được camera!")
    exit()

print("🎥 Camera đang chạy... Nhấn ESC để thoát.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Đổi khung hình sang ảnh xám
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Phát hiện khuôn mặt trong khung hình bằng Haar Cascade
    detected_faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in detected_faces:
        # Cắt riêng vùng khuôn mặt và resize chuẩn hóa
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (100, 100))

        # Dự đoán: trả về mã ID và độ sai số (confidence)
        # LƯU Ý: confidence CÀNG THẤP tức là khuôn mặt CÀNG KHỚP
        label, confidence = recognizer.predict(face)

        # Lấy tên gọi ứng với mã ID, nếu không có trả về "Unknown"
        name = labels.get(label, "Unknown")

        if confidence < 80:
            # Nhận diện thành công → ghi điểm danh
            mark(name)
            color = (0, 255, 0)  # Xanh lá
            text = f"{name} ({confidence:.0f})"
        else:
            # Không đủ độ tin cậy
            color = (0, 0, 255)  # Đỏ
            text = "Unknown"

        # Vẽ khung bao quanh khuôn mặt và tên
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, text, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Hiện khung hình lên UI
    cv2.imshow("Face Attendance", frame)

    # Thoát nếu nhấn ESC (27)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
print("👋 Đã tắt camera.")