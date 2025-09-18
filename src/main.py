import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import yaml
import json
import cv2
import numpy as np

# 导入认证模块
from auth import check_authentication, show_auth_page, show_user_info, init_auth_database, can_view_feedback, can_submit_feedback, get_current_user_role

# 导入图片预览模块
from image_preview import show_image_preview_interface
from image_preview_optimized import show_optimized_image_preview_interface

# 导入网络存储模块
from network_storage import network_config, get_storage_path, ensure_storage_directory, copy_to_central_storage

# 导入在线用户管理
get_online_users_count = lambda: 0
track_user_online = None
OnlineUserManager = None
try:
    from online_users import get_online_users_count, track_user_online, OnlineUserManager
    ONLINE_USERS_AVAILABLE = True
except ImportError:
    ONLINE_USERS_AVAILABLE = False

# 初始化变量，确保在任何情况下都有定义
o3d = None
OPEN3D_AVAILABLE = False

try:
    import open3d as o3d
    # 测试基本功能是否可用
    test_pcd = o3d.geometry.PointCloud()
    OPEN3D_AVAILABLE = True
    print("✅ Open3D imported successfully")
except ImportError as e:
    o3d = None
    OPEN3D_AVAILABLE = False
    print(f"⚠️ Open3D库未安装: {e}")
    st.warning("⚠️ Open3D库未安装，点云可视化功能将受限。请参考安装说明。")
except Exception as e:
    o3d = None
    OPEN3D_AVAILABLE = False
    print(f"⚠️ Open3D库导入失败: {e}")
    st.warning(f"⚠️ Open3D库导入失败: {e}。建议使用Python 3.11或3.12版本。")

# 初始化laspy变量
laspy = None
LASPY_AVAILABLE = False

try:
    import laspy
    LASPY_AVAILABLE = True
except ImportError:
    laspy = None
    LASPY_AVAILABLE = False

def load_point_cloud(file_path):
    """加载点云数据"""
    try:
        # 添加调试信息
        st.write(f"🔍 **调试信息**: 正在加载文件 {file_path}")
        st.write(f"🔍 **文件存在**: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            st.error(f"🚫 文件不存在: {file_path}")
            return None, None
            
        if file_path.endswith('.pcd'):
            if OPEN3D_AVAILABLE and o3d is not None:
                st.write(f"🔍 **Open3D状态**: 可用")
                pcd = o3d.io.read_point_cloud(file_path)
                
                # 检查点云是否为空
                if len(pcd.points) == 0:
                    st.error("🚫 PCD文件中没有点云数据")
                    return None, None
                    
                points = np.asarray(pcd.points)
                colors = np.asarray(pcd.colors) if pcd.has_colors() else None
                
                # 添加详细调试信息
                st.write(f"🔍 **加载结果**: 点数={len(points):,}, 有颜色={colors is not None}")
                if colors is not None:
                    st.write(f"🔍 **颜色范围**: R[{colors[:, 0].min():.3f}, {colors[:, 0].max():.3f}], G[{colors[:, 1].min():.3f}, {colors[:, 1].max():.3f}], B[{colors[:, 2].min():.3f}, {colors[:, 2].max():.3f}]")
                
                return points, colors
            else:
                st.error("🚫 需要安装 Open3D 库来读取 PCD 文件")
                return None, None
        
        elif file_path.endswith('.las') or file_path.endswith('.laz'):
            if LASPY_AVAILABLE and laspy is not None:
                las_file = laspy.read(file_path)
                # 将坐标数据转换为numpy数组
                x_coords = np.array(las_file.x)  # type: ignore
                y_coords = np.array(las_file.y)  # type: ignore
                z_coords = np.array(las_file.z)  # type: ignore
                points = np.column_stack([x_coords, y_coords, z_coords])
                colors = None
                if hasattr(las_file, 'red') and hasattr(las_file, 'green') and hasattr(las_file, 'blue'):
                    red_vals = np.array(las_file.red)  # type: ignore
                    green_vals = np.array(las_file.green)  # type: ignore
                    blue_vals = np.array(las_file.blue)  # type: ignore
                    colors = np.column_stack([red_vals, green_vals, blue_vals]) / 65535.0
                return points, colors
            else:
                st.error("🚫 需要安装 laspy 库来读取 LAS/LAZ 文件")
                return None, None
        
        elif file_path.endswith('.txt') or file_path.endswith('.xyz'):
            # 简单的文本格式点云数据
            data = np.loadtxt(file_path)
            if data.shape[1] >= 3:
                points = data[:, :3]
                colors = data[:, 3:6] if data.shape[1] >= 6 else None
                return points, colors
            else:
                st.error("🚫 文本文件格式不正确，至少需要 3 列（X, Y, Z）")
                return None, None
        
        else:
            st.error(f"🚫 不支持的点云文件格式: {os.path.splitext(file_path)[1]}")
            return None, None
    
    except Exception as e:
        st.error(f"🚫 加载点云文件失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None, None

def visualize_single_pointcloud(file_path):
    """单个点云文件可视化"""
    st.write(f"📄 **文件**: {os.path.basename(file_path)}")
    st.write(f"📁 **完整路径**: {file_path}")
    
    with st.spinner("🔄 正在加载点云数据..."):
        points, colors = load_point_cloud(file_path)
    
    if points is None:
        st.error("⚠️ 点云数据加载失败，无法进行可视化")
        return
    
    st.success(f"✅ 点云数据加载成功！共 {len(points):,} 个点")
    
    # 显示点云统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 点数量", f"{len(points):,}")
    with col2:
        st.metric("📎 X范围", f"{points[:, 0].min():.2f} ~ {points[:, 0].max():.2f}")
    with col3:
        st.metric("📎 Y范围", f"{points[:, 1].min():.2f} ~ {points[:, 1].max():.2f}")
    with col4:
        st.metric("📎 Z范围", f"{points[:, 2].min():.2f} ~ {points[:, 2].max():.2f}")
    
    # 可视化参数设置
    st.subheader("⚙️ 可视化参数")
    col1, col2 = st.columns(2)
    
    with col1:
        # 采样参数
        max_points = st.slider("🎯 最大显示点数", 1000, min(100000, len(points)), 
                               min(10000, len(points)), 
                               help="为了性能考虑，建议不超过 100,000 个点")
        
        # 点大小
        point_size = st.slider("🔴 点大小", 1, 10, 3)
        
    with col2:
        # 颜色映射方式
        color_mode = st.selectbox(
            "🎨 颜色映射",
            ["高度 (Z)", "原始颜色", "均匀颜色"],
            help="选择点云的颜色显示方式"
        )
        
        # 视角选择
        view_mode = st.selectbox(
            "👁️ 视角模式",
            ["3D 视角", "从上向下 (XY)", "从前向后 (XZ)", "从左向右 (YZ)"]
        )
    
    # 采样点云数据
    st.write(f"🔍 **采样信息**: 原始点数={len(points):,}, 目标点数={max_points:,}")
    
    if len(points) > max_points:
        indices = np.random.choice(len(points), max_points, replace=False)
        sampled_points = points[indices]
        sampled_colors = colors[indices] if colors is not None else None
        st.write(f"⚙️ 已采样到 {len(sampled_points):,} 个点")
    else:
        sampled_points = points
        sampled_colors = colors
        st.write(f"⚙️ 使用全部 {len(sampled_points):,} 个点")
    
    # 准备颜色数据
    st.write(f"🔍 **颜色处理**: 选择模式={color_mode}, 有原始颜色={sampled_colors is not None}")
    
    if color_mode == "高度 (Z)":
        color_values = sampled_points[:, 2]
        colorscale = 'Viridis'
        st.write("🎨 使用Z轴高度作为颜色")
    elif color_mode == "原始颜色" and sampled_colors is not None:
        # 确保颜色值在正确范围内
        normalized_colors = np.clip(sampled_colors, 0, 1)
        color_values = [f'rgb({int(r*255)},{int(g*255)},{int(b*255)})' 
                       for r, g, b in normalized_colors]
        colorscale = None
        st.write(f"🎨 使用原始颜色，颜色范围: R[{normalized_colors[:, 0].min():.3f}, {normalized_colors[:, 0].max():.3f}]")
    else:
        color_values = 'blue'
        colorscale = None
        st.write("🎨 使用均匀蓝色")
    
    # 创建 3D 散点图
    st.write("🔍 **正在创建3D散点图...**")
    
    try:
        fig = go.Figure(data=[go.Scatter3d(
            x=sampled_points[:, 0],
            y=sampled_points[:, 1],
            z=sampled_points[:, 2],
            mode='markers',
            marker=dict(
                size=point_size,
                color=color_values,
                colorscale=colorscale,
                opacity=0.8,
                colorbar=dict(title="高度") if color_mode == "高度 (Z)" else None
            ),
            text=[f'X: {x:.2f}<br>Y: {y:.2f}<br>Z: {z:.2f}' 
                  for x, y, z in sampled_points[:100]],  # 只为前100个点添加悬停信息
            hovertemplate='%{text}<extra></extra>'
        )])
        
        st.write("✅ 3D散点图创建成功")
        
    except Exception as e:
        st.error(f"⚠️ 创建3D散点图失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    # 设置布局
    camera_settings = {
        "3D 视角": dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        "从上向下 (XY)": dict(eye=dict(x=0, y=0, z=3)),
        "从前向后 (XZ)": dict(eye=dict(x=0, y=3, z=0)),
        "从左向右 (YZ)": dict(eye=dict(x=3, y=0, z=0))
    }
    
    # 安全获取camera设置，确保键存在
    default_camera = camera_settings["3D 视角"]
    # 确保view_mode不为None，如果为None则使用默认值
    view_mode_safe = view_mode if view_mode is not None else "3D 视角"
    selected_camera = camera_settings.get(view_mode_safe, default_camera)
    
    try:
        fig.update_layout(
            title=f'🌌 点云可视化: {os.path.basename(file_path)}',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                camera=selected_camera,
                aspectmode='cube'
            ),
            height=600,
            margin=dict(r=0, b=0, l=0, t=40)
        )
        
        st.write("✅ 布局设置成功")
        
        # 显示图表
        st.write("🔍 **正在渲染可视化图表...**")
        # st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig, use_container_width=True, height=800, config={'staticPlot': False})
        st.success("✨ 点云可视化完成！")
        
    except Exception as e:
        st.error(f"⚠️ 布局设置或渲染失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    # 显示详细统计信息
    with st.expander("📊 详细统计信息"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**基本信息**")
            st.write(f"- 原始点数: {len(points):,}")
            st.write(f"- 显示点数: {len(sampled_points):,}")
            st.write(f"- 文件大小: {os.path.getsize(file_path):,} bytes")
            st.write(f"- 有无颜色: {'Yes' if colors is not None else 'No'}")
        
        with col2:
            st.write("**坐标统计**")
            for i, axis in enumerate(['X', 'Y', 'Z']):
                st.write(f"- {axis} 轴: [{points[:, i].min():.3f}, {points[:, i].max():.3f}]")
                st.write(f"  平均值: {points[:, i].mean():.3f}, 标准差: {points[:, i].std():.3f}")

def visualize_multiple_pointclouds(file_paths):
    """多个点云文件可视化"""
    st.subheader(f"📋 多点云文件对比 ({len(file_paths)} 个文件)")
    
    # 显示模式选择
    display_mode = st.radio(
        "📊 显示模式",
        ["并排显示", "叠加显示", "对比分析"],
        horizontal=True
    )
    
    if display_mode == "并排显示":
        # 选择要显示的文件
        selected_files = st.multiselect(
            "📁 选择要显示的文件",
            file_paths,
            default=file_paths[:2],  # 默认选择前两个
            format_func=lambda x: os.path.basename(x)
        )
        
        if selected_files:
            cols = st.columns(min(len(selected_files), 2))
            for i, file_path in enumerate(selected_files):
                with cols[i % 2]:
                    st.write(f"**{os.path.basename(file_path)}**")
                    with st.spinner(f"加载 {os.path.basename(file_path)}..."):
                        points, colors = load_point_cloud(file_path)
                    
                    if points is not None:
                        # 简化版可视化
                        max_points = 5000  # 并排显示时减少点数
                        if len(points) > max_points:
                            indices = np.random.choice(len(points), max_points, replace=False)
                            sampled_points = points[indices]
                        else:
                            sampled_points = points
                        
                        fig = go.Figure(data=[go.Scatter3d(
                            x=sampled_points[:, 0],
                            y=sampled_points[:, 1],
                            z=sampled_points[:, 2],
                            mode='markers',
                            marker=dict(
                                size=2,
                                color=sampled_points[:, 2],
                                colorscale='Viridis',
                                opacity=0.7
                            )
                        )])
                        
                        fig.update_layout(
                            title=os.path.basename(file_path),
                            scene=dict(
                                xaxis_title='X',
                                yaxis_title='Y',
                                zaxis_title='Z',
                                aspectmode='cube'
                            ),
                            height=400,
                            margin=dict(r=0, b=0, l=0, t=40)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        st.metric("📊 点数", f"{len(points):,}")
    
    elif display_mode == "叠加显示":
        # 在一个图中显示多个点云
        selected_files = st.multiselect(
            "📁 选择要叠加显示的文件",
            file_paths,
            default=file_paths[:3],  # 默认选择前三个
            format_func=lambda x: os.path.basename(x)
        )
        
        if selected_files:
            max_points_per_file = st.slider(
                "🎯 每个文件最大点数", 
                100, 5000, 2000,
                help="为了性能考虑，限制每个文件的显示点数"
            )
            
            fig = go.Figure()
            colors_palette = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
            
            total_points = 0
            for i, file_path in enumerate(selected_files):
                with st.spinner(f"加载 {os.path.basename(file_path)}..."):
                    points, colors = load_point_cloud(file_path)
                
                if points is not None:
                    # 采样
                    if len(points) > max_points_per_file:
                        indices = np.random.choice(len(points), max_points_per_file, replace=False)
                        sampled_points = points[indices]
                    else:
                        sampled_points = points
                    
                    # 为不同文件使用不同颜色
                    color = colors_palette[i % len(colors_palette)]
                    
                    fig.add_trace(go.Scatter3d(
                        x=sampled_points[:, 0],
                        y=sampled_points[:, 1],
                        z=sampled_points[:, 2],
                        mode='markers',
                        marker=dict(
                            size=2,
                            color=color,
                            opacity=0.6
                        ),
                        name=os.path.basename(file_path)
                    ))
                    
                    total_points += len(sampled_points)
            
            fig.update_layout(
                title=f'🌌 多点云叠加显示 (总计 {total_points:,} 个点)',
                scene=dict(
                    xaxis_title='X',
                    yaxis_title='Y',
                    zaxis_title='Z',
                    aspectmode='cube'
                ),
                height=700,
                margin=dict(r=0, b=0, l=0, t=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    else:  # 对比分析
        st.subheader("📊 点云数据对比分析")
        
        # 加载所有点云的统计信息
        stats_data = []
        for file_path in file_paths:
            with st.spinner(f"分析 {os.path.basename(file_path)}..."):
                points, colors = load_point_cloud(file_path)
            
            if points is not None:
                stats = {
                    '文件名': os.path.basename(file_path),
                    '点数量': len(points),
                    'X范围': f"{points[:, 0].min():.2f} ~ {points[:, 0].max():.2f}",
                    'Y范围': f"{points[:, 1].min():.2f} ~ {points[:, 1].max():.2f}",
                    'Z范围': f"{points[:, 2].min():.2f} ~ {points[:, 2].max():.2f}",
                    'X平均': f"{points[:, 0].mean():.3f}",
                    'Y平均': f"{points[:, 1].mean():.3f}",
                    'Z平均': f"{points[:, 2].mean():.3f}",
                    '文件大小(MB)': f"{os.path.getsize(file_path) / 1024 / 1024:.2f}",
                    '有无颜色': 'Yes' if colors is not None else 'No'
                }
                stats_data.append(stats)
        
        if stats_data:
            # 显示对比表格
            df_stats = pd.DataFrame(stats_data)
            st.dataframe(df_stats, use_container_width=True)
            
            # 点数量对比图
            col1, col2 = st.columns(2)
            
            with col1:
                fig_points = px.bar(
                    df_stats, 
                    x='文件名', 
                    y='点数量',
                    title='📊 点数量对比'
                )
                fig_points.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig_points, use_container_width=True)
            
            with col2:
                # 文件大小对比
                df_stats['文件大小数值'] = df_stats['文件大小(MB)'].astype(float)
                fig_size = px.bar(
                    df_stats, 
                    x='文件名', 
                    y='文件大小数值',
                    title='💾 文件大小对比 (MB)'
                )
                fig_size.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig_size, use_container_width=True)

def init_database():
    """初始化SQLite数据库"""
    # 获取数据库路径
    db_path = network_config.get_database_path()
    ensure_storage_directory(os.path.dirname(db_path))
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 创建数据集表
    c.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            upload_time TEXT,
            file_count INTEGER DEFAULT 0,
            file_paths TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    """初始化SQLite数据库"""
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    # 创建数据集表
    c.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            upload_time TEXT,
            file_count INTEGER DEFAULT 0,
            file_paths TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def show_homepage():
    """显示首页"""
    st.title("🚗 无人驾驶数据管理平台")
    
    # 平台介绍
    st.markdown("""
    ## 欢迎使用无人驾驶数据管理平台 
    
    这是一个专门用于管理和共享无人驾驶相关多模态传感器数据的平台，支持：
    
    ### 🎯 核心功能
    - 📤 **数据上传**: 支持激光雷达、摄像头、GPS、IMU等传感器数据
    - 📁 **数据浏览**: 便捷的数据集管理和文件浏览
    - 📈 **数据可视化**: 直观的数据可视化和分析工具
    
    ### 📊 支持的数据格式
    - **ROS数据**: .bag
    - **点云数据**: .pcd
    - **图像数据**: .png, .jpg
    - **配置文件**: .yaml, .yml
    - **传感器数据**: .csv, .json
    
    ### 🎯 目标用户
    - 自动驾驶研究人员
    - 高校学生和教师  
    - 算法工程师
    - 数据科学家
    """)
    
    # 统计信息
    db_path = network_config.get_database_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM datasets")
    dataset_count = c.fetchone()[0]
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("数据集总数", dataset_count)
    with col2:
        st.metric("支持格式", "6种")
    with col3:
        st.metric("在线用户", "1")

def show_upload_page():
    """显示数据上传页面"""
    st.title("📤 数据上传")
    
    # 数据集信息
    dataset_name = st.text_input("数据集名称", placeholder="请输入数据集名称")
    dataset_desc = st.text_area("数据集描述", placeholder="请描述数据集的内容和用途")
    
    # 文件上传
    uploaded_files = st.file_uploader(
        "选择文件",
        accept_multiple_files=True,
        type=['bag', 'pcd', 'png', 'jpg', 'yaml', 'yml', 'csv', 'json'],
        help="支持的文件格式：.bag, .pcd, .png, .jpg, .yaml, .yml, .csv, .json"
    )
    
    if uploaded_files:
        st.subheader("文件预览")
        for file in uploaded_files:
            with st.expander(f"📄 {file.name}"):
                st.write(f"文件大小: {file.size} bytes")
                st.write(f"文件类型: {file.type}")
    
    if st.button("上传数据集", type="primary") and dataset_name and uploaded_files:
        with st.spinner("正在上传文件..."):
            try:
                # 创建存储目录
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                dataset_dir = os.path.join(network_config.get_datasets_path(), f"{dataset_name}_{timestamp}")
                ensure_storage_directory(dataset_dir)
                
                # 保存文件
                file_paths = []
                for file in uploaded_files:
                    file_path = os.path.join(dataset_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getvalue())
                    file_paths.append(file_path)
                
                # 保存到数据库
                db_path = network_config.get_database_path()
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO datasets (name, description, upload_time, file_count, file_paths)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    dataset_name,
                    dataset_desc,
                    datetime.now().isoformat(),
                    len(file_paths),
                    ",".join(file_paths)
                ))
                conn.commit()
                conn.close()
                
                st.success(f"✅ 上传成功！共{len(file_paths)}个文件")
                st.balloons()
                
            except Exception as e:
                st.error(f"上传失败: {str(e)}")

def show_browse_page():
    """显示数据浏览页面"""
    st.title("📁 数据浏览")
    
    # 从数据库获取数据集列表
    db_path = network_config.get_database_path()
    conn = sqlite3.connect(db_path)
    datasets = pd.read_sql_query("SELECT * FROM datasets ORDER BY upload_time DESC", conn)
    conn.close()
    
    if len(datasets) == 0:
        st.info("暂无数据集，请先上传数据")
        return
    
    # 搜索功能
    search_term = st.text_input("🔍 搜索数据集", placeholder="输入数据集名称进行搜索")
    if search_term:
        datasets = datasets[datasets['name'].str.contains(search_term, case=False, na=False)]
    
    # 显示数据集列表
    for _, dataset in datasets.iterrows():
        with st.expander(f"📊 {dataset['name']} ({dataset['file_count']} 个文件)"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**描述**: {dataset['description'] or '无描述'}")
                st.write(f"**上传时间**: {pd.to_datetime(dataset['upload_time']).strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 显示文件列表
                file_paths_str = dataset['file_paths']
                if file_paths_str is not None and str(file_paths_str).strip():
                    file_paths = str(file_paths_str).split(",")
                    st.write("**文件列表**:")
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            st.write(f"  - {os.path.basename(file_path)} ({file_size} bytes)")
                        else:
                            st.write(f"  - {os.path.basename(file_path)} (文件不存在)")
            
            with col2:
                if st.button(f"查看详情", key=f"view_{dataset['id']}"):
                    st.session_state.selected_dataset_id = dataset['id']
                if st.button(f"删除数据集", key=f"delete_{dataset['id']}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_{dataset['id']}", False):
                        delete_dataset(dataset['id'])
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{dataset['id']}"] = True
                        st.warning("再次点击确认删除")

def show_visualization_page():
    """显示数据可视化页面"""
    st.title("📈 数据可视化")
    
    # 获取数据集列表
    db_path = network_config.get_database_path()
    conn = sqlite3.connect(db_path)
    datasets = pd.read_sql_query("SELECT id, name FROM datasets", conn)
    conn.close()
    
    if len(datasets) == 0:
        st.info("暂无数据集可视化")
        return
    
    # 选择数据集
    dataset_options = dict(zip(datasets['id'], datasets['name']))
    selected_dataset = st.selectbox(
        "选择数据集",
        options=list(dataset_options.keys()),
        format_func=lambda x: dataset_options[x]
    )
    
    if selected_dataset:
        # 获取选中数据集的文件
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT file_paths FROM datasets WHERE id = ?", (selected_dataset,))
        result = c.fetchone()
        conn.close()
        
        if result and result[0]:
            file_paths = str(result[0]).split(",")
            
            # 按文件类型分类
            image_files = [f for f in file_paths if f.endswith(('.png', '.jpg', '.jpeg'))]
            csv_files = [f for f in file_paths if f.endswith('.csv')]
            yaml_files = [f for f in file_paths if f.endswith(('.yaml', '.yml'))]
            json_files = [f for f in file_paths if f.endswith('.json')]
            pcd_files = [f for f in file_paths if f.endswith('.pcd')]
            bag_files = [f for f in file_paths if f.endswith('.bag')]
            
            # 显示图像数据
            if image_files:
                st.subheader("🖼️ 图像数据")
                
                # 性能模式选择
                if len(image_files) > 20:  # 大于20张图片时提供选择
                    performance_mode = st.radio(
                        "🚀 选择模式",
                        ["性能优化模式", "标准模式"],
                        index=0,  # 默认优化模式
                        horizontal=True,
                        help=f"检测到{len(image_files)}张图片，建议使用性能优化模式"
                    )
                    
                    if performance_mode == "性能优化模式":
                        show_optimized_image_preview_interface(image_files)
                    else:
                        show_image_preview_interface(image_files)
                else:
                    # 少量图片直接使用标准模式
                    show_image_preview_interface(image_files)
            
            # 显示CSV数据
            if csv_files:
                st.subheader("📊 数据文件")
                for csv_file in csv_files:
                    if os.path.exists(csv_file):
                        try:
                            df = pd.read_csv(csv_file)
                            st.write(f"**文件**: {os.path.basename(csv_file)}")
                            st.write(f"**数据形状**: {df.shape}")
                            st.dataframe(df.head(100))  # 只显示前100行
                            
                            # 简单统计图表
                            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                            if len(numeric_cols) >= 2:
                                col1, col2 = st.columns(2)
                                with col1:
                                    fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1])
                                    st.plotly_chart(fig, use_container_width=True)
                                with col2:
                                    fig = px.histogram(df, x=numeric_cols[0])
                                    st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"无法读取CSV文件: {e}")
            
            # 显示YAML配置
            if yaml_files:
                st.subheader("⚙️ 配置文件")
                for yaml_file in yaml_files:
                    if os.path.exists(yaml_file):
                        try:
                            with open(yaml_file, 'r', encoding='utf-8') as f:
                                yaml_data = yaml.safe_load(f)
                            st.write(f"**文件**: {os.path.basename(yaml_file)}")
                            st.json(yaml_data)
                        except Exception as e:
                            st.error(f"无法读取YAML文件: {e}")
            
            # 显示JSON数据
            if json_files:
                st.subheader("📋 JSON数据")
                for json_file in json_files:
                    if os.path.exists(json_file):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                            st.write(f"**文件**: {os.path.basename(json_file)}")
                            st.json(json_data)
                        except Exception as e:
                            st.error(f"无法读取JSON文件: {e}")
            
            # 显示点云数据
            if pcd_files:
                st.subheader("📡 点云数据")
                
                # 检查PCD文件是否实际存在
                valid_pcd_files = []
                for pcd_file in pcd_files:
                    if os.path.exists(pcd_file):
                        valid_pcd_files.append(pcd_file)
                        st.write(f"✅ 找到PCD文件: {os.path.basename(pcd_file)} ({os.path.getsize(pcd_file):,} bytes)")
                    else:
                        st.write(f"❌ PCD文件不存在: {os.path.basename(pcd_file)}")
                
                if not valid_pcd_files:
                    st.error("⚠️ 没有找到有效的PCD文件")
                    return
                
                # 可视化模式选择
                if len(valid_pcd_files) == 1:
                    # 单个文件直接可视化
                    st.write("🎯 自动选择单个PCD文件进行可视化")
                    visualize_single_pointcloud(valid_pcd_files[0])
                else:
                    # 多个文件提供选择
                    viz_mode = st.radio(
                        "🎨 可视化模式",
                        ["单个文件", "多文件对比"],
                        key=f"viz_mode_{selected_dataset}",
                        horizontal=True
                    )
                    
                    if viz_mode == "单个文件":
                        # 选择单个文件进行详细可视化
                        selected_pcd = st.selectbox(
                            "📁 选择点云文件",
                            valid_pcd_files,
                            format_func=lambda x: f"{os.path.basename(x)} ({os.path.getsize(x):,} bytes)",
                            key=f"pcd_select_{selected_dataset}"
                        )
                        if selected_pcd:
                            visualize_single_pointcloud(selected_pcd)
                    else:
                        # 多文件对比可视化
                        visualize_multiple_pointclouds(valid_pcd_files)
            
            if bag_files:
                st.subheader("🎒 ROS Bag文件")
                for bag_file in bag_files:
                    st.write(f"**文件**: {os.path.basename(bag_file)}")
                    st.info("ROS Bag数据解析功能开发中...")

def delete_dataset(dataset_id):
    """删除数据集"""
    try:
        # 获取文件路径
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT file_paths FROM datasets WHERE id = ?", (dataset_id,))
        result = c.fetchone()
        
        if result and result[0]:
            file_paths = str(result[0]).split(",")
            # 删除文件和目录
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # 删除目录（如果为空）
            if file_paths:
                dataset_dir = os.path.dirname(file_paths[0])
                if os.path.exists(dataset_dir) and not os.listdir(dataset_dir):
                    os.rmdir(dataset_dir)
        
        # 从数据库删除记录
        c.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        conn.commit()
        conn.close()
        
        st.success("数据集删除成功")
    except Exception as e:
        st.error(f"删除失败: {str(e)}")

def show_documentation_page():
    """显示使用文档页面"""
    st.title("📚 使用文档")
    
    # 文档导航
    doc_tab = st.selectbox(
        "选择文档类型",
        ["平台简介", "功能指南", "性能优化", "发布说明"]
    )
    
    if doc_tab == "平台简介":
        st.markdown("""
        ## 🚗 平台简介
        
        无人驾驶数据管理平台是一个专业的多模态数据管理系统。
        
        ### 主要特性
        - 📁 **数据管理**: 支持多种传感器数据格式
        - 🖼️ **图片预览**: 智能时间轴浏览，支持多种时间戳格式
        - 🌌 **点云可视化**: 高性能3D点云显示和分析
        - 📊 **数据分析**: 丰富的可视化和统计功能
        
        ### 支持格式
        - **点云数据**: .pcd, .las/.laz, .txt/.xyz
        - **图像数据**: .png, .jpg, .jpeg
        - **配置文件**: .yaml, .yml, .json
        - **数据文件**: .csv
        - **ROS数据**: .bag
        """)
    
    elif doc_tab == "功能指南":
        st.markdown("""
        ## 🗺️ 功能指南
        
        ### 📁 数据上传
        1. 点击"数据上传"菜单
        2. 输入数据集名称和描述
        3. 选择要上传的文件
        4. 点击"上传数据集"
        
        ### 🔍 数据浏览
        1. 在"数据浏览"页面查看所有数据集
        2. 使用搜索功能查找特定数据集
        3. 点击"查看详情"查看文件列表
        
        ### 🖼️ 图片预览
        1. 在"数据可视化"中选择包含图片的数据集
        2. 选择预览模式：时间轴/网格/单张
        3. 使用拖动滑块或导航按钮浏览
        
        ### 🌌 点云可视化
        1. 选择包含.pcd文件的数据集
        2. 调整可视化参数（点大小、颜色模式等）
        3. 选择不同的视角模式
        """)
    
    elif doc_tab == "性能优化":
        # 读取性能优化指南
        perf_guide_path = "docs/performance_optimization_guide.md"
        if os.path.exists(perf_guide_path):
            with open(perf_guide_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.markdown(content)
        else:
            st.info("性能优化指南文档未找到")
    
    else:  # 发布说明
        # 读取发布说明
        release_notes_path = "RELEASE_NOTES.md"
        if os.path.exists(release_notes_path):
            with open(release_notes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.markdown(content)
        else:
            st.info("发布说明文档未找到")


def show_feature_request_page():
    """显示功能建议页面"""
    st.title("💡 功能建议")
    
    # 获取当前用户信息
    current_user = st.session_state.get('user', {})
    username = current_user.get('username', '')
    user_role = get_current_user_role()
    
    st.markdown("""
    欢迎提出您的功能建议！您的反馈将帮助我们不断改进平台。
    """)
    
    # 权限提示
    if user_role == 'super_admin':
        st.info("🔑 您是超级管理员，可以查看和管理所有功能建议")
    else:
        st.info("📝 您可以提交功能建议，但仅超级管理员可以查看具体内容")
    
    # 功能建议表单
    with st.form("feature_request_form"):
        st.subheader("提交功能建议")
        
        # 基本信息
        user_name = st.text_input("您的姓名（可选）", value=username)
        user_email = st.text_input("联系邮箱（可选）")
        
        # 功能分类
        feature_category = st.selectbox(
            "功能分类",
            ["数据管理", "可视化功能", "用户交互", "性能优化", "其他"]
        )
        
        # 功能描述
        feature_title = st.text_input("功能标题", placeholder="简要描述您的功能建议")
        feature_description = st.text_area(
            "详细描述",
            placeholder="请详细描述您希望的功能...",
            height=100
        )
        
        # 使用场景
        use_case = st.text_area(
            "使用场景",
            placeholder="请描述该功能的具体使用场景...",
            height=80
        )
        
        # 优先级
        priority = st.selectbox(
            "优先级",
            ["低", "中", "高", "紧急"]
        )
        
        # 提交按钮
        submitted = st.form_submit_button("📨 提交建议")
        
        if submitted and feature_title and feature_description:
            if can_submit_feedback(username):
                # 保存功能建议
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                suggestion = {
                    'timestamp': timestamp,
                    'user_name': user_name or username or '匿名用户',
                    'user_email': user_email,
                    'category': feature_category,
                    'title': feature_title,
                    'description': feature_description,
                    'use_case': use_case,
                    'priority': priority
                }
                
                # 尝试保存到文件
                try:
                    data_dir = network_config.get_data_path()
                    suggestions_file = os.path.join(data_dir, "feature_suggestions.json")
                    ensure_storage_directory(data_dir)
                    
                    # 读取现有建议
                    if os.path.exists(suggestions_file):
                        with open(suggestions_file, 'r', encoding='utf-8') as f:
                            suggestions = json.load(f)
                    else:
                        suggestions = []
                    
                    suggestions.append(suggestion)
                    
                    # 保存建议
                    with open(suggestions_file, 'w', encoding='utf-8') as f:
                        json.dump(suggestions, f, ensure_ascii=False, indent=2)
                    
                    st.success("🎉 功能建议提交成功！感谢您的反馈。")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"保存失败: {e}")
            else:
                st.error("您没有权限提交功能建议")
    
    # 显示已有建议（仅超级管理员可见）
    if can_view_feedback(username):
        if st.expander("📄 查看已有建议（仅超级管理员可见）"):
            try:
                data_dir = network_config.get_data_path()
                suggestions_file = os.path.join(data_dir, "feature_suggestions.json")
                if os.path.exists(suggestions_file):
                    with open(suggestions_file, 'r', encoding='utf-8') as f:
                        suggestions = json.load(f)
                    
                    if suggestions:
                        st.write(f"📊 **总计**: {len(suggestions)} 条功能建议")
                        
                        # 按类别筛选
                        categories = list(set([s['category'] for s in suggestions]))
                        selected_category = st.selectbox("筛选类别", ["全部"] + categories)
                        
                        # 按优先级筛选
                        priorities = list(set([s['priority'] for s in suggestions]))
                        selected_priority = st.selectbox("筛选优先级", ["全部"] + priorities)
                        
                        # 筛选建议
                        filtered_suggestions = suggestions
                        if selected_category != "全部":
                            filtered_suggestions = [s for s in filtered_suggestions if s['category'] == selected_category]
                        if selected_priority != "全部":
                            filtered_suggestions = [s for s in filtered_suggestions if s['priority'] == selected_priority]
                        
                        # 显示建议
                        for i, suggestion in enumerate(reversed(filtered_suggestions[-20:])):
                            with st.container():
                                priority_icon = {"低": "🔵", "中": "🟡", "高": "🟠", "紧急": "🔴"}.get(
                                    suggestion['priority'], "🟡")
                                st.write(f"{priority_icon} **{suggestion['title']}** - {suggestion['category']}")
                                st.write(f"提交时间: {suggestion['timestamp']} | 提交者: {suggestion['user_name']}")
                                st.write(suggestion['description'])
                                if suggestion['use_case']:
                                    st.write(f"使用场景: {suggestion['use_case']}")
                                if suggestion.get('user_email'):
                                    st.write(f"联系邮箱: {suggestion['user_email']}")
                                st.markdown("---")
                    else:
                        st.info("还没有功能建议")
                else:
                    st.info("还没有功能建议")
            except Exception as e:
                st.error(f"读取建议失败: {e}")
    else:
        st.info("🔒 仅超级管理员可以查看已提交的功能建议")


def show_bug_report_page():
    """显示问题反馈页面"""
    st.title("🐛 问题反馈")
    
    # 获取当前用户信息
    current_user = st.session_state.get('user', {})
    username = current_user.get('username', '')
    user_role = get_current_user_role()
    
    st.markdown("""
    遇到问题了吗？请告诉我们！您的反馈将帮助我们及时修复问题。
    """)
    
    # 权限提示
    if user_role == 'super_admin':
        st.info("🔑 您是超级管理员，可以查看和管理所有问题反馈")
    else:
        st.info("📝 您可以提交问题反馈，但仅超级管理员可以查看具体内容")
    
    # 问题反馈表单
    with st.form("bug_report_form"):
        st.subheader("提交问题报告")
        
        # 基本信息
        user_name = st.text_input("您的姓名（可选）", value=username)
        user_email = st.text_input("联系邮箱（可选）")
        
        # 问题分类
        bug_category = st.selectbox(
            "问题类型",
            ["功能错误", "性能问题", "界面问题", "数据问题", "其他"]
        )
        
        # 问题描述
        bug_title = st.text_input("问题标题", placeholder="简要描述问题")
        bug_description = st.text_area(
            "问题描述",
            placeholder="请详细描述您遇到的问题...",
            height=100
        )
        
        # 复现步骤
        reproduction_steps = st.text_area(
            "复现步骤",
            placeholder="请描述如何复现该问题...",
            height=80
        )
        
        # 环境信息
        col1, col2 = st.columns(2)
        with col1:
            browser = st.selectbox("浏览器", ["Chrome", "Firefox", "Safari", "Edge", "其他"])
        with col2:
            os_type = st.selectbox("操作系统", ["Windows", "macOS", "Linux", "其他"])
        
        # 严重程度
        severity = st.selectbox(
            "严重程度",
            ["轻微", "一般", "严重", "致命"]
        )
        
        # 提交按钮
        submitted = st.form_submit_button("📨 提交问题报告")
        
        if submitted and bug_title and bug_description:
            if can_submit_feedback(username):
                # 保存问题报告
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                bug_report = {
                    'timestamp': timestamp,
                    'user_name': user_name or username or '匿名用户',
                    'user_email': user_email,
                    'category': bug_category,
                    'title': bug_title,
                    'description': bug_description,
                    'reproduction_steps': reproduction_steps,
                    'browser': browser,
                    'os': os_type,
                    'severity': severity
                }
                
                # 尝试保存到文件
                try:
                    data_dir = network_config.get_data_path()
                    bugs_file = os.path.join(data_dir, "bug_reports.json")
                    ensure_storage_directory(data_dir)
                    
                    # 读取现有报告
                    if os.path.exists(bugs_file):
                        with open(bugs_file, 'r', encoding='utf-8') as f:
                            bug_reports = json.load(f)
                    else:
                        bug_reports = []
                    
                    bug_reports.append(bug_report)
                    
                    # 保存报告
                    with open(bugs_file, 'w', encoding='utf-8') as f:
                        json.dump(bug_reports, f, ensure_ascii=False, indent=2)
                    
                    st.success("🎉 问题报告提交成功！我们将尽快处理。")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"保存失败: {e}")
            else:
                st.error("您没有权限提交问题反馈")
    
    # 显示已有问题报告（仅超级管理员可见）
    if can_view_feedback(username):
        if st.expander("📄 查看已有问题报告（仅超级管理员可见）"):
            try:
                data_dir = network_config.get_data_path()
                bugs_file = os.path.join(data_dir, "bug_reports.json")
                if os.path.exists(bugs_file):
                    with open(bugs_file, 'r', encoding='utf-8') as f:
                        bug_reports = json.load(f)
                    
                    if bug_reports:
                        st.write(f"📊 **总计**: {len(bug_reports)} 个问题报告")
                        
                        # 按类型筛选
                        categories = list(set([r['category'] for r in bug_reports]))
                        selected_category = st.selectbox("筛选问题类型", ["全部"] + categories, key="bug_category_filter")
                        
                        # 按严重程度筛选
                        severities = list(set([r['severity'] for r in bug_reports]))
                        selected_severity = st.selectbox("筛选严重程度", ["全部"] + severities, key="bug_severity_filter")
                        
                        # 筛选报告
                        filtered_reports = bug_reports
                        if selected_category != "全部":
                            filtered_reports = [r for r in filtered_reports if r['category'] == selected_category]
                        if selected_severity != "全部":
                            filtered_reports = [r for r in filtered_reports if r['severity'] == selected_severity]
                        
                        # 显示报告
                        for i, report in enumerate(reversed(filtered_reports[-20:])):
                            with st.container():
                                severity_icon = {"轻微": "🟢", "一般": "🟡", "严重": "🟠", "致命": "🔴"}.get(
                                    report['severity'], "🟡")
                                st.write(f"{severity_icon} **{report['title']}** - {report['category']}")
                                st.write(
                                    f"提交时间: {report['timestamp']} | 提交者: {report['user_name']} | 环境: {report['os']} + {report['browser']}")
                                st.write(report['description'])
                                if report['reproduction_steps']:
                                    st.write(f"复现步骤: {report['reproduction_steps']}")
                                if report.get('user_email'):
                                    st.write(f"联系邮箱: {report['user_email']}")
                                st.markdown("---")
                    else:
                        st.info("还没有问题报告")
                else:
                    st.info("还没有问题报告")
            except Exception as e:
                st.error(f"读取报告失败: {e}")
    else:
        st.info("🔒 仅超级管理员可以查看已提交的问题报告")


def show_online_users_widget():
    """显示在线用户统计组件"""
    if not ONLINE_USERS_AVAILABLE:
        return
    
    try:
        # 获取在线人数
        online_count = get_online_users_count()
        
        # 显示在线人数
        st.sidebar.markdown("---")
        st.sidebar.markdown("👥 **在线状态**")
        
        # 使用不同颜色表示在线人数
        if online_count == 0:
            color = "red"
            status = "禁锁"
        elif online_count == 1:
            color = "blue"
            status = "单人"
        elif online_count <= 5:
            color = "orange"
            status = "活跃"
        else:
            color = "green"
            status = "热闹"
        
        # 显示在线人数
        st.sidebar.markdown(
            f"<div style='text-align: center; padding: 10px; background: linear-gradient(90deg, #{color}20, #{color}40); border-radius: 8px; margin: 5px 0;'>" +
            f"<h3 style='margin: 0; color: {color};'>👥 {online_count} 人在线</h3>" +
            f"<p style='margin: 5px 0; color: {color}; font-size: 12px;'>{status}</p>" +
            "</div>",
            unsafe_allow_html=True
        )
        
        # 显示详细统计（仅超级管理员可见）
        user_role = get_current_user_role()
        if user_role == 'super_admin':
            with st.sidebar.expander("📈 详细统计"):
                try:
                    # 创建管理器实例
                    if OnlineUserManager:
                        db_path = network_config.get_database_path()
                        manager = OnlineUserManager(db_path)
                        
                        # 获取访问统计
                        stats = manager.get_visit_stats()
                        
                        st.write(f"👥 当前在线: {stats['online_count']} 人")
                        st.write(f"📅 今日访问: {stats['today_visits']} 人")
                        st.write(f"📊 总访问量: {stats['total_visits']} 人")
                        
                        # 显示在线用户列表
                        online_users = manager.get_online_users()
                        if online_users:
                            st.write("👤 **在线用户**:")
                            for user in online_users[:5]:  # 只显示前5个
                                st.write(f"- {user['username']} ({user['online_duration']})")
                            
                            if len(online_users) > 5:
                                st.write(f"... 及其他 {len(online_users) - 5} 人")
                    else:
                        st.write("在线用户管理器不可用")
                            
                except Exception as e:
                    st.write(f"获取统计失败: {e}")
        
    except Exception as e:
        st.sidebar.write(f"在线人数获取失败: {e}")


def track_page_visit(page_name: str):
    """跟踪页面访问"""
    if not ONLINE_USERS_AVAILABLE:
        return
    
    # 获取用户session token
    session_token = st.session_state.get('session_token')
    if session_token and track_user_online:
        try:
            track_user_online(session_token, page_name)  # type: ignore
        except Exception as e:
            print(f"跟踪页面访问失败: {e}")


def show_admin_settings_page():
    """显示管理员设置页面"""
    # 获取当前用户信息
    current_user = st.session_state.get('user', {})
    username = current_user.get('username', '')
    user_role = get_current_user_role()
    
    # 检查权限
    if user_role != 'super_admin':
        st.error("🚫 您没有权限访问此页面。仅超级管理员可以访问。")
        return
    
    st.title("⚙️ 管理员设置")
    
    st.markdown("""
    您好，超级管理员！在这里您可以配置数据集中存储和服务器设置。
    """)
    
    # 服务器模式配置
    st.subheader("🚀 服务器模式")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        current_server_config = network_config.get_server_info()
        is_server_mode = st.checkbox(
            "启用中央服务器模式", 
            value=current_server_config.get('enabled', False),
            help="启用后，所有用户数据将集中存储在您的电脑上"
        )
        
        if is_server_mode:
            st.info("ℹ️ 中央服务器模式已启用，所有数据将集中存储")
        else:
            st.warning("⚠️ 当前为本地模式，每个用户的数据在各自的电脑上")
    
    with col2:
        if st.button("🚀 部署服务器", help="启动服务器部署向导"):
            st.session_state.page = '服务器部署'
            st.rerun()
    
    # 数据存储配置
    st.subheader("💾 数据存储配置")
    
    current_config = network_config.config
    
    # 存储类型
    storage_type = st.selectbox(
        "存储类型",
        ["local", "network_share", "custom_path"],
        index=["local", "network_share", "custom_path"].index(current_config.get('storage_type', 'local')),
        format_func=lambda x: {
            "local": "🖥️ 本地存储",
            "network_share": "🌍 网络共享",
            "custom_path": "📁 自定义路径"
        }[x]
    )
    
    # 存储路径
    storage_path = ""
    if storage_type != "local":
        storage_path = st.text_input(
            "存储路径",
            value=current_config.get('storage_path', ''),
            placeholder="例如: //192.168.1.100/shared/platform_data 或 D:/platform_data",
            help="请输入您希望存储数据的路径"
        )
        
        if storage_path:
            # 检查路径是否可访问
            if os.path.exists(storage_path):
                st.success(f"✅ 路径可访问: {storage_path}")
            else:
                st.warning(f"⚠️ 路径不存在或不可访问: {storage_path}")
                if st.button("📁 创建目录"):
                    try:
                        os.makedirs(storage_path, exist_ok=True)
                        st.success("✅ 目录创建成功")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 创建目录失败: {e}")
    
    # 保存配置
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 保存设置", type="primary"):
            try:
                # 更新配置
                if storage_type == "local":
                    network_config.config.update({
                        "enabled": False,
                        "storage_type": "local",
                        "storage_path": ""
                    })
                else:
                    network_config.config.update({
                        "enabled": True,
                        "storage_type": storage_type,
                        "storage_path": storage_path
                    })
                
                # 更新服务器模式
                network_config.config["central_server"]["enabled"] = is_server_mode
                
                network_config.save_config()
                st.success("✅ 设置保存成功！")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ 保存失败: {e}")
    
    with col2:
        if st.button("🔄 重置为默认"):
            network_config.config = {
                "enabled": False,
                "storage_type": "local",
                "storage_path": "",
                "server_config": {},
                "central_server": {
                    "enabled": False,
                    "host": "",
                    "port": 8501
                }
            }
            network_config.save_config()
            st.success("✅ 已重置为默认设置")
            st.rerun()
    
    # 当前配置显示
    st.subheader("📊 当前配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("💾 **数据存储**")
        st.write(f"- 类型: {current_config.get('storage_type', 'local')}")
        st.write(f"- 启用: {'Yes' if current_config.get('enabled', False) else 'No'}")
        if current_config.get('storage_path'):
            st.write(f"- 路径: {current_config['storage_path']}")
    
    with col2:
        st.write("🚀 **服务器模式**")
        server_config = current_config.get('central_server', {})
        st.write(f"- 启用: {'Yes' if server_config.get('enabled', False) else 'No'}")
        if server_config.get('host'):
            st.write(f"- 地址: {server_config['host']}:{server_config.get('port', 8501)}")
    
    # 数据管理
    st.subheader("📁 数据管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            db_path = network_config.get_database_path()
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM datasets")
            dataset_count = c.fetchone()[0]
            conn.close()
            st.metric("📁 数据集", dataset_count)
        except:
            st.metric("📁 数据集", "N/A")
    
    with col2:
        try:
            datasets_path = network_config.get_datasets_path()
            if os.path.exists(datasets_path):
                total_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                               for dirpath, dirnames, filenames in os.walk(datasets_path)
                               for filename in filenames)
                st.metric("💾 存储大小", f"{total_size / 1024 / 1024:.1f} MB")
            else:
                st.metric("💾 存储大小", "0 MB")
        except:
            st.metric("💾 存储大小", "N/A")
    
    with col3:
        try:
            data_path = network_config.get_data_path()
            feedback_files = ['feature_suggestions.json', 'bug_reports.json']
            total_feedback = 0
            for file in feedback_files:
                file_path = os.path.join(data_path, file)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        total_feedback += len(data)
            st.metric("📝 反馈数", total_feedback)
        except:
            st.metric("📝 反馈数", "N/A")


def show_server_deploy_page():
    """显示服务器部署页面"""
    # 检查权限
    current_user = st.session_state.get('user', {})
    user_role = get_current_user_role()
    
    if user_role != 'super_admin':
        st.error("🚫 您没有权限访问此页面。仅超级管理员可以访问。")
        return
    
    # 导入部署模块
    try:
        from scripts.deploy_server import deploy_server
        deploy_server()
    except ImportError:
        st.error("❌ 部署模块不可用")
        
        # 手动部署说明
        st.title("🚀 手动部署指南")
        
        st.markdown("""
        ## 📝 部署步骤
        
        ### 1. 准备工作
        - 确保您的电脑具有固定IP地址或域名
        - 确保防火墙允许相关端口通信
        
        ### 2. 启动命令
        在命令行中执行：
        ```bash
        cd /path/to/platform
        python -m streamlit run src/main.py --server.port 8501 --server.address 0.0.0.0
        ```
        
        ### 3. 访问地址
        其他用户可以通过以下地址访问：
        ```
        http://您的IP地址:8501
        ```
        
        ### 4. 注意事项
        - 保持命令行窗口开启
        - 定期备份数据
        - 监控系统资源使用
        """)


def show_online_users_page():
    """显示在线用户管理页面（仅超级管理员）"""
    # 检查权限
    current_user = st.session_state.get('user', {})
    user_role = get_current_user_role()
    
    if user_role != 'super_admin':
        st.error("🚫 您没有权限访问此页面。仅超级管理员可以访问。")
        return
    
    if not ONLINE_USERS_AVAILABLE:
        st.error("❌ 在线用户管理功能不可用")
        return
    
    st.title("👥 在线用户管理")
    
    try:
        if OnlineUserManager:
            db_path = network_config.get_database_path()
            manager = OnlineUserManager(db_path)
            
            # 获取统计数据
            stats = manager.get_visit_stats()
            online_users = manager.get_online_users()
            
            # 显示统计卡片
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("👥 当前在线", stats['online_count'])
            
            with col2:
                st.metric("📅 今日访问", stats['today_visits'])
            
            with col3:
                st.metric("📊 总访问量", stats['total_visits'])
            
            with col4:
                # 实时更新按钮
                if st.button("🔄 刷新"):
                    st.rerun()
            
            # 在线用户列表
            st.subheader("👤 在线用户列表")
            
            if online_users:
                # 创建表格
                users_data = []
                for user in online_users:
                    users_data.append({
                        '👤 用户名': user['username'],
                        '📱 IP地址': user['ip_address'] or '未知',
                        '🕐 登录时间': user['login_time'][:19] if user['login_time'] else '未知',
                        '❤️ 最后活动': user['last_seen'][:19] if user['last_seen'] else '未知',
                        '🕰️ 在线时长': user['online_duration'],
                        '📄 当前页面': user['page_path'] or '未知'
                    })
                
                # 显示表格
                import pandas as pd
                df = pd.DataFrame(users_data)
                st.dataframe(df, use_container_width=True)
                
                # 显示详细信息
                with st.expander("📈 详细分析"):
                    # 用户分布统计
                    st.write("**👥 用户类型分布:**")
                    guest_count = sum(1 for u in online_users if u['username'] == '游客')
                    registered_count = len(online_users) - guest_count
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("👤 注册用户", registered_count)
                    with col2:
                        st.metric("👥 游客用户", guest_count)
                    
                    # 活跃页面统计
                    st.write("**📄 活跃页面:**")
                    page_counts = {}
                    for user in online_users:
                        page = user['page_path'] or '未知'
                        page_counts[page] = page_counts.get(page, 0) + 1
                    
                    for page, count in sorted(page_counts.items(), key=lambda x: x[1], reverse=True):
                        st.write(f"- {page}: {count} 人")
                
            else:
                st.info("😴 当前没有在线用户")
            
            # 管理功能
            st.subheader("🔧 管理功能")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🧹 清理无效会话"):
                    manager.cleanup_inactive_users()
                    st.success("✅ 已清理无效会话")
                    st.rerun()
            
            with col2:
                if st.button("📈 查看访问日志"):
                    # 显示访问日志（简化版）
                    import pandas as pd  # 重新导入
                    conn = sqlite3.connect(db_path)
                    df_visits = pd.read_sql_query("""
                        SELECT visit_time, username, ip_address, action 
                        FROM user_visits 
                        ORDER BY visit_time DESC 
                        LIMIT 50
                    """, conn)
                    conn.close()
                    
                    if not df_visits.empty:
                        st.dataframe(df_visits, use_container_width=True)
                    else:
                        st.info("没有访问日志")
        else:
            st.error("在线用户管理器不可用")
            
    except Exception as e:
        st.error(f"加载在线用户数据失败: {e}")
        import traceback
        st.code(traceback.format_exc())


def main():
    """主函数"""
    st.set_page_config(
        page_title="无人驾驶数据平台",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化数据库
    init_database()
    init_auth_database()
    
    # 检查用户认证
    if not check_authentication():
        show_auth_page()
        return
    
    # 显示用户信息
    show_user_info()
    
    # 显示在线用户统计
    show_online_users_widget()
    
    # 侧边栏导航
    st.sidebar.title("🚗 导航菜单")
    
    # 检查session state中是否有页面跳转
    current_page = st.session_state.get('page', '首页')
    
    # 根据用户角色显示不同菜单
    user_role = get_current_user_role()
    
    if user_role == 'super_admin':
        # 超级管理员可以看到所有功能
        page_options = ["首页", "数据上传", "数据浏览", "数据可视化", "使用文档", "功能建议", "问题反馈", "管理员设置", "在线用户", "服务器部署"]
    else:
        # 普通用户只能看到基本功能
        page_options = ["首页", "数据上传", "数据浏览", "数据可视化", "使用文档", "功能建议", "问题反馈"]
    
    page = st.sidebar.selectbox(
        "选择功能",
        page_options,
        index=page_options.index(current_page) if current_page in page_options else 0,
        help="选择要使用的功能模块"
    )
    
    # 更新session state
    st.session_state.page = page
    
    # 侧边栏信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 平台信息")
    
    try:
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM datasets")
        count = c.fetchone()[0]
        conn.close()
        st.sidebar.metric("数据集数量", count)
    except:
        st.sidebar.metric("数据集数量", "0")
    
    # 页面路由
    if page == "首页":
        track_page_visit("首页")
        show_homepage()
    elif page == "数据上传":
        track_page_visit("数据上传")
        show_upload_page()
    elif page == "数据浏览":
        track_page_visit("数据浏览")
        show_browse_page()
    elif page == "数据可视化":
        track_page_visit("数据可视化")
        show_visualization_page()
    elif page == "使用文档":
        track_page_visit("使用文档")
        show_documentation_page()
    elif page == "功能建议":
        track_page_visit("功能建议")
        show_feature_request_page()
    elif page == "问题反馈":
        track_page_visit("问题反馈")
        show_bug_report_page()
    elif page == "管理员设置":
        track_page_visit("管理员设置")
        show_admin_settings_page()
    elif page == "在线用户":
        track_page_visit("在线用户")
        show_online_users_page()
    elif page == "服务器部署":
        track_page_visit("服务器部署")
        show_server_deploy_page()

if __name__ == "__main__":
    main()