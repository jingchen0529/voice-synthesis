"""Edge TTS 服务"""
import os
import asyncio
import json
import edge_tts
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import EdgeTtsVoice
from app.core.config import settings


async def get_all_voices() -> List[Dict]:
    """从 edge-tts 获取所有可用音色"""
    voices = await edge_tts.list_voices()
    return voices


def _format_voice_personalities(voice_tag) -> str:
    """将 VoicePersonalities 列表转换为逗号分隔的字符串"""
    if not isinstance(voice_tag, dict):
        return ""
    personalities = voice_tag.get("VoicePersonalities", [])
    if isinstance(personalities, list):
        return ", ".join(personalities)
    return str(personalities) if personalities else ""


def sync_voices_to_db(db: Session) -> int:
    """同步 edge-tts 音色到数据库"""
    voices = asyncio.run(get_all_voices())
    count = 0
    
    for voice in voices:
        short_name = voice.get("ShortName", "")
        existing = db.query(EdgeTtsVoice).filter(EdgeTtsVoice.short_name == short_name).first()
        
        if not existing:
            # 提取显示名称（从 LocalName 或 ShortName 解析）
            local_name = voice.get("LocalName", "")
            display_name = local_name if local_name else short_name.split("-")[-1].replace("Neural", "")
            
            new_voice = EdgeTtsVoice(
                short_name=short_name,
                name=voice.get("Name", short_name),
                locale=voice.get("Locale", ""),
                language=voice.get("Locale", "").split("-")[0] if voice.get("Locale") else "",
                gender=voice.get("Gender", ""),
                display_name=display_name,
                voice_type=_format_voice_personalities(voice.get("VoiceTag")),
                status=1,
                # 中文音色排序靠前
                sort_order=0 if voice.get("Locale", "").startswith("zh") else 100
            )
            db.add(new_voice)
            count += 1
    
    db.commit()
    return count


def get_voices_from_db(
    db: Session,
    locale: Optional[str] = None,
    gender: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict]:
    """从数据库获取音色列表"""
    query = db.query(EdgeTtsVoice).filter(EdgeTtsVoice.status == 1)
    
    if locale:
        query = query.filter(EdgeTtsVoice.locale.like(f"{locale}%"))
    
    if gender:
        query = query.filter(EdgeTtsVoice.gender == gender)
    
    if search:
        query = query.filter(
            (EdgeTtsVoice.display_name.like(f"%{search}%")) |
            (EdgeTtsVoice.short_name.like(f"%{search}%"))
        )
    
    voices = query.order_by(EdgeTtsVoice.sort_order, EdgeTtsVoice.locale, EdgeTtsVoice.short_name).all()
    
    return [
        {
            "id": v.id,
            "short_name": v.short_name,
            "display_name": v.display_name,
            "locale": v.locale,
            "gender": v.gender,
            "label": f"{v.display_name} ({v.locale}, {v.gender})"
        }
        for v in voices
    ]


def get_locales_from_db(db: Session) -> List[Dict]:
    """获取所有可用的语言区域"""
    from sqlalchemy import distinct
    
    # 直接从数据库获取 locale 和对应的语言名称
    locales = db.query(
        EdgeTtsVoice.locale,
        EdgeTtsVoice.locale_name
    ).filter(EdgeTtsVoice.status == 1).distinct().all()
    
    result = []
    for locale, locale_name in locales:
        result.append({
            "value": locale,
            "label": locale_name or locale
        })
    
    # 中文优先排序
    result.sort(key=lambda x: (0 if x["value"].startswith("zh") else 1, x["value"]))
    
    return result


async def generate_audio(
    text: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
    output_path: Optional[str] = None
) -> str:
    """
    使用 edge-tts 生成语音
    
    Args:
        text: 要转换的文本
        voice: 音色名称
        rate: 语速，如 "+20%", "-10%", "+0%"
        volume: 音量，如 "+20%", "-10%", "+0%"
        pitch: 音调，如 "+10Hz", "-10Hz", "+0Hz"
        output_path: 输出路径，不指定则自动生成
    
    Returns:
        生成的音频文件路径
    """
    if not output_path:
        import uuid
        os.makedirs(f"{settings.OUTPUT_DIR}/tts", exist_ok=True)
        output_path = f"{settings.OUTPUT_DIR}/tts/{uuid.uuid4()}.mp3"
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
    await communicate.save(output_path)
    
    return output_path


async def generate_audio_with_subtitles(
    text: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
    output_path: Optional[str] = None
) -> Tuple[str, List[Dict]]:
    """
    使用 edge-tts 生成语音并获取字幕时间戳
    
    Returns:
        (音频文件路径, 字幕列表)
        字幕列表格式: [{"text": "你好", "start": 0.0, "end": 0.5}, ...]
    """
    import uuid
    
    if not output_path:
        os.makedirs(f"{settings.OUTPUT_DIR}/tts", exist_ok=True)
        output_path = f"{settings.OUTPUT_DIR}/tts/{uuid.uuid4()}.mp3"
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
    
    # 收集音频数据和字幕
    audio_data = b""
    subtitles = []
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            # 词级时间戳
            offset = chunk.get("offset", 0)
            duration = chunk.get("duration", 0)
            word_text = chunk.get("text", "")
            
            start_time = offset / 10_000_000
            end_time = (offset + duration) / 10_000_000
            
            subtitles.append({
                "text": word_text,
                "start": round(start_time, 3),
                "end": round(end_time, 3),
                "type": "word"
            })
        elif chunk["type"] == "SentenceBoundary":
            # 句子级时间戳
            offset = chunk.get("offset", 0)
            duration = chunk.get("duration", 0)
            sentence_text = chunk.get("text", "")
            
            start_time = offset / 10_000_000
            end_time = (offset + duration) / 10_000_000
            
            subtitles.append({
                "text": sentence_text,
                "start": round(start_time, 3),
                "end": round(end_time, 3),
                "type": "sentence"
            })
    
    # 保存音频
    with open(output_path, "wb") as f:
        f.write(audio_data)
    
    return output_path, subtitles


def merge_word_subtitles_to_sentences(
    subtitles: List[Dict],
    script: str
) -> List[Dict]:
    """
    将字幕整理为逐句字幕
    
    Args:
        subtitles: 字幕列表（可能是词级或句子级）
        script: 原始文案
    
    Returns:
        逐句字幕列表
    """
    # 如果已经是句子级字幕，直接返回
    sentence_subs = [s for s in subtitles if s.get("type") == "sentence"]
    if sentence_subs:
        return [{
            "text": s["text"],
            "start": s["start"],
            "end": s["end"]
        } for s in sentence_subs]
    
    # 如果是词级字幕，需要合并
    word_subs = [s for s in subtitles if s.get("type") == "word"]
    if not word_subs:
        # 没有字幕数据，按标点分割文案
        import re
        sentences = re.split(r'([。！？.!?\n]+)', script)
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            if sentence:
                result.append({
                    "text": sentence + punct,
                    "start": 0,
                    "end": 0
                })
        return result
    
    # 合并词级字幕为句子
    import re
    sentences = re.split(r'([。！？.!?\n]+)', script)
    merged_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i].strip()
        punct = sentences[i + 1] if i + 1 < len(sentences) else ""
        if sentence:
            merged_sentences.append(sentence + punct)
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        merged_sentences.append(sentences[-1].strip())
    
    if not merged_sentences:
        merged_sentences = [script]
    
    # 将词分配到句子
    result = []
    word_idx = 0
    
    for sentence in merged_sentences:
        sentence_words = []
        sentence_start = None
        sentence_end = None
        
        remaining_text = sentence
        while word_idx < len(word_subs) and remaining_text:
            word = word_subs[word_idx]
            word_text = word["text"]
            
            if word_text in remaining_text:
                if sentence_start is None:
                    sentence_start = word["start"]
                sentence_end = word["end"]
                sentence_words.append(word)
                
                idx = remaining_text.find(word_text)
                remaining_text = remaining_text[idx + len(word_text):]
                word_idx += 1
            else:
                break
        
        if sentence_words:
            result.append({
                "text": sentence,
                "start": sentence_start,
                "end": sentence_end,
                "words": sentence_words
            })
        elif sentence:
            result.append({
                "text": sentence,
                "start": 0,
                "end": 0
            })
    
    return result
