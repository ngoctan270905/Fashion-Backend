from fastapi import HTTPException, status

class CustomException(HTTPException):
    """
        Lớp ngoại lệ cơ sở kế thừa từ HTTPException của FastAPI.

        Dùng để chuẩn hóa cách tạo các HTTP exception trong toàn bộ hệ thống,
        giúp code dễ đọc, dễ bảo trì và mở rộng sau này.
    """

    def __init__(self, status_code: int, detail: str = None, headers: dict = None):
        """
            Khởi tạo một HTTP exception tùy chỉnh.
        """
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class NotFoundException(CustomException):
    """
        Ngoại lệ được sử dụng khi không tìm thấy tài nguyên.

        Trả về HTTP 404 Not Found.
    """
    def __init__(self, detail: str = "Resource not found", headers: dict = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)

class UnauthorizedException(CustomException):
    """
       Ngoại lệ được sử dụng khi người dùng chưa xác thực
       hoặc xác thực thất bại.

       Trả về HTTP 401 Unauthorized.
       Mặc định thêm header 'WWW-Authenticate: Bearer'.
    """
    def __init__(self, detail: str = "Not authenticated", headers: dict = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"},
        )

class ForbiddenException(CustomException):
    """
       Ngoại lệ được sử dụng khi người dùng không có quyền
       thực hiện hành động.

       Trả về HTTP 403 Forbidden.
    """
    def __init__(self, detail: str = "Not authorized to perform this action", headers: dict = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers=headers)

class ConflictException(CustomException):
    """
       Ngoại lệ được sử dụng khi xảy ra xung đột dữ liệu
       (ví dụ: trùng email, trùng username,...).

       Trả về HTTP 409 Conflict.
    """
    def __init__(self, detail: str = "Conflict occurred", headers: dict = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, headers=headers)
