"""
图片预览性能测试和对比
"""

import sys
import os
import time
import psutil
import gc
sys.path.append('src')

from image_preview import organize_images_by_timestamp
from image_preview_optimized import organize_images_fast


def measure_performance(func, *args, **kwargs):
    """测量函数性能"""
    # 记录开始状态
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    
    # 执行函数
    result = func(*args, **kwargs)
    
    # 记录结束状态
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    execution_time = end_time - start_time
    memory_delta = end_memory - start_memory
    
    return result, execution_time, memory_delta


def test_image_processing_performance():
    """测试图片处理性能"""
    print("🚀 图片预览性能测试")
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
    
    # 测试标准模式
    print("🔍 测试标准模式...")
    gc.collect()  # 清理内存
    
    try:
        result_std, time_std, memory_std = measure_performance(
            organize_images_by_timestamp, image_files
        )
        print(f"✅ 标准模式完成")
        print(f"   执行时间: {time_std:.2f} 秒")
        print(f"   内存增量: {memory_std:.1f} MB")
        print(f"   处理结果: {len(result_std)} 张图片")
    except Exception as e:
        print(f"❌ 标准模式失败: {e}")
        result_std, time_std, memory_std = None, float('inf'), float('inf')
    
    print()
    
    # 测试优化模式
    print("⚡ 测试优化模式...")
    gc.collect()  # 清理内存
    
    try:
        # 直接测试基本功能，不模拟streamlit
        from image_preview_optimized import get_basic_image_info
        
        start_time = time.time()
        current_process = psutil.Process()
        start_memory = current_process.memory_info().rss / 1024 / 1024
        
        result_opt = []
        for img_path in image_files:
            info = get_basic_image_info(img_path)
            if info:
                result_opt.append(info)
        
        # 排序
        result_opt.sort(key=lambda x: x['timestamp'])
        
        end_time = time.time()
        end_memory = current_process.memory_info().rss / 1024 / 1024
        
        time_opt = end_time - start_time
        memory_opt = end_memory - start_memory
        
        print(f"✅ 优化模式完成")
        print(f"   执行时间: {time_opt:.2f} 秒")
        print(f"   内存增量: {memory_opt:.1f} MB")
        print(f"   处理结果: {len(result_opt)} 张图片")
        
    except Exception as e:
        print(f"❌ 优化模式失败: {e}")
        result_opt, time_opt, memory_opt = None, float('inf'), float('inf')
    
    print()
    
    # 性能对比
    print("📈 性能对比")
    print("-" * 30)
    
    if time_std != float('inf') and time_opt != float('inf'):
        time_improvement = ((time_std - time_opt) / time_std) * 100
        memory_improvement = ((memory_std - memory_opt) / memory_std) * 100
        
        print(f"⏱️  执行时间提升: {time_improvement:.1f}%")
        print(f"💾 内存使用改善: {memory_improvement:.1f}%")
        
        if time_improvement > 0:
            print(f"🚀 优化模式快了 {time_improvement:.1f}%")
        else:
            print(f"⚠️  优化模式慢了 {abs(time_improvement):.1f}%")
            
        if memory_improvement > 0:
            print(f"💚 内存节省 {memory_improvement:.1f}%")
        else:
            print(f"⚠️  内存增加 {abs(memory_improvement):.1f}%")
    
    print()
    
    # 性能建议
    print("💡 性能建议")
    print("-" * 30)
    
    if len(image_files) > 50:
        print("📷 图片数量较多，强烈建议使用性能优化模式")
    elif len(image_files) > 20:
        print("📷 图片数量中等，建议使用性能优化模式")
    else:
        print("📷 图片数量较少，两种模式都可以")
    
    print()
    print("🔧 优化建议:")
    print("1. 对于>20张图片，使用性能优化模式")
    print("2. 开启图片缓存")
    print("3. 使用分页浏览")
    print("4. 限制同时加载的图片数量")
    print("5. 使用缩略图而不是原图")


def test_cache_effectiveness():
    """测试缓存效果"""
    print("\n🗄️ 缓存效果测试")
    print("=" * 30)
    
    try:
        from image_preview_optimized import ImageCache
        
        cache = ImageCache(max_size=10)
        test_dir = "data/test_images"
        
        if not os.path.exists(test_dir):
            print("❌ 测试目录不存在")
            return
        
        image_files = []
        for filename in os.listdir(test_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filepath = os.path.join(test_dir, filename)
                image_files.append(filepath)
                if len(image_files) >= 5:  # 只测试前5张
                    break
        
        print(f"📊 测试文件: {len(image_files)} 张图片")
        
        # 第一次加载（无缓存）
        start_time = time.time()
        for img_path in image_files:
            cache.get_thumbnail(img_path)
        first_load_time = time.time() - start_time
        
        print(f"⏱️  首次加载时间: {first_load_time:.2f} 秒")
        
        # 第二次加载（有缓存）
        start_time = time.time()
        for img_path in image_files:
            cache.get_thumbnail(img_path)
        cached_load_time = time.time() - start_time
        
        print(f"⚡ 缓存加载时间: {cached_load_time:.2f} 秒")
        
        if first_load_time > 0:
            speedup = (first_load_time - cached_load_time) / first_load_time * 100
            print(f"🚀 缓存加速: {speedup:.1f}%")
        
        print(f"📦 缓存状态: {len(cache.cache)}/{cache.max_size}")
        
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")


def main():
    """主测试函数"""
    print("⚡ 图片预览性能优化测试工具")
    print("=" * 60)
    
    test_image_processing_performance()
    test_cache_effectiveness()
    
    print("=" * 60)
    print("🎉 性能测试完成！")
    print("💡 根据测试结果选择最适合的预览模式")


if __name__ == "__main__":
    main()