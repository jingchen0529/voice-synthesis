#!/usr/bin/env python3
"""
PyArmor 加密部署脚本

使用方法：
1. 在开发机器上安装 PyArmor: pip install pyarmor
2. 在目标服务器上获取机器码: pyarmor hdinfo
3. 将机器码填入 TARGET_MACHINE_ID
4. 运行此脚本生成加密包: python scripts/encrypt_deploy.py
5. 将 dist_encrypted/ 目录部署到服务器

注意：此脚本在开发机器上运行，不要在服务器上运行
"""

import os
import shutil
import subprocess
import sys

# ==================== 配置 ====================

# 目标服务器机器码（在服务器上运行 pyarmor hdinfo 获取）
TARGET_MACHINE_ID = "your-server-machine-id-here"

# 需要加密的目录
SOURCE_DIR = "app"

# 输出目录
OUTPUT_DIR = "dist_encrypted"

# 排除的文件/目录
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
]

# 需要复制但不加密的文件
COPY_FILES = [
    "main.py",
    "requirements.txt",
    ".env.example",
]

COPY_DIRS = [
    "sql",
    "scripts",
]

# ==================== 脚本 ====================

def check_pyarmor():
    """检查 PyArmor 是否安装"""
    try:
        result = subprocess.run(["pyarmor", "--version"], capture_output=True, text=True)
        print(f"PyArmor 版本: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("错误: PyArmor 未安装，请运行: pip install pyarmor")
        return False


def get_machine_id():
    """获取当前机器的机器码"""
    result = subprocess.run(["pyarmor", "hdinfo"], capture_output=True, text=True)
    print("当前机器信息:")
    print(result.stdout)
    return result.stdout


def clean_output():
    """清理输出目录"""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    print(f"已清理输出目录: {OUTPUT_DIR}")


def encrypt_code():
    """加密代码"""
    print(f"\n开始加密 {SOURCE_DIR} 目录...")
    
    # PyArmor 8.x 命令
    cmd = [
        "pyarmor", "gen",
        "--output", OUTPUT_DIR,
        "--platform", "linux.x86_64",  # 目标平台
        "--bind-device", TARGET_MACHINE_ID,  # 绑定机器码
        "--recursive",  # 递归加密子目录
        SOURCE_DIR
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"加密失败:\n{result.stderr}")
        # 尝试 PyArmor 7.x 命令
        print("\n尝试 PyArmor 7.x 命令...")
        cmd_v7 = [
            "pyarmor", "obfuscate",
            "--output", f"{OUTPUT_DIR}/{SOURCE_DIR}",
            "--recursive",
            "--bind-device", TARGET_MACHINE_ID,
            f"{SOURCE_DIR}/__init__.py"
        ]
        result = subprocess.run(cmd_v7, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"加密失败:\n{result.stderr}")
            return False
    
    print("加密成功!")
    return True


def copy_additional_files():
    """复制其他必要文件"""
    print("\n复制其他文件...")
    
    for file in COPY_FILES:
        if os.path.exists(file):
            shutil.copy(file, OUTPUT_DIR)
            print(f"  复制: {file}")
    
    for dir_name in COPY_DIRS:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, f"{OUTPUT_DIR}/{dir_name}")
            print(f"  复制目录: {dir_name}")
    
    # 创建必要的空目录
    for dir_name in ["uploads", "outputs", "ai_models"]:
        os.makedirs(f"{OUTPUT_DIR}/{dir_name}", exist_ok=True)
        # 创建 .gitkeep
        with open(f"{OUTPUT_DIR}/{dir_name}/.gitkeep", "w") as f:
            pass
    
    print("文件复制完成!")


def create_run_script():
    """创建运行脚本"""
    run_script = """#!/bin/bash
# 启动脚本

cd "$(dirname "$0")"

# 激活虚拟环境
source .venv/bin/activate

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000
"""
    
    with open(f"{OUTPUT_DIR}/run.sh", "w") as f:
        f.write(run_script)
    
    os.chmod(f"{OUTPUT_DIR}/run.sh", 0o755)
    print("创建启动脚本: run.sh")


def create_readme():
    """创建部署说明"""
    readme = """# 加密版本部署说明

## 此版本已绑定服务器机器码，仅能在授权服务器上运行

### 部署步骤

1. 上传整个目录到服务器

2. 创建虚拟环境并安装依赖:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyarmor-runtime  # 运行时依赖
```

3. 配置环境变量:
```bash
cp .env.example .env
vim .env
```

4. 初始化数据库:
```bash
mysql -u user -p database < sql/init.sql
```

5. 启动服务:
```bash
./run.sh
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 注意事项

- 此版本仅能在绑定的服务器上运行
- 请勿尝试反编译或修改加密代码
- 如需更换服务器，请联系开发者重新授权
"""
    
    with open(f"{OUTPUT_DIR}/README.md", "w") as f:
        f.write(readme)
    
    print("创建部署说明: README.md")


def main():
    print("=" * 50)
    print("PyArmor 加密部署脚本")
    print("=" * 50)
    
    # 检查是否在 backend 目录
    if not os.path.exists("app"):
        print("错误: 请在 backend 目录下运行此脚本")
        sys.exit(1)
    
    # 检查机器码配置
    if TARGET_MACHINE_ID == "your-server-machine-id-here":
        print("\n警告: 请先配置目标服务器机器码!")
        print("在服务器上运行以下命令获取机器码:")
        print("  pip install pyarmor")
        print("  pyarmor hdinfo")
        print("\n然后将机器码填入此脚本的 TARGET_MACHINE_ID 变量")
        sys.exit(1)
    
    if not check_pyarmor():
        sys.exit(1)
    
    clean_output()
    
    if not encrypt_code():
        sys.exit(1)
    
    copy_additional_files()
    create_run_script()
    create_readme()
    
    print("\n" + "=" * 50)
    print(f"加密完成! 输出目录: {OUTPUT_DIR}")
    print("将此目录部署到目标服务器即可")
    print("=" * 50)


if __name__ == "__main__":
    main()
