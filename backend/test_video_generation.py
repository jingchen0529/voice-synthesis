"""测试视频生成流程"""
import requests
import time
import os

BASE_URL = "http://localhost:8000/api"

# 先登录获取 token
def login():
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    print(f"登录失败: {resp.text}")
    return None

def test_video_generation():
    token = login()
    if not token:
        print("❌ 登录失败，无法测试")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 模拟前端配置
    task_data = {
        # 文案配置
        "topic": "测试视频",
        "script": "这是一个测试视频，用于验证视频生成功能是否正常工作。",
        "script_language": "zh",
        
        # 配音配置
        "voice_language": "zh",
        "voice_name": "zh-CN-XiaoxiaoNeural",
        "voice_speed": "+0%",
        
        # 视频配置
        "video_resolution": "720p",
        "video_layout": "9:16",
        "video_fps": 30,
        "fit_mode": "crop",
        
        # 转场配置
        "transition_enabled": True,
        "transition_type": "fade",
        "transition_duration": 0.5,
        
        # 字幕配置
        "subtitle_enabled": True,
        "subtitle_font": "Heiti-SC-Medium",
        "subtitle_size": 48,
        "subtitle_color": "#FFFFFF",
        "subtitle_stroke_color": "#000000",
        "subtitle_stroke_width": 2.0,
        "subtitle_position": "bottom",
        
        # 特效配置
        "effect_type": None,
        "color_filter": "none",
        "brightness": 1.0,
        "contrast": 1.0,
        "saturation": 1.0,
        
        # BGM 配置
        "bgm_enabled": False,
        "bgm_volume": 0.3,
        
        # 输出配置
        "output_quality": "high",
        
        # 素材 - 不使用上传素材，让系统生成纯色背景
        "media_paths": [],
    }
    
    print("📤 创建视频任务...")
    print(f"   配置: {task_data['video_resolution']} {task_data['video_layout']} {task_data['video_fps']}fps")
    print(f"   字幕: {task_data['subtitle_position']} 位置, {task_data['subtitle_size']}px")
    
    resp = requests.post(f"{BASE_URL}/video/create", json=task_data, headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ 创建任务失败: {resp.status_code}")
        print(f"   错误: {resp.text}")
        return
    
    result = resp.json()
    task_id = result.get("task_id")
    print(f"✅ 任务创建成功: {task_id}")
    
    # 轮询任务状态
    print("\n⏳ 等待视频生成...")
    max_wait = 120  # 最多等待 120 秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        resp = requests.get(f"{BASE_URL}/video/{task_id}/status", headers=headers)
        if resp.status_code != 200:
            print(f"❌ 查询状态失败: {resp.text}")
            break
        
        status = resp.json()
        progress = status.get("progress", 0)
        message = status.get("message", "")
        state = status.get("status", "")
        
        print(f"   [{progress:3d}%] {message}")
        
        if state == "completed":
            print(f"\n✅ 视频生成完成!")
            download_url = status.get("download_url", "")
            duration = status.get("duration", 0)
            print(f"   时长: {duration:.1f}s")
            print(f"   下载: {download_url}")
            
            # 检查文件是否存在
            output_path = f"outputs/{task_id}.mp4"
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"   文件: {output_path} ({file_size/1024:.1f}KB)")
                
                # 验证视频是否可播放
                try:
                    from moviepy.editor import VideoFileClip
                    with VideoFileClip(output_path) as clip:
                        print(f"   验证: ✅ 视频可播放")
                        print(f"         尺寸: {clip.size[0]}x{clip.size[1]}")
                        print(f"         帧率: {clip.fps}fps")
                        print(f"         时长: {clip.duration:.1f}s")
                except Exception as e:
                    print(f"   验证: ❌ 视频无法播放 - {e}")
            else:
                print(f"   ⚠️ 文件不存在: {output_path}")
            return
        
        if state == "failed":
            error = status.get("error_message", message)
            print(f"\n❌ 视频生成失败: {error}")
            return
        
        time.sleep(2)
    
    print(f"\n⚠️ 超时，任务仍在处理中")

if __name__ == "__main__":
    test_video_generation()
