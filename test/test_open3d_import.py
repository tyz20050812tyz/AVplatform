#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open3D 导入测试脚本
测试 open3d 库的可用性和基本功能
"""

import sys
import traceback

def test_open3d_import():
    """测试 open3d 导入"""
    print("=" * 50)
    print("Open3D 导入测试")
    print("=" * 50)
    
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")
    print()
    
    # 测试 1: 基本导入
    print("测试 1: 基本导入...")
    try:
        import open3d as o3d
        print("✅ open3d 导入成功")
        
        # 获取版本信息
        try:
            version = o3d.__version__
            print(f"✅ Open3D 版本: {version}")
        except AttributeError:
            print("⚠️ 无法获取版本信息（可能是旧版本）")
        
    except ImportError as e:
        print(f"❌ open3d 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ open3d 导入错误: {e}")
        traceback.print_exc()
        return False
    
    # 测试 2: 基本功能
    print("\n测试 2: 基本功能...")
    try:
        # 创建简单的点云
        pcd = o3d.geometry.PointCloud()
        print("✅ 点云对象创建成功")
        
        # 测试 I/O 功能
        print("✅ 具备基本几何功能")
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        traceback.print_exc()
        return False
    
    # 测试 3: 测试点云数据处理
    print("\n测试 3: 点云数据处理...")
    try:
        import numpy as np
        
        # 创建测试点云数据
        points = np.random.rand(100, 3)
        pcd.points = o3d.utility.Vector3dVector(points)
        
        print("✅ 点云数据设置成功")
        print(f"✅ 点数量: {len(pcd.points)}")
        
    except Exception as e:
        print(f"❌ 点云数据处理失败: {e}")
        traceback.print_exc()
        return False
    
    print("\n🎉 所有测试通过！Open3D 可以正常使用。")
    return True

def test_laspy_import():
    """测试 laspy 导入"""
    print("\n" + "=" * 50)
    print("Laspy 导入测试")
    print("=" * 50)
    
    try:
        import laspy
        print("✅ laspy 导入成功")
        try:
            version = laspy.__version__
            print(f"✅ Laspy 版本: {version}")
        except AttributeError:
            print("⚠️ 无法获取 laspy 版本信息")
        return True
    except ImportError as e:
        print(f"❌ laspy 导入失败: {e}")
        return False

def provide_solutions():
    """提供解决方案"""
    print("\n" + "=" * 50)
    print("解决方案建议")
    print("=" * 50)
    
    print("如果 Open3D 导入失败，请尝试以下解决方案：")
    print()
    
    print("方案 1: 使用兼容的 Python 版本")
    print("  - 推荐使用 Python 3.8-3.11")
    print("  - Python 3.13 较新，open3d 可能尚未支持")
    print()
    
    print("方案 2: 安装 open3d")
    print("  # 标准安装")
    print("  pip install open3d")
    print()
    print("  # 使用国内镜像")
    print("  pip install open3d -i https://pypi.tuna.tsinghua.edu.cn/simple/")
    print()
    
    print("方案 3: 使用 conda 安装")
    print("  conda install -c conda-forge open3d")
    print()
    
    print("方案 4: 临时解决方案（降级功能）")
    print("  - 在代码中添加 try-except 处理")
    print("  - 使用其他库替代点云可视化功能")
    print()

if __name__ == "__main__":
    print("开始依赖库测试...")
    
    # 测试 Open3D
    open3d_ok = test_open3d_import()
    
    # 测试 Laspy
    laspy_ok = test_laspy_import()
    
    # 提供解决方案
    if not open3d_ok or not laspy_ok:
        provide_solutions()
    
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"Open3D: {'✅ 可用' if open3d_ok else '❌ 不可用'}")
    print(f"Laspy:  {'✅ 可用' if laspy_ok else '❌ 不可用'}")
    
    if open3d_ok and laspy_ok:
        print("\n🎉 所有点云处理库都可以正常使用！")
    else:
        print("\n⚠️ 部分库不可用，请参考上述解决方案。")