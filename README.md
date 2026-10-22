# 🎯 BOT-FIND-JOB

> **Multi-Agent AI Career Copilot**  
> Hệ thống hỗ trợ tìm việc thực chiến: Tự động đánh giá CV cũ + GitHub Repositories → Tìm kiếm việc làm → May đo CV chuẩn ATS theo JD → Sinh bộ câu hỏi phỏng vấn thực chiến.

---

## ⚡ Tính năng chính

- **Agent 1 (Profile Evaluator)**: Phân tích CV và quét code trên GitHub (ngôn ngữ, commit, README, file structure) để đánh giá năng lực thực tế được chứng minh.
- **Agent 2 (Job Scout)**: Tự động tìm tin tuyển dụng IT (ITviec, TopDev, VietnamWorks, LinkedIn) qua DuckDuckGo (hoàn toàn miễn phí).
- **Agent 3 (Job Matcher)**: Chấm điểm độ tương thích (Match Score 0–100%) giữa profile của bạn và từng tin tuyển dụng.
- **Agent 4 (CV Tailor)**: Viết lại CV mới chuẩn ATS theo từng JD cụ thể, lồng ghép từ khóa và số liệu từ code thật (không bịa đặt).
- **Agent 5 (Interview Prep)**: Sinh bộ Q&A phỏng vấn: Technical Deep Dive xoáy thẳng vào repository của bạn, câu hỏi sát JD, tình huống STAR, và câu hỏi ngược cho nhà tuyển dụng.

---

## 🚀 Hướng dẫn cài đặt & Chạy

### 1. Chuẩn bị môi trường & API Key

Hệ thống sử dụng **Google Gemini 2.5 Flash** (hoàn toàn miễn phí):
1. Lấy API key miễn phí tại: [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Cấu hình file `.env` (đã có sẵn hoặc copy từ `.env.example`):
```bash
cp .env.example .env
```
Nội dung file `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=
```
*(Lưu ý: `GITHUB_TOKEN` để trống nếu chỉ quét public repo).*

3. Cài đặt thư viện (nếu chưa cài):
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

---

### 2. Cách 1: Chạy Giao diện Web (Streamlit UI - Khuyên dùng)

Giao diện trực quan, hỗ trợ kéo-thả upload file CV, paste JD, preview và tải CV:

```bash
./venv/bin/streamlit run app.py
```
*(Hoặc nếu đã activate venv: `streamlit run app.py`)*

👉 Mở trình duyệt tại: **`http://localhost:8501`**

---

### 3. Cách 2: Chạy Giao diện dòng lệnh (CLI)

Chạy trực tiếp qua terminal bằng file `run.py`:

```bash
./venv/bin/python run.py
```
*(Hoặc nếu đã activate venv: `python run.py`)*

- Đặt file CV cũ vào thư mục: `data/input/` (hỗ trợ `.pdf`, `.docx`, `.txt`, `.md`).
- Kết quả CV mới và bộ câu hỏi sẽ xuất ra tại: `data/output/`.

---

## 📂 Cấu trúc Repository

```text
bot-find-job/
├── app.py                      # Giao diện Streamlit UI
├── run.py                      # Entry point chạy CLI
├── requirements.txt            # Danh sách thư viện Python
├── .env                        # Chứa API key và cấu hình cá nhân
├── .agent/                     # Đặc tả & checklist kiểm thử từng Agent
│   ├── AGENT_profile_evaluator.md
│   ├── AGENT_job_scout.md
│   ├── AGENT_job_matcher.md
│   ├── AGENT_cv_tailor.md
│   └── AGENT_interview_prep.md
├── docs/
│   └── PDD.md                  # Project Design Document (tài liệu thiết kế chi tiết)
├── data/
│   ├── input/                  # Chứa file CV gốc
│   └── output/                 # Chứa CV mới (.md) và bộ Q&A phỏng vấn
└── src/
    ├── state.py                # Pydantic data schemas
    ├── main.py                 # Điều phối pipeline CLI
    ├── agents/                 # Mã nguồn các Agent
    │   ├── profile_evaluator.py
    │   ├── job_scout.py
    │   ├── job_matcher.py
    │   ├── cv_tailor.py
    │   └── interview_prep.py
    └── tools/                  # Công cụ bổ trợ
        ├── github_loader.py    # Quét dữ liệu từ GitHub
        └── pdf_parser.py       # Trích xuất văn bản từ PDF
```
