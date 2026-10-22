import os
import json
import warnings
warnings.filterwarnings("ignore")

import google.generativeai as genai
from dotenv import load_dotenv
from typing import List
from src.state import DeveloperProfile, JobListing

load_dotenv()

class JobMatcherAgent:
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Chưa thiết lập GEMINI_API_KEY!")
        
        chosen_model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=chosen_model,
            generation_config={"response_mime_type": "application/json"}
        )

    def match_and_rank(self, profile: DeveloperProfile, jobs: List[JobListing]) -> List[JobListing]:
        """
        So sánh hồ sơ ứng viên với danh sách các job để chấm điểm match_score và đưa ra phân tích.
        """
        if not jobs:
            return []

        jobs_data = [
            {"job_id": j.job_id, "title": j.title, "company": j.company, "snippet": j.jd_text, "url": j.url}
            for j in jobs
        ]

        prompt = f"""
Bạn là chuyên gia cố vấn tuyển dụng IT.
Nhiệm vụ: Hãy chấm điểm mức độ phù hợp (từ 0 đến 100 điểm) giữa Hồ sơ ứng viên và từng Công việc trong danh sách.

HỒ SƠ ỨNG VIÊN:
{profile.model_dump_json(indent=2)}

DANH SÁCH CÔNG VIỆC:
{json.dumps(jobs_data, ensure_ascii=False, indent=2)}

TIÊU CHÍ ĐÁNH GIÁ:
- match_score: Điểm từ 0 đến 100 (tính theo kỹ năng thực tế có khớp không, level có quá tầm hay dưới tầm không).
- pros: Điểm mạnh, lợi thế cạnh tranh của ứng viên với job này.
- cons: Kỹ năng còn thiếu hoặc điểm chưa khớp.
- recommendation_reason: Lời khuyên ngắn (vd: Nên nộp ngay, Tỷ lệ trúng cao, hoặc Chỉ nên nộp làm phương án phụ).

OUTPUT FORMAT:
Trả về JSON danh sách các job đã được chấm điểm:
[
  {{
    "job_id": "job_1",
    "match_score": 85,
    "pros": ["Khớp kỹ năng X", "Có repo chứng minh"],
    "cons": ["Thiếu Y"],
    "recommendation_reason": "Nên nộp ngay"
  }}
]
"""
        response = self.model.generate_content(prompt)
        scored_list = json.loads(response.text)

        # Merge scores back into JobListing objects
        score_map = {item["job_id"]: item for item in scored_list if "job_id" in item}
        
        for job in jobs:
            if job.job_id in score_map:
                s = score_map[job.job_id]
                job.match_score = s.get("match_score", 0)
                job.pros = s.get("pros", [])
                job.cons = s.get("cons", [])
                job.recommendation_reason = s.get("recommendation_reason", "")

        # Sắp xếp giảm dần theo điểm
        jobs.sort(key=lambda x: x.match_score or 0, reverse=True)
        return jobs

