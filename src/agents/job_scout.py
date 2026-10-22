import os
import json
import re
import warnings
warnings.filterwarnings("ignore")
from typing import List, Dict, Any, Optional

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

import google.generativeai as genai
from dotenv import load_dotenv
from src.state import JobListing

load_dotenv()

# Danh sách từ khóa nước ngoài rõ rệt để loại bỏ khi tìm kiếm nội địa Việt Nam
OVERSEAS_INDICATORS = [
    "united states", "usa", "san francisco", "california", "new york", "london", "uk",
    "canada", "toronto", "germany", "berlin", "australia", "sydney", "singapore",
    "india", "bangalore", "tokyo", "japan", "france", "paris", "europe"
]

VIETNAM_MAJOR_CITIES = [
    "vietnam", "việt nam", "da nang", "đà nẵng", "hanoi", "hà nội", "ho chi minh",
    "hồ chí minh", "hcm", "saigon", "sài gòn", "can tho", "cần thơ", "hai phong", "hải phòng"
]

class JobScoutAgent:
    def __init__(self, api_key: str = None, model_name: str = None):
        self.ddgs = DDGS()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        chosen_model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=chosen_model,
                generation_config={"response_mime_type": "application/json"}
            )
        else:
            self.model = None

    def search_jobs(
        self,
        keywords: str,
        location: str = "Vietnam",
        limit: int = 15,
        timelimit: Optional[str] = "m",
        allow_remote: bool = True,
        check_reputation: bool = True
    ) -> List[JobListing]:
        """
        Tìm kiếm tin tuyển dụng MỚI NHẤT từ nhiều nguồn uy tín:
        - Tự động bóc tách và truy vấn song song cho từng Role để tối đa hóa số lượng kết quả (không bị nghẽn query).
        - Khi location là Vietnam: Bao quát cả các thành phố lớn (Hà Nội, TP.HCM, Đà Nẵng).
        - Giữ lại 100% các công ty (kể cả có rủi ro) và gắn cờ cảnh báo rõ ràng kèm lý do.
        """
        domestic_sites = [
            "site:topcv.vn", "site:itviec.com", "site:topdev.vn", "site:vietnamworks.com",
            "site:careerviet.vn", "site:glints.com/vn", "site:nodeflair.com",
            "site:vn.linkedin.com/jobs", "site:vieclam24h.vn"
        ]

        remote_sites = [
            "site:weworkremotely.com", "site:remoteok.com",
            "site:wellfound.com/jobs", "site:remotive.com", "site:himalayas.app/jobs"
        ]

        # 1. Chuẩn hóa danh sách từ khóa tìm kiếm (tách theo OR hoặc dấu phẩy)
        target_roles = self._parse_keywords_to_roles(keywords)
        clean_loc = location.strip() if location else "Vietnam"

        # Nếu location là Vietnam -> Cho phép nhận diện cả Hà Nội, Đà Nẵng, HCM...
        is_vietnam_scope = clean_loc.lower() in ["vietnam", "việt nam", "vn", "all"]

        site_list = domestic_sites + (remote_sites if allow_remote else [])
        site_filter = f"({' OR '.join(site_list[:6])})" # Giữ tối đa 6 domain chính để query gọn nhẹ

        raw_results = []
        seen_urls = set()

        # 2. Thực hiện tìm kiếm lần lượt cho từng role để thu được số lượng bài nhiều nhất
        per_role_limit = max(4, limit // max(1, len(target_roles)) + 3)

        for role in target_roles:
            if is_vietnam_scope:
                query = f"{site_filter} {role} Vietnam"
            else:
                query = f"{site_filter} {role} {clean_loc}"

            # Thử tìm với timelimit trước
            sub_raw = []
            if timelimit:
                try:
                    sub_raw = list(self.ddgs.text(query, timelimit=timelimit, max_results=per_role_limit))
                except Exception:
                    pass

            if not sub_raw:
                try:
                    sub_raw = list(self.ddgs.text(query, max_results=per_role_limit))
                except Exception:
                    sub_raw = []

            for r in sub_raw:
                href = r.get("href", "")
                if href and href not in seen_urls:
                    seen_urls.add(href)
                    raw_results.append(r)

            if len(raw_results) >= limit * 2:
                break

        # 3. Xử lý và lọc kết quả
        jobs = []
        for r in raw_results:
            title = r.get("title", "")
            snippet = r.get("body", "")
            url = r.get("href", "")

            if not title or not url:
                continue

            # Bỏ qua các trang chủ / trang landing page rỗng
            if self._is_generic_landing_page(url, title):
                continue

            # Nếu không cho phép remote: Kiểm tra không dính nước ngoài
            if not allow_remote:
                if not self._is_strictly_local(title, snippet, url, clean_loc):
                    continue

            # Xác định địa điểm cụ thể của job (Hà Nội, Đà Nẵng, TP.HCM...)
            detected_location = self._detect_job_city(title, snippet, clean_loc)

            # Trích xuất tên công ty
            company = self._extract_company(title, snippet)

            job = JobListing(
                job_id=f"job_{len(jobs)+1}",
                title=title,
                company=company,
                location=detected_location,
                jd_text=snippet,
                url=url,
                posted_date="Gần đây (tháng này)" if timelimit == "m" else "Mới cập nhật"
            )
            jobs.append(job)

            if len(jobs) >= limit:
                break

        # 4. Kiểm tra danh tiếng và cảnh báo công ty (GIỮ LẠI TẤT CẢ JOB, CHỈ GẮN CẢNH BÁO)
        if check_reputation and jobs:
            self.verify_companies(jobs)

        return jobs

    def _parse_keywords_to_roles(self, keywords: str) -> List[str]:
        """Tách chuỗi keywords dài thành các cụm role sạch sẽ (loại bỏ ngoặc kép, chú thích trong ngoặc)."""
        # Tách theo OR hoặc dấu phẩy
        parts = re.split(r'\s+OR\s+|,|;', keywords)
        clean_roles = []
        for p in parts:
            # Bỏ ngoặc đơn như (AI/ML Focus), bỏ quote
            cleaned = re.sub(r'\(.*?\)', '', p).replace('"', '').strip()
            if cleaned and len(cleaned) > 2 and cleaned not in clean_roles:
                clean_roles.append(cleaned)
        return clean_roles if clean_roles else [keywords]

    def _is_generic_landing_page(self, url: str, title: str) -> bool:
        """Kiểm tra xem link có phải là trang chủ đơn thuần không."""
        clean_url = url.rstrip("/")
        if clean_url in [
            "https://topcv.vn", "https://www.topcv.vn",
            "https://itviec.com", "https://www.itviec.com",
            "https://vietnamworks.com", "https://www.vietnamworks.com",
            "https://topdev.vn", "https://www.topdev.vn",
            "https://careerviet.vn", "https://www.careerviet.vn"
        ]:
            return True
        if title.lower().startswith("topcv - cv xịn việc làm chất") or title.lower().startswith("itviec | top it jobs"):
            return True
        return False

    def _is_strictly_local(self, title: str, snippet: str, url: str, required_location: str) -> bool:
        """Loại bỏ các job ở nước ngoài (Mỹ, Châu Âu, Singapore...)."""
        combined_text = f"{title} {snippet} {url}".lower()

        # Nếu có từ khóa nước ngoài rõ ràng mà không có đề cập Việt Nam
        for overseas in OVERSEAS_INDICATORS:
            if overseas in combined_text:
                has_vn = any(v in combined_text for v in VIETNAM_MAJOR_CITIES)
                if not has_vn:
                    return False
                if "linkedin.com/jobs/view" in url and "vn.linkedin.com" not in url:
                    return False

        # Nếu người dùng chọn đích danh 1 tỉnh/thành (ví dụ: Da Nang)
        req_norm = required_location.lower()
        if req_norm in ["da nang", "đà nẵng"]:
            if "đà nẵng" not in combined_text and "da nang" not in combined_text and "danang" not in combined_text:
                return False

        if req_norm in ["hanoi", "hà nội"]:
            if "hà nội" not in combined_text and "hanoi" not in combined_text:
                return False

        if req_norm in ["hcm", "hồ chí minh", "ho chi minh", "saigon", "sài gòn"]:
            if "hồ chí minh" not in combined_text and "ho chi minh" not in combined_text and "hcm" not in combined_text and "sài gòn" not in combined_text:
                return False

        return True

    def _detect_job_city(self, title: str, snippet: str, default_loc: str) -> str:
        """Phát hiện thành phố cụ thể của job để hiển thị rõ cho người dùng."""
        text = f"{title} {snippet}".lower()
        cities = []
        if "đà nẵng" in text or "da nang" in text or "danang" in text:
            cities.append("Đà Nẵng")
        if "hà nội" in text or "hanoi" in text:
            cities.append("Hà Nội")
        if "hồ chí minh" in text or "ho chi minh" in text or "hcm" in text or "sài gòn" in text:
            cities.append("TP. Hồ Chí Minh")
        if cities:
            return ", ".join(cities)
        return default_loc

    def _extract_company(self, title: str, snippet: str) -> str:
        """Trích xuất tên công ty sạch từ title."""
        company = "N/A"
        if " - " in title:
            parts = title.split(" - ")
            company = parts[-1].strip()
            for site in ["ITviec", "TopDev", "TopCV", "VietnamWorks", "CareerViet", "Glints", "LinkedIn", "Vieclam24h"]:
                if site.lower() in company.lower():
                    company = parts[-2].strip() if len(parts) >= 2 else "Công ty Tech"
        elif " tại " in title:
            company = title.split(" tại ")[-1].strip()
        return company

    def verify_companies(self, jobs: List[JobListing]):
        """
        Rà soát danh tiếng công ty: tìm kiếm thông tin phốt, review xấu, dấu hiệu công ty ma/lừa đảo.
        LƯU Ý: Không loại bỏ bất kỳ job nào, chỉ gắn cờ cảnh báo và điểm uy tín.
        """
        companies_to_check = set()
        for j in jobs:
            c = j.company.strip()
            if c and c not in ["N/A", "Công ty Tech"] and len(c) > 2:
                companies_to_check.add(c)

        for comp in companies_to_check:
            warning, score = self._check_single_company(comp)
            for j in jobs:
                if j.company.strip() == comp:
                    j.company_warning = warning
                    j.company_reputation_score = score

    def _check_single_company(self, company_name: str) -> (str, int):
        """Tìm kiếm review/phốt về công ty và dùng AI phân tích rủi ro."""
        try:
            search_query = f"{company_name} review công ty phốt lừa đảo"
            search_results = list(self.ddgs.text(search_query, max_results=3))
            
            if not search_results:
                return ("", 100)

            snippets = "\n".join([f"- {r.get('title')}: {r.get('body')}" for r in search_results])

            if not self.model:
                keywords_alert = ["phốt", "lừa đảo", "nợ lương", "quỵt tiền", "đa cấp", "công ty ma", "cảnh giác"]
                found_alerts = [k for k in keywords_alert if k in snippets.lower()]
                if found_alerts:
                    return (f"⚠️ Cảnh báo tìm thấy từ khóa tiêu cực ({', '.join(found_alerts)}) trên diễn đàn/mạng xã hội.", 50)
                return ("", 100)

            prompt = f"""
Bạn là chuyên gia thẩm định và bảo vệ quyền lợi người tìm việc.
Hãy phân tích các mẩu tin sau về công ty '{company_name}':

{snippets}

Mục tiêu kiểm tra:
1. Công ty có dấu hiệu lừa đảo, công ty ma (địa chỉ ảo, khai khống nhân sự, mới lập để tuyển lừa tiền), đa cấp, nợ lương, nợ bảo hiểm, phốt văn hóa tệ không?
2. Đưa ra điểm uy tín (0-100) và lời cảnh báo ngắn gọn nếu có rủi ro.

YÊU CẦU OUTPUT JSON:
{{
  "is_suspicious": true / false,
  "reputation_score": điểm từ 0 đến 100 (100 là hoàn toàn sạch/uy tín, dưới 60 là có vấn đề),
  "warning": "Cảnh báo ngắn gọn về rủi ro cho ứng viên (để trống nếu uy tín)"
}}
"""
            resp = self.model.generate_content(prompt)
            data = json.loads(resp.text)
            if data.get("is_suspicious") or data.get("reputation_score", 100) < 70:
                warning = data.get("warning") or "⚠️ Công ty có phản hồi tiêu cực trên mạng, hãy kiểm tra kỹ trước khi nhận việc."
                score = data.get("reputation_score", 60)
                return (warning, score)
            return ("", 100)

        except Exception:
            return ("", 100)
