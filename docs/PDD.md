# BOT-FIND-JOB — Project Design Document (PDD)

> *Phiên bản: 0.1.0 | Cập nhật: 2026-10-22 | Tác giả: Nguyen Khoa Nguyen*

---

## 1. TẦM NHÌN & MỤC TIÊU (Vision & Goals)

### 1.1 Vấn đề cần giải quyết

Người tìm việc trong ngành IT thường đối mặt với 4 vấn đề cốt lõi:

| # | Vấn đề | Hệ quả |
|---|---|---|
| 1 | **CV Generic** — dùng 1 CV nộp cho tất cả mọi nơi | Bị lọc bởi ATS trước khi HR đọc |
| 2 | **Tự đánh giá sai năng lực** — liệt kê kỹ năng không có bằng chứng thực tế | Không thuyết phục được NTD kỹ thuật |
| 3 | **Tìm job thủ công, tốn thời gian** — lướt từng trang, không có bộ lọc thông minh | Mất hàng giờ mà không ra kết quả tốt |
| 4 | **Vào phỏng vấn không chuẩn bị** — không biết trọng tâm của từng công ty | Trả lời chung chung, thiếu thuyết phục |

### 1.2 Giải pháp

**bot-find-job** là hệ thống **Multi-Agent AI** kết hợp phân tích năng lực thực tế (qua GitHub) với tự động hóa toàn bộ quy trình ứng tuyển — từ tìm job, may đo CV, đến luyện phỏng vấn.

### 1.3 Mục tiêu chính

- **MVP (v0.1)**: CLI chạy được end-to-end: CV → GitHub → Đề xuất Job → CV mới → Bộ Q&A.
- **v0.2**: Giao diện Streamlit, upload CV từ máy, JD paste trực tiếp.
- **v0.3**: Tự động crawl job định kỳ, email/Telegram alert khi có job phù hợp.

---

## 2. KIẾN TRÚC HỆ THỐNG (System Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│         CLI (run.py) ──── Streamlit UI (app.py)         │
└────────────────────────┬────────────────────────────────┘
                         │
            ┌────────────▼────────────┐
            │      ORCHESTRATOR       │
            │      (src/main.py)      │
            └──┬──────────────────┬───┘
               │                  │
    ┌──────────▼──┐          ┌────▼──────────┐
    │   TOOLS     │          │    AGENTS      │
    │             │          │                │
    │ pdf_parser  │◄────────►│ 1. Profile     │
    │ github_     │          │    Evaluator   │
    │   loader    │          │                │
    └─────────────┘          │ 2. Job Scout   │
                             │                │
    ┌─────────────┐          │ 3. Job Matcher │
    │   DATA I/O  │◄────────►│                │
    │             │          │ 4. CV Tailor   │
    │ data/input/ │          │                │
    │ data/output/│          │ 5. Interview   │
    └─────────────┘          │    Prep        │
                             └────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   GEMINI 2.5 FLASH   │
                          │   (Google AI Free)   │
                          └─────────────────────┘
```

---

## 3. CÁC AGENT VÀ LUỒNG DỮ LIỆU (Agent Pipeline)

### 3.1 Tổng quan luồng

```
CV File ──┐
          ├──► [Agent 1: Profile Evaluator] ──► DeveloperProfile (JSON)
GitHub ───┘                                            │
                                                       ▼
Search Criteria ──────────────────────► [Agent 2: Job Scout] ──► List[JobListing]
                                                       │
                                DeveloperProfile ──────┤
                                                       ▼
                                           [Agent 3: Job Matcher] ──► Ranked Jobs
                                                       │
                                         HUMAN IN THE LOOP: Chọn Job
                                                       │
                              ┌────────────────────────┤
                              │                        │
                              ▼                        ▼
                  [Agent 4: CV Tailor]    [Agent 5: Interview Prep]
                              │                        │
                              ▼                        ▼
                  tailored_cv_{id}.md    interview_kit_{id}.md
```

### 3.2 Chi tiết từng Agent

| Agent | File | Input | Output | LLM? |
|---|---|---|---|---|
| Profile Evaluator | `profile_evaluator.py` | CV text + GitHub repos | `DeveloperProfile` | ✅ Gemini |
| Job Scout | `job_scout.py` | keywords + location | `List[JobListing]` | ❌ DuckDuckGo |
| Job Matcher | `job_matcher.py` | Profile + Jobs | `List[JobListing]` có điểm | ✅ Gemini |
| CV Tailor | `cv_tailor.py` | Profile + JD + CV gốc | `TailoredResume` (Markdown) | ✅ Gemini |
| Interview Prep | `interview_prep.py` | Profile + JD | `InterviewKit` (Markdown) | ✅ Gemini |

---

## 4. DATA MODELS (Pydantic Schemas — `src/state.py`)

### `DeveloperProfile`
```python
name: str
target_roles: List[str]
years_of_experience: str
core_skills: List[str]
verified_strengths: List[str]   # Chứng minh bằng GitHub
gaps_to_improve: List[str]      # Thiếu hụt so với thị trường
projects: List[VerifiedProject]
overall_summary: str
```

### `JobListing`
```python
job_id: str
title: str
company: str
location: str
salary: Optional[str]
jd_text: str
url: str
match_score: Optional[int]      # Agent 3 điền vào
pros: List[str]                 # Agent 3 điền vào
cons: List[str]                 # Agent 3 điền vào
recommendation_reason: str      # Agent 3 điền vào
```

### `TailoredResume`
```python
job_id: str
resume_markdown: str
added_keywords: List[str]
tailored_highlights: List[str]
```

### `InterviewKit`
```python
job_id: str
technical_deep_dive: List[{question, suggested_answer}]
jd_specific_questions: List[{question, suggested_answer}]
behavioral_questions: List[{question, suggested_answer}]
questions_to_ask_interviewer: List[str]
```

---

## 5. CẤU TRÚC THƯ MỤC (Directory Structure)

```
bot-find-job/
├── run.py                          # Entry point chính (xử lý PYTHONPATH)
├── app.py                          # Streamlit UI (v0.2+)
├── requirements.txt                # Thư viện Python
├── .env                            # API Keys (KHÔNG commit lên Git)
├── .env.example                    # Mẫu .env để hướng dẫn
├── .gitignore
├── README.md                       # Hướng dẫn nhanh
│
├── docs/
│   └── PDD.md                      # File này — Project Design Document
│
├── src/
│   ├── __init__.py
│   ├── main.py                     # Orchestrator: điều phối 5 Agent
│   ├── state.py                    # Pydantic data models
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── profile_evaluator.py    # Agent 1
│   │   ├── job_scout.py            # Agent 2
│   │   ├── job_matcher.py          # Agent 3
│   │   ├── cv_tailor.py            # Agent 4
│   │   ├── interview_prep.py       # Agent 5
│   │   ├── AGENT_profile_evaluator.md
│   │   ├── AGENT_job_scout.md
│   │   ├── AGENT_job_matcher.md
│   │   ├── AGENT_cv_tailor.md
│   │   └── AGENT_interview_prep.md
│   │
│   └── tools/
│       ├── __init__.py
│       ├── github_loader.py        # Cào GitHub API
│       └── pdf_parser.py           # Đọc CV PDF/TXT/MD
│
└── data/
    ├── input/                      # Bỏ CV cũ vào đây
    └── output/                     # CV mới + bộ Q&A xuất ra đây
```

---

## 6. CÔNG NGHỆ SỬ DỤNG (Tech Stack)

| Thành phần | Công nghệ | Lý do chọn |
|---|---|---|
| Ngôn ngữ | Python 3.10+ | Hệ sinh thái AI/Data mạnh nhất |
| LLM | Gemini 2.5 Flash | **Miễn phí**, context window 1M token, đọc cả codebase |
| LLM Client | `google-generativeai` | Official SDK của Google |
| Data Validation | Pydantic v2 | Đảm bảo LLM output luôn có cấu trúc đúng |
| PDF Parser | `pdfplumber` | Trích xuất text chính xác từ CV PDF |
| Job Search | `ddgs` (DuckDuckGo) | **Miễn phí**, không cần API key |
| GitHub Data | GitHub REST API | Public, 60 req/h không cần token |
| CLI UI | `rich` | Terminal đẹp, có color và table |
| Web UI | Streamlit (v0.2+) | Nhanh nhất để build data app UI |
| Env Management | `python-dotenv` | Quản lý secrets an toàn |

---

## 7. LỘ TRÌNH PHÁT TRIỂN (Roadmap)

### ✅ v0.1 — MVP CLI (Hoàn thành)
- [x] Agent 1: Profile Evaluator (CV + GitHub)
- [x] Agent 2: Job Scout (DuckDuckGo)
- [x] Agent 3: Job Matcher & Scorer
- [x] Agent 4: CV Tailor (ATS-friendly Markdown)
- [x] Agent 5: Interview Prep Kit
- [x] CLI interface với `rich`
- [x] Agent documentation (AGENT_*.md)

### 🚧 v0.2 — Streamlit UI
- [ ] Upload CV từ máy tính (kéo-thả)
- [ ] Nhập GitHub username qua form
- [ ] Hiển thị danh sách job dạng thẻ bài có điểm màu
- [ ] Preview CV mới ngay trong UI
- [ ] Download CV (Markdown hoặc PDF)

### 📋 v0.3 — Tự động hóa & Mở rộng
- [ ] Scheduler: Tự động tìm job theo lịch (hàng ngày)
- [ ] Notification: Telegram bot alert khi có job phù hợp ≥ 80 điểm
- [ ] CV → PDF export (WeasyPrint / Typst)
- [ ] Multi-language JD support (tiếng Anh và tiếng Việt)
- [ ] Job application tracker (đã nộp, đang chờ, phỏng vấn, kết quả)

---

## 8. NGUYÊN TẮC THIẾT KẾ (Design Principles)

1. **Free First**: Mọi thành phần đều phải có phiên bản miễn phí hoạt động được. Không phụ thuộc vào dịch vụ trả phí bắt buộc.
2. **Evidence-Based**: Mọi đánh giá năng lực phải có bằng chứng cụ thể từ code (tên repo, commit, cấu trúc file). Không nhận xét chung chung.
3. **No Fabrication**: Agent 4 (CV Tailor) tuyệt đối không bịa đặt kinh nghiệm. Chỉ làm nổi bật sự thật.
4. **Human-in-the-Loop**: Người dùng luôn là người quyết định cuối cùng — chọn job, chọn apply, không auto-submit.
5. **Fast First**: Ưu tiên cho ra kết quả có thể dùng ngay (CV mới, bộ Q&A) trong vòng < 2 phút.

