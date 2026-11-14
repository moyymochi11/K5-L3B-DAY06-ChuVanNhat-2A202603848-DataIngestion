# Day 06 · Data Ingestion Engineering

**Học viên:** Chu Văn Nhật · **MSSV:** 2A202603848 · **Lớp:** L3B  
**Chủ đề & Corpus:** Sổ tay Sinh viên Quốc tế VinUniversity (*VinUniversity International Student Handbook 2024-2025*, 54 trang vật lý, 42 trang nội dung hữu ích).  
**Báo cáo cá nhân chi tiết:** [report/individual/2A202603848_ChuVanNhat.md](report/individual/2A202603848_ChuVanNhat.md) (hoặc [report/individual/MSSV_HoTen.md](report/individual/MSSV_HoTen.md)).

---

## 🚀 Hướng dẫn chạy và tái lập (Quickstart & Reproduction)

### 1. Cài đặt thư viện
Dự án sử dụng Python 3.11+, Vector Store bền vững **ChromaDB** và Embedding Model thật **all-MiniLM-L6-v2** (384 chiều, chạy hoàn toàn local qua ONNX Runtime, không cần Docker, chi phí $0.00).

```bash
pip install -r starter/requirements.txt
```

### 2. Chạy toàn bộ Pipeline (3 Chiến lược A / B / C & Đánh giá Benchmark)
Chạy lệnh sau tại thư mục gốc của dự án:

```bash
py -m starter.src.run
# Hoặc: py -m src.run
```

Kết quả sẽ tự động được xuất ra:
* Vết truy xuất chi tiết từng câu: `results/traces_strategy_A.json`, `traces_strategy_B.json`, `traces_strategy_C.json`.
* Tổng kết benchmark: `results/benchmark_summary.json`.
* Đánh giá thủ công Coherence & Grounding: `results/manual_audit.json`.
* Nhật ký thí nghiệm: `artifacts/experiment_log.csv`.

---

## 📊 Bảng tổng kết kết quả 3 Chiến lược

| Tiêu chí | Chiến lược A (Fixed 500) | Chiến lược B (Paragraph) | Chiến lược C (Paragraph + Filter) |
|---|:---:|:---:|:---:|
| **Số lượng chunk** | 117 chunks | 115 chunks | 115 chunks |
| **Thời gian nạp** | 5.54s | 5.13s | 0.13s |
| **Chi phí** | **$0.00** | **$0.00** | **$0.00** |
| **Dev Hit@1 / Hit@3** | 9/15 (60.0%) / 14/15 (93.3%) | **10/15 (66.7%)** / 13/15 (86.7%) | **10/15 (66.7%)** / 13/15 (86.7%) |
| **Test Hit@1 / Hit@3** | 4/5 (80.0%) / 4/5 (80.0%) | 4/5 (80.0%) / **5/5 (100.0%)** | 4/5 (80.0%) / **5/5 (100.0%)** |
| **Coherence trung bình /2** | 1.10 / 2.0 (bị cắt cụt câu) | **2.00 / 2.0 (trọn vẹn ý)** | **2.00 / 2.0 (trọn vẹn ý)** |
| **Metadata đúng & đủ (Test)**| 15/15 (100%) | 15/15 (100%) | 15/15 (100%) |
| **Filter tuân thủ (Test)** | 0/1 (0%) | 0/1 (0%) | **1/1 (100%)** |
| **Grounding trung bình /2** | 1.60 / 2.0 | **2.00 / 2.0** | **2.00 / 2.0** |

---

## 📁 Cấu trúc thư mục bài nộp

```text
├── STUDENT.md                               # Thông tin cá nhân học viên
├── README.md                                # Hướng dẫn cài đặt, chạy và cấu trúc dự án
├── data/
│   ├── manifest.json                        # Khai báo nguồn, quyền, 42 trang nội dung hợp lệ
│   └── vinuni_international_student_handbook.pdf  # Tài liệu PDF gốc
├── benchmark/
│   └── benchmark.json                       # 20 câu hỏi (15 dev / 5 test), gold evidence & filter
├── artifacts/
│   └── experiment_log.csv                   # Nhật ký đo đạc thông số và giả thuyết A/B/C
├── results/
│   ├── benchmark_summary.json               # Tổng hợp tỷ lệ Hit@1, Hit@3, Filter compliance
│   ├── manual_audit.json                    # Bảng chấm tay Coherence, Metadata và Grounding
│   ├── traces_strategy_A.json               # Trace top-3 chi tiết Strategy A
│   ├── traces_strategy_B.json               # Trace top-3 chi tiết Strategy B
│   └── traces_strategy_C.json               # Trace top-3 chi tiết Strategy C
├── report/individual/
│   ├── 2A202603848_ChuVanNhat.md            # Báo cáo cá nhân hoàn chỉnh theo mẫu
│   └── MSSV_HoTen.md                        # Bản sao báo cáo cá nhân
├── src/                                     # Mã nguồn pipeline tại root
└── starter/                                 # Khung starter gốc và mã nguồn hoàn thiện
    ├── src/                                 # Ingestion, chunking, embeddings, store, evaluation, run
    └── requirements.txt                     # Danh sách thư viện cần thiết
```
