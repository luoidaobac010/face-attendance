# Face Attendance System

Hệ thống điểm danh tự động bằng nhận diện khuôn mặt sử dụng OpenCV (Haar Cascade & LBPH).

## 🗺️ Lộ Trình Thuyết Trình Gợi Ý (Roadmap)

Bài thuyết trình dự án có thể được chia thành 5 phần sau để ban giám khảo/người nghe dễ theo dõi:

1. **Phần 1: Giới thiệu dự án (Introduction)**
   - Đặt vấn đề: Tại sao cần hệ thống điểm danh bằng khuôn mặt? (Khắc phục điểm danh giấy, tránh điểm danh hộ, tự động hóa...).
   - Mục tiêu dự án: Xây dựng hệ thống tự động nhận diện và ghi nhận thời gian ra/vào.

2. **Phần 2: Luồng hoạt động của hệ thống (System Flow)**
   - Bước 1: **Thu thập dữ liệu (Collect)** - Chụp ảnh khuôn mặt người dùng.
   - Bước 2: **Huấn luyện mô hình (Train)** - Học các đặc trưng khuôn mặt.
   - Bước 3: **Nhận diện & Điểm danh (Recognize)** - So sánh khuôn mặt với dữ liệu đã học và ghi vào file Excel/CSV.

3. **Phần 3: Các thuật toán cốt lõi (Core Algorithms)** 
   - Giải thích thuật toán **Haar Cascade** (Dùng để tìm ra khuôn mặt nằm ở đâu trong khung hình).
   - Giải thích thuật toán **LBPH** (Dùng để xác định khuôn mặt đó là của ai).
   *(Xem chi tiết lý thuyết ở phần dưới)*

4. **Phần 4: Demo thực tế (Live Demonstration)**
   - Bật camera và demo trực tiếp việc điểm danh.
   - Hiển thị file ghi nhận kết quả (`attendance.csv` / `attendance.xlsx`) theo thời gian thực.

5. **Phần 5: Hạn chế và Hướng phát triển (Future Works)**
   - Hạn chế: Haar Cascade dễ bị ảnh hưởng bởi ánh sáng; LBPH có thể bị đánh lừa bởi ảnh chụp (spoofing).
   - Hướng phát triển: Nâng cấp lên các model Deep Learning như YOLO/MTCNN để phát hiện, FaceNet/ArcFace để nhận diện, hoặc thêm chức năng Liveness Detection (chống giả mạo).

---

## 🧠 Các Thuật Toán Sử Dụng & Lý Thuyết

Dự án sử dụng thư viện **OpenCV** với 2 thuật toán Machine Learning truyền thống:

### 1. Thuật toán Haar Cascade (Face Detection - Phát hiện khuôn mặt)
* **Mục đích:** Tìm kiếm xem trong khung hình camera có khuôn mặt nào không, và khoanh vùng vị trí tọa độ $(x, y, w, h)$ của khuôn mặt đó.
* **Lý thuyết hoạt động:**
  1. **Đặc trưng Haar (Haar Features):** Thuật toán sử dụng các cửa sổ hình chữ nhật (trắng và đen) trượt qua lại trên bức ảnh xám. Nó tính sự chênh lệch tổng giá trị các pixel ở vùng đen và vùng trắng. Ví dụ: Vùng mắt thường tối hơn vùng gò má. Sự chênh lệch này tạo ra một "đặc trưng" để nhận biết.
     - **Công thức:** $\Delta = \sum (\text{Pixels vùng đen}) - \sum (\text{Pixels vùng trắng})$
  2. **Integral Image (Ảnh tích phân):** Để tính toán sự chênh lệch pixel cực nhanh cho hàng ngàn khung chữ nhật, thuật toán dùng khái niệm Integral Image để tăng tốc (chỉ tốn $O(1)$ thời gian tính toán cho mỗi đặc trưng).
  3. **Adaboost Learning:** Ban đầu có hàng trăm ngàn đặc trưng, Adaboost sẽ chọn lọc ra những đặc trưng tốt nhất (ví dụ: khoảng 6000 đặc trưng) để loại bỏ những thứ vô ích.
  4. **Cascade of Classifiers (Bộ phân loại tầng):** Nó ghép các đặc trưng thành các "trạm kiểm duyệt". Trạm 1 chỉ dùng 1-2 đặc trưng cơ bản (vd: sống mũi, hốc mắt). Nếu một vùng ảnh trượt qua trạm 1 mà bị fail -> Loại ngay lập tức. Càng vào sâu, trạm kiểm duyệt càng phức tạp. Giúp thuật toán quét khung hình rất nhanh vì phần lớn background sẽ bị loại từ sớm.
* **Tóm tắt:** *"Haar Cascade hoạt động như một cỗ máy trượt các ô đen trắng qua ảnh để tìm sự tương phản sáng tối. Bằng cách dùng nhiều lớp lọc từ dễ đến khó, nó loại bỏ nhanh những vùng không phải mặt người và chỉ giữ lại khuôn mặt với tốc độ rất nhanh."*

### 2. Thuật toán LBPH (Face Recognition - Nhận diện khuôn mặt)
* **Mục đích:** Sau khi Haar Cascade cắt được khuôn mặt, LBPH sẽ phân tích khuôn mặt đó và đối chiếu với dữ liệu đã train để định danh (ID/Tên người).
* **LBPH là viết tắt của:** Local Binary Patterns Histograms (Biểu đồ mẫu nhị phân cục bộ).
* **Lý thuyết hoạt động:**
  1. **Trích xuất đặc trưng LBP (Local Binary Pattern):** Thuật toán chia khuôn mặt thành nhiều ô lưới nhỏ. Tại mỗi điểm ảnh (pixel), nó so sánh cường độ sáng của pixel đó với 8 pixel xung quanh.
     - Nếu pixel xung quanh >= pixel trung tâm -> Gán giá trị $1$.
     - Nếu pixel xung quanh < pixel trung tâm -> Gán giá trị $0$.
     - Kết quả tạo ra một chuỗi nhị phân 8 bit (ví dụ: `10011011`), sau đó chuyển thành số thập phân.
     - **Công thức tính LBP:** $LBP(x_c, y_c) = \sum_{p=0}^{7} s(i_p - i_c) 2^p$
       *(Trong đó: $i_c$ là cường độ pixel trung tâm, $i_p$ là cường độ 8 pixel xung quanh, hàm $s(x)=1$ nếu $x \ge 0$, ngược lại $s(x)=0$)*
  2. **Tạo Histogram (Biểu đồ):** Từ các giá trị thập phân trên, nó vẽ ra một biểu đồ Histogram đại diện cho các vùng trên khuôn mặt (mắt, mũi, miệng). Kết hợp các biểu đồ nhỏ này lại ta có một "bức thư họa" (vector đặc trưng) hoàn chỉnh của khuôn mặt.
  3. **Huấn luyện (Training):** Thuật toán tạo ra các Histogram chuẩn cho từng người và lưu vào file (ví dụ: `trainer.yml`).
  4. **Nhận diện (Predicting):** Khi có khuôn mặt mới, thuật toán cũng chuyển thành Histogram và đo khoảng cách (thường dùng khoảng cách Euclidean) với các Histogram trong Database. 
     - **Công thức khoảng cách Euclidean:** $D = \sqrt{\sum_{i=1}^{n} (H1_i - H2_i)^2}$
       *(Với $H1$ và $H2$ là hai vector Histogram cần so sánh)*
     - Khoảng cách này chính là độ tin cậy (`confidence`). Số này **càng nhỏ** -> Hai ảnh càng giống nhau -> Xác nhận đúng người.
* **Tóm tắt:** *"LBPH không nhìn toàn bộ khuôn mặt mà chia mặt thành các ô vuông nhỏ. Ở mỗi pixel, nó so sánh ánh sáng với các pixel xung quanh để vẽ ra một biểu đồ cấu trúc. Khi có người đứng trước camera, nó tạo biểu đồ của người đó và so sánh với biểu đồ đã học để tìm ra người giống nhất. Thuật toán này rất ổn định trong điều kiện ánh sáng thay đổi."*
