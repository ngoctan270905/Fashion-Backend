# Tính năng: API Cập nhật Thông tin Cá nhân Người dùng

Tài liệu này phác thảo kế hoạch phát triển theo từng giai đoạn để triển khai một điểm cuối API cho phép người dùng đã xác thực cập nhật thông tin cá nhân của họ.

## Giai đoạn 1: Định nghĩa Điểm cuối API và Xác thực Đầu vào

1.  **Định nghĩa Điểm cuối API:**
    *   Điểm cuối: `/api/v1/users/me`
    *   Phương thức HTTP: `PUT` (để cập nhật toàn bộ).
    *   Mô tả: Cho phép người dùng đã xác thực cập nhật toàn bộ thông tin hồ sơ của chính họ.

2.  **Tạo Mô hình Yêu cầu Pydantic (schema `UserUpdate`):**
    *   Định nghĩa các trường cho thông tin có thể cập nhật (ví dụ: `first_name`, `last_name`, `email`, `phone_number`, `address`).
    *   Đảm bảo các trường là tùy chọn cho các yêu cầu `PATCH` (sử dụng `Optional` từ `typing` hoặc `None` làm giá trị mặc định).
    *   Thêm các trình xác thực Pydantic thích hợp (ví dụ: định dạng email, ràng buộc độ dài chuỗi).
    *   Vị trí: `app/schemas/user.py`

## Giai đoạn 2: Xác thực, Ủy quyền và Dependency Injection

1.  **Thực hiện Xác thực:**
    *   Đảm bảo điểm cuối được bảo vệ bởi một dependency xác thực (`get_current_active_user`).
    *   Trích xuất đối tượng `current_user` từ dependency.

2.  **Dependency cho Dịch vụ Người dùng:**
    *   Inject `UserService` vào điểm cuối bằng cách sử dụng hệ thống dependency injection của FastAPI.

## Giai đoạn 3: Logic Lớp Dịch vụ (`UserService`)

1.  **Thêm phương thức `update_user` vào `UserService`:**
    *   Chữ ký phương thức: `async def update_user(self, user_id: str, user_data: UserUpdate) -> User:`
    *   Logic:
        *   Nhận `user_id` và schema `UserUpdate`.
        *   Chuyển đổi `UserUpdate` thành một từ điển, lọc bỏ các giá trị chưa được đặt/None để cập nhật một phần.
        *   Gọi `UserRepository` để cập nhật người dùng trong cơ sở dữ liệu.
        *   Trả về đối tượng `User` đã cập nhật.

2.  **Xử lý Lỗi trong Dịch vụ:**
    *   Xử lý các trường hợp không tìm thấy người dùng.
    *   Xử lý các lỗi cơ sở dữ liệu tiềm ẩn hoặc vi phạm ràng buộc duy nhất (ví dụ: nếu cập nhật thành email đã tồn tại). Nâng `HTTPException` với các mã trạng thái thích hợp.

## Giai đoạn 4: Tương tác Lớp Repository (`UserRepository`)

1.  **Thêm phương thức `update_user` vào `UserRepository`:**
    *   Chữ ký phương thức: `async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:`
    *   Logic:
        *   Kết nối với collection MongoDB.
        *   Xây dựng truy vấn cập nhật dựa trên `user_data`.
        *   Sử dụng `find_one_and_update` với `return_document=ReturnDocument.AFTER` để lấy tài liệu đã cập nhật.
        *   Chuyển đổi tài liệu MongoDB trở lại mô hình miền `User`.
        *   Trả về `User` đã cập nhật hoặc `None` nếu không tìm thấy.

## Giai đoạn 5: Tích hợp vào Router và Kiểm thử

1.  **Thêm điểm cuối `PATCH /api/v1/users/me` vào `app/api/v1/endpoints/users.py`:**
    *   Định nghĩa hàm thao tác đường dẫn.
    *   Inject các dependency: `current_user: User = Depends(get_current_active_user)` và `user_service: UserService = Depends(get_user_service)`.
    *   Gọi `user_service.update_user` với `current_user.id` và nội dung yêu cầu.
    *   Trả về dữ liệu người dùng đã cập nhật.

2.  **Thực hiện Kiểm thử Đơn vị/Tích hợp:**
    *   Viết các bài kiểm tra cho xác thực schema `UserUpdate`.
    *   Viết các bài kiểm tra đơn vị cho phương thức `UserService.update_user` (mocking `UserRepository`).
    *   Viết các bài kiểm tra tích hợp cho điểm cuối `PATCH /api/v1/users/me`:
        *   Kiểm tra cập nhật thành công với dữ liệu hợp lệ.
        *   Kiểm tra cập nhật một phần.
        *   Kiểm tra truy cập trái phép.
        *   Kiểm tra dữ liệu đầu vào không hợp lệ.
        *   Kiểm tra các trường hợp dữ liệu có thể xung đột (ví dụ: ràng buộc duy nhất email).
