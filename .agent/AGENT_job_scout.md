# Agent 2: Job Scout

## Mục tiêu
Tự động **tìm kiếm tin tuyển dụng IT miễn phí** từ các nguồn như ITviec, TopDev, VietnamWorks, LinkedIn Jobs thông qua DuckDuckGo Search — không cần API key trả phí.

## Input
| Tên tham số | Kiểu | Mô tả |
|---|---|---|
| `keywords` | `str` | Từ khóa tìm việc (vd: "NLP Engineer", "Python Data Engineer") |
| `location` | `str` | Địa điểm (vd: "Vietnam", "Da Nang", "Remote") |
| `limit` | `int` | Số lượng kết quả tối đa cần lấy (mặc định 10) |

## Output — `List[JobListing]`
| Trường | Kiểu | Mô tả |
|---|---|---|
| `job_id` | `str` | ID tự sinh (vd: `job_1`, `job_2`) |
| `title` | `str` | Tiêu đề job (trích từ title kết quả tìm kiếm) |
| `company` | `str` | Tên công ty (trích từ title nếu có dấu ` - `) |
| `location` | `str` | Địa điểm |
| `jd_text` | `str` | Snippet / mô tả ngắn từ kết quả tìm kiếm |
| `url` | `str` | Link gốc đến trang tuyển dụng |

## Search Strategy
Query được cấu trúc để ưu tiên các trang job IT Việt Nam:
```
(site:itviec.com OR site:topdev.vn OR site:vietnamworks.com OR site:linkedin.com/jobs) {keywords} {location}
```

> **Lưu ý**: Kết quả phụ thuộc vào trang web mục tiêu. Snippet JD thường ngắn (~150–300 ký tự). Agent 3 (Matcher) sẽ làm giàu thêm bằng AI scoring.

## Kiểm tra Agent hoạt động đúng
- [ ] Trả về `List[JobListing]` không lỗi khi mạng có thể kết nối
- [ ] Mỗi `JobListing` có `url` không rỗng trỏ đến nguồn tuyển dụng thật
- [ ] Khi không tìm thấy kết quả → trả về list rỗng `[]` (không crash)
- [ ] `job_id` là duy nhất trong batch
- [ ] Không bị lỗi khi location chứa ký tự tiếng Việt (vd: "Đà Nẵng")

