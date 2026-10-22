from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class VerifiedProject(BaseModel):
    name: str = Field(description="Tên repo/dự án")
    tech_stack: List[str] = Field(default_factory=list, description="Công nghệ sử dụng chính")
    highlights: str = Field(description="Điểm nổi bật, độ phức tạp hoặc giá trị của dự án")
    evidence: str = Field(description="Bằng chứng từ GitHub (commits, files, README)")

class DeveloperProfile(BaseModel):
    name: Optional[str] = Field(default="Ứng viên", description="Họ tên")
    target_roles: List[str] = Field(default_factory=list, description="Các vị trí phù hợp nhất")
    years_of_experience: Optional[str] = Field(default="N/A", description="Số năm kinh nghiệm ước tính")
    core_skills: List[str] = Field(default_factory=list, description="Kỹ năng lõi đã được kiểm chứng")
    verified_strengths: List[str] = Field(default_factory=list, description="Thế mạnh thực tế dựa trên code và CV")
    gaps_to_improve: List[str] = Field(default_factory=list, description="Điểm còn thiếu so với thị trường")
    projects: List[VerifiedProject] = Field(default_factory=list, description="Các dự án tiêu biểu")
    overall_summary: str = Field(description="Tóm tắt năng lực thực tế của ứng viên")

class JobListing(BaseModel):
    job_id: str
    title: str
    company: str
    location: str = "Vietnam"
    salary: Optional[str] = "Thoả thuận"
    jd_text: str
    url: str = ""
    posted_date: Optional[str] = ""
    company_warning: Optional[str] = Field(default="", description="Cảnh báo rủi ro về công ty (phốt, công ty ma, địa chỉ ảo)")
    company_reputation_score: Optional[int] = Field(default=100, description="Điểm uy tín công ty (0-100)")
    match_score: Optional[int] = 0
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    recommendation_reason: Optional[str] = ""

class TailoredResume(BaseModel):
    job_id: str
    resume_markdown: str
    added_keywords: List[str] = Field(default_factory=list)
    tailored_highlights: List[str] = Field(default_factory=list)

class InterviewKit(BaseModel):
    job_id: str
    technical_deep_dive: List[Dict[str, str]] = Field(default_factory=list, description="Câu hỏi đào sâu kỹ thuật từ code & CV kèm gợi ý trả lời")
    jd_specific_questions: List[Dict[str, str]] = Field(default_factory=list, description="Câu hỏi trực tiếp về yêu cầu trong JD")
    behavioral_questions: List[Dict[str, str]] = Field(default_factory=list, description="Câu hỏi tình huống theo STAR")
    questions_to_ask_interviewer: List[str] = Field(default_factory=list, description="Câu hỏi ngược lại cho nhà tuyển dụng")

