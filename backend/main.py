import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import router as api_router
from app.core.config import settings

# 创建目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

app = FastAPI(
    title="Voice Synthesis API",
    description="语音合成、视频混剪等AI服务API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")

# 静态文件服务（用于访问上传的文件和生成的输出）
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/static/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")


@app.get("/", response_class=HTMLResponse)
async def index():
    """首页"""
    template_path = os.path.join(os.path.dirname(__file__), "templates/demo.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Voice Synthesis API</h1><p>访问 <a href='/docs'>/docs</a> 查看API文档</p>"


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
