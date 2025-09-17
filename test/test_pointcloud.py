#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
点云可视化功能测试脚本
测试点云数据的加载和可视化功能
"""

import numpy as np
import os
import tempfile
from typing import Tuple, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    import open3d as o3d

# 尝试导入 open3d，如果失败则设置标志
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    o3d = None  # type: ignore
    OPEN3D_AVAILABLE = False
    print("⚠️ Open3D 库未安装，部分功能将不可用")

def load_point_cloud_for_test(file_path: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    测试专用的点云加载函数，不依赖Streamlit
    返回: (points, colors) 或 (None, None)
    """
    try:
        if file_path.endswith('.pcd'):
            if OPEN3D_AVAILABLE and o3d is not None:
                pcd = o3d.io.read_point_cloud(file_path)  # type: ignore
                points = np.asarray(pcd.points)  # type: ignore
                colors = np.asarray(pcd.colors) if pcd.has_colors() else None  # type: ignore
                return points, colors
            else:
                print("⚠️ 需要安装 Open3D 库来读取 PCD 文件")
                return None, None
        
        elif file_path.endswith('.las') or file_path.endswith('.laz'):
            try:
                import laspy
                las_file = laspy.read(file_path)
                points = np.vstack([las_file.x, las_file.y, las_file.z]).T
                colors = None
                if hasattr(las_file, 'red') and hasattr(las_file, 'green') and hasattr(las_file, 'blue'):
                    colors = np.vstack([las_file.red, las_file.green, las_file.blue]).T / 65535.0
                return points, colors
            except ImportError:
                print("⚠️ 需要安装 laspy 库来读取 LAS/LAZ 文件")
                return None, None
        
        elif file_path.endswith('.txt') or file_path.endswith('.xyz'):
            # 简单的文本格式点云数据
            data = np.loadtxt(file_path)
            if data.shape[1] >= 3:
                points = data[:, :3]
                colors = data[:, 3:6] if data.shape[1] >= 6 else None
                return points, colors
            else:
                print("⚠️ 文本文件格式不正确，至少需要 3 列（X, Y, Z）")
                return None, None
        
        else:
            print(f"⚠️ 不支持的点云文件格式: {os.path.splitext(file_path)[1]}")
            return None, None
    
    except Exception as e:
        print(f"⚠️ 加载点云文件失败: {str(e)}")
        return None, None

def create_sample_pointcloud() -> List[str]:
    """创建示例点云数据文件"""
    # 创建一个简单的立方体点云
    n_points = 1000
    
    # 生成随机点云数据
    points = []
    
    # 立方体的8个面
    for i in range(n_points):
        x = np.random.uniform(-1, 1)
        y = np.random.uniform(-1, 1)
        z = np.random.uniform(-1, 1)
        
        # 让点云形成一个球体
        if x*x + y*y + z*z <= 1:
            points.append([x, y, z])
    
    points = np.array(points)
    
    # 创建临时文件
    temp_dir = "temp_pointclouds"
    os.makedirs(temp_dir, exist_ok=True)
    
    # 保存为不同格式
    files_created = []
    
    # 1. 保存为 .txt 格式
    txt_file = os.path.join(temp_dir, "sample_sphere.txt")
    np.savetxt(txt_file, points, fmt='%.6f', delimiter=' ')
    files_created.append(txt_file)
    
    # 2. 保存为带颜色的 .txt 格式
    colors = np.random.random((len(points), 3))  # RGB 颜色
    points_with_colors = np.hstack([points, colors])
    txt_color_file = os.path.join(temp_dir, "sample_sphere_colored.txt")
    np.savetxt(txt_color_file, points_with_colors, fmt='%.6f', delimiter=' ')
    files_created.append(txt_color_file)
    
    # 3. 尝试创建 PCD 文件（如果有 open3d）
    if OPEN3D_AVAILABLE and o3d is not None:
        try:
            pcd = o3d.geometry.PointCloud()  # type: ignore
            pcd.points = o3d.utility.Vector3dVector(points)  # type: ignore
            pcd.colors = o3d.utility.Vector3dVector(colors)  # type: ignore
            
            pcd_file = os.path.join(temp_dir, "sample_sphere.pcd")
            o3d.io.write_point_cloud(pcd_file, pcd)  # type: ignore
            files_created.append(pcd_file)
            print("✅ PCD 文件创建成功")
        except Exception as e:
            print(f"⚠️ PCD 文件创建失败: {e}")
    else:
        print("⚠️ Open3D 未安装，跳过 PCD 文件创建")
    
    return files_created

def test_pointcloud_loading():
    """测试点云加载功能"""
    print("🧪 开始测试点云功能...")
    
    # 创建示例文件
    files = create_sample_pointcloud()
    print(f"📁 创建了 {len(files)} 个示例文件:")
    for file in files:
        print(f"  - {file}")
    
    # 测试加载功能
    try:
        for file_path in files:
            print(f"\n🔄 测试加载: {os.path.basename(file_path)}")
            points, colors = load_point_cloud_for_test(file_path)
            
            if points is not None:
                print(f"  ✅ 成功加载 {len(points)} 个点")
                print(f"  📊 点云范围: X[{points[:,0].min():.2f}, {points[:,0].max():.2f}]")
                print(f"  📊 点云范围: Y[{points[:,1].min():.2f}, {points[:,1].max():.2f}]")
                print(f"  📊 点云范围: Z[{points[:,2].min():.2f}, {points[:,2].max():.2f}]")
                print(f"  🎨 有颜色信息: {'Yes' if colors is not None else 'No'}")
            else:
                print(f"  ❌ 加载失败")
    
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    
    print("\n🎯 测试完成！")
    print("💡 要查看完整的可视化功能，请安装 Streamlit:")
    print("   pip install streamlit")
    print("   然后运行: streamlit run main.py")

if __name__ == "__main__":
    test_pointcloud_loading()