"""
Streamlit UI cho Bot-Find-Job.
Chạy bằng lệnh: streamlit run app.py
"""
import sys
import os
import json
import warnings
import tempfile
warnings.filterwarnings("ignore")

# Fix Python path để import src.*
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bot-Find-Job 🤖",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar: Cấu hình ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Cấu hình")

    gemini_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Lấy miễn phí tại https://aistudio.google.com/app/apikey",
    )

    github_user = st.text_input(
        "GitHub Username hoặc URL",
        value=os.getenv("GITHUB_USERNAME", ""),
        placeholder="vd: Tdpro1612",
        help="Bot sẽ quét các repo gần nhất để đánh giá năng lực thực tế của bạn",
    )

    st.divider()
    st.markdown("### 🔗 Links hữu ích")
    st.markdown("- [Lấy Gemini Key miễn phí](https://aistudio.google.com/app/apikey)")
    st.markdown("- [Tạo GitHub Token](https://github.com/settings/tokens)")

# ── Main content ───────────────────────────────────────────────────────────────
st.title("🤖 Bot-Find-Job")
st.caption("Multi-Agent AI: Phân tích CV + GitHub → Tìm Job → May đo CV → Luyện phỏng vấn")

if not gemini_key:
    st.warning("⚠️ Hãy nhập Gemini API Key ở thanh bên trái để bắt đầu.")
    st.stop()

os.environ["GEMINI_API_KEY"] = gemini_key

# ── STEP 1: Upload CV ──────────────────────────────────────────────────────────
st.header("Bước 1 — Upload CV của bạn")

col1, col2 = st.columns([2, 1])
with col1:
    uploaded_file = st.file_uploader(
        "Kéo-thả hoặc chọn file CV",
        type=["pdf", "txt", "md"],
        help="Hỗ trợ PDF, TXT, Markdown",
    )

with col2:
    st.info(
        "**Gợi ý:**\nNếu đã để CV trong `data/input/`, "
        "có thể bỏ qua bước upload và bấm nút bên dưới."
    )
    use_existing = st.checkbox("Dùng CV đã có trong data/input/")

cv_text = ""
cv_source = ""

if uploaded_file is not None:
    # Lưu file upload tạm thời
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    from src.tools.pdf_parser import extract_text_from_file
    try:
        cv_text = extract_text_from_file(tmp_path)
        cv_source = uploaded_file.name
        st.success(f"✅ Đã đọc CV: **{uploaded_file.name}** ({len(cv_text):,} ký tự)")
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
    finally:
        os.unlink(tmp_path)

elif use_existing:
    from src.tools.pdf_parser import extract_text_from_file
    input_dir = Path("data/input")
    cv_files = [f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in [".pdf", ".txt", ".md"]]
    if cv_files:
        cv_path = cv_files[0]
        cv_text = extract_text_from_file(str(cv_path))
        cv_source = cv_path.name
        st.success(f"✅ Dùng CV có sẵn: **{cv_path.name}** ({len(cv_text):,} ký tự)")
    else:
        st.warning("Không tìm thấy CV trong `data/input/`. Hãy upload file.")

if cv_text:
    with st.expander("Xem nội dung CV vừa đọc được"):
        st.text(cv_text[:2000] + ("..." if len(cv_text) > 2000 else ""))

# ── STEP 2: Phân tích năng lực ─────────────────────────────────────────────────
st.header("Bước 2 — Hồ sơ năng lực (Developer Profile)")

if not cv_text:
    st.info("↑ Hãy upload CV trước để tiếp tục.")
    st.stop()

# Đảm bảo đường dẫn tuyệt đối chính xác
BASE_DIR = Path(__file__).resolve().parent
profile_cache_path = BASE_DIR / "data" / "output" / "developer_profile.json"

# Luôn thử nạp từ file JSON nếu session_state đang None hoặc chưa có
if "profile" not in st.session_state or st.session_state.profile is None:
    st.session_state.profile = None
    if profile_cache_path.exists():
        try:
            from src.state import DeveloperProfile
            with open(profile_cache_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                st.session_state.profile = DeveloperProfile(**saved_data)
        except Exception as e:
            st.warning(f"Không thể đọc file cache: {e}")

if "github_data" not in st.session_state:
    st.session_state.github_data = []
if "repo_summaries" not in st.session_state:
    st.session_state.repo_summaries = []
if "loaded_user" not in st.session_state:
    st.session_state.loaded_user = ""

# TH1: ĐÃ CÓ FILE DEVELOPER_PROFILE.JSON ĐÃ LƯU
if st.session_state.profile is not None:
    p = st.session_state.profile
    st.success(f"💾 **Đang sử dụng hồ sơ năng lực đã lưu** (`{profile_cache_path}`). Bạn có thể dùng ngay kết quả này để tìm việc ở Bước 3!")
    
    st.subheader(f"👤 {p.name} — {p.years_of_experience}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🎯 Vị trí phù hợp nhất:**")
        for role in p.target_roles:
            st.markdown(f"- **{role}**")
        st.markdown("**💪 Kỹ năng lõi:**")
        st.code(", ".join(p.core_skills))

    with col2:
        st.markdown("**✅ Thế mạnh đã chứng minh qua code:**")
        for s in p.verified_strengths[:4]:
            st.markdown(f"- {s}")
        st.markdown("**⚠️ Điểm cần bổ sung/lưu ý:**")
        for g in p.gaps_to_improve[:3]:
            st.markdown(f"- {g}")

    if p.projects:
        with st.expander(f"📁 Xem {len(p.projects)} dự án GitHub tiêu biểu đã được đưa vào hồ sơ"):
            for prj in p.projects:
                st.markdown(f"**🔹 {prj.name}** (`{', '.join(prj.tech_stack)}`)")
                st.caption(f"{prj.highlights}")

    st.info(f"📋 **Tóm tắt năng lực:** {p.overall_summary}")

    # Cho phép người dùng mở rộng nếu muốn quét lại từ đầu
    with st.expander("🔄 Bạn muốn quét lại GitHub & phân tích lại từ đầu? (Bấm để mở)"):
        clean_user = github_user.strip() if github_user else ""
        col_gh1, col_gh2 = st.columns([3, 1])
        with col_gh1:
            st.markdown(f"**Tài khoản GitHub:** `{clean_user or 'Chưa nhập'}`")
        with col_gh2:
            btn_fetch = st.button("🔄 Lấy 10 repo gần nhất", use_container_width=True)

        if btn_fetch or (clean_user and not st.session_state.repo_summaries and clean_user != st.session_state.loaded_user):
            from src.tools.github_loader import GitHubLoader
            if clean_user:
                with st.spinner(f"Đang tải 10 repo gần nhất của @{clean_user}..."):
                    try:
                        loader = GitHubLoader()
                        st.session_state.repo_summaries = loader.get_user_recent_repos_summary(clean_user, limit=10)
                        st.session_state.loaded_user = clean_user
                        st.success(f"✅ Đã tìm thấy {len(st.session_state.repo_summaries)} repo gần nhất!")
                    except Exception as e:
                        st.error(f"Lỗi tải GitHub: {e}")
                        st.session_state.repo_summaries = []

        selected_repo_names = []
        if st.session_state.repo_summaries:
            st.markdown("##### 📌 Chọn các repository tâm đắc (1-5 repo):")
            cols_grid = st.columns(2)
            for idx, repo in enumerate(st.session_state.repo_summaries):
                col_target = cols_grid[idx % 2]
                with col_target:
                    default_checked = idx < 3
                    repo_label = f"**{repo['name']}** ({repo['language']}) — ⭐ {repo['stars']}"
                    is_checked = st.checkbox(
                        repo_label,
                        value=default_checked,
                        key=f"re_repo_chk_{repo['name']}",
                        help=f"Mô tả: {repo['description']}\nCập nhật: {repo['updated_at']}"
                    )
                    st.caption(f"_{repo['description'][:80]}..._ [Xem repo]({repo['url']})")
                    if is_checked:
                        selected_repo_names.append(repo['name'])

        if st.button("🚀 Phân tích lại & Ghi đè file JSON", type="primary", use_container_width=True):
            from src.tools.github_loader import GitHubLoader
            from src.agents.profile_evaluator import ProfileEvaluatorAgent

            st.session_state.github_data = []
            if clean_user and selected_repo_names:
                with st.spinner(f"Đang đào sâu chi tiết {len(selected_repo_names)} repo..."):
                    try:
                        loader = GitHubLoader()
                        owner = loader.extract_username(clean_user)
                        st.session_state.github_data = loader.get_selected_repos_deep_dive(owner, selected_repo_names[:5])
                    except Exception as e:
                        st.warning(f"Lỗi đọc repo: {e}")

            with st.spinner("Gemini AI đang phân tích lại..."):
                try:
                    evaluator = ProfileEvaluatorAgent()
                    profile_obj = evaluator.evaluate(cv_text, st.session_state.github_data)
                    st.session_state.profile = profile_obj
                    with open(profile_cache_path, "w", encoding="utf-8") as f:
                        f.write(profile_obj.model_dump_json(indent=2))
                    st.success("✅ Đã cập nhật lại hồ sơ thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi Gemini: {e}")

# TH2: CHƯA CÓ FILE DEVELOPER_PROFILE.JSON (LẦN ĐẦU CHẠY)
else:
    st.info("Chưa có hồ sơ năng lực lưu sẵn. Vui lòng chọn các repo bên dưới và bấm phân tích để tạo hồ sơ lần đầu:")
    clean_user = github_user.strip() if github_user else ""

    col_gh1, col_gh2 = st.columns([3, 1])
    with col_gh1:
        st.markdown(f"**Tài khoản GitHub:** `{clean_user or 'Chưa nhập'}`")
    with col_gh2:
        btn_fetch = st.button("🔄 Lấy 10 repo gần nhất", use_container_width=True)

    if btn_fetch or (clean_user and not st.session_state.repo_summaries and clean_user != st.session_state.loaded_user):
        from src.tools.github_loader import GitHubLoader
        if clean_user:
            with st.spinner(f"Đang tải 10 repo gần nhất của @{clean_user}..."):
                try:
                    loader = GitHubLoader()
                    st.session_state.repo_summaries = loader.get_user_recent_repos_summary(clean_user, limit=10)
                    st.session_state.loaded_user = clean_user
                    st.success(f"✅ Đã tìm thấy {len(st.session_state.repo_summaries)} repo gần nhất!")
                except Exception as e:
                    st.error(f"Lỗi tải GitHub: {e}")
                    st.session_state.repo_summaries = []

    selected_repo_names = []
    if st.session_state.repo_summaries:
        st.markdown("##### 📌 Chọn các repository bạn tâm đắc nhất (tối đa 5 repo để đưa vào CV):")
        cols_grid = st.columns(2)
        for idx, repo in enumerate(st.session_state.repo_summaries):
            col_target = cols_grid[idx % 2]
            with col_target:
                default_checked = idx < 3
                repo_label = f"**{repo['name']}** ({repo['language']}) — ⭐ {repo['stars']}"
                is_checked = st.checkbox(
                    repo_label,
                    value=default_checked,
                    key=f"repo_chk_{repo['name']}",
                    help=f"Mô tả: {repo['description']}\nCập nhật: {repo['updated_at']}"
                )
                st.caption(f"_{repo['description'][:80]}..._ [Xem repo]({repo['url']})")
                if is_checked:
                    selected_repo_names.append(repo['name'])

    if st.button("🔍 Đánh giá năng lực thực tế (Agent 1)", type="primary", use_container_width=True):
        from src.tools.github_loader import GitHubLoader
        from src.agents.profile_evaluator import ProfileEvaluatorAgent

        st.session_state.github_data = []
        if clean_user and selected_repo_names:
            with st.spinner(f"Đang đào sâu chi tiết {len(selected_repo_names)} repo tâm đắc..."):
                try:
                    loader = GitHubLoader()
                    owner = loader.extract_username(clean_user)
                    st.session_state.github_data = loader.get_selected_repos_deep_dive(owner, selected_repo_names[:5])
                except Exception as e:
                    st.warning(f"Lỗi đọc repo: {e}")

        with st.spinner("Gemini AI đang phân tích đối chiếu CV + Code thực tế..."):
            try:
                evaluator = ProfileEvaluatorAgent()
                profile_obj = evaluator.evaluate(cv_text, st.session_state.github_data)
                st.session_state.profile = profile_obj

                # Tự động lưu ra file JSON để tái sử dụng
                profile_cache_path.parent.mkdir(parents=True, exist_ok=True)
                with open(profile_cache_path, "w", encoding="utf-8") as f:
                    f.write(profile_obj.model_dump_json(indent=2))

                st.success(f"✅ Đã phân tích xong và lưu kết quả vào `{profile_cache_path}`!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi Gemini: {e}")



# ── STEP 3: Tìm việc ──────────────────────────────────────────────────────────
st.header("Bước 3 — Tìm kiếm & Đề xuất Job")

if not st.session_state.profile:
    st.info("↑ Hoàn thành Bước 2 trước.")
    st.stop()

p = st.session_state.profile
available_roles = p.target_roles if p.target_roles else ["Software Engineer"]

col1, col2 = st.columns([3, 1])
with col1:
    # Cho phép chọn nhiều role từ kết quả của Agent 1 hoặc tự thêm từ khóa mới
    selected_roles = st.multiselect(
        "Vị trí mục tiêu (Đã lấy đầy đủ từ đánh giá của Agent 1):",
        options=available_roles,
        default=available_roles,
        help="Bot sẽ tìm kiếm các cơ hội việc làm kết hợp tất cả các vị trí bạn chọn."
    )
    custom_keywords = st.text_input(
        "Thêm từ khóa kỹ năng / chuyên sâu (tùy chọn):",
        placeholder="vd: LangChain, RAG, PyTorch, Multi-Agent"
    )
with col2:
    search_location = st.text_input("Địa điểm ưu tiên:", value="Vietnam", placeholder="vd: Da Nang, Remote, Vietnam")
    allow_remote_job = st.checkbox("🌐 Cho phép tìm job Remote (Kết hợp nền tảng quốc tế)", value=True, help="Nếu bật, bot sẽ tìm kiếm trên cả We Work Remotely, RemoteOK, Wellfound, Remotive, Himalayas. Nếu tắt, chỉ tìm Onsite/Hybrid tại địa điểm đã chọn.")
    timelimit_option = st.selectbox(
        "Độ mới của tin:",
        options=["m", "w", "d", ""],
        format_func=lambda x: {
            "m": "1 tháng qua (Tránh hết hạn)",
            "w": "1 tuần qua (Mới nhất)",
            "d": "24 giờ qua",
            "": "Tất cả thời gian"
        }.get(x, x),
        index=0
    )

# Ghép các keywords thành query hoàn chỉnh
search_keywords_list = list(selected_roles)
if custom_keywords.strip():
    search_keywords_list.append(custom_keywords.strip())
final_search_query = " OR ".join([f'"{r}"' for r in search_keywords_list]) if search_keywords_list else "IT Software Engineer"

num_jobs = st.slider("Số lượng job tìm tối đa:", 3, 10, 5)
check_company_risk = st.checkbox("🛡️ Tự động quét & cảnh báo rủi ro công ty (phốt, công ty ma, nợ lương, địa chỉ ảo)", value=True)

# Khu vực tìm job tự động HOẶC paste JD thủ công
tab_auto, tab_manual = st.tabs(["🔎 Tìm tự động (Đa nguồn)", "📋 Paste JD thủ công"])

if "ranked_jobs" not in st.session_state:
    st.session_state.ranked_jobs = []
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None

with tab_auto:
    if st.button("🚀 Tìm kiếm & Thẩm định Job", type="primary", use_container_width=True):
        from src.agents.job_scout import JobScoutAgent
        from src.agents.job_matcher import JobMatcherAgent

        remote_msg = " + Remote quốc tế" if allow_remote_job else " (Chỉ Onsite/Địa phương)"
        with st.spinner(f"Agent 2 đang săn tin tuyển dụng mới nhất ({timelimit_option or 'mọi lúc'}) từ các nguồn uy tín{remote_msg}..."):
            try:
                scout = JobScoutAgent()
                raw_jobs = scout.search_jobs(
                    keywords=final_search_query,
                    location=search_location,
                    limit=num_jobs,
                    timelimit=timelimit_option or None,
                    allow_remote=allow_remote_job,
                    check_reputation=check_company_risk
                )
                if raw_jobs:
                    st.success(f"✅ Tìm được {len(raw_jobs)} tin tuyển dụng mới và hợp lệ!")
                else:
                    st.warning("Chưa tìm thấy job mới trong khung thời gian này. Hãy thử chuyển sang 'Tất cả thời gian' hoặc tab 'Paste JD thủ công'.")
            except Exception as e:
                st.error(f"Lỗi tìm kiếm: {e}")
                raw_jobs = []

        if raw_jobs:
            with st.spinner("Agent 3 đang chấm điểm mức độ phù hợp và lợi thế cạnh tranh của bạn..."):
                try:
                    matcher = JobMatcherAgent()
                    st.session_state.ranked_jobs = matcher.match_and_rank(p, raw_jobs)
                except Exception as e:
                    st.error(f"Lỗi chấm điểm: {e}")
                    st.session_state.ranked_jobs = raw_jobs

    if st.session_state.ranked_jobs:
        st.subheader("📊 Danh sách Job phù hợp nhất (Đã rà soát rủi ro)")
        for i, job in enumerate(st.session_state.ranked_jobs):
            score = job.match_score or 0
            color = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            
            # Tiêu đề hiển thị có cảnh báo nếu công ty bị phốt
            warning_badge = " ⚠️ [CẢNH BÁO RỦI RO]" if job.company_warning else ""
            expander_title = f"{color} [{score}% Match]{warning_badge} {job.title} — {job.company}"
            
            with st.expander(expander_title):
                col1, col2 = st.columns([3, 1])
                with col1:
                    if job.company_warning:
                        st.error(f"🚨 **CẢNH BÁO THẨM ĐỊNH CÔNG TY:**\n{job.company_warning}")
                    
                    st.markdown(f"**Thời gian tin:** `{job.posted_date or 'Mới'}` | **Địa điểm:** `{job.location}`")
                    
                    if job.pros:
                        st.markdown("**✅ Điểm mạnh khớp JD:**")
                        for pro in job.pros:
                            st.markdown(f"  - {pro}")
                    if job.cons:
                        st.markdown("**⚠️ Còn thiếu:**")
                        for con in job.cons:
                            st.markdown(f"  - {con}")
                    if job.recommendation_reason:
                        st.info(f"💡 {job.recommendation_reason}")
                    if job.url:
                        st.markdown(f"🔗 [Xem tin tuyển dụng gốc]({job.url})")
                with col2:
                    if st.button(f"✏️ Chọn Job này", key=f"select_{i}"):
                        st.session_state.selected_job = job
                        st.rerun()

with tab_manual:
    st.markdown("Dán nội dung JD hoặc link tuyển dụng vào đây:")
    manual_title = st.text_input("Tên vị trí", placeholder="vd: Senior NLP Engineer")
    manual_jd = st.text_area("Nội dung JD / Link / Mô tả công việc", height=200,
                              placeholder="Dán toàn bộ nội dung JD vào đây...")

    if st.button("✅ Dùng JD này để tạo CV & bộ câu hỏi", use_container_width=True):
        if manual_jd.strip():
            from src.state import JobListing
            manual_job = JobListing(
                job_id="manual_job",
                title=manual_title or "Vị trí từ JD thủ công",
                company="Công ty từ JD",
                jd_text=manual_jd,
                url="",
                match_score=None,
            )
            st.session_state.selected_job = manual_job
            st.success("✅ Đã chọn JD thủ công, cuộn xuống Bước 4!")
        else:
            st.warning("Hãy nhập nội dung JD trước.")

# ── STEP 4: Tạo CV + Q&A ──────────────────────────────────────────────────────
st.header("Bước 4 — Tạo CV mới & Bộ câu hỏi phỏng vấn")

if not st.session_state.selected_job:
    st.info("↑ Chọn 1 job ở Bước 3 để tiếp tục.")
    st.stop()

job = st.session_state.selected_job
st.success(f"✅ Job đang chọn: **{job.title}** — {job.company}")

col1, col2 = st.columns(2)

if "tailored_cv" not in st.session_state:
    st.session_state.tailored_cv = None
if "interview_kit" not in st.session_state:
    st.session_state.interview_kit = None

with col1:
    if st.button("📄 Tạo CV mới sát JD", type="primary", use_container_width=True):
        from src.agents.cv_tailor import CVTailorAgent
        with st.spinner("Agent 4 đang viết CV đo ni đóng giày..."):
            try:
                tailor = CVTailorAgent()
                result = tailor.tailor(p, job.title, job.jd_text, cv_text)
                st.session_state.tailored_cv = result

                out_dir = Path("data/output")
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"tailored_cv_{job.job_id}.md"
                out_path.write_text(result.resume_markdown, encoding="utf-8")
                st.success(f"✅ Đã lưu: {out_path}")
            except Exception as e:
                st.error(f"Lỗi: {e}")

with col2:
    if st.button("🎤 Tạo bộ câu hỏi phỏng vấn", type="primary", use_container_width=True):
        from src.agents.interview_prep import InterviewPrepAgent
        with st.spinner("Agent 5 đang biên soạn bộ câu hỏi thực chiến..."):
            try:
                interviewer = InterviewPrepAgent()
                kit = st.session_state.interview_kit = interviewer.generate_kit(p, job.title, job.jd_text)

                out_dir = Path("data/output")
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"interview_kit_{job.job_id}.md"
                lines = [f"# BỘ CÂU HỎI PHỎNG VẤN: {job.title}\n",
                         "## 1. TECHNICAL DEEP DIVE\n"]
                for q in kit.technical_deep_dive:
                    lines += [f"### Q: {q.get('question')}\n", f"**Gợi ý:** {q.get('suggested_answer')}\n\n"]
                lines.append("## 2. JD-SPECIFIC QUESTIONS\n")
                for q in kit.jd_specific_questions:
                    lines += [f"### Q: {q.get('question')}\n", f"**Gợi ý:** {q.get('suggested_answer')}\n\n"]
                lines.append("## 3. BEHAVIORAL (STAR)\n")
                for q in kit.behavioral_questions:
                    lines += [f"### Q: {q.get('question')}\n", f"**Kịch bản:** {q.get('suggested_answer')}\n\n"]
                lines.append("## 4. HỎI NGƯỢC LẠI INTERVIEWER\n")
                for q in kit.questions_to_ask_interviewer:
                    lines.append(f"- {q}\n")
                out_path.write_text("".join(lines), encoding="utf-8")
                st.success(f"✅ Đã lưu: {out_path}")
            except Exception as e:
                st.error(f"Lỗi: {e}")

# Hiển thị kết quả CV mới
if st.session_state.tailored_cv:
    cv_result = st.session_state.tailored_cv
    st.subheader("📄 CV mới đã được tối ưu")
    if cv_result.added_keywords:
        st.markdown(f"**Từ khóa ATS đã thêm:** `{'` | `'.join(cv_result.added_keywords)}`")

    tab_preview, tab_raw = st.tabs(["👁️ Preview", "📝 Markdown raw"])
    with tab_preview:
        st.markdown(cv_result.resume_markdown)
    with tab_raw:
        st.code(cv_result.resume_markdown, language="markdown")

    st.download_button(
        label="⬇️ Tải CV (Markdown)",
        data=cv_result.resume_markdown,
        file_name=f"CV_{p.name.replace(' ', '_')}_{job.job_id}.md",
        mime="text/markdown",
        use_container_width=True,
    )

# Hiển thị bộ câu hỏi
if st.session_state.interview_kit:
    kit = st.session_state.interview_kit
    st.subheader("🎤 Bộ câu hỏi phỏng vấn thực chiến")

    tabs = st.tabs(["💻 Technical", "📋 JD-Specific", "⭐ Behavioral (STAR)", "🗣️ Hỏi ngược NTD"])

    with tabs[0]:
        for q in kit.technical_deep_dive:
            with st.expander(f"❓ {q.get('question', '')}"):
                st.markdown(f"**Gợi ý trả lời:**\n{q.get('suggested_answer', '')}")

    with tabs[1]:
        for q in kit.jd_specific_questions:
            with st.expander(f"❓ {q.get('question', '')}"):
                st.markdown(f"**Gợi ý:**\n{q.get('suggested_answer', '')}")

    with tabs[2]:
        for q in kit.behavioral_questions:
            with st.expander(f"❓ {q.get('question', '')}"):
                st.markdown(f"**Kịch bản STAR:**\n{q.get('suggested_answer', '')}")

    with tabs[3]:
        for q in kit.questions_to_ask_interviewer:
            st.markdown(f"- {q}")

