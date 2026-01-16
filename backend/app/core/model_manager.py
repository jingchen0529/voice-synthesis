"""
AI 模型统一管理模块
支持多模型懒加载、路径管理、设备分配
"""
import os
from typing import Dict, Any, Optional
from functools import lru_cache
from app.core.config import settings


class ModelManager:
    """AI 模型管理器（单例）"""
    
    _instance = None
    _models: Dict[str, Any] = {}
    _device: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def device(self) -> str:
        """获取计算设备"""
        if self._device is None:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[ModelManager] Using device: {self._device}")
        return self._device
    
    def _get_model_path(self, model_key: str) -> str:
        """获取模型完整路径"""
        relative_path = settings.MODEL_PATHS.get(model_key)
        if not relative_path:
            raise ValueError(f"Unknown model key: {model_key}")
        
        # 相对于 backend 目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_dir, relative_path)
    
    def get_tts_model(self):
        """获取 TTS 模型（懒加载）"""
        if "tts" not in self._models:
            from TTS.api import TTS
            
            model_path = self._get_model_path("tts_xtts_v2")
            config_path = os.path.join(model_path, "config.json")
            
            if os.path.exists(model_path) and os.path.exists(config_path):
                print(f"[ModelManager] Loading TTS model from: {model_path}")
                self._models["tts"] = TTS(
                    model_path=model_path,
                    config_path=config_path
                ).to(self.device)
            else:
                print(f"[ModelManager] Local model not found, downloading XTTS v2...")
                self._models["tts"] = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            
            print("[ModelManager] TTS model loaded!")
        
        return self._models["tts"]
    
    def get_model(self, model_key: str) -> Any:
        """
        通用模型获取接口
        后续可扩展支持更多模型类型
        """
        loaders = {
            "tts_xtts_v2": self.get_tts_model,
            # 后续添加更多模型加载器
            # "whisper": self.get_whisper_model,
            # "video_encoder": self.get_video_encoder,
        }
        
        loader = loaders.get(model_key)
        if not loader:
            raise ValueError(f"No loader for model: {model_key}")
        
        return loader()
    
    def is_loaded(self, model_key: str) -> bool:
        """检查模型是否已加载"""
        return model_key in self._models
    
    def unload_model(self, model_key: str):
        """卸载指定模型释放内存"""
        if model_key in self._models:
            del self._models[model_key]
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print(f"[ModelManager] Unloaded model: {model_key}")
    
    def unload_all(self):
        """卸载所有模型"""
        self._models.clear()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[ModelManager] All models unloaded")
    
    def list_available_models(self) -> Dict[str, str]:
        """列出所有可用模型及其路径"""
        result = {}
        for key, path in settings.MODEL_PATHS.items():
            full_path = self._get_model_path(key)
            result[key] = {
                "path": full_path,
                "exists": os.path.exists(full_path),
                "loaded": key in self._models
            }
        return result


@lru_cache()
def get_model_manager() -> ModelManager:
    """获取模型管理器实例"""
    return ModelManager()
