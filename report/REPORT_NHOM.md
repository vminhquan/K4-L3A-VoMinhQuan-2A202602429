# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định đào tạo và dịch vụ học vụ đại học

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề này vì phù hợp trực tiếp với biến thể K4-L3A và có câu hỏi thực tế cho sinh viên, giảng viên và cán bộ. ViRHE4QA có context, câu hỏi và gold answer tiếng Việt, phù hợp để thử retrieval và metadata filtering.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy chế đào tạo chính quy | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 165112 | `{"audience":"student","department":"Phòng Đào tạo","category":"Quy chế đào tạo"}` |
| 2 | Quy định tổ chức thi | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 172845 | `{"audience":"student","department":"Phòng Khảo thí","category":"Kiểm tra và thi cử"}` |
| 3 | Quy định khóa luận tốt nghiệp | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 81053 | `{"audience":"student","department":"Phòng Đào tạo","category":"Đánh giá tốt nghiệp"}` |
| 4 | Quy chế văn bằng, chứng chỉ | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 127573 | `{"audience":"all","department":"Phòng Đào tạo","category":"Hồ sơ học vụ"}` |
| 5 | Quy định dạy học trực tuyến | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 90254 | `{"audience":"all","department":"Phòng Đào tạo","category":"Dạy và học"}` |
| 6 | Quy định tiêu chuẩn giảng viên | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 86554 | `{"audience":"faculty","department":"Phòng Công tác giảng viên","category":"Dạy và học"}` |
| 7 | Quy định công tác giáo trình | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 114266 | `{"audience":"faculty","department":"Phòng Công tác giảng viên","category":"Dạy và học"}` |
| 8 | Quy trình phân công cán bộ coi thi | https://github.com/DoPhamPhucTinh/R2GQA | 2026-09-19 / not-stated | 54176 | `{"audience":"staff","department":"Phòng Khảo thí","category":"Kiểm tra và thi cử"}` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string | `student`, `faculty`, `staff`, `all` | Lọc theo đối tượng áp dụng |
| `department` | string | `Phòng Đào tạo`, `Phòng Khảo thí` | Lọc theo đơn vị phụ trách |
| `category` | string | `Dạy và học`, `Kiểm tra và thi cử` | Lọc theo loại quy định |
| `language` | string | `vi` | Xác định ngôn ngữ corpus |
| `source_url` | string | GitHub R2GQA | Truy vết nguồn |
| `retrieved_at` | date | `2026-09-19` | Thời điểm lấy dữ liệu |
| `document_version` | string | `not-stated` | Không bịa version khi nguồn không nêu |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Quy chế đào tạo chính quy | FixedSizeChunker (`fixed_size`) | 331 | 498.83 | Có thể cắt giữa điều khoản |
| Quy chế đào tạo chính quy | SentenceChunker (`by_sentences`) | 538 | 304.61 | Dễ đọc hơn nhưng chưa giữ heading |
| Quy chế đào tạo chính quy | RecursiveChunker (`recursive`) | 543 | 302.51 | Giữ cấu trúc tốt hơn fixed-size |
| Quy định tổ chức thi | FixedSizeChunker (`fixed_size`) | 346 | 499.55 | Có nguy cơ cắt giữa quy trình |
| Quy định tổ chức thi | SentenceChunker (`by_sentences`) | 602 | 285.12 | Chunk ngắn, nhiều context bị tách |
| Quy định tổ chức thi | RecursiveChunker (`recursive`) | 568 | 302.73 | Cân bằng hơn giữa độ dài và cấu trúc |
| Quy định khóa luận tốt nghiệp | FixedSizeChunker (`fixed_size`) | 163 | 497.26 | Chunk lớn, dễ chứa nhiều ý |
| Quy định khóa luận tốt nghiệp | SentenceChunker (`by_sentences`) | 275 | 292.81 | Dễ đọc nhưng nhiều chunk |
| Quy định khóa luận tốt nghiệp | RecursiveChunker (`recursive`) | 254 | 317.56 | Giữ đoạn/điều tốt hơn baseline |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** FixedSizeChunker với overlap
- **Mô tả & lý do chọn cho chủ đề này:** Làm baseline đơn giản, dễ tái lập và đo tác động của overlap.
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn:** Ưu tiên paragraph, newline và sentence trước khi cắt theo ký tự, phù hợp với quy định có nhiều điều khoản.
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:** Heading/section chunker
- **Mô tả & lý do chọn:** Tách theo `Điều` hoặc `Chương`; section quá dài sẽ fallback về recursive. Đây là chiến lược heading bắt buộc của K4.
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Metadata filter | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-----------------|-------------------------------|--------------------------|
| 1 | Khi sinh viên xin hoãn thi giữa kỳ, hồ sơ cần được xử lý như thế nào? | `{"audience":"student"}` | Sinh viên có lý do chính đáng không thể dự thi giữa kỳ phải nộp đơn kèm minh chứng cho Phòng Đào tạo Đại học trong vòng 03 ngày kể từ ngày thi. | Điều tổng hợp S1 — Quy chế đào tạo chính quy |
| 2 | Bộ phận nào của Trường sẽ xem xét các trường hợp có lí do chính đáng để vắng thi giữa kỳ? | `{}` | P.ĐTĐH | Điều 21 — Quy định tổ chức thi |
| 3 | Thời hạn lưu trữ đề thi các môn học hệ đại học chính quy của Trường là bao lâu? | `{}` | 9 năm | Điều 21 — Quy định khóa luận tốt nghiệp |
| 4 | Sinh viên thuộc chương trình tài năng có các hình thức nào? | `{}` | chính thức và dự bị | Điều 2 — Quy trình phân công cán bộ coi thi |
| 5 | Trong các thành phần điểm của điểm môn học thì điểm giữa kỳ có tên gọi khác là gì? | `{}` | điểm thi giữa học phần | Điều 11 — Quy định khóa luận tốt nghiệp |

> **Note về metadata filter:** Câu 1 được chạy hai lần với cùng một query. Filter `{"audience":"student"}` trả về trách nhiệm của sinh viên trong Điều tổng hợp S1; filter `{"audience":"faculty"}` trả về trách nhiệm của giảng viên trong Điều tổng hợp F1. Hai gold answer đều được trích nguyên văn từ hai file Markdown, nhưng đây là dữ liệu synthetic do nhóm thêm để kiểm thử filter, không phải quy định chính thức của trường.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Chưa chạy | Chưa chạy | Chờ mọi thành viên chạy |
| 2 | Chưa chạy | Chưa chạy | Chờ mọi thành viên chạy |
| 3 | Chưa chạy | Chưa chạy | Chờ mọi thành viên chạy |
| 4 | Chưa chạy | Chưa chạy | Chờ mọi thành viên chạy |
| 5 | Chưa chạy | Chưa chạy | Chờ mọi thành viên chạy |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Chưa kết luận trước khi mọi thành viên chạy cùng 5 query với chiến lược riêng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> Chưa tổng hợp; sẽ tập trung vào độ mạch lạc của chunk, top-3 retrieval và tác động của metadata filter.

**Bài học rút ra khi so sánh trong nhóm:**
> Chưa tổng hợp; cần kết quả chạy thật của cả nhóm.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Chưa tổng hợp; nhóm sẽ kiểm tra lại document mapping và làm sạch context nhiễu trước benchmark.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
