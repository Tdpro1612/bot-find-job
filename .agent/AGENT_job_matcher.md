# Agent 3: Job Matcher & Scorer

## Mục tiêu
**Chấm điểm mức độ tương thích** (0–100%) giữa hồ sơ năng lực của ứng viên và từng tin tuyển dụng, giúp ứng viên ưu tiên nộp vào những job có xác suất pass cao nhất — thay vì nộp đại trà mà không có chiến lược.

## Input
| Tên tham số | Kiểu | Mô tả |
|---|---|---|
| `profile` | `DeveloperProfile` | Hồ sơ đã phân tích từ Agent 1 |
| `jobs` | `List[JobListing]` | Danh sách job thô từ Agent 2 |

## Output — `List[JobListing]` (đã được bổ sung điểm và phân tích)
Các trường bổ sung sau khi chạy Agent 3:

| Trường | Kiểu | Mô tả |
|---|---|---|
| `match_score` | `int` | Điểm 0–100, càng cao càng phù hợp |
| `pros` | `List[str]` | Điểm mạnh của ứng viên khớp với JD |
| `cons` | `List[str]` | Kỹ năng còn thiếu so với JD |
| `recommendation_reason` | `str` | Lời khuyên ngắn (vd: "Nên nộp ngay", "Phương án dự phòng") |

Danh sách được **sắp xếp giảm dần theo `match_score`**.

## Scoring Criteria (qua Prompt Gemini)
- **Kỹ năng kỹ thuật khớp**: So sánh `core_skills` của ứng viên với keywords trong JD.
- **Level phù hợp**: Không quá tầm (over-qualified) cũng không dưới tầm (under-qualified).
- **Bằng chứng GitHub**: Ưu tiên khi ứng viên có repo thực tế minh chứng cho yêu cầu JD.
- **Thiếu hụt**: Trừ điểm nếu JD đòi kỹ năng ứng viên chưa có bằng chứng.

## Kiểm tra Agent hoạt động đúng
- [ ] Mỗi `JobListing` trong output có `match_score` trong khoảng `[0, 100]`
- [ ] `pros` và `cons` không rỗng với mỗi job
- [ ] Danh sách output được sắp xếp giảm dần theo `match_score`
- [ ] Không crash khi `jobs` là list rỗng (trả về `[]`)
- [ ] `job_id` trong output khớp với `job_id` trong input (không bị nhầm job)

