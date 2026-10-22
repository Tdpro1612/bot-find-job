import os
import sys
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Load biến môi trường
load_dotenv()

from src.tools.pdf_parser import extract_text_from_file
from src.tools.github_loader import GitHubLoader
from src.agents.profile_evaluator import ProfileEvaluatorAgent
from src.agents.job_scout import JobScoutAgent
from src.agents.job_matcher import JobMatcherAgent
from src.agents.cv_tailor import CVTailorAgent
from src.agents.interview_prep import InterviewPrepAgent

console = Console()

def check_gemini_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        console.print("[bold red]Chưa tìm thấy GEMINI_API_KEY trong file .env![/bold red]")
        console.print("Bạn có thể lấy miễn phí tại: [blue]https://aistudio.google.com/app/apikey[/blue]")
        api_key = input("Nhập GEMINI_API_KEY của bạn vào đây: ").strip()
        if api_key:
            # Lưu vào .env
            env_path = Path(".env")
            with open(env_path, "a", encoding="utf-8") as f:
                f.write(f"\nGEMINI_API_KEY={api_key}\n")
            os.environ["GEMINI_API_KEY"] = api_key
            console.print("[green]Đã lưu GEMINI_API_KEY vào .env thành công![/green]")
        else:
            console.print("[bold red]Không có API key, thoát chương trình.[/bold red]")
            sys.exit(1)
    return api_key

def find_cv_file():
    input_dir = Path("data/input")
    input_dir.mkdir(parents=True, exist_ok=True)
    
    cv_files = [f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in [".pdf", ".docx", ".txt", ".md"]]
    if not cv_files:
        return None
    return cv_files[0]

def main():
    console.print(Panel.fit(
        "[bold cyan]BOT-FIND-JOB (Multi-Agent Job Hunter & Career Copilot)[/bold cyan]\n"
        "[dim]Hệ thống tự động phân tích CV + GitHub -> Tìm việc -> May đo CV -> Luyện phỏng vấn[/dim]",
        border_style="cyan"
    ))

    # 0. Kiểm tra API Key
    check_gemini_key()

    # 1. Tìm hoặc yêu cầu file CV
    cv_path = find_cv_file()
    if not cv_path:
        console.print("\n[yellow]Chưa thấy file CV trong thư mục `data/input/`![/yellow]")
        path_input = input("Nhập đường dẫn đến file CV của bạn (hoặc copy file vào data/input rồi bấm Enter): ").strip()
        if path_input and Path(path_input).exists():
            cv_path = Path(path_input)
        else:
            cv_path = find_cv_file()
            if not cv_path:
                console.print("[bold red]Vui lòng cung cấp file CV để tiếp tục.[/bold red]")
                sys.exit(1)

    console.print(f"[green]✓ Đã tìm thấy CV:[/green] {cv_path.name}")
    cv_text = extract_text_from_file(str(cv_path))

    # 2. Nhận diện GitHub Username (từ .env hoặc nhập tay)
    default_gh = os.getenv("GITHUB_USERNAME")
    if not default_gh:
        raw_token = os.getenv("GITHUB_TOKEN", "")
        if "github.com" in raw_token or "/" in raw_token:
            default_gh = GitHubLoader.extract_username(raw_token)

    prompt_gh = f"\nNhập GitHub username hoặc URL (Mặc định: '{default_gh}'): " if default_gh else "\nNhập GitHub username của bạn (ví dụ: Tdpro1612): "
    github_user = input(prompt_gh).strip() or default_gh

    if not github_user:
        console.print("[yellow]Bỏ qua phân tích GitHub, chỉ phân tích dựa trên CV.[/yellow]")
        github_data = []
    else:
        with console.status(f"[cyan]Đang cào dữ liệu và code từ GitHub ({github_user})...[/cyan]"):
            try:
                gh_loader = GitHubLoader()
                github_data = gh_loader.get_user_recent_repos(github_user, limit=4)
                console.print(f"[green]✓ Đã quét thành công {len(github_data)} repository gần nhất từ GitHub![/green]")
            except Exception as e:
                console.print(f"[red]Lỗi khi đọc GitHub: {e}. Sẽ tiếp tục chỉ với CV.[/red]")
                github_data = []

    # 3. Phân tích năng lực (Agent 1)
    profile_cache = Path("data/output/developer_profile.json")
    profile = None

    if profile_cache.exists():
        console.print(f"\n[green]💾 Tìm thấy hồ sơ năng lực đã lưu tại:[/green] {profile_cache}")
        use_saved = input("Bạn có muốn sử dụng lại hồ sơ này không? (y/n, Mặc định: y): ").strip().lower()
        if use_saved != "n":
            try:
                import json
                with open(profile_cache, "r", encoding="utf-8") as f:
                    profile = DeveloperProfile(**json.load(f))
                console.print("[green]✓ Đã tải hồ sơ năng lực thành công![/green]")
            except Exception as e:
                console.print(f"[yellow]Không đọc được file cache: {e}. Sẽ tiến hành phân tích lại.[/yellow]")
                profile = None

    if not profile:
        with console.status("[cyan]Agent 1 đang đánh giá năng lực thực tế từ CV và Code...[/cyan]"):
            evaluator = ProfileEvaluatorAgent()
            profile = evaluator.evaluate(cv_text, github_data)
            
            # Lưu lại file JSON
            profile_cache.parent.mkdir(parents=True, exist_ok=True)
            with open(profile_cache, "w", encoding="utf-8") as f:
                f.write(profile.model_dump_json(indent=2))
            console.print(f"[green]✓ Đã lưu hồ sơ năng lực vào {profile_cache}![/green]")

    console.print(Panel(
        f"[bold]Họ tên:[/bold] {profile.name} | [bold]Kinh nghiệm:[/bold] {profile.years_of_experience}\n"
        f"[bold]Vị trí mục tiêu:[/bold] {', '.join(profile.target_roles)}\n"
        f"[bold]Kỹ năng lõi:[/bold] {', '.join(profile.core_skills)}\n\n"
        f"[bold green]Thế mạnh đã được chứng minh qua code:[/bold green]\n" + 
        "\n".join([f"  • {s}" for s in profile.verified_strengths]) + "\n\n"
        f"[bold yellow]Điểm cần bổ sung/lưu ý:[/bold yellow]\n" + 
        "\n".join([f"  • {g}" for g in profile.gaps_to_improve]),
        title="[bold green]HỒ SƠ NĂNG LỰC ĐÃ ĐƯỢC XÁC THỰC[/bold green]",
        border_style="green"
    ))

    # 4. Tìm kiếm việc làm (Agent 2)
    roles_str = " OR ".join([f'"{r}"' for r in profile.target_roles]) if profile.target_roles else "Software Engineer"
    console.print(f"\n[cyan]Các vị trí từ Agent 1 đề xuất:[/cyan] {', '.join(profile.target_roles)}")
    search_role = input(f"Nhập từ khóa tìm việc (Mặc định kết hợp tất cả: {roles_str}): ").strip() or roles_str
    search_location = input("Nhập địa điểm (Mặc định: 'Vietnam' - có thể gõ 'Remote' hoặc 'Da Nang'): ").strip() or "Vietnam"
    remote_choice = input("Bạn có muốn tìm kiếm cả việc làm Remote quốc tế không? (y/n, Mặc định: y): ").strip().lower()
    allow_remote_cli = False if remote_choice == "n" else True

    with console.status(f"[cyan]Agent 2 đang săn tin tuyển dụng mới nhất (Remote: {allow_remote_cli}) và thẩm định rủi ro công ty...[/cyan]"):
        scout = JobScoutAgent()
        raw_jobs = scout.search_jobs(
            keywords=search_role,
            location=search_location,
            limit=8,
            timelimit="m",
            allow_remote=allow_remote_cli,
            check_reputation=True
        )

    if not raw_jobs:
        console.print("[yellow]Không tìm thấy job tự động. Bạn có thể tự dán JD bên dưới.[/yellow]")
    else:
        # 5. Chấm điểm & Xếp hạng (Agent 3)
        with console.status("[cyan]Agent 3 đang phân tích độ phù hợp của các Job...[/cyan]"):
            matcher = JobMatcherAgent()
            ranked_jobs = matcher.match_and_rank(profile, raw_jobs)

        # Hiển thị bảng việc làm
        table = Table(title=f"CÁC CƠ HỘI VIỆC LÀM PHÙ HỢP NHẤT ({search_role})", border_style="cyan")
        table.add_column("STT", style="bold yellow", width=4)
        table.add_column("Match %", style="bold green", width=8)
        table.add_column("Tiêu đề & Công ty", style="white")
        table.add_column("Cảnh báo / Đánh giá", style="yellow")
        table.add_column("Link", style="blue")

        for idx, j in enumerate(ranked_jobs, 1):
            match_str = f"{j.match_score}%" if j.match_score else "N/A"
            reasons = ""
            if j.company_warning:
                reasons = f"[bold red]⚠️ {j.company_warning}[/bold red]\n"
            reasons += j.recommendation_reason or (j.pros[0] if j.pros else "")
            table.add_row(str(idx), match_str, f"{j.title}\n[dim]{j.company}[/dim]", reasons, j.url)

        console.print(table)

    # 6. Lựa chọn Job để may đo CV & Luyện phỏng vấn
    console.print("\n[bold]BƯỚC TIẾP THEO:[/bold]")
    console.print("1. Chọn số thứ tự Job ở trên để apply")
    console.print("2. Hoặc nhập [bold cyan]'paste'[/bold cyan] để tự dán link/nội dung JD một công ty bạn đang nhắm tới")
    choice = input("Lựa chọn của bạn (vd: 1 hoặc paste): ").strip()

    selected_title = ""
    selected_jd = ""
    selected_id = "custom_job"

    if choice.isdigit() and 1 <= int(choice) <= len(ranked_jobs):
        target_job = ranked_jobs[int(choice) - 1]
        selected_title = target_job.title
        selected_jd = f"{target_job.title} at {target_job.company}\n{target_job.jd_text}\nLink: {target_job.url}"
        selected_id = f"job_{choice}"
    else:
        selected_title = input("Nhập tên vị trí (vd: Senior Python Developer): ").strip()
        console.print("Dán nội dung JD vào đây (Bấm Enter 2 lần khi xong):")
        lines = []
        while True:
            line = input()
            if not line and lines and not lines[-1]:
                break
            lines.append(line)
        selected_jd = "\n".join(lines).strip()

    if not selected_jd:
        selected_jd = selected_title

    # 7. May đo CV (Agent 4)
    with console.status(f"[cyan]Agent 4 đang tạo CV đo ni đóng giày cho '{selected_title}'...[/cyan]"):
        cv_tailor = CVTailorAgent()
        tailored_cv = cv_tailor.tailor(profile, selected_title, selected_jd, cv_text)

    # Lưu CV
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    cv_out_path = output_dir / f"tailored_cv_{selected_id}.md"
    with open(cv_out_path, "w", encoding="utf-8") as f:
        f.write(tailored_cv.resume_markdown)
    
    console.print(f"\n[bold green]✓ ĐÃ TẠO CV MỚI THÀNH CÔNG:[/bold green] [cyan]{cv_out_path}[/cyan]")
    console.print(f"[dim]Từ khóa đã tối ưu theo JD:[/dim] {', '.join(tailored_cv.added_keywords)}")

    # 8. Sinh bộ Q&A phỏng vấn (Agent 5)
    with console.status("[cyan]Agent 5 đang biên soạn bộ câu hỏi phỏng vấn thực chiến...[/cyan]"):
        interviewer = InterviewPrepAgent()
        kit = interviewer.generate_kit(profile, selected_title, selected_jd)

    qa_out_path = output_dir / f"interview_kit_{selected_id}.md"
    with open(qa_out_path, "w", encoding="utf-8") as f:
        f.write(f"# BỘ CÂU HỎI & KỊCH BẢN PHỎNG VẤN: {selected_title}\n\n")
        f.write("## 1. TECHNICAL DEEP DIVE (XOÁY THẲNG VÀO CODE CỦA BẠN)\n")
        for item in kit.technical_deep_dive:
            f.write(f"### Q: {item.get('question')}\n")
            f.write(f"**Gợi ý trả lời ghi điểm:**\n{item.get('suggested_answer')}\n\n")

        f.write("## 2. JD-SPECIFIC QUESTIONS (TRỌNG TÂM YÊU CẦU CÔNG VIỆC)\n")
        for item in kit.jd_specific_questions:
            f.write(f"### Q: {item.get('question')}\n")
            f.write(f"**Gợi ý:**\n{item.get('suggested_answer')}\n\n")

        f.write("## 3. BEHAVIORAL QUESTIONS (MÔ HÌNH STAR)\n")
        for item in kit.behavioral_questions:
            f.write(f"### Q: {item.get('question')}\n")
            f.write(f"**Kịch bản:**\n{item.get('suggested_answer')}\n\n")

        f.write("## 4. CÂU HỎI THÔNG MINH HỎI NGƯỢC LẠI INTERVIEWER\n")
        for q in kit.questions_to_ask_interviewer:
            f.write(f"- {q}\n")

    console.print(f"[bold green]✓ ĐÃ BIÊN SOẠN BỘ PHỎNG VẤN THỬ:[/bold green] [cyan]{qa_out_path}[/cyan]")
    console.print("\n[bold green]HOÀN TẤT! Bạn có thể xem ngay CV mới và bộ câu hỏi trong thư mục data/output/ để nộp đơn ngay hôm nay![/bold green]")

if __name__ == "__main__":
    main()
