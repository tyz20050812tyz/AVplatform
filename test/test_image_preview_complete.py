"""
完整的图片预览功能测试
验证所有核心功能是否正常工作
"""

import unittest
import sys
import os
import tempfile
from PIL import Image
from datetime import datetime

# 添加源代码路径
sys.path.append('src')

from image_preview import (
    extract_timestamp_from_filename,
    get_image_metadata,
    organize_images_by_timestamp,
    create_image_timeline_chart
)


class TestImagePreviewFeatures(unittest.TestCase):
    """图片预览功能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.test_images = []
        
        # 创建测试图片
        test_cases = [
            ("test_20240101_120000.png", (100, 100)),
            ("img_2024-01-01_14-30-00.jpg", (150, 150)),
            ("unix_1704067200.png", (120, 120)),
            ("daily_20240102.jpg", (200, 150)),
            ("no_timestamp.png", (80, 80))
        ]
        
        for filename, size in test_cases:
            img_path = os.path.join(self.test_dir, filename)
            img = Image.new('RGB', size, (255, 0, 0))
            img.save(img_path)
            self.test_images.append(img_path)
    
    def tearDown(self):
        """测试后清理"""
        for img_path in self.test_images:
            if os.path.exists(img_path):
                os.remove(img_path)
        os.rmdir(self.test_dir)
    
    def test_timestamp_extraction(self):
        """测试时间戳提取功能"""
        # 测试标准格式
        timestamp = extract_timestamp_from_filename("test_20240101_120000.png")
        self.assertIsNotNone(timestamp)
        self.assertEqual(timestamp.year, 2024)
        self.assertEqual(timestamp.month, 1)
        self.assertEqual(timestamp.day, 1)
        self.assertEqual(timestamp.hour, 12)
        
        # 测试连字符格式
        timestamp = extract_timestamp_from_filename("img_2024-01-01_14-30-00.jpg")
        self.assertIsNotNone(timestamp)
        self.assertEqual(timestamp.hour, 14)
        self.assertEqual(timestamp.minute, 30)
        
        # 测试Unix时间戳
        timestamp = extract_timestamp_from_filename("unix_1704067200.png")
        self.assertIsNotNone(timestamp)
        self.assertEqual(timestamp.year, 2024)
        
        # 测试日期格式
        timestamp = extract_timestamp_from_filename("daily_20240102.jpg")
        self.assertIsNotNone(timestamp)
        self.assertEqual(timestamp.day, 2)
        
        # 测试无时间戳
        timestamp = extract_timestamp_from_filename("no_timestamp.png")
        self.assertIsNone(timestamp)
    
    def test_metadata_extraction(self):
        """测试元数据提取功能"""
        img_path = self.test_images[0]  # test_20240101_120000.png
        metadata = get_image_metadata(img_path)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['size'], (100, 100))
        self.assertEqual(metadata['format'], 'PNG')
        self.assertEqual(metadata['mode'], 'RGB')
        self.assertIsInstance(metadata['file_size'], int)
        self.assertGreater(metadata['file_size'], 0)
    
    def test_image_organization(self):
        """测试图片整理功能"""
        organized_data = organize_images_by_timestamp(self.test_images)
        
        # 验证返回的数据结构
        self.assertEqual(len(organized_data), 5)
        
        for img_data in organized_data:
            self.assertIn('path', img_data)
            self.assertIn('filename', img_data)
            self.assertIn('timestamp', img_data)
            self.assertIn('time_source', img_data)
            self.assertIn('metadata', img_data)
            
            # 验证时间戳是datetime对象
            self.assertIsInstance(img_data['timestamp'], datetime)
        
        # 验证排序（应该按时间戳排序）
        timestamps = [img['timestamp'] for img in organized_data]
        self.assertEqual(timestamps, sorted(timestamps))
        
        # 验证时间来源
        sources = [img['time_source'] for img in organized_data]
        self.assertIn('文件名', sources)
        self.assertIn('文件修改时间', sources)
    
    def test_timeline_chart_creation(self):
        """测试时间轴图表创建"""
        organized_data = organize_images_by_timestamp(self.test_images)
        
        # 创建时间轴图表
        fig = create_image_timeline_chart(organized_data)
        
        if fig is not None:  # 如果plotly可用
            self.assertIsNotNone(fig)
            # 验证图表数据
            self.assertEqual(len(fig.data), 1)
            self.assertEqual(len(fig.data[0].x), len(organized_data))
    
    def test_timestamp_priority(self):
        """测试时间戳优先级"""
        # 创建带时间戳的文件名
        timestamp_file = os.path.join(self.test_dir, "priority_20240315_100000.png")
        img = Image.new('RGB', (100, 100), (0, 255, 0))
        img.save(timestamp_file)
        
        organized_data = organize_images_by_timestamp([timestamp_file])
        
        # 验证使用文件名时间戳而不是文件修改时间
        self.assertEqual(organized_data[0]['time_source'], '文件名')
        self.assertEqual(organized_data[0]['timestamp'].year, 2024)
        self.assertEqual(organized_data[0]['timestamp'].month, 3)
        self.assertEqual(organized_data[0]['timestamp'].day, 15)
        
        # 清理
        os.remove(timestamp_file)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 空列表
        result = organize_images_by_timestamp([])
        self.assertEqual(result, [])
        
        # 不存在的文件
        result = organize_images_by_timestamp(["/nonexistent/file.jpg"])
        self.assertEqual(result, [])
        
        # 无效时间戳格式
        timestamp = extract_timestamp_from_filename("invalid_format.jpg")
        self.assertIsNone(timestamp)


def run_tests():
    """运行所有测试"""
    print("🧪 开始图片预览功能完整测试")
    print("=" * 50)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestImagePreviewFeatures)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 50)
    if result.wasSuccessful():
        print("✅ 所有测试通过！图片预览功能运行正常。")
    else:
        print(f"❌ 测试失败：{len(result.failures)} 个失败，{len(result.errors)} 个错误")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()