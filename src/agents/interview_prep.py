import os
import json
import warnings
warnings.filterwarnings("ignore")

import google.generativeai as genai
from dotenv import load_dotenv
from src.state import DeveloperProfile, InterviewKit

load_dotenv()

class InterviewPrepAgent:
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

    def generate_kit(self, profile: DeveloperProfile, job_title: str, jd_text: str) -> InterviewKit:
        """
        Tạo bộ câu hỏi và đáp án phỏng vấn thử nghiệm sát với JD và code của ứng viên.
        """
        prompt = f"""
Bạn là một Technical Interviewer / Engineering Manager dày dạn kinh nghiệm.
Nhiệm vụ: Chuẩn bị một bộ câu hỏi và kịch bản phỏng vấn thực chiến cho ứng viên chuẩn bị thi tuyển vào vị trí dưới đây.

VỊ TRÍ:
{job_title}

JD YÊU CẦU:
{jd_text}

THÔNG TIN ỨNG VIÊN & CODE GITHUB:
{profile.model_dump_json(indent=2)}

YÊU CẦU CHI TIẾT:
1. `technical_deep_dive`: 4-5 câu hỏi kỹ thuật sâu xoáy thẳng vào các repo, tech stack thực tế của ứng viên. Kèm theo câu trả lời gợi ý (key talking points) để ứng viên ghi điểm.
2. `jd_specific_questions`: 3-4 câu hỏi trọng tâm nhà tuyển dụng chắc chắn sẽ hỏi dựa trên JD này.
3. `behavioral_questions`: 2-3 câu hỏi tình huống (xử lý xung đột, deadline gấp, debug sự cố production) theo mô hình STAR.
4. `questions_to_ask_interviewer`: 3 câu hỏi thông minh, thể hiện tư duy kiến trúc và sự chủ động để hỏi ngược lại NTD.

YÊU CẦU OUTPUT JSON:
{{
  "job_id": "job_applied",
  "technical_deep_dive": [
    {{"question": "Câu hỏi xoáy vào code/repo", "suggested_answer": "Gợi ý trả lời sắc bén"}}
  ],
  "jd_specific_questions": [
    {{"question": "Câu hỏi JD", "suggested_answer": "Gợi ý cách trả lời thể hiện kinh nghiệm"}}
  ],
  "behavioral_questions": [
    {{"question": "Câu hỏi tình huống", "suggested_answer": "Cách trả lời theo STAR (Situation, Task, Action, Result)"}}
  ],
  "questions_to_ask_interviewer": [
    "Câu hỏi 1 cho interviewer", "Câu hỏi 2"
  ]
}}
"""
        response = self.model.generate_content(prompt)
        data = json.loads(response.text)
        return InterviewKit(**data)

