# Benchmark queries — ViRHE4QA (K4-L3A)

Bộ 5 query bao phủ đủ 4 dạng câu hỏi (tra cứu thẩm quyền, tra số liệu thời hạn, liệt kê hình thức, tra cứu thuật ngữ) và các chiều metadata của corpus (`audience`, `department`, `category`).
Mọi gold answer đều được trích xuất trực tiếp từ tài liệu Markdown trong `data/university/`, không suy đoán.

| # | Dạng câu hỏi | Audience | Query | Gold answer | Document (`doc_id`) | Metadata filter | Kết quả Retrieval |
|---:|---|---|---|---|---|---|:---:|
| 1 | **Hỏi quy trình & Lọc đối tượng** | `student` | Khi sinh viên xin hoãn thi giữa kỳ, hồ sơ cần được xử lý như thế nào? | Sinh viên có lý do chính đáng không thể dự thi giữa kỳ phải nộp đơn kèm minh chứng cho Phòng Đào tạo Đại học trong vòng 03 ngày kể từ ngày thi. | `quy-che-dao-tao-chinh-quy` | `{"audience": "student"}` | **Top-1 (2/2)** |
| 2 | **Tra cứu thẩm quyền** | `student` | Bộ phận nào của Trường sẽ xem xét các trường hợp có lí do chính đáng để vắng thi giữa kỳ? | P.ĐTĐH | `quy-dinh-to-chuc-thi` | `{}` | **Top-1 (2/2)** |
| 3 | **Tra số liệu thời hạn** | `student` | Thời hạn lưu trữ đề thi các môn học hệ đại học chính quy của Trường là bao lâu? | 9 năm | `quy-dinh-khoa-luan-tot-nghiep` | `{}` | **Top-1 (2/2)** |
| 4 | **Liệt kê hình thức** | `staff` | Sinh viên thuộc chương trình tài năng có các hình thức nào? | chính thức và dự bị | `quy-trinh-phan-cong-can-bo-coi-thi` | `{}` | **Top-1 (2/2)** |
| 5 | **Tra cứu thuật ngữ** | `student` | Trong các thành phần điểm của điểm môn học thì điểm giữa kỳ có tên gọi khác là gì? | điểm thi giữa học phần | `quy-dinh-khoa-luan-tot-nghiep` | `{}` | **Top-1 (2/2)** |

> **Ghi chú về metadata filter (Câu 1):** 
> - Với filter `{"audience": "student"}`: hệ thống truy xuất và trả về trách nhiệm nộp đơn của sinh viên trong `quy-che-dao-tao-chinh-quy.md`.
> - Với filter `{"audience": "faculty"}`: hệ thống hướng vào quy định trách nhiệm xác nhận lý do và nộp điểm bổ sung của giảng viên trong `quy-dinh-tieu-chuan-giang-vien.md`.
