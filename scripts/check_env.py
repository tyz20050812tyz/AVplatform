#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查和安装脚本
自动检测环境并提供解决方案
"""

import sys
import subprocess
import importlib
import traceback
from pathlib import Path

class DependencyChecker:
    def __init__(self):
        self.python_version = sys.version_info
        self.missing_deps = []
        self.available_deps = []
        
    def check_dependency(self, package_name, import_name=None):
        """检查单个依赖"""
        if import_name is None:
            import_name = package_name
            
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'Unknown')
            self.available_deps.append((package_name, version))
            print(f"✅ {package_name}: {version}")
            return True
        except ImportError:
            self.missing_deps.append(package_name)
            print(f"❌ {package_name}: 未安装")
            return False
        except Exception as e:
            self.missing_deps.append(package_name)
            print(f"⚠️ {package_name}: 导入错误 - {e}")
            return False
    
    def check_all_dependencies(self):
        """检查所有依赖"""
        print("=" * 60)
        print("依赖检查报告")
        print("=" * 60)
        print(f"Python 版本: {sys.version}")
        print(f"Python 路径: {sys.executable}")
        print()
        
        # 定义依赖列表
        dependencies = [
            ('streamlit', 'streamlit'),
            ('pandas', 'pandas'),
            ('plotly', 'plotly'),
            ('Pillow', 'PIL'),
            ('opencv-python', 'cv2'),
            ('PyYAML', 'yaml'),
            ('numpy', 'numpy'),
            ('matplotlib', 'matplotlib'),
            ('laspy', 'laspy'),
            ('open3d', 'open3d'),  # 这个可能失败
        ]
        
        print("检查依赖库...")
        for package, import_name in dependencies:
            self.check_dependency(package, import_name)
        
        print()
        print("=" * 60)
        print("检查结果摘要")
        print("=" * 60)
        print(f"可用依赖: {len(self.available_deps)}")
        print(f"缺失依赖: {len(self.missing_deps)}")
        
        if self.missing_deps:
            print(f"缺失的库: {', '.join(self.missing_deps)}")
        
        return len(self.missing_deps) == 0
    
    def provide_solutions(self):
        """提供解决方案"""
        if not self.missing_deps:
            print("\n🎉 所有依赖都已安装！")
            return
        
        print("\n" + "=" * 60)
        print("解决方案")
        print("=" * 60)
        
        # 特殊处理 Open3D
        if 'open3d' in self.missing_deps:
            print("🔍 Open3D 问题诊断：")
            if self.python_version >= (3, 13):
                print("  ⚠️ Python 3.13 兼容性问题")
                print("  推荐解决方案：")
                print("  1. 降级到 Python 3.11 或 3.12")
                print("  2. 使用 Conda 环境")
                print("  3. 暂时跳过 Open3D（程序会自动降级功能）")
                print()
        
        # 安装命令
        print("📦 安装命令：")
        print("1. 标准安装：")
        print("   pip install -r config/requirements.txt")
        print()
        print("2. 使用国内镜像：")
        print("   pip install -r config/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        print()
        print("3. 逐个安装缺失的库：")
        for dep in self.missing_deps:
            if dep != 'open3d':  # Open3D 特殊处理
                print(f"   pip install {dep}")
        print()
        
        # 环境建议
        if 'open3d' in self.missing_deps:
            print("4. 创建兼容环境（推荐）：")
            print("   # 使用 Python 3.11")
            print("   python3.11 -m venv venv_py311")
            print("   venv_py311\\Scripts\\activate  # Windows")
            print("   # source venv_py311/bin/activate  # Linux/Mac")
            print("   pip install -r config/requirements.txt")
            print()
    
    def test_pointcloud_functionality(self):
        """测试点云功能"""
        print("\n" + "=" * 60)
        print("点云功能测试")
        print("=" * 60)
        
        # 测试基本的点云处理
        try:
            import numpy as np
            print("✅ NumPy 可用 - 基本数学运算支持")
            
            # 创建测试数据
            test_points = np.random.rand(100, 3)
            print(f"✅ 创建测试点云数据: {test_points.shape}")
            
        except Exception as e:
            print(f"❌ 基本功能测试失败: {e}")
            return False
        
        # 测试 Open3D
        try:
            import open3d as o3d
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(test_points)
            print("✅ Open3D 点云创建成功")
            return True
        except Exception as e:
            print(f"⚠️ Open3D 不可用: {e}")
            print("  程序将使用备用方案进行点云可视化")
            return False

def main():
    print("🔍 开始环境检查...")
    
    checker = DependencyChecker()
    
    # 检查依赖
    all_ok = checker.check_all_dependencies()
    
    # 提供解决方案
    checker.provide_solutions()
    
    # 测试点云功能
    checker.test_pointcloud_functionality()
    
    # 总结
    print("\n" + "=" * 60)
    print("环境检查完成")
    print("=" * 60)
    
    if all_ok:
        print("🎉 环境配置完美！可以开始使用所有功能。")
    else:
        print("⚠️ 部分依赖缺失，但程序可以运行（功能可能受限）")
        print("   建议按照上述解决方案安装缺失的依赖")
    
    print(f"\n📍 当前工作目录: {Path.cwd()}")
    print("🚀 要启动应用，请运行: streamlit run src/main.py")

if __name__ == "__main__":
    main()