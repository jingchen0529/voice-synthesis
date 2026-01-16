"""初始化 Edge TTS 音色到数据库"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.edge_tts_service import sync_voices_to_db


def main():
    print("开始同步 Edge TTS 音色到数据库...")
    db = SessionLocal()
    try:
        count = sync_voices_to_db(db)
        print(f"成功导入 {count} 个新音色")
    except Exception as e:
        print(f"导入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
