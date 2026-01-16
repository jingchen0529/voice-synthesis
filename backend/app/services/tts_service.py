from app.core.model_manager import get_model_manager


def get_tts():
    """获取 TTS 实例（通过统一模型管理器）"""
    return get_model_manager().get_tts_model()


def generate_speech(text: str, speaker_wav: str, language: str, output_path: str) -> str:
    """
    生成语音
    :param text: 要合成的文本
    :param speaker_wav: 参考音频路径
    :param language: 语言代码
    :param output_path: 输出文件路径
    :return: 输出文件路径
    """
    tts = get_tts()
    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wav,
        language=language,
        file_path=output_path
    )
    return output_path


# 支持的语言
SUPPORTED_LANGUAGES = {
    "zh": "中文",
    "en": "English",
    "ar": "العربية",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "ru": "Русский",
}

# 支持的音频格式
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}
