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
from auth import check_authentication, show_auth_page, show_user_info, init_auth_database

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    st.warning("⚠️ Open3D库未安装，点云可视化功能将受限。请运行: pip install open3d")

try:
    import laspy
    LASPY_AVAILABLE = True
except ImportError:
    LASPY_AVAILABLE = False

def load_point_cloud(file_path):
    """加载点云数据"""
    try:
        if file_path.endswith('.pcd'):
            if OPEN3D_AVAILABLE:
                pcd = o3d.io.read_point_cloud(file_path)
                points = np.asarray(pcd.points)
                colors = np.asarray(pcd.colors) if pcd.has_colors() else None
                return points, colors
            else:
                st.error("🚫 需要安装 Open3D 库来读取 PCD 文件")
                return None, None
        
        elif file_path.endswith('.las') or file_path.endswith('.laz'):
            if LASPY_AVAILABLE:
                las_file = laspy.read(file_path)
                points = np.vstack([las_file.x, las_file.y, las_file.z]).T
                colors = None
                if hasattr(las_file, 'red') and hasattr(las_file, 'green') and hasattr(las_file, 'blue'):
                    colors = np.vstack([las_file.red, las_file.green, las_file.blue]).T / 65535.0
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
        return None, None

def visualize_single_pointcloud(file_path):
    """单个点云文件可视化"""
    st.write(f"📄 **文件**: {os.path.basename(file_path)}")
    
    with st.spinner("🔄 正在加载点云数据..."):
        points, colors = load_point_cloud(file_path)
    
    if points is None:
        return
    
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
    if len(points) > max_points:
        indices = np.random.choice(len(points), max_points, replace=False)
        sampled_points = points[indices]
        sampled_colors = colors[indices] if colors is not None else None
    else:
        sampled_points = points
        sampled_colors = colors
    
    # 准备颜色数据
    if color_mode == "高度 (Z)":
        color_values = sampled_points[:, 2]
        colorscale = 'Viridis'
    elif color_mode == "原始颜色" and sampled_colors is not None:
        color_values = [f'rgb({int(r*255)},{int(g*255)},{int(b*255)})' 
                       for r, g, b in sampled_colors]
        colorscale = None
    else:
        color_values = 'blue'
        colorscale = None
    
    # 创建 3D 散点图
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
    
    # 设置布局
    camera_settings = {
        "3D 视角": dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        "从上向下 (XY)": dict(eye=dict(x=0, y=0, z=3)),
        "从前向后 (XZ)": dict(eye=dict(x=0, y=3, z=0)),
        "从左向右 (YZ)": dict(eye=dict(x=3, y=0, z=0))
    }
    
    fig.update_layout(
        title=f'🌌 点云可视化: {os.path.basename(file_path)}',
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            camera=camera_settings.get(view_mode, camera_settings["三维视角"]),
            aspectmode='cube'
        ),
        height=600,
        margin=dict(r=0, b=0, l=0, t=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
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
    conn = sqlite3.connect('data.db')
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
                dataset_dir = f"datasets/{dataset_name}_{timestamp}"
                os.makedirs(dataset_dir, exist_ok=True)
                
                # 保存文件
                file_paths = []
                for file in uploaded_files:
                    file_path = os.path.join(dataset_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getvalue())
                    file_paths.append(file_path)
                
                # 保存到数据库
                conn = sqlite3.connect('data.db')
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
    conn = sqlite3.connect('data.db')
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
    conn = sqlite3.connect('data.db')
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
                cols = st.columns(3)
                for i, img_path in enumerate(image_files[:9]):  # 最多显示9张
                    with cols[i % 3]:
                        if os.path.exists(img_path):
                            try:
                                image = Image.open(img_path)
                                st.image(image, caption=os.path.basename(img_path), use_column_width=True)
                            except Exception as e:
                                st.error(f"无法显示图像: {e}")
            
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
                
                # 可视化模式选择
                if len(pcd_files) == 1:
                    # 单个文件直接可视化
                    visualize_single_pointcloud(pcd_files[0])
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
                            pcd_files,
                            format_func=lambda x: os.path.basename(x),
                            key=f"pcd_select_{selected_dataset}"
                        )
                        if selected_pcd:
                            visualize_single_pointcloud(selected_pcd)
                    else:
                        # 多文件对比可视化
                        visualize_multiple_pointclouds(pcd_files)
            
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
    
    # 侧边栏导航
    st.sidebar.title("🚗 导航菜单")
    page = st.sidebar.selectbox(
        "选择功能",
        ["首页", "数据上传", "数据浏览", "数据可视化"],
        help="选择要使用的功能模块"
    )
    
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
    
    st.sidebar.markdown("### 🔗 快速链接")
    st.sidebar.markdown("[📚 使用文档](#)")
    st.sidebar.markdown("[💡 功能建议](#)")
    st.sidebar.markdown("[🐛 问题反馈](#)")
    
    # 页面路由
    if page == "首页":
        show_homepage()
    elif page == "数据上传":
        show_upload_page()
    elif page == "数据浏览":
        show_browse_page()
    elif page == "数据可视化":
        show_visualization_page()

if __name__ == "__main__":
    main()