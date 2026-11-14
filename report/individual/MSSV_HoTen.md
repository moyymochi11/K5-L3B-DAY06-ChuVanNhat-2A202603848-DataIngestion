# Báo cáo cá nhân — Day 6

## Dữ liệu và pipeline
- **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:**
  - Chủ đề: Sổ tay Sinh viên Quốc tế VinUniversity (VinUniversity International Student Handbook 2024-2025).
  - Nguồn & quyền: Tài liệu công khai hướng dẫn sinh viên được phát hành chính thức trên cổng thông tin VinUniversity (`vinuni.edu.vn`), được phép tiếp cận và phân tích phục vụ giáo dục theo quy định của nhà trường và [RULES.md](RULES.md).
  - Số trang: Tổng cộng **54 trang vật lý**.
  - Quy tắc tính trang: Chỉ tính các trang có nội dung văn bản hữu ích ($\ge 80$ ký tự sau chuẩn hóa). Đã lọc bỏ 12 trang không đạt (trang bìa, trang chuyển mục, trang tranh đồ họa hoặc rỗng: các trang 1, 2, 7, 11, 20, 22, 29, 37, 48, 50, 53, 54). Tổng số trang nội dung hữu ích được đưa vào pipeline là **42 trang** (đạt yêu cầu $\ge 30$ trang).
- **Chuẩn hóa, lỗi và giới hạn:**
  - Đọc text trực tiếp từ PDF điện tử bằng thư viện `pypdf`.
  - Chuẩn hóa Unicode theo chuẩn NFKC (`unicodedata.normalize('NFKC', text)`).
  - Chuẩn hóa khoảng trắng: thay thế chuỗi khoảng trắng và xuống dòng thừa bằng khoảng trắng đơn, giữ nguyên dấu câu kết thúc (`.`, `!`, `?`) để hỗ trợ chia câu.
  - Giới hạn: Một số bảng biểu chi phí dạng lưới bị duỗi thành chuỗi văn bản tuyến tính; tuy nhiên từ khóa và giá trị tiền tệ vẫn được bảo toàn nguyên vẹn.
- **Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí:**
  - Embedding Model: `all-MiniLM-L6-v2` chạy local qua ONNX Runtime (384 chiều, sentence-transformers architecture).
  - Vector Store: `ChromaDB` (phiên bản 1.5.9), lưu trữ bền vững (PersistentClient) tại `starter/chroma_store`.
  - Distance Metric: Cosine Similarity ($1 - \text{cosine\_distance}$).
  - Lệnh chạy: `py -m starter.src.run`
  - Chi phí: **$0.00** (chạy hoàn toàn local, không dùng API trả phí).
- **Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn:**
  - Metadata bắt buộc: `document_id` (`vinuni-handbook-2024`), `source` (`vinuni_handbook.pdf`), `page` (số trang vật lý thực tế từ 1 đến 54).
  - Trường lọc bổ sung:
    - `section`: Phân loại theo 7 chương mục mục lục của cuốn sổ tay (`campus_overview`, `pre_arrival`, `arrival_settling_in`, `academic_support`, `social_integration`, `health_and_insurance`, `legal_and_emergency`). Giá trị trích xuất chuẩn xác từ Mục lục (Table of Contents - trang 4). Lý do chọn: Cho phép cô lập phạm vi tìm kiếm theo ngữ cảnh người dùng hỏi (ví dụ hỏi về y tế thì chỉ tìm trong mục sức khỏe, tránh nhiễu từ các mục khác).
    - `year`: 2024 (năm hiệu lực tài liệu).
    - `language`: `en`.

## Cấu hình và benchmark
- **A / B / C (tham số cụ thể, khác biệt duy nhất B–C):**
  - **Chiến lược A (Fixed-Size Baseline):** Cắt theo cửa sổ cố định kích thước 500 ký tự, overlap 50 ký tự (`fixed_size`). Không áp dụng bộ lọc metadata (`filter = None`).
  - **Chiến lược B (Structure-Aware Chunking):** Cắt theo ranh giới câu/đoạn văn tự nhiên (`by_paragraph`), gom các câu hoàn chỉnh tối đa 500 ký tự. Không áp dụng bộ lọc metadata (`filter = None`).
  - **Chiến lược C (Structure-Aware + Metadata Filtering):** Chunking giống hệt Chiến lược B (gom câu tối đa 500 ký tự). Khác biệt duy nhất so với B: Khi câu hỏi có chỉ định điều kiện lọc (`filter`), hệ thống áp dụng `where` filter trong ChromaDB để giới hạn phạm vi chunk.
- **≥20 câu: phân chia ≥15 dev / ≥5 test, câu metadata filter và cách kiểm chứng evidence:**
  - Benchmark gồm đúng **20 câu hỏi**: tách trước **15 câu Dev** (`q01`–`q15`) và **5 câu Test** (`q16`–`q20`).
  - Có 4 câu kiểm tra metadata filter: 3 câu thuộc Dev (`q05`, `q10`, `q14`) và 1 câu thuộc Test (`q18`).
  - Kiểm chứng evidence: 100% câu hỏi đều có `evidence_quote` được đối chiếu bằng văn bản tự động và thủ công, khẳng định tồn tại nguyên văn trên đúng `gold_page` tương ứng.
- **Tiêu chí chọn chiến lược đã chốt trước khi xem test:**
  - Ưu tiên 1: Tối đa hóa Evidence Hit@3 trên tập Dev để đảm bảo không bỏ sót bằng chứng.
  - Ưu tiên 2: Tính mạch lạc (Chunk Coherence) phải đạt mức tối thiểu $\ge 1.5/2.0$ để AI agent và người đọc hiểu trọn vẹn ngữ cảnh.
  - Ưu tiên 3: Tỷ lệ tuân thủ filter (Filter Compliance) đạt 100% khi người dùng có cung cấp điều kiện lọc.

## Kết quả
| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---|---|---|---|---|
| **A** (Fixed) | Dev | 9/15 (60.0%) | 14/15 (93.3%) | 117 | 5.49s | $0.00 |
| **A** (Fixed) | Test | 4/5 (80.0%) | 4/5 (80.0%) | 117 | 5.49s | $0.00 |
| **B** (Paragraph) | Dev | 10/15 (66.7%) | 13/15 (86.7%) | 115 | 5.42s | $0.00 |
| **B** (Paragraph) | Test | 4/5 (80.0%) | 5/5 (100.0%) | 115 | 5.42s | $0.00 |
| **C** (B + Filter) | Dev | 10/15 (66.7%) | 13/15 (86.7%) | 115 | 0.13s | $0.00 |
| **C** (B + Filter) | Test | 4/5 (80.0%) | 5/5 (100.0%) | 115 | 0.13s | $0.00 |

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| **A** | 1.10 / 2.0 (n=10) | 15/15 (100%) | 0/1 (0%) Test (2/4 All) | 0: 1 câu, 1: 0 câu, 2: 4 câu (TB: 1.60/2.0) |
| **B** | 2.00 / 2.0 (n=10) | 15/15 (100%) | 0/1 (0%) Test (1/4 All) | 0: 0 câu, 1: 0 câu, 2: 5 câu (TB: 2.00/2.0) |
| **C** | 2.00 / 2.0 (n=10) | 15/15 (100%) | 1/1 (100%) Test (4/4 All) | 0: 0 câu, 1: 0 câu, 2: 5 câu (TB: 2.00/2.0) |

- **Đường dẫn trace, nhãn thủ công và cách chọn mẫu:**
  - Trace chi tiết từng câu hỏi: `results/traces_strategy_A.json`, `results/traces_strategy_B.json`, `results/traces_strategy_C.json`.
  - File tổng hợp benchmark: `results/benchmark_summary.json`.
  - Nhật ký đánh giá thủ công: `results/manual_audit.json`.
  - Mẫu Coherence: Chọn 10 trang nội dung đầu tiên đã sắp xếp (trang 3, 5, 6, 8, 9, 10, 12, 13, 14, 15).
  - Mẫu Metadata & Grounding: Toàn bộ 5 câu thuộc Test set ($\times 3$ hits = 15 records).

## Phân tích và kết luận
- **So sánh A–B và B–C; 2 ví dụ sai có ID câu và nguồn:**
  - *So sánh A–B (Fixed vs Structure-aware):* 
    - Chiến lược A bị chia cắt cơ học ở ngưỡng 500 ký tự nên có tới 9/10 mẫu coherence bị cắt đứt câu giữa chừng (điểm trung bình chỉ đạt 1.10/2). 
    - **Ví dụ sai 1 (`q16`, trang 6):** Câu hỏi: *"Who is the contact person in charge of Dormitory at VinUniversity?"*. Trong Chiến lược A, cửa sổ cố định đã cắt trang 6 thành 2 chunk: chunk đầu giữ phần email quốc tế, chunk sau bắt đầu từ *"Dung (dung.nv...)"* và vô tình làm đứt gãy thông tin *"Le Bao Anh (anh.lb@vinuni.edu.vn) Dormitory"*. Hậu quả là cả 3 hit của Chiến lược A đều không chứa bằng chứng (Hit@3 = 0, Grounding = 0). Ngược lại, Chiến lược B gom theo câu hoàn chỉnh nên giữ trọn vẹn danh sách liên hệ, đưa chunk chứa Lê Bảo Anh lên Rank 3 (Hit@3 = 1, Grounding = 2).
  - *So sánh B–C (Không lọc vs Có lọc metadata):*
    - Cả hai đều đạt Hit@3 = 5/5 trên tập Test, nhưng Chiến lược C triệt tiêu hoàn toàn các chunk rác đến từ các phân mục không liên quan.
    - **Ví dụ sai 2 (`q18`, trang 49):** Câu hỏi: *"Are international students covered by Vietnam's Social Insurance program for healthcare?"* (yêu cầu filter: `section = health_and_insurance`). Ở Chiến lược B (không lọc), Rank 2 là chunk `vinuni-handbook-2024_p28_para_1` thuộc mục `arrival_settling_in` (bảng chi phí sinh hoạt có nhắc từ "Health insurance ~ 4.570.000"), hoàn toàn không giải quyết được tính pháp lý của bảo hiểm xã hội. Ở Chiến lược C, nhờ có filter `where={"section": "health_and_insurance"}`, toàn bộ top-3 đều thuộc đúng trang 49, cung cấp trọn vẹn thông tin phòng khám và hãng bảo hiểm liên kết. Tỷ lệ tuân thủ filter đạt 100%.
- **Chiến lược chọn, đánh đổi, điều kiện áp dụng:**
  - **Chiến lược được chọn: Chiến lược C (hoặc B khi người dùng không cung cấp filter).**
  - Đánh đổi: Chunking theo câu/đoạn đòi hỏi bộ parser xử lý kỹ hơn fixed window; metadata filtering đòi hỏi tài liệu phải có nhãn chương mục đáng tin cậy. Nếu người dùng nhập sai nhãn filter, nguy cơ lọc nhầm tài liệu có thể xảy ra.
  - Điều kiện áp dụng: Phù hợp nhất cho các hệ thống hỏi đáp tài liệu quy chuẩn (sổ tay, quy chế, chính sách) nơi người dùng hoặc giao diện có thể xác định trước phạm vi chủ đề.
- **Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí:**
  - Dữ liệu 42 trang nội dung dù đủ chuẩn nhưng vẫn là quy mô nhỏ trong thực tế doanh nghiệp.
  - Tập Test gồm 5 câu là mẫu đại diện minh họa, không đủ lớn để suy rộng về mặt thống kê xác suất cao.
  - Chi phí $0.00 là do dùng model local ONNX; nếu chuyển sang API đám mây lớn (Gemini Embedding / OpenAI text-embedding-3-small) sẽ phát sinh chi phí token dù chất lượng ngữ nghĩa có thể tăng thêm.
- **Nếu làm lại hoặc mở rộng, cải tiến gì?**
  - Thử nghiệm Hybrid Retrieval (kết hợp Chroma vector search với BM25 keyword search) để xử lý tốt hơn các mã môn học hoặc tên viết tắt đặc thù (như VISA, SAM, SSIC).
  - Bổ sung trích xuất bảng chuyên dụng (table parsing) để xử lý các bảng chi phí và khung chương trình học kỳ chính xác hơn.
