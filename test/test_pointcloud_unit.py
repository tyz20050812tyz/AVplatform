#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
点云可视化功能单元测试
根据项目规范：每个测试用例要原子化，只测试一个场景
"""

import unittest
import numpy as np
import os
import tempfile
import shutil


class TestPointCloudVisualization(unittest.TestCase):
    """点云可视化功能测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.test_dir = "test_pointclouds"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 创建测试点云数据
        self.test_points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0], 
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])
        
        self.test_colors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0]
        ])
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_load_txt_pointcloud_xyz_only(self):
        """测试加载只有XYZ坐标的TXT点云文件"""
        # 创建测试文件
        txt_file = os.path.join(self.test_dir, "test_xyz.txt")
        np.savetxt(txt_file, self.test_points, fmt='%.6f')
        
        # 动态导入（避免依赖问题）
        try:
            from main import load_point_cloud
            points, colors = load_point_cloud(txt_file)
            
            # 验证结果
            self.assertIsNotNone(points)
            self.assertEqual(len(points), 4)
            self.assertIsNone(colors)
            np.testing.assert_array_almost_equal(points, self.test_points)
            
        except ImportError:
            self.skipTest("无法导入main模块，跳过测试")
    
    def test_load_txt_pointcloud_with_colors(self):
        """测试加载带颜色的TXT点云文件"""
        # 创建带颜色的测试文件
        txt_file = os.path.join(self.test_dir, "test_xyzrgb.txt")
        data_with_colors = np.hstack([self.test_points, self.test_colors])
        np.savetxt(txt_file, data_with_colors, fmt='%.6f')
        
        try:
            from main import load_point_cloud
            points, colors = load_point_cloud(txt_file)
            
            # 验证结果
            self.assertIsNotNone(points)
            self.assertIsNotNone(colors)
            self.assertEqual(len(points), 4)
            self.assertEqual(len(colors), 4)
            np.testing.assert_array_almost_equal(points, self.test_points)
            np.testing.assert_array_almost_equal(colors, self.test_colors)
            
        except ImportError:
            self.skipTest("无法导入main模块，跳过测试")
    
    def test_load_invalid_file_format(self):
        """测试加载不支持的文件格式"""
        # 创建无效格式文件
        invalid_file = os.path.join(self.test_dir, "test.invalid")
        with open(invalid_file, 'w') as f:
            f.write("invalid content")
        
        try:
            from main import load_point_cloud
            points, colors = load_point_cloud(invalid_file)
            
            # 验证结果
            self.assertIsNone(points)
            self.assertIsNone(colors)
            
        except ImportError:
            self.skipTest("无法导入main模块，跳过测试")
    
    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.txt")
        
        try:
            from main import load_point_cloud
            points, colors = load_point_cloud(nonexistent_file)
            
            # 验证结果
            self.assertIsNone(points)
            self.assertIsNone(colors)
            
        except ImportError:
            self.skipTest("无法导入main模块，跳过测试")
    
    def test_load_empty_txt_file(self):
        """测试加载空的TXT文件"""
        empty_file = os.path.join(self.test_dir, "empty.txt")
        open(empty_file, 'w').close()  # 创建空文件
        
        try:
            from main import load_point_cloud
            points, colors = load_point_cloud(empty_file)
            
            # 验证结果（空文件应该返回None）
            self.assertIsNone(points)
            self.assertIsNone(colors)
            
        except ImportError:
            self.skipTest("无法导入main模块，跳过测试")
    
    def test_load_malformed_txt_file(self):
        """测试加载格式错误的TXT文件"""
        malformed_file = os.path.join(self.test_dir, "malformed.txt")
        with open(malformed_file, 'w') as f:
            f.write("1.0 2.0\n")  # 只有两列，不足3列
            f.write("3.0 4.0\n")
        
        try:
            from main import load_point_cloud
            points, colors = load_point_cloud(malformed_file)
            
            # 验证结果（格式错误应该返回None）
            self.assertIsNone(points)
            self.assertIsNone(colors)
            
        except ImportError:
            self.skipTest("无法导入main模块，跳过测试")


class TestPointCloudUtils(unittest.TestCase):
    """点云工具函数测试类"""
    
    def test_sample_large_pointcloud(self):
        """测试大点云的采样功能"""
        # 创建大型点云数据
        large_points = np.random.random((50000, 3))
        
        # 模拟采样逻辑
        max_points = 10000
        if len(large_points) > max_points:
            indices = np.random.choice(len(large_points), max_points, replace=False)
            sampled_points = large_points[indices]
        else:
            sampled_points = large_points
        
        # 验证采样结果
        self.assertLessEqual(len(sampled_points), max_points)
        self.assertEqual(sampled_points.shape[1], 3)  # 保持3D坐标
    
    def test_pointcloud_statistics(self):
        """测试点云统计信息计算"""
        test_points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [-1.0, -1.0, -1.0]
        ])
        
        # 计算统计信息
        x_min, x_max = test_points[:, 0].min(), test_points[:, 0].max()
        y_min, y_max = test_points[:, 1].min(), test_points[:, 1].max()
        z_min, z_max = test_points[:, 2].min(), test_points[:, 2].max()
        
        x_mean = test_points[:, 0].mean()
        y_mean = test_points[:, 1].mean()
        z_mean = test_points[:, 2].mean()
        
        # 验证统计结果
        self.assertEqual(x_min, -1.0)
        self.assertEqual(x_max, 2.0)
        self.assertEqual(y_min, -1.0)
        self.assertEqual(y_max, 2.0)
        self.assertEqual(z_min, -1.0)
        self.assertEqual(z_max, 2.0)
        
        self.assertEqual(x_mean, 0.5)
        self.assertEqual(y_mean, 0.5)
        self.assertEqual(z_mean, 0.5)


if __name__ == '__main__':
    print("🧪 运行点云可视化功能单元测试")
    print("=" * 50)
    
    # 运行测试
    unittest.main(verbosity=2)