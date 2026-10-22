import os
import json
import warnings
warnings.filterwarnings("ignore")

import google.generativeai as genai
from dotenv import load_dotenv
from src.state import DeveloperProfile, TailoredResume

load_dotenv()

class CVTailorAgent:
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

    def tailor(self, profile: DeveloperProfile, job_title: str, jd_text: str, original_cv_text: str = "") -> TailoredResume:
        """
        Tạo CV mới tối ưu hóa ATS và nhắm trúng các yêu cầu trong JD dựa trên kinh nghiệm thực tế.
        """
        prompt = f"""
Bạn là một chuyên gia viết CV (Professional Resume Writer & Career Coach) chuyên ngành IT/Tech.
Nhiệm vụ của bạn: Dựa trên thông tin ứng viên và bản mô tả công việc (JD), hãy tạo ra một bản CV ĐƯỢC ĐO NI ĐÓNG GIÀY (tailored) cho vị trí này.

TIÊU CHÍ QUAN TRỌNG:
1. Thân thiện với hệ thống lọc tự động (ATS-Friendly): Tự nhiên lồng ghép các từ khóa kỹ thuật có trong JD.
2. Dùng công thức STAR / Google XYZ ("Accomplished [X] as measured by [Y], by doing [Z]").
3. Khai thác tối đa các dự án thực tế trên GitHub của ứng viên để làm bằng chứng thuyết phục.
4. KHÔNG BỊA ĐẶT KINH NGHIỆM: Chỉ làm nổi bật các kỹ năng và dự án mà ứng viên thực sự có hoặc có nền tảng vững chắc.
5. Định dạng Markdown chuyên nghiệp, rõ ràng, sẵn sàng để convert sang PDF.

VỊ TRÍ ỨNG TUYỂN:
{job_title}

MÔ TẢ CÔNG VIỆC (JD):
{jd_text}

HỒ SƠ ỨNG VIÊN ĐÃ ĐƯỢC KIỂM CHỨNG (TỪ GITHUB & CV CŨ):
{profile.model_dump_json(indent=2)}

THÔNG TIN BỔ SUNG TỪ CV GỐC:
{original_cv_text[:2000]}

YÊU CẦU OUTPUT:
Trả về JSON đúng cấu trúc:
{{
  "job_id": "job_applied",
  "resume_markdown": "Nội dung CV hoàn chỉnh bằng Markdown, chuẩn cấu trúc quốc tế (Header, Summary, Skills, Work Experience/Projects, Education/Certifications)",
  "added_keywords": ["Từ khóa 1 lấy từ JD", "Từ khóa 2"],
  "tailored_highlights": ["Giải thích ngắn tại sao sửa như thế này giúp tăng cơ hội pass CV"]
}}
"""
        response = self.model.generate_content(prompt)
        data = json.loads(response.text)
        return TailoredResume(**data)

