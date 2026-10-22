import os
import json
import warnings
warnings.filterwarnings("ignore")

import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, List
from src.state import DeveloperProfile

load_dotenv()

class ProfileEvaluatorAgent:
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Chưa thiết lập GEMINI_API_KEY. Hãy điền vào file .env!")
        
        chosen_model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=chosen_model,
            generation_config={"response_mime_type": "application/json"}
        )

    def evaluate(self, cv_text: str, github_data: List[Dict[str, Any]]) -> DeveloperProfile:
        """
        Đánh giá toàn diện năng lực dựa trên CV và các repository GitHub được chọn.
        """
        prompt = f"""
Bạn là một chuyên gia tuyển dụng kỹ thuật (Tech Recruiter & Senior Tech Lead) hàng đầu.
Nhiệm vụ của bạn là đánh giá năng lực thực tế của lập trình viên bằng cách đối chiếu giữa:
1. CV cũ của ứng viên.
2. Dữ liệu thực tế từ các GitHub Repositories được ứng viên lựa chọn là tâm đắc/tiêu biểu nhất (ngôn ngữ, README, file cấu trúc, commit messages).

Mục tiêu:
- Tìm ra những thế mạnh ĐÃ ĐƯỢC CHỨNG MINH bằng code thực tế (đặc biệt nhấn mạnh các repo tiêu biểu mà ứng viên chọn).
- Phát hiện những lỗ hổng kỹ năng (gaps) mà thị trường tuyển dụng hiện nay hay đòi hỏi.
- Đề xuất các vị trí công việc (Target Roles) mà ứng viên có cơ hội trúng tuyển cao nhất.
- Trích xuất thông tin các dự án tiêu biểu từ GitHub để làm tư liệu trực tiếp may đo CV sau này.

DỮ LIỆU CV:
{cv_text}

DỮ LIỆU GITHUB REPOSITORIES TIÊU BIỂU ĐÃ CHỌN:
{json.dumps(github_data, ensure_ascii=False, indent=2)}

YÊU CẦU OUTPUT:
Hãy trả về một JSON duy nhất khớp chính xác với cấu trúc sau:
{{
  "name": "Họ và tên ứng viên",
  "target_roles": ["Vị trí 1", "Vị trí 2"],
  "years_of_experience": "Ước lượng số năm (vd: 2-3 năm, fresher, senior)",
  "core_skills": ["Skill 1", "Skill 2"],
  "verified_strengths": ["Thế mạnh 1 đã chứng minh qua repo X", "Thế mạnh 2"],
  "gaps_to_improve": ["Điểm yếu hoặc thiếu so với thị trường tuyển dụng"],
  "projects": [
    {{
      "name": "Tên repo",
      "tech_stack": ["Ngôn ngữ / Framework chính"],
      "highlights": "Điểm ấn tượng về kiến trúc, chức năng hoặc độ phức tạp",
      "evidence": "Bằng chứng cụ thể từ repo/commits"
    }}
  ],
  "overall_summary": "Tóm tắt ngắn gọn 3-4 câu sắc bén về năng lực thực tế để chuẩn bị nộp việc"
}}
"""
        response = self.model.generate_content(prompt)
        data = json.loads(response.text)
        return DeveloperProfile(**data)

