# Ngày 7 — Bài tập
## Nền tảng Dữ liệu: Embedding & Vector Store | Bài tập thực hành

---

## Phần 1 — Khởi động (Cá nhân)

### Bài tập 1.1 — Cosine Similarity (Độ tương tự Cosine) bằng ngôn ngữ đời thường

**Điều gì xảy ra khi hai đoạn văn bản có độ tương tự cosine cao?**
> Độ tương tự cosine cao (tiến gần về 1) biểu thị hai vector chỉ cùng một hướng trong không gian nhiều chiều, nghĩa là hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa và chủ đề, bất kể câu từ biểu đạt khác nhau hay độ dài ngắn khác nhau.

**Ví dụ cụ thể về hai câu có độ tương tự CAO:**
- Câu A: *"Sinh viên có trách nhiệm bảo vệ tài khoản Cổng thông tin đào tạo của mình và không cho người khác sử dụng."*
- Câu B: *"Người học phải tự quản lý mật khẩu tài khoản học vụ cá nhân, chịu trách nhiệm hoàn toàn nếu để lộ thông tin đăng nhập."*
- *Giải thích:* Cùng quy định về nghĩa vụ bảo mật tài khoản học vụ dù dùng các từ đồng nghĩa khác nhau.

**Ví dụ cụ thể về hai câu có độ tương tự THẤP:**
- Câu A: *"Mức nhuận bút đối với sách giáo trình xuất bản được quy định là 70.000đ trên một trang chuẩn."*
- Câu B: *"Đội bóng rổ sinh viên của trường đã xuất sắc giành huy chương vàng tại giải thể thao toàn thành phố."*
- *Giải thích:* Hai câu thuộc hai miền kiến thức độc lập (tài chính thù lao giảng viên vs hoạt động thể thao phong trào), vector chỉ về hai hướng gần như vuông góc.

**Tại sao độ tương tự cosine lại được ưu tiên hơn khoảng cách Euclid (Euclidean distance) đối với text embeddings?**
> Khoảng cách Euclid bị nhạy cảm mạnh bởi độ lớn (magnitude/chiều dài) của vector — câu dài có nhiều từ lặp lại sẽ có độ lớn vector lớn, kéo khoảng cách Euclid ra xa dù cùng chủ đề. Ngược lại, Cosine similarity chỉ đo góc giữa hai vector (hướng ngữ nghĩa), loại bỏ sai lệch do độ dài văn bản; khi vector được chuẩn hóa L2, Cosine similarity tương đương với tích vô hướng (Dot Product), giúp tính toán cực nhanh.

---

### Bài tập 1.2 — Bài toán tính toán Chunking

- Một tài liệu có độ dài 10,000 ký tự. Bạn tiến hành chia nhỏ (chunk) với `chunk_size=500` (kích thước chunk), `overlap=50` (độ chồng chéo). Bạn dự kiến sẽ có bao nhiêu chunks?
  - **Phép tính:**
    - Bước trượt (stride): $\text{stride} = \text{chunk\_size} - \text{overlap} = 500 - 50 = 450$ ký tự.
    - Công thức tổng quát: $\lceil (\text{độ\_dài} - \text{overlap}) / (\text{chunk\_size} - \text{overlap}) \rceil = \lceil (10,000 - 50) / 450 \rceil = \lceil 9,950 / 450 \rceil = \lceil 22.11 \rceil = 23$ chunks.
  - **Đáp án:** **23 chunks**

- Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk sẽ thay đổi như thế nào? Tại sao bạn lại muốn tăng độ chồng chéo?
  - Khi overlap tăng lên 100, bước trượt giảm xuống $500 - 100 = 400$ ký tự. Số chunk là: $\lceil (10,000 - 100) / 400 \rceil = \lceil 9,900 / 400 \rceil = \lceil 24.75 \rceil = 25$ chunks (**tăng thêm 2 chunks**).
  - **Lý do muốn tăng overlap:** Giúp duy trì tính toàn vẹn ngữ cảnh tại các ranh giới cắt, tránh trường hợp một điều khoản quy định hoặc mệnh đề quan trọng bị cắt đôi thành 2 nửa riêng biệt làm mất thông tin khi nhúng vector.

---

## Phần 2 — Lập trình cốt lõi (Cá nhân)

Hoàn thành tất cả các TODOs trong `src/chunking.py`, `src/store.py`, và `src/agent.py`. `Document` dataclass và `FixedSizeChunker` đã được triển khai sẵn làm ví dụ.

### Danh sách cần làm (Checklist)
- [x] `Document` dataclass — ĐÃ TRIỂN KHAI SẴN
- [x] `FixedSizeChunker` — ĐÃ TRIỂN KHAI SẴN
- [x] `SentenceChunker` — tách dựa trên ranh giới câu bằng Regex Lookbehind, nhóm lại thành các chunks
- [x] `RecursiveChunker` — phân cấp separators `["\n\n", "\n", ". ", " ", ""]`, đệ quy và gom mảnh thông minh
- [x] `compute_similarity` — công thức tính độ tương tự cosine kèm cơ chế bảo vệ chia cho 0
- [x] `ChunkingStrategyComparator` — gọi cả ba chiến lược, tính toán các chỉ số thống kê (count, avg_length)
- [x] `EmbeddingStore.__init__` — khởi tạo store lưu trữ trong bộ nhớ kết hợp batching & caching
- [x] `EmbeddingStore.add_documents` — nhúng (embed) và lưu trữ từng tài liệu vào kho RAM
- [x] `EmbeddingStore.search` — nhúng truy vấn, xếp hạng theo tích vô hướng (dot product) / cosine similarity
- [x] `EmbeddingStore.get_collection_size` — trả về số lượng tài liệu/chunk trong kho
- [x] `EmbeddingStore.search_with_filter` — tiền lọc (pre-filtering) theo siêu dữ liệu (metadata), sau đó tìm kiếm
- [x] `EmbeddingStore.delete_document` — xóa tất cả các chunks của một doc_id
- [x] `KnowledgeBaseAgent.answer` — truy xuất (retrieve) + tạo prompt có ngữ cảnh + gọi LLM

> **Kết quả kiểm thử:** Đạt **42 / 42 bài test PASSED (100%)** khi chạy `pytest tests/ -v`.

---

## Phần 3 — So Sánh Chiến Lược Truy Xuất (Nhóm)

### Bài tập 3.0 — Chuẩn Bị Tài Liệu

**Chủ đề:** Quy định đào tạo và dịch vụ học vụ đại học (ViRHE4QA).

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|--------------------|----------------------|:--------:|-----------------|
| 1 | Quy chế đào tạo chính quy | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 165,112 | `{"audience":"student","department":"Phòng Đào tạo","category":"Quy chế đào tạo"}` |
| 2 | Quy định tổ chức thi | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 172,845 | `{"audience":"student","department":"Phòng Khảo thí","category":"Kiểm tra và thi cử"}` |
| 3 | Quy định khóa luận tốt nghiệp | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 81,053 | `{"audience":"student","department":"Phòng Đào tạo","category":"Đánh giá tốt nghiệp"}` |
| 4 | Quy chế văn bằng, chứng chỉ | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 127,573 | `{"audience":"all","department":"Phòng Đào tạo","category":"Hồ sơ học vụ"}` |
| 5 | Quy định dạy học trực tuyến | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 90,254 | `{"audience":"all","department":"Phòng Đào tạo","category":"Dạy và học"}` |
| 6 | Quy định tiêu chuẩn giảng viên | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 86,554 | `{"audience":"faculty","department":"Phòng Công tác giảng viên","category":"Dạy và học"}` |
| 7 | Quy định công tác giáo trình | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 114,266 | `{"audience":"faculty","department":"Phòng Công tác giảng viên","category":"Dạy và học"}` |
| 8 | Quy trình phân công cán bộ coi thi | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 54,176 | `{"audience":"staff","department":"Phòng Khảo thí","category":"Kiểm tra và thi cử"}` |

**Cấu trúc metadata (Metadata Schema):**
- `audience`: Đối tượng áp dụng (`student`, `faculty`, `staff`, `all`).
- `department`: Đơn vị ban hành (`Phòng Đào tạo`, `Phòng Khảo thí`, `Phòng Công tác giảng viên`).
- `category`: Phân loại quy định (`Quy chế đào tạo`, `Kiểm tra và thi cử`, `Hồ sơ học vụ`, `Dạy và học`, `Đánh giá tốt nghiệp`).
- `language`: `vi`.
- `source_url`, `retrieved_at`, `document_version`: `not-stated`.

---

### Bài tập 3.1 — Thiết Kế Chiến Lược Truy Xuất

**Chiến lược cá nhân triển khai:** `RecursiveChunker` (kết hợp `HeadingChunker` cho nhóm).

```python
class RecursiveChunker:
    """Chiến lược phân đoạn đệ quy theo cấu trúc văn bản.

    Lý do thiết kế: Ưu tiên phân tách theo đoạn văn lớn (\\n\\n) và dòng (\\n) trước khi
    cắt câu hoặc từ, giữ nguyên vẹn các danh sách gạch đầu dòng điều khoản học vụ.
    """
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)
```

---

### Bài tập 3.2 — Chuẩn Bị Câu Hỏi Đánh Giá (Benchmark Queries)

Bộ 5 câu hỏi chuẩn (ViRHE4QA):

| # | Câu hỏi (Query) | Metadata filter | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|:---------------:|-------------------------------|--------------------------|
| 1 | Khi sinh viên xin hoãn thi giữa kỳ, hồ sơ cần được xử lý như thế nào? | `{"audience":"student"}` | Sinh viên có lý do chính đáng không thể dự thi giữa kỳ phải nộp đơn kèm minh chứng cho Phòng Đào tạo Đại học trong vòng 03 ngày kể từ ngày thi. | Điều tổng hợp S1 — Quy chế đào tạo chính quy |
| 2 | Bộ phận nào của Trường sẽ xem xét các trường hợp có lí do chính đáng để vắng thi giữa kỳ? | `{}` | P.ĐTĐH | Điều 21 — Quy định tổ chức thi |
| 3 | Thời hạn lưu trữ đề thi các môn học hệ đại học chính quy của Trường là bao lâu? | `{}` | 9 năm | Điều 21 — Quy định khóa luận tốt nghiệp |
| 4 | Sinh viên thuộc chương trình tài năng có các hình thức nào? | `{}` | chính thức và dự bị | Điều 2 — Quy trình phân công cán bộ coi thi |
| 5 | Trong các thành phần điểm của điểm môn học thì điểm giữa kỳ có tên gọi khác là gì? | `{}` | điểm thi giữa học phần | Điều 11 — Quy định khóa luận tốt nghiệp |

---

### Bài tập 3.3 — Dự Đoán Độ Tương Tự Cosine (Cá nhân)

| Cặp | Câu A | Câu B | Dự đoán | Thực tế | Đánh giá |
|:---:|:------|:------|:-------:|:-------:|:--------:|
| 1 | Sinh viên năm cuối cần hoàn thành khóa luận tốt nghiệp đúng thời hạn quy định. | Hạn nộp khóa luận tốt nghiệp đối với sinh viên năm thứ 4 là bắt buộc. | cao | **0.6319** | Đúng |
| 2 | Sinh viên được phép sử dụng tài liệu trong phòng thi môn này. | Tuyệt đối không được mang hoặc sử dụng bất kỳ tài liệu nào trong giờ thi. | cao | **0.5942** | Đúng |
| 3 | Thời gian thông báo lịch thi kết thúc học phần là trước 30 ngày. | Món phở bò truyền thống của Hà Nội có hương vị thơm ngon đậm đà. | thấp | **0.1734** | Đúng |
| 4 | Quy chế đào tạo đại học chính quy áp dụng cho toàn bộ sinh viên. | The full-time undergraduate training regulations apply to all university students. | cao | **0.4529** | Đúng |
| 5 | Hồ sơ đề nghị cấp bằng cử nhân phải có chữ ký của Trưởng khoa. | Chiếc xe ô tô đang chạy bằng phẳng trên con đường cao tốc mới mở. | thấp | **0.2067** | Đúng |

> **Hiện tượng bất ngờ:** Cặp 2 mang nghĩa đối lập ("được phép" vs "tuyệt đối không được") nhưng điểm Cosine rất cao (0.5942), vì mô hình embedding nhóm văn bản theo chủ đề ngữ cảnh (thi cử, tài liệu, phòng thi) chứ không suy luận logic phủ định.

---

### Bài tập 3.4 — Chạy Đánh Giá & So Sánh Trong Nhóm

- **Chiến lược cá nhân (`RecursiveChunker`):** Đạt **8 / 10 điểm** (5/5 câu hỏi có chunk liên quan trong Top-3; 3/5 câu đạt Top-1 tuyệt đối).
- **So sánh với `HeadingChunker`:** `HeadingChunker` đạt **9-10 / 10 điểm** nhờ gắn thêm tiền tố tiêu đề điều luật `[Điều...]` vào đầu mỗi chunk nhỏ.
- **Tác dụng của Metadata Filtering:** Rất rõ rệt ở Câu 1. Khi có `audience: student`, hệ thống loại bỏ hoàn toàn quy định trách nhiệm của giảng viên, định tuyến chính xác vào nghĩa vụ nộp đơn trong vòng 3 ngày của sinh viên.

---

### Bài tập 3.5 — Phân Tích Lỗi (Failure Analysis)

- **Trường hợp lỗi:** Khi không áp dụng metadata filter ở Câu 2 và Câu 3, thứ hạng Top-1 đôi khi bị chiếm bởi các đoạn văn bản có từ vựng lặp lại nhiều lần (như "hồ sơ liên quan", "thời gian lưu trữ 60 ngày"), đẩy đoạn trích quy định "9 năm" xuống vị trí Top-2.
- **Nguyên nhân:** Mô hình dense embeddings có xu hướng ưu tiên các chunk có mật độ từ khóa trùng lặp dày đặc. Ngoài ra, trong kho dữ liệu đại học có nhiều điều khoản được trích dẫn lặp lại nguyên văn ở nhiều file khác nhau (cross-document redundancy).
- **Đề xuất cải thiện:** Kết hợp Hybrid Search (BM25 + Dense Vector) và áp dụng thêm một tầng Re-ranker (Cross-Encoder) để đánh giá lại Top-10 trước khi gửi context cho LLM.

---

## Danh Sách Kiểm Tra Nộp Bài (Submission Checklist)

- [x] Vượt qua tất cả các bài kiểm thử (tests): `pytest tests/ -v` (42 / 42 passed)
- [x] Cập nhật thư mục `src/` (cá nhân)
- [x] Hoàn thành báo cáo nhóm (`report/REPORT_NHOM.md` — 1 file/nhóm)
- [x] Hoàn thành báo cáo cá nhân (`report/REPORT_CANHAN.md` — 1 file/sinh viên)
