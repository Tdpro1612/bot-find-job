import os
import warnings
warnings.filterwarnings("ignore")
from typing import List, Dict, Any

# Hỗ trợ cả hai tên package: ddgs (mới) và duckduckgo_search (cũ)
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from src.state import JobListing

class JobScoutAgent:
    def __init__(self):
        self.ddgs = DDGS()

    def search_jobs(self, keywords: str, location: str = "Vietnam", limit: int = 10) -> List[JobListing]:
        """
        Tìm kiếm tin tuyển dụng từ các nguồn (ITviec, TopDev, LinkedIn, VietnamWorks) không tốn phí API.
        """
        query = f"(site:itviec.com OR site:topdev.vn OR site:vietnamworks.com OR site:linkedin.com/jobs) {keywords} {location}"
        
        results = []
        try:
            raw_results = list(self.ddgs.text(query, max_results=limit))
            for i, r in enumerate(raw_results):
                title = r.get("title", "Tuyển dụng")
                snippet = r.get("body", "")
                url = r.get("href", "")
                
                # Trích xuất công ty sơ bộ từ title nếu có format: Job Title - Company
                company = "N/A"
                if " - " in title:
                    parts = title.split(" - ")
                    company = parts[-1].strip()

                results.append(JobListing(
                    job_id=f"job_{i+1}",
                    title=title,
                    company=company,
                    location=location,
                    jd_text=snippet,
                    url=url
                ))
        except Exception as e:
            print(f"[JobScout] Lỗi khi tìm kiếm qua DuckDuckGo: {str(e)}")

        return results

