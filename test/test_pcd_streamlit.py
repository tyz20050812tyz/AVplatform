#!/usr/bin/env python3
"""
PCD文件可视化测试 - Streamlit应用
用于直接测试PCD文件的可视化功能
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import os
import sys

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 设置页面配置
st.set_page_config(
    page_title="PCD文件可视化测试",
    page_icon="🔬",
    layout="wide"
)

# 初始化Open3D
o3d = None
OPEN3D_AVAILABLE = False

try:
    import open3d as o3d
    test_pcd = o3d.geometry.PointCloud()
    OPEN3D_AVAILABLE = True
    st.success("✅ Open3D导入成功")
except ImportError as e:
    o3d = None
    OPEN3D_AVAILABLE = False
    st.error(f"❌ Open3D库未安装: {e}")
except Exception as e:
    o3d = None
    OPEN3D_AVAILABLE = False
    st.error(f"❌ Open3D库导入失败: {e}")

def load_pcd_file(file_path):
    """加载PCD文件"""
    try:
        st.write(f"🔍 正在加载文件: {file_path}")
        
        if not os.path.exists(file_path):
            st.error(f"❌ 文件不存在: {file_path}")
            return None, None
            
        if OPEN3D_AVAILABLE and o3d is not None:
            pcd = o3d.io.read_point_cloud(file_path)
            
            if len(pcd.points) == 0:
                st.error("❌ PCD文件中没有点云数据")
                return None, None
                
            points = np.asarray(pcd.points)
            colors = np.asarray(pcd.colors) if pcd.has_colors() else None
            
            st.success(f"✅ 加载成功: {len(points):,} 个点，有颜色: {colors is not None}")
            return points, colors
        else:
            st.error("❌ Open3D不可用")
            return None, None
            
    except Exception as e:
        st.error(f"❌ 加载失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None, None

def create_visualization(points, colors=None):
    """创建可视化"""
    try:
        st.write("🎨 正在创建可视化...")
        
        # 采样数据
        max_points = 5000
        if len(points) > max_points:
            indices = np.random.choice(len(points), max_points, replace=False)
            sampled_points = points[indices]
            sampled_colors = colors[indices] if colors is not None else None
        else:
            sampled_points = points
            sampled_colors = colors
            
        st.write(f"📊 使用点数: {len(sampled_points):,}")
        
        # 准备颜色
        if sampled_colors is not None:
            # 确保颜色值在正确范围内
            normalized_colors = np.clip(sampled_colors, 0, 1)
            color_values = [f'rgb({int(r*255)},{int(g*255)},{int(b*255)})' 
                           for r, g, b in normalized_colors]
            colorscale = None
            st.write("🎨 使用原始颜色")
        else:
            color_values = sampled_points[:, 2]  # 使用Z值
            colorscale = 'Viridis'
            st.write("🎨 使用高度颜色映射")
        
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
                  for x, y, z in sampled_points[:min(100, len(sampled_points))]],
            hovertemplate='%{text}<extra></extra>'
        )])
        
        # 设置布局
        fig.update_layout(
            title='🌌 PCD点云可视化测试',
            scene=dict(
                xaxis_title='X轴',
                yaxis_title='Y轴',
                zaxis_title='Z轴',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                aspectmode='cube'
            ),
            height=700,
            margin=dict(r=0, b=0, l=0, t=40)
        )
        
        st.success("✅ 可视化创建成功")
        return fig
        
    except Exception as e:
        st.error(f"❌ 可视化创建失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

def main():
    """主函数"""
    st.title("🔬 PCD文件可视化测试")
    st.markdown("---")
    
    # 文件选择
    st.subheader("📁 选择PCD文件")
    
    # 预设的测试文件
    test_files = []
    test_dir = "data/temp_pointclouds"
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            if file.endswith('.pcd'):
                test_files.append(os.path.join(test_dir, file))
    
    if test_files:
        st.write("**可用的测试文件:**")
        for file in test_files:
            st.write(f"- {file}")
        
        selected_file = st.selectbox(
            "选择要测试的PCD文件:",
            test_files,
            format_func=lambda x: os.path.basename(x)
        )
    else:
        st.warning("⚠️ 未找到测试PCD文件")
        selected_file = st.text_input("请输入PCD文件的完整路径:")
    
    if selected_file and st.button("🚀 加载并可视化", type="primary"):
        st.markdown("---")
        st.subheader("📊 加载结果")
        
        # 加载文件
        points, colors = load_pcd_file(selected_file)
        
        if points is not None:
            # 显示基本信息
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("点数量", f"{len(points):,}")
            with col2:
                st.metric("X范围", f"{points[:, 0].min():.2f}~{points[:, 0].max():.2f}")
            with col3:
                st.metric("Y范围", f"{points[:, 1].min():.2f}~{points[:, 1].max():.2f}")
            with col4:
                st.metric("Z范围", f"{points[:, 2].min():.2f}~{points[:, 2].max():.2f}")
            
            st.markdown("---")
            st.subheader("🌌 3D可视化")
            
            # 创建可视化
            fig = create_visualization(points, colors)
            
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
                st.success("🎉 可视化完成！")
            else:
                st.error("❌ 可视化失败")
        else:
            st.error("❌ 文件加载失败")
    
    # 显示系统信息
    with st.expander("🔧 系统信息"):
        st.write("**依赖状态:**")
        st.write(f"- Open3D可用: {OPEN3D_AVAILABLE}")
        st.write(f"- 当前工作目录: {os.getcwd()}")
        st.write(f"- Python版本: {sys.version}")
        
        if test_files:
            st.write("**测试文件信息:**")
            for file in test_files:
                if os.path.exists(file):
                    size = os.path.getsize(file)
                    st.write(f"- {os.path.basename(file)}: {size:,} bytes")

if __name__ == "__main__":
    main()