"""
测试16位时间戳解析修复
"""

import sys
import os
sys.path.append('src')

from image_preview import extract_timestamp_from_filename
from datetime import datetime


def test_16_bit_timestamp():
    """测试16位时间戳"""
    print("🧪 测试16位时间戳解析")
    print("=" * 40)
    
    # 您提供的时间戳示例
    test_timestamp = "1501822123278663"
    
    # 手动计算预期结果
    first_10_digits = test_timestamp[:10]  # 1501822123
    expected_unix = int(first_10_digits)    # 1501822123
    
    print(f"原始时间戳: {test_timestamp}")
    print(f"前10位: {first_10_digits}")
    print(f"Unix时间戳: {expected_unix}")
    
    try:
        expected_datetime = datetime.fromtimestamp(expected_unix)
        print(f"预期时间: {expected_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    except (ValueError, OSError) as e:
        print(f"❌ Unix时间戳无效: {e}")
        return
    
    # 测试文件名解析
    test_cases = [
        f"unix_{test_timestamp}.png",
        f"unix-{test_timestamp}.jpg",
        f"image_unix_{test_timestamp}_frame.png",
    ]
    
    print("\n🔍 文件名解析测试:")
    for filename in test_cases:
        result = extract_timestamp_from_filename(filename)
        if result:
            print(f"✅ {filename}")
            print(f"   -> {result.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 验证是否正确
            if result == expected_datetime:
                print(f"   ✓ 解析正确")
            else:
                print(f"   ❌ 解析错误，预期: {expected_datetime}")
        else:
            print(f"❌ {filename}")
            print(f"   -> 无法解析")
        print()


def test_other_formats():
    """测试其他格式确保没有破坏"""
    print("🧪 测试其他时间戳格式（确保兼容性）")
    print("=" * 40)
    
    test_cases = [
        ("unix_1704074400.png", "2024-01-01 10:00:00"),
        ("unix_1704074400123.png", "2024-01-01 10:00:00"),  # 13位毫秒
        ("img_20240101_120000.jpg", "2024-01-01 12:00:00"),
        ("daily_20240315.png", "2024-03-15 00:00:00"),
    ]
    
    for filename, expected_str in test_cases:
        result = extract_timestamp_from_filename(filename)
        if result:
            actual_str = result.strftime('%Y-%m-%d %H:%M:%S')
            if actual_str == expected_str:
                print(f"✅ {filename} -> {actual_str}")
            else:
                print(f"❌ {filename} -> {actual_str} (预期: {expected_str})")
        else:
            print(f"❌ {filename} -> 无法解析")


def main():
    """主测试函数"""
    print("🔧 时间戳解析修复验证")
    print("=" * 50)
    
    test_16_bit_timestamp()
    print()
    test_other_formats()
    
    print("=" * 50)
    print("✅ 测试完成")


if __name__ == "__main__":
    main()