# Agent 2: Job Scout

## Mục tiêu
Tự động **tìm kiếm tin tuyển dụng IT MỚI NHẤT (còn hạn nộp)**, phân loại linh hoạt giữa thị trường nội địa và thị trường Remote quốc tế, đồng thời **thẩm định pháp lý & danh tiếng công ty** để bảo vệ ứng viên trước các rủi ro tuyển dụng:

1. **Phân vùng nguồn tuyển dụng linh hoạt**:
   - **Nội địa & Tech Việt Nam**: ITviec, TopDev, VietnamWorks, CareerViet, Glints, NodeFlair, LinkedIn Jobs, Việc Làm 24h.
   - **Remote Quốc tế**: We Work Remotely, Remote OK, Wellfound (AngelList), Remotive, Himalayas.
   - *Quy tắc Remote*: Nếu người dùng **cho phép Remote (`allow_remote=True`)**, hệ thống sẽ kết hợp cả hai nhóm nguồn. Nếu người dùng **không cho phép (`allow_remote=False`)**, hệ thống loại bỏ hoàn toàn các nền tảng remote và lọc bớt các tin remote/làm việc từ xa để tập trung 100% vào việc Onsite/Hybrid tại địa phương đã chọn.

2. **Thẩm định uy tín & Phát hiện công ty có vấn đề**:
   - Tự động rà soát thông tin bóc phốt, nợ lương, nợ bảo hiểm, văn hóa độc hại, quỵt OT trên mạng xã hội và các diễn đàn đánh giá doanh nghiệp.
   - Phát hiện các dấu hiệu công ty ma, địa chỉ ảo (ví dụ: đăng ký trụ sở tại bãi đất trống, không có trụ sở thật), khai khống quy mô nhân sự bất thường dù mới thành lập ít ngày.

---

## Input
| Tên tham số | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `keywords` | `str` | Bắt buộc | Từ khóa vị trí (lấy đầy đủ từ các role do Agent 1 đề xuất hoặc tùy chỉnh) |
| `location` | `str` | `"Vietnam"` | Địa điểm làm việc mong muốn (vd: "Da Nang", "Hanoi", "Ho Chi Minh") |
| `limit` | `int` | `10` | Số lượng kết quả tối đa cần tìm kiếm |
| `timelimit` | `Optional[str]` | `'m'` | Bộ lọc thời gian: `'m'` (1 tháng qua - tránh hết hạn), `'w'` (1 tuần qua), `'d'` (24h qua) |
| `allow_remote` | `bool` | `True` | **Chế độ Remote**: `True` = Kết hợp các sàn Remote quốc tế; `False` = Bỏ qua toàn bộ sàn Remote, chỉ tìm việc Onsite/Hybrid tại địa phương |
| `check_reputation` | `bool` | `True` | Bật tính năng AI tự động rà soát phốt, nợ lương và công ty ma |

---

## Output — `List[JobListing]`
| Trường dữ liệu | Kiểu | Mô tả |
|---|---|---|
| `job_id` | `str` | ID định danh duy nhất (vd: `job_1`, `job_2`) |
| `title` | `str` | Tiêu đề tin tuyển dụng |
| `company` | `str` | Tên công ty tuyển dụng |
| `location` | `str` | Địa điểm làm việc |
| `jd_text` | `str` | Snippet / tóm tắt yêu cầu công việc |
| `url` | `str` | Đường dẫn trực tiếp đến bài đăng tuyển dụng gốc |
| `posted_date` | `str` | Nhãn thời gian đăng tin (đảm bảo tin còn mới) |
| `company_warning` | `str` | Nội dung cảnh báo rủi ro chi tiết (nếu phát hiện phốt, công ty ma, nợ lương) |
| `company_reputation_score` | `int` | Điểm uy tín công ty từ 0 đến 100 (dưới 70 là có vấn đề) |

---

## Search Strategy & Query Architecture

### Khi `allow_remote = True` (Bao gồm cả Remote):
Kết hợp cả 2 nhóm sàn tuyển dụng và truy vấn cả địa phương lẫn từ khóa Remote:
```text
(site:itviec.com OR site:topdev.vn OR site:topcv.vn OR site:vietnamworks.com OR site:careerviet.vn OR site:glints.com/vn OR site:nodeflair.com OR site:linkedin.com/jobs OR site:vieclam24h.vn OR site:weworkremotely.com OR site:remoteok.com OR site:wellfound.com/jobs OR site:remotive.com OR site:himalayas.app/jobs) {keywords} ({location} OR Remote) tuyển dụng
```

### Khi `allow_remote = False` (Chỉ Onsite / Hybrid tại địa phương):
Loại bỏ hoàn toàn các trang Remote quốc tế và thêm toán tử phủ định từ khóa remote:
```text
(site:itviec.com OR site:topdev.vn OR site:topcv.vn OR site:vietnamworks.com OR site:careerviet.vn OR site:glints.com/vn OR site:nodeflair.com OR site:linkedin.com/jobs OR site:vieclam24h.vn) {keywords} {location} tuyển dụng -remote -"làm việc từ xa"
```

---

## Tiêu chí Kiểm tra Agent hoạt động đúng (Checklist)
- [ ] Khi `allow_remote=True`: Kết quả tìm kiếm có thể xuất hiện các vị trí từ sàn remote quốc tế hoặc tin tuyển dụng remote.
- [ ] Khi `allow_remote=False`: Không xuất hiện tin từ `weworkremotely`, `remoteok`, `wellfound`, `remotive`, `himalayas`; tập trung vào vị trí địa phương.
- [ ] Bộ lọc `timelimit='m'` loại bỏ các tin cũ đã hết hạn nộp.
- [ ] Khi phát hiện công ty có lịch sử nợ lương, địa chỉ ma hoặc phốt bóc phốt nghiêm trọng, trường `company_warning` được gán nội dung cảnh báo chi tiết và `company_reputation_score` bị hạ thấp.
- [ ] Hệ thống hoạt động mượt mà không crash khi người dùng nhập tiếng Việt có dấu.
