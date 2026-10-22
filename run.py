"""
Entry point chính của Bot-Find-Job.
Chạy bằng lệnh: python run.py
"""
import sys
import os

# Tự động thêm thư mục gốc của project vào Python path
# để các import dạng 'from src.xxx import ...' hoạt động mà không cần export PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()

