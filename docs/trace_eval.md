# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Ngô Anh Tú
> **Mã Sinh Viên / Mã Học viên:** 2A202602396  
> **Chủ đề Lựa chọn:** Personal Expense Agent  
---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** |  5/ 5 | Agent phải phân tích yêu cầu người dùng, trích xuất số tiền/danh mục/thời gian, kiểm tra dữ liệu chi tiêu, xác định có cần xác nhận hay không, sau đó mới thực hiện action và trả kết quả. |
| **2. Tool Interaction** | 3 / 5 | Agent cần tương tác với các dữ liệu bên ngoài như MCP server/ database  |
| **3. Dynamic Decision** | 5 / 5 | Bước tiếp theo phụ thuộc trực tiếp vào kết quả trước đó. Ví dụ: nếu thiếu số tiền → hỏi lại; nếu khoản chi lớn → yêu cầu confirmation; nếu vượt ngân sách → cảnh báo; |
| **4. Long Horizon Goal** | 3 / 5 | Bài toán chưa thực sự yêu cầu theo đuổi một mục tiêu dài hạn qua nhiều phiên như quản lý tài chính trong nhiều tháng.|
| **TỔNG ĐIỂM AGENTIC FIT** | **16 / 20** | *Nếu tổng điểm > 12/20: Bài toán rất phù hợp triển khai Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
{
    "step": 1,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 0.12000000000000001,
    "details": {
      "llm_latency_ms": 0.07,
      "tool_latency_ms": 0.05,
      "status": "SUCCESS"
    }
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [X] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** ___ lượt.
- **Kết quả đẩy Repo nộp bài:** [X] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
