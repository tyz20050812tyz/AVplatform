#!/usr/bin/env python3
"""
直接测试现有PCD文件的可视化
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
    page_title="现有PCD文件测试",
    page_icon="🧪",
    layout="wide"
)

def main():
    """主函数"""
    st.title("🧪 现有PCD文件可视化测试")
    st.markdown("使用现有的测试PCD文件验证可视化功能是否正常")
    st.markdown("---")
    
    # 导入主应用的功能
    try:
        from main import load_point_cloud, OPEN3D_AVAILABLE
        st.success("✅ 成功导入主应用功能模块")
        st.write(f"🔧 Open3D可用状态: {OPEN3D_AVAILABLE}")
    except Exception as e:
        st.error(f"❌ 导入主应用功能失败: {str(e)}")
        return
    
    # 查找测试PCD文件
    test_pcd_file = "data/temp_pointclouds/sample_sphere.pcd"
    
    st.subheader("📁 测试文件信息")
    if os.path.exists(test_pcd_file):
        file_size = os.path.getsize(test_pcd_file)
        st.success(f"✅ 找到测试文件: {test_pcd_file}")
        st.write(f"📊 文件大小: {file_size:,} bytes")
        
        if st.button("🚀 开始可视化测试", type="primary"):
            st.markdown("---")
            st.subheader("🔄 加载和可视化过程")
            
            # 调用改进的可视化函数
            try:
                from main import visualize_single_pointcloud
                st.write("📞 调用可视化函数...")
                visualize_single_pointcloud(test_pcd_file)
            except Exception as e:
                st.error(f"❌ 可视化函数调用失败: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                
                # 尝试手动实现简化版可视化
                st.markdown("---")
                st.subheader("🔧 手动实现可视化")
                
                try:
                    # 直接加载数据
                    points, colors = load_point_cloud(test_pcd_file)
                    
                    if points is not None:
                        st.success(f"✅ 数据加载成功: {len(points):,} 个点")
                        
                        # 简单可视化
                        max_points = 5000
                        if len(points) > max_points:
                            indices = np.random.choice(len(points), max_points, replace=False)
                            sampled_points = points[indices]
                            sampled_colors = colors[indices] if colors is not None else None
                        else:
                            sampled_points = points
                            sampled_colors = colors
                        
                        # 准备颜色
                        if sampled_colors is not None:
                            normalized_colors = np.clip(sampled_colors, 0, 1)
                            color_values = [f'rgb({int(r*255)},{int(g*255)},{int(b*255)})' 
                                           for r, g, b in normalized_colors]
                            colorscale = None
                        else:
                            color_values = sampled_points[:, 2]
                            colorscale = 'Viridis'
                        
                        # 创建图表
                        fig = go.Figure(data=[go.Scatter3d(
                            x=sampled_points[:, 0],
                            y=sampled_points[:, 1],
                            z=sampled_points[:, 2],
                            mode='markers',
                            marker=dict(
                                size=3,
                                color=color_values,
                                colorscale=colorscale,
                                opacity=0.8
                            )
                        )])
                        
                        fig.update_layout(
                            title='🌌 PCD点云可视化（手动实现）',
                            scene=dict(
                                xaxis_title='X',
                                yaxis_title='Y',
                                zaxis_title='Z',
                                aspectmode='cube'
                            ),
                            height=600
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        st.success("✅ 手动可视化成功！")
                    else:
                        st.error("❌ 数据加载失败")
                        
                except Exception as e2:
                    st.error(f"❌ 手动可视化也失败: {str(e2)}")
                    import traceback
                    st.code(traceback.format_exc())
    else:
        st.error(f"❌ 测试文件不存在: {test_pcd_file}")
        
        # 列出可用文件
        test_dir = "data/temp_pointclouds"
        if os.path.exists(test_dir):
            files = os.listdir(test_dir)
            st.write("**可用文件:**")
            for file in files:
                file_path = os.path.join(test_dir, file)
                if os.path.isfile(file_path):
                    st.write(f"- {file} ({os.path.getsize(file_path):,} bytes)")
        else:
            st.write("测试目录不存在")

if __name__ == "__main__":
    main()