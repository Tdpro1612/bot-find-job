# Agent 1: Profile Evaluator

## Mục tiêu
Đọc nội dung CV cũ + dữ liệu GitHub (ngôn ngữ lập trình, README, cấu trúc thư mục, commit messages) để tổng hợp **hồ sơ năng lực thực tế** của ứng viên — phân biệt rõ những gì ứng viên *thực sự có thể làm* (chứng minh bằng code) so với những gì chỉ được viết trên CV.

## Input
| Tên tham số | Kiểu | Mô tả |
|---|---|---|
| `cv_text` | `str` | Nội dung thuần text trích xuất từ file CV (PDF/TXT/MD) |
| `github_data` | `List[Dict]` | Danh sách repo tâm đắc do người dùng tick chọn (1–5 repos từ 10 repos gần nhất), mỗi item gồm: `name`, `languages`, `root_files`, `recent_commits`, `readme_preview` |

## Output — `DeveloperProfile` (Pydantic Model)
| Trường | Kiểu | Mô tả |
|---|---|---|
| `name` | `str` | Họ tên ứng viên |
| `target_roles` | `List[str]` | Các vị trí phù hợp nhất (vd: NLP Engineer, Data Engineer) |
| `years_of_experience` | `str` | Ước lượng số năm kinh nghiệm |
| `core_skills` | `List[str]` | Kỹ năng cốt lõi đã được kiểm chứng |
| `verified_strengths` | `List[str]` | Thế mạnh *có bằng chứng* từ GitHub/CV |
| `gaps_to_improve` | `List[str]` | Điểm yếu / lỗ hổng so với thị trường |
| `projects` | `List[VerifiedProject]` | Dự án tiêu biểu kèm tech stack và bằng chứng |
| `overall_summary` | `str` | Đoạn tóm tắt 3–4 câu sắc bén về năng lực |

## Prompt Strategy
- Yêu cầu Gemini đóng vai **Senior Tech Lead + Tech Recruiter** để đánh giá client-side bias (ứng viên tự khai) vs server-side evidence (code GitHub).
- Dùng JSON mode (`response_mime_type: application/json`) để đảm bảo output parse được.
- Model mặc định: `gemini-2.5-flash` (lấy từ env `GEMINI_MODEL`).

## Kiểm tra Agent hoạt động đúng
- [ ] `profile.name` không rỗng
- [ ] `profile.target_roles` có ít nhất 1 phần tử
- [ ] `profile.verified_strengths` có nội dung cụ thể, trích dẫn tên repo (không phải lời chung chung)
- [ ] `profile.gaps_to_improve` phản ánh thực tế thị trường (Cloud/MLOps/API...)
- [ ] Output parse được thành `DeveloperProfile` Pydantic model không lỗi

