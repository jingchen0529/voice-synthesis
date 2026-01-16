"""
直接测试 TTS 模型合成
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.core.model_manager import get_model_manager

def test_tts():
    print("=" * 50)
    print("TTS 模型测试")
    print("=" * 50)
    
    # 检查模型状态
    manager = get_model_manager()
    models = manager.list_available_models()
    
    print("\n可用模型:")
    for key, info in models.items():
        status = "✅ 存在" if info["exists"] else "❌ 不存在"
        print(f"  - {key}: {status}")
        print(f"    路径: {info['path']}")
    
    # 检查是否有参考音频
    # 需要一个参考音频文件来克隆声音
    test_audio = None
    for ext in ['.wav', '.mp3', '.m4a']:
        for name in ['test', 'sample', 'reference', 'speaker']:
            path = f"{name}{ext}"
            if os.path.exists(path):
                test_audio = path
                break
        if test_audio:
            break
    
    if not test_audio:
        print("\n⚠️  没有找到参考音频文件")
        print("请提供一个参考音频文件（wav/mp3/m4a），放在 backend 目录下")
        print("例如: test.wav, sample.mp3")
        print("\n或者你可以指定路径运行:")
        print("  python test_tts.py /path/to/your/audio.wav")
        
        if len(sys.argv) > 1:
            test_audio = sys.argv[1]
            if not os.path.exists(test_audio):
                print(f"\n❌ 指定的文件不存在: {test_audio}")
                return
        else:
            return
    
    print(f"\n使用参考音频: {test_audio}")
    print("\n正在加载模型...")
    
    try:
        tts = manager.get_tts_model()
        print("✅ 模型加载成功!")
        
        # 测试合成
        text = "你好，这是一个语音合成测试。"
        output_path = "test_output.wav"
        
        print(f"\n正在合成: {text}")
        tts.tts_to_file(
            text=text,
            speaker_wav=test_audio,
            language="zh",
            file_path=output_path
        )
        
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"\n✅ 合成成功!")
            print(f"   输出文件: {output_path}")
            print(f"   文件大小: {size / 1024:.1f} KB")
        else:
            print("\n❌ 合成失败，输出文件不存在")
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tts()
