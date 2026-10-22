# Agent 4: CV Tailor (Tailored CV Generator)

## Mục tiêu
Tái cấu trúc và viết lại CV nhắm trúng **một Job Description cụ thể** — tối ưu cho hệ thống lọc ATS (Applicant Tracking System), lồng ghép từ khóa trong JD một cách tự nhiên, và dùng bằng chứng code thực tế từ GitHub để thuyết phục nhà tuyển dụng. Không bịa đặt kinh nghiệm.

## Input
| Tên tham số | Kiểu | Mô tả |
|---|---|---|
| `profile` | `DeveloperProfile` | Hồ sơ đầy đủ từ Agent 1 (đã kiểm chứng qua GitHub) |
| `job_title` | `str` | Tên vị trí ứng tuyển |
| `jd_text` | `str` | Nội dung JD đầy đủ hoặc snippet |
| `original_cv_text` | `str` | Nội dung CV gốc (dùng để lấy thêm chi tiết như số năm, công ty cũ) |

## Output — `TailoredResume`
| Trường | Kiểu | Mô tả |
|---|---|---|
| `job_id` | `str` | ID job tương ứng |
| `resume_markdown` | `str` | CV hoàn chỉnh định dạng Markdown, cấu trúc quốc tế (Header, Summary, Skills, Experience/Projects, Education) |
| `added_keywords` | `List[str]` | Từ khóa lấy từ JD đã được lồng ghép vào CV |
| `tailored_highlights` | `List[str]` | Giải thích lý do chỉnh sửa giúp tăng cơ hội pass |

## CV Writing Principles
- **ATS-Friendly**: Từ khóa kỹ thuật trong JD xuất hiện tự nhiên ở Summary và Experience.
- **Google/XYZ Formula**: `"Accomplished [X] as measured by [Y], by doing [Z]"` — tập trung vào impact thay vì list công việc.
- **GitHub Evidence**: Dùng tên repo, tech stack, commit themes làm bằng chứng cụ thể.
- **No Fabrication**: Chỉ làm nổi bật những gì ứng viên đã thực sự làm, không thêm kinh nghiệm không có.

## File Output
- Markdown: `data/output/tailored_cv_{job_id}.md`
- (Tương lai) PDF: `data/output/tailored_cv_{job_id}.pdf`

## Kiểm tra Agent hoạt động đúng
- [ ] `resume_markdown` có đầy đủ 5 section: Header, Summary, Skills, Projects/Experience, Education
- [ ] `added_keywords` có ít nhất 3 từ khóa lấy từ JD
- [ ] Không chứa thông tin bịa đặt (kiểm tra cross-reference với `profile.core_skills`)
- [ ] File `.md` được ghi vào `data/output/` thành công
- [ ] CV đọc được và có cấu trúc rõ ràng (test bằng mắt hoặc markdown renderer)

