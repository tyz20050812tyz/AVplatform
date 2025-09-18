#!/usr/bin/env python3
"""
PCD文件可视化测试脚本
用于诊断PCD文件可视化问题
"""
import numpy as np
import plotly.graph_objects as go
import os
import sys

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_pcd_loading():
    """测试PCD文件加载功能"""
    print("🧪 开始测试PCD文件加载...")
    
    # 测试Open3D导入
    try:
        import open3d as o3d
        print("✅ Open3D导入成功")
        
        # 测试基本功能
        test_pcd = o3d.geometry.PointCloud()
        print("✅ Open3D基本功能正常")
        
    except ImportError as e:
        print(f"❌ Open3D导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ Open3D功能测试失败: {e}")
        return False
    
    # 测试PCD文件加载
    pcd_file = "data/temp_pointclouds/sample_sphere.pcd"
    
    if not os.path.exists(pcd_file):
        print(f"❌ PCD文件不存在: {pcd_file}")
        return False
    
    try:
        print(f"📁 正在加载PCD文件: {pcd_file}")
        pcd = o3d.io.read_point_cloud(pcd_file)
        
        # 检查点云数据
        points = np.asarray(pcd.points)
        colors = np.asarray(pcd.colors) if pcd.has_colors() else None
        
        print(f"✅ PCD文件加载成功")
        print(f"   📊 点数量: {len(points):,}")
        print(f"   📏 形状: {points.shape}")
        print(f"   🎨 有颜色: {'Yes' if colors is not None else 'No'}")
        
        if len(points) > 0:
            print(f"   📍 X范围: [{points[:, 0].min():.3f}, {points[:, 0].max():.3f}]")
            print(f"   📍 Y范围: [{points[:, 1].min():.3f}, {points[:, 1].max():.3f}]")
            print(f"   📍 Z范围: [{points[:, 2].min():.3f}, {points[:, 2].max():.3f}]")
        
        return True, points, colors
        
    except Exception as e:
        print(f"❌ PCD文件加载失败: {e}")
        return False

def test_plotly_visualization(points, colors=None):
    """测试Plotly可视化功能"""
    print("\n🧪 开始测试Plotly可视化...")
    
    try:
        import plotly.graph_objects as go
        print("✅ Plotly导入成功")
        
        # 采样数据（避免过多点影响性能）
        max_points = 5000
        if len(points) > max_points:
            indices = np.random.choice(len(points), max_points, replace=False)
            sampled_points = points[indices]
            sampled_colors = colors[indices] if colors is not None else None
        else:
            sampled_points = points
            sampled_colors = colors
        
        print(f"📊 使用点数: {len(sampled_points):,}")
        
        # 准备颜色数据
        if sampled_colors is not None:
            color_values = [f'rgb({int(r*255)},{int(g*255)},{int(b*255)})' 
                           for r, g, b in sampled_colors]
            colorscale = None
            print("🎨 使用原始颜色")
        else:
            color_values = sampled_points[:, 2]  # 使用Z值作为颜色
            colorscale = 'Viridis'
            print("🎨 使用高度颜色映射")
        
        # 创建3D散点图
        fig = go.Figure(data=[go.Scatter3d(
            x=sampled_points[:, 0],
            y=sampled_points[:, 1],
            z=sampled_points[:, 2],
            mode='markers',
            marker=dict(
                size=3,
                color=color_values,
                colorscale=colorscale,
                opacity=0.8,
                colorbar=dict(title="高度") if colorscale else None
            ),
            text=[f'X: {x:.2f}<br>Y: {y:.2f}<br>Z: {z:.2f}' 
                  for x, y, z in sampled_points[:100]],  # 只为前100个点添加悬停信息
            hovertemplate='%{text}<extra></extra>'
        )])
        
        # 设置布局
        fig.update_layout(
            title='PCD点云可视化测试',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y', 
                zaxis_title='Z',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                aspectmode='cube'
            ),
            height=600,
            margin=dict(r=0, b=0, l=0, t=40)
        )
        
        # 保存HTML文件
        output_file = "pcd_visualization_test.html"
        fig.write_html(output_file)
        print(f"✅ 可视化图表已保存: {output_file}")
        print(f"📂 请用浏览器打开文件查看可视化效果")
        
        return True
        
    except Exception as e:
        print(f"❌ Plotly可视化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 PCD文件可视化测试开始")
    print("=" * 50)
    
    # 测试PCD文件加载
    result = test_pcd_loading()
    if isinstance(result, tuple):
        success, points, colors = result
        if success:
            # 测试可视化
            test_plotly_visualization(points, colors)
        else:
            print("❌ 无法进行可视化测试，因为PCD加载失败")
    else:
        print("❌ PCD文件加载测试失败")
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")

if __name__ == "__main__":
    main()