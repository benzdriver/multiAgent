"""
清除浏览器缓存的辅助脚本
用法: python clear_browser_cache.py
"""
import webbrowser
import time
import os
from pathlib import Path

def clear_cache():
    print("🧹 清除浏览器缓存向导...")
    print("\n步骤1: 关闭所有打开的浏览器窗口")
    input("完成后按Enter继续...")
    
    print("\n步骤2: 准备打开浏览器缓存设置页面...")
    input("按Enter打开浏览器...")
    
    webbrowser.open('chrome://settings/clearBrowserData')
    
    print("\n步骤3: 在打开的页面中:")
    print("- 选择'缓存的图片和文件'")
    print("- 选择'Cookie及其他站点数据'")
    print("- 时间范围选择'所有时间'")
    print("- 点击'清除数据'按钮")
    
    input("\n完成缓存清除后按Enter继续...")
    
    build_frontend()
    
    print("\n🚀 准备启动应用...")
    start_app()

def build_frontend():
    print("\n🔨 重新构建前端资源...")
    os.chdir(Path(__file__).parent / "webui" / "frontend")
    os.system("npm run build")
    print("✅ 前端资源重建完成")

def start_app():
    print("\n🚀 启动应用...")
    os.chdir(Path(__file__).parent)
    os.system("python -m webui.app")

if __name__ == "__main__":
    clear_cache()
