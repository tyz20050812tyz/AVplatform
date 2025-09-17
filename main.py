import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
from PIL import Image
import yaml
import json
import cv2
import numpy as np

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
    
    if datasets.empty:
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
                if dataset['file_paths']:
                    file_paths = dataset['file_paths'].split(",")
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
    
    if datasets.empty:
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
            file_paths = result[0].split(",")
            
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
            
            # 其他文件类型提示
            if pcd_files:
                st.subheader("📡 点云数据")
                for pcd_file in pcd_files:
                    st.write(f"**文件**: {os.path.basename(pcd_file)}")
                    st.info("点云数据可视化功能开发中...")
            
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
            file_paths = result[0].split(",")
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