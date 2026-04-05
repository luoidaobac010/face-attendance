import cv2
import os

# Load bộ phát hiện khuôn mặt Haar Cascade (có sẵn trong OpenCV)
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# Nhập tên người dùng để tạo thư mục lưu trữ riêng cho mỗi người
name = input("Nhập tên: ")
path = f"dataset/{name}"

# Tạo thư mục (nếu chưa có). exist_ok=True giúp không báo lỗi nếu thư mục đã tồn tại.
os.makedirs(path, exist_ok=True)

# Khởi động Webcam (ID = 0 thường là camera mặc định)
cap = cv2.VideoCapture(0)

# Kiểm tra camera có mở được không
if not cap.isOpened():
    print("❌ Không mở được camera!")
    exit()

count = 0  # Đếm số lượng ảnh đã chụp
MAX_IMAGES = 50  # Chỉ cần 50 ảnh là đủ (giảm từ 200 → 50 để tiết kiệm bộ nhớ)

print(f"📸 Đang chụp {MAX_IMAGES} ảnh khuôn mặt cho '{name}'...")
print("💡 Hãy xoay mặt nhiều góc khác nhau để model học tốt hơn!")
print("🛑 Nhấn ESC để dừng sớm.")

while count < MAX_IMAGES:
    # Đọc mỗi khung hình (frame) từ camera
    ret, frame = cap.read()
    if not ret:
        break

    # Chuyển khung hình sang ảnh xám (Grayscale)
    # Lý do: Trong nhận diện khuôn mặt, màu sắc ít quan trọng và ảnh xám giúp xử lý nhanh hơn.
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Dùng Haar Cascade để phát hiện vùng khuôn mặt trong khung hình
    # scaleFactor=1.3: thu nhỏ ảnh 30% mỗi lần quét (tốc độ vs độ chính xác)
    # minNeighbors=5: cần ít nhất 5 vùng lân cận xác nhận là mặt (tránh nhận nhầm)
    detected_faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in detected_faces:
        # Cắt riêng vùng khuôn mặt từ ảnh xám (không lưu nền phía sau)
        face = gray[y:y+h, x:x+w]

        # Resize chuẩn hóa về 100x100 pixel cho đồng nhất khi train
        face = cv2.resize(face, (100, 100))

        # Lưu ảnh khuôn mặt (chỉ vùng mặt, không có nền)
        cv2.imwrite(f"{path}/{count}.jpg", face)
        count += 1

        # Vẽ khung xanh bao quanh khuôn mặt trên giao diện
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Hiện số ảnh đã chụp trên màn hình
        cv2.putText(frame, f"{count}/{MAX_IMAGES}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Hiển thị khung hình lên giao diện để người dùng có thể thấy
    cv2.imshow("Collecting", frame)

    # Thoát nếu nhấn ESC (mã 27)
    if cv2.waitKey(1) == 27:
        break

# Giải phóng bộ nhớ của camera và đóng tất cả cửa sổ giao diện
cap.release()
cv2.destroyAllWindows()
print(f"✔ Đã chụp {count} ảnh khuôn mặt cho '{name}'")