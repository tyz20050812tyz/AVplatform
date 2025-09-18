"""
测试图片预览功能
"""

import sys
import os
sys.path.append('src')

from image_preview import (
    extract_timestamp_from_filename, 
    organize_images_by_timestamp,
    get_image_metadata
)
from datetime import datetime


def test_timestamp_extraction():
    """测试时间戳提取功能"""
    print("🧪 测试时间戳提取功能...")
    
    test_cases = [
        "sequence_20240101_100000.png",
        "hourly_2024-01-01_10-00-00.jpg", 
        "unix_1704074400.png",
        "daily_20240101.png",
        "no_timestamp_1.jpg"
    ]
    
    for filename in test_cases:
        timestamp = extract_timestamp_from_filename(filename)
        if timestamp:
            print(f"✅ {filename} -> {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"❌ {filename} -> 无法提取时间戳")


def test_image_organization():
    """测试图片整理功能"""
    print("\\n🧪 测试图片整理功能...")
    
    test_dir = "data/test_images"
    if not os.path.exists(test_dir):
        print(f"❌ 测试目录不存在: {test_dir}")
        return
    
    # 获取图片文件列表
    image_files = []
    for filename in os.listdir(test_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(test_dir, filename)
            image_files.append(filepath)
    
    print(f"📊 找到 {len(image_files)} 个图片文件")
    
    # 整理图片
    image_data = organize_images_by_timestamp(image_files)
    
    print(f"📅 按时间排序的前5个文件:")
    for i, img_info in enumerate(image_data[:5]):
        print(f"  {i+1}. {img_info['filename']}")
        print(f"     时间: {img_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     来源: {img_info['time_source']}")
        print()


def test_metadata_extraction():
    """测试元数据提取功能"""
    print("🧪 测试元数据提取功能...")
    
    test_dir = "data/test_images"
    if not os.path.exists(test_dir):
        print(f"❌ 测试目录不存在: {test_dir}")
        return
    
    # 测试第一个图片文件
    image_files = [f for f in os.listdir(test_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print("❌ 没有找到图片文件")
        return
    
    test_file = os.path.join(test_dir, image_files[0])
    metadata = get_image_metadata(test_file)
    
    if metadata:
        print(f"✅ 成功提取元数据: {image_files[0]}")
        print(f"   尺寸: {metadata['size']}")
        print(f"   格式: {metadata['format']}")
        print(f"   颜色模式: {metadata['mode']}")
        print(f"   文件大小: {metadata['file_size']} 字节")
        if 'datetime' in metadata:
            print(f"   EXIF时间: {metadata['datetime']}")
    else:
        print(f"❌ 无法提取元数据: {image_files[0]}")


def main():
    """主测试函数"""
    print("🚀 图片预览功能测试开始")
    print("=" * 50)
    
    test_timestamp_extraction()
    test_image_organization()
    test_metadata_extraction()
    
    print("=" * 50)
    print("🏁 测试完成")


if __name__ == "__main__":
    main()