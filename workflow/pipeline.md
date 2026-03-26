# Pipeline

## Bước 1: Coder Agent
- Đọc yêu cầu
- Áp dụng coding_rules.md
- Viết code

## Bước 2: Reviewer Agent
- Đọc code vừa viết
- Áp dụng review_rules.md
- Đưa ra nhận xét

## Bước 3: Kiểm tra Checklist
- Chạy qua pr_checklist.md
- Nếu pass → tiếp tục
- Nếu fail → quay lại Bước 1

## Bước 4: Lưu Log
- Lưu kết quả toàn bộ pipeline vào /logs
- Ghi lại: thời gian, kết quả từng bước, lỗi nếu có