import os
import requests
from typing import Dict, Any, List, Optional
import base64

class GitHubLoader:
    def __init__(self, token: Optional[str] = None):
        raw_token = token or os.getenv("GITHUB_TOKEN", "")
        # Nếu người dùng vô tình điền link github hoặc username vào GITHUB_TOKEN thì không dùng làm token xác thực
        if raw_token and not raw_token.startswith("http") and not raw_token.startswith("github.com"):
            self.token = raw_token.strip()
        else:
            self.token = None

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Bot-Find-Job-Assistant"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    @staticmethod
    def extract_username(input_str: str) -> str:
        """
        Trích xuất username từ chuỗi nhập vào hoặc URL GitHub.
        Ví dụ: 'https://github.com/Tdpro1612' -> 'Tdpro1612'
        """
        clean = input_str.strip().rstrip("/")
        if "/" in clean:
            return clean.split("/")[-1]
        return clean

    def get_user_recent_repos(self, username_or_url: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các repo được cập nhật/push gần nhất của user.
        """
        username = self.extract_username(username_or_url)
        url = f"https://api.github.com/users/{username}/repos?sort=pushed&direction=desc&per_page={limit * 2}"
        resp = requests.get(url, headers=self.headers, timeout=15)
        if resp.status_code == 404:
            raise ValueError(f"Không tìm thấy GitHub user: {username}")
        if resp.status_code == 403:
            raise PermissionError("Bị chạm giới hạn Rate Limit của GitHub API. Hãy thêm GITHUB_TOKEN vào .env")
        resp.raise_for_status()

        repos = resp.json()
        # Ưu tiên repo chính chủ (không phải fork) trước
        own_repos = [r for r in repos if not r.get("fork")]
        selected = own_repos[:limit] if own_repos else repos[:limit]

        detailed_repos = []
        for r in selected:
            repo_name = r["name"]
            owner = r["owner"]["login"]
            detail = self.get_repo_deep_dive(owner, repo_name)
            detailed_repos.append(detail)

        return detailed_repos

    def get_repo_deep_dive(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """
        Đào sâu thông tin repo: Languages, README, cấu trúc thư mục, recent commits.
        """
        base_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        
        # 1. Thống kê ngôn ngữ
        lang_resp = requests.get(f"{base_url}/languages", headers=self.headers, timeout=10)
        languages = lang_resp.json() if lang_resp.status_code == 200 else {}

        # 2. Lấy README
        readme_content = ""
        readme_resp = requests.get(f"{base_url}/readme", headers=self.headers, timeout=10)
        if readme_resp.status_code == 200:
            data = readme_resp.json()
            if data.get("content"):
                try:
                    readme_content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")[:3000] # Giới hạn 3000 ký tự đầu
                except Exception:
                    readme_content = ""

        # 3. Lấy cấu trúc file ở root (để xem có Docker, Test, CI/CD không)
        contents_resp = requests.get(f"{base_url}/contents", headers=self.headers, timeout=10)
        root_files = []
        if contents_resp.status_code == 200:
            root_files = [item["name"] for item in contents_resp.json() if "name" in item]

        # 4. Lấy 5 commits gần nhất
        commits_resp = requests.get(f"{base_url}/commits?per_page=5", headers=self.headers, timeout=10)
        recent_commits = []
        if commits_resp.status_code == 200:
            for c in commits_resp.json():
                msg = c.get("commit", {}).get("message", "").split("\n")[0]
                recent_commits.append(msg)

        return {
            "name": repo_name,
            "url": f"https://github.com/{owner}/{repo_name}",
            "description": readme_resp.json().get("description") if readme_resp.status_code == 200 else "",
            "languages": languages,
            "root_files": root_files,
            "recent_commits": recent_commits,
            "readme_preview": readme_content
        }

