"""
简化版图片预览性能测试
"""

import sys
import os
import time
sys.path.append('src')


def simple_performance_test():
    """简单的性能测试"""
    print("⚡ 图片预览性能测试")
    print("=" * 50)
    
    # 获取测试图片
    test_dir = "data/test_images"
    if not os.path.exists(test_dir):
        print("❌ 测试目录不存在，请先运行图片生成脚本")
        return
    
    image_files = []
    for filename in os.listdir(test_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(test_dir, filename)
            image_files.append(filepath)
    
    print(f"📊 测试文件数量: {len(image_files)} 张图片")
    print()
    
    # 测试基本功能
    print("🔍 测试基本图片信息提取...")
    
    try:
        from image_preview_optimized import get_basic_image_info
        
        start_time = time.time()
        results = []
        
        for i, img_path in enumerate(image_files):
            print(f"  处理 {i+1}/{len(image_files)}: {os.path.basename(img_path)}")
            info = get_basic_image_info(img_path)
            if info:
                results.append(info)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ 处理完成")
        print(f"   处理时间: {processing_time:.2f} 秒")
        print(f"   平均每张: {processing_time/len(image_files):.3f} 秒")
        print(f"   成功处理: {len(results)}/{len(image_files)} 张")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return
    
    print()
    
    # 测试缓存性能
    print("🗄️ 测试图片缓存...")
    
    try:
        from image_preview_optimized import ImageCache
        
        cache = ImageCache(max_size=10)
        test_files = image_files[:5]  # 只测试前5张
        
        # 第一次加载
        start_time = time.time()
        for img_path in test_files:
            cache.get_thumbnail(img_path)
        first_load = time.time() - start_time
        
        # 第二次加载（缓存）
        start_time = time.time()
        for img_path in test_files:
            cache.get_thumbnail(img_path)
        cached_load = time.time() - start_time
        
        print(f"✅ 缓存测试完成")
        print(f"   首次加载: {first_load:.3f} 秒")
        print(f"   缓存加载: {cached_load:.3f} 秒")
        
        if first_load > 0:
            speedup = (first_load - cached_load) / first_load * 100
            print(f"   缓存加速: {speedup:.1f}%")
        
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
    
    print()
    
    # 性能建议
    print("💡 性能优化建议")
    print("-" * 30)
    
    if len(image_files) > 50:
        print("📷 图片数量较多 (>50张):")
        print("   ✅ 强烈建议使用性能优化模式")
        print("   ✅ 启用图片缓存")
        print("   ✅ 使用分页浏览")
    elif len(image_files) > 20:
        print("📷 图片数量中等 (20-50张):")
        print("   ✅ 建议使用性能优化模式") 
        print("   ✅ 可以启用缓存")
    else:
        print("📷 图片数量较少 (<20张):")
        print("   ✅ 标准模式和优化模式都可以")
        print("   ✅ 性能差异不明显")
    
    print()
    print("🔧 通用优化建议:")
    print("   1. 使用缩略图而不是原图")
    print("   2. 限制同时显示的图片数量")
    print("   3. 启用图片预览缓存")
    print("   4. 对大量图片使用分页")
    print("   5. 避免同时加载所有EXIF数据")


def test_file_access_speed():
    """测试文件访问速度"""
    print("\n📁 文件访问速度测试")
    print("=" * 30)
    
    test_dir = "data/test_images"
    if not os.path.exists(test_dir):
        print("❌ 测试目录不存在")
        return
    
    image_files = []
    for filename in os.listdir(test_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(test_dir, filename)
            image_files.append(filepath)
    
    # 测试文件基本信息获取速度
    start_time = time.time()
    for img_path in image_files:
        os.path.exists(img_path)
        os.path.getsize(img_path)
        os.path.getmtime(img_path)
    file_info_time = time.time() - start_time
    
    print(f"📊 文件信息获取: {file_info_time:.3f} 秒 ({len(image_files)} 个文件)")
    print(f"📊 平均每个文件: {file_info_time/len(image_files)*1000:.1f} 毫秒")
    
    # 测试图片头部信息读取
    start_time = time.time()
    success_count = 0
    for img_path in image_files:
        try:
            from PIL import Image
            with Image.open(img_path) as img:
                img.size  # 只获取尺寸，不加载完整图片
                success_count += 1
        except:
            pass
    header_time = time.time() - start_time
    
    print(f"📊 图片头部读取: {header_time:.3f} 秒 ({success_count} 个成功)")
    print(f"📊 平均每个图片: {header_time/len(image_files)*1000:.1f} 毫秒")


def main():
    """主测试函数"""
    print("⚡ 图片预览性能分析工具")
    print("=" * 60)
    
    simple_performance_test()
    test_file_access_speed()
    
    print("=" * 60)
    print("🎉 性能测试完成！")
    print()
    print("📝 如何使用测试结果:")
    print("   1. 查看处理时间评估当前性能")
    print("   2. 根据图片数量选择合适模式") 
    print("   3. 在应用中选择'性能优化模式'")
    print("   4. 观察缓存加速效果")


if __name__ == "__main__":
    main()