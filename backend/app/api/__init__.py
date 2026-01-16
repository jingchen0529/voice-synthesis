from fastapi import APIRouter
from app.api import auth, tts, video, openapi, lead

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(tts.router, prefix="/tts", tags=["语音合成"])
router.include_router(video.router, prefix="/video", tags=["视频混剪"])
router.include_router(openapi.router, prefix="/open", tags=["开放API"])
router.include_router(lead.router, prefix="/lead", tags=["获客线索"])
