"""
图片预览功能演示脚本
展示新功能的核心特性
"""

import os
import sys
sys.path.append('src')

from image_preview import extract_timestamp_from_filename, organize_images_by_timestamp


def demo_timestamp_extraction():
    """演示时间戳提取功能"""
    print("🎯 时间戳提取功能演示")
    print("=" * 40)
    
    test_files = [
        "camera_20240315_143022.jpg",           # 标准格式
        "IMG_2024-03-15_14-30-22.png",         # 带连字符
        "unix_1710506622.jpg",                 # Unix时间戳
        "daily_20240315.png",                  # 仅日期
        "photo_no_timestamp.jpg"               # 无时间戳
    ]
    
    for filename in test_files:
        timestamp = extract_timestamp_from_filename(filename)
        if timestamp:
            print(f"✅ {filename}")
            print(f"   -> {timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}")
        else:
            print(f"❌ {filename}")
            print(f"   -> 无法识别时间戳")
        print()


def demo_image_organization():
    """演示图片整理功能"""
    print("📅 图片时间序列整理演示")
    print("=" * 40)
    
    # 检查测试图片目录
    test_dir = "data/test_images"
    if not os.path.exists(test_dir):
        print(f"❌ 测试目录不存在: {test_dir}")
        return
    
    # 获取图片文件
    image_files = []
    for filename in os.listdir(test_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(test_dir, filename)
            image_files.append(filepath)
    
    print(f"📊 发现 {len(image_files)} 个图片文件")
    
    # 整理图片
    image_data = organize_images_by_timestamp(image_files)
    
    # 按类型分组统计
    by_source = {}
    for img in image_data:
        source = img['time_source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(img)
    
    print("📈 时间戳来源统计:")
    for source, images in by_source.items():
        print(f"  {source}: {len(images)} 张")
    
    print("\\n⏰ 时间序列 (前10张):")
    for i, img_info in enumerate(image_data[:10]):
        print(f"  {i+1:2d}. {img_info['timestamp'].strftime('%m-%d %H:%M')} | {img_info['filename']}")
    
    if len(image_data) > 10:
        print(f"  ... 还有 {len(image_data) - 10} 张")


def show_feature_summary():
    """显示功能总结"""
    print("\\n🚀 图片预览功能总结")
    print("=" * 50)
    
    features = [
        "✅ 智能时间戳识别 - 支持多种格式",
        "✅ 时间轴拖动预览 - 流畅的时间浏览体验", 
        "✅ 单张图片详情 - 完整的元数据展示",
        "✅ 网格批量预览 - 高效浏览大量图片",
        "✅ 自动排序整理 - 按时间智能排列",
        "✅ 多源时间戳 - 文件名/EXIF/修改时间",
        "✅ 响应式设计 - 适配不同屏幕",
        "✅ 性能优化 - 大量图片的流畅体验"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\\n🎯 使用场景:")
    scenarios = [
        "📸 摄影作品时间轴浏览",
        "🚗 自动驾驶数据序列分析", 
        "📊 数据采集时间序列可视化",
        "🔍 图片数据集快速检索",
        "📅 时间相关的图像数据分析"
    ]
    
    for scenario in scenarios:
        print(f"  {scenario}")


def main():
    """主演示函数"""
    print("🎨 图片预览功能演示")
    print("🕒 " + "="*48)
    
    demo_timestamp_extraction()
    print()
    demo_image_organization()
    show_feature_summary()
    
    print("\\n" + "="*50)
    print("💡 访问 http://localhost:8502 体验完整功能")
    print("📖 查看 docs/image_preview_guide.md 了解详细使用方法")


if __name__ == "__main__":
    main()