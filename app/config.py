"""全局配置 - 从环境变量或.env文件读取"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥
SECRET_KEY = os.getenv("SECRET_KEY", "please-change-this-to-a-random-string")

# 管理员初始账号
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "9800"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# 数据库
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'notifyhub.db'}")

# JWT
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "72"))

# 历史记录保留天数
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))

# 模板和静态文件路径
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 确保data目录存在
(BASE_DIR / "data").mkdir(exist_ok=True)