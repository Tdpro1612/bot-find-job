# Agent 5: Interview Prep (Mock Interview & Q&A Kit Generator)

## Mục tiêu
Chuẩn bị cho ứng viên **bộ câu hỏi phỏng vấn thực chiến** sát với cả JD lẫn kinh nghiệm cụ thể từ GitHub — bao gồm gợi ý đáp án, câu hỏi tình huống (STAR), và câu hỏi thông minh để hỏi ngược lại nhà tuyển dụng. Mục tiêu là ứng viên bước vào phòng phỏng vấn đã ôn đúng trọng tâm.

## Input
| Tên tham số | Kiểu | Mô tả |
|---|---|---|
| `profile` | `DeveloperProfile` | Hồ sơ từ Agent 1 (kèm dự án, kỹ năng, thế mạnh thực tế) |
| `job_title` | `str` | Tên vị trí ứng tuyển |
| `jd_text` | `str` | Nội dung JD |

## Output — `InterviewKit`
| Trường | Kiểu | Mô tả |
|---|---|---|
| `technical_deep_dive` | `List[{question, suggested_answer}]` | 4–5 câu hỏi kỹ thuật xoáy vào code/repo cụ thể của ứng viên |
| `jd_specific_questions` | `List[{question, suggested_answer}]` | 3–4 câu hỏi trực tiếp từ yêu cầu JD |
| `behavioral_questions` | `List[{question, suggested_answer}]` | 2–3 câu tình huống theo mô hình STAR |
| `questions_to_ask_interviewer` | `List[str]` | 3 câu hỏi thông minh để hỏi ngược lại NTD |

## Câu hỏi Technical Deep Dive — Design Intent
Các câu hỏi phải **xoáy cụ thể vào repo/commit** của ứng viên, ví dụ:
> *"Trong repo `data-material-plants`, bạn sử dụng kiến trúc multi-agent — tại sao chọn thiết kế này thay vì monolithic pipeline? Nếu cần scale lên 10x data volume thì bottleneck ở đâu?"*

Không được hỏi chung chung như *"Bạn có kinh nghiệm về Python không?"*

## File Output
- Markdown: `data/output/interview_kit_{job_id}.md`

## Kiểm tra Agent hoạt động đúng
- [ ] `technical_deep_dive` có ít nhất 1 câu hỏi trích dẫn tên repo cụ thể của ứng viên
- [ ] `jd_specific_questions` liên quan trực tiếp đến JD (không phải câu hỏi chung chung)
- [ ] `behavioral_questions` tuân theo cấu trúc STAR (Situation, Task, Action, Result)
- [ ] `questions_to_ask_interviewer` thể hiện tư duy kiến trúc, không hỏi về lương/benefit
- [ ] File `.md` được ghi vào `data/output/` thành công và đọc được

