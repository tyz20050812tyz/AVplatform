"""
生成带时间戳的测试图片
用于演示图片预览功能
"""

import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import random


def create_test_image(width=800, height=600, text="Test Image", color=None):
    """创建测试图片"""
    if color is None:
        color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
    
    # 创建图片
    image = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(image)
    
    # 尝试使用系统字体
    try:
        # 在Windows上尝试使用默认字体
        font = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        try:
            # 在Linux上尝试使用默认字体
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except OSError:
            # 使用默认字体
            font = ImageFont.load_default()
    
    # 在图片上绘制文本
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 绘制白色背景矩形
    padding = 20
    draw.rectangle([x - padding, y - padding, x + text_width + padding, y + text_height + padding], 
                   fill=(255, 255, 255, 200))
    
    # 绘制黑色文本
    draw.text((x, y), text, fill=(0, 0, 0), font=font)
    
    return image


def generate_test_images():
    """生成一系列测试图片"""
    # 创建测试图片目录
    test_dir = "data/test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # 生成不同时间戳的图片
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    
    # 场景1: 按分钟间隔的图片序列
    print("生成分钟间隔图片序列...")
    for i in range(10):
        timestamp = base_time + timedelta(minutes=i * 5)
        filename = f"sequence_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(test_dir, filename)
        
        image = create_test_image(
            text=f"图片 {i+1}\\n{timestamp.strftime('%H:%M:%S')}",
            color=(100 + i * 15, 150, 200)
        )
        image.save(filepath)
        print(f"创建: {filename}")
    
    # 场景2: 按小时间隔的图片
    print("\\n生成小时间隔图片序列...")
    for i in range(6):
        timestamp = base_time + timedelta(hours=i * 2)
        filename = f"hourly_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
        filepath = os.path.join(test_dir, filename)
        
        image = create_test_image(
            text=f"小时图片 {i+1}\\n{timestamp.strftime('%Y-%m-%d %H:%M')}",
            color=(200, 100 + i * 20, 150)
        )
        image.save(filepath)
        print(f"创建: {filename}")
    
    # 场景3: Unix时间戳命名的图片
    print("\\n生成Unix时间戳图片...")
    for i in range(5):
        timestamp = base_time + timedelta(seconds=i * 3600)  # 每小时一张
        unix_timestamp = int(timestamp.timestamp())
        filename = f"unix_{unix_timestamp}.png"
        filepath = os.path.join(test_dir, filename)
        
        image = create_test_image(
            text=f"Unix: {unix_timestamp}\\n{timestamp.strftime('%Y-%m-%d %H:%M')}",
            color=(150, 200, 100 + i * 25)
        )
        image.save(filepath)
        print(f"创建: {filename}")
    
    # 场景4: 日期格式的图片
    print("\\n生成日期格式图片...")
    for i in range(7):
        timestamp = base_time + timedelta(days=i)
        filename = f"daily_{timestamp.strftime('%Y%m%d')}.png"
        filepath = os.path.join(test_dir, filename)
        
        image = create_test_image(
            text=f"日期图片\\n{timestamp.strftime('%Y-%m-%d')}",
            color=(200 - i * 20, 180, 220)
        )
        image.save(filepath)
        print(f"创建: {filename}")
    
    # 场景5: 无时间戳的图片（使用文件修改时间）
    print("\\n生成无时间戳图片...")
    for i in range(3):
        filename = f"no_timestamp_{i+1}.jpg"
        filepath = os.path.join(test_dir, filename)
        
        image = create_test_image(
            text=f"无时间戳图片 {i+1}\\n使用文件修改时间",
            color=(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        )
        image.save(filepath)
        print(f"创建: {filename}")
    
    print(f"\\n✅ 测试图片生成完成！")
    print(f"📁 图片保存在: {os.path.abspath(test_dir)}")
    print(f"📊 总共生成了 {10 + 6 + 5 + 7 + 3} 张测试图片")


if __name__ == "__main__":
    generate_test_images()