"""
图片预览功能模块
支持单张图片预览和基于时间戳的拖动预览
"""

import streamlit as st
import os
import re
from datetime import datetime
from PIL import Image, ExifTags
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def extract_timestamp_from_filename(filename):
    """从文件名中提取时间戳"""
    # 常见的时间戳格式模式（按优先级排序）
    patterns = [
        r'unix[_-]?(\d{16})',  # 16位时间戳（需要取后10位） - 最高优先级
        r'unix[_-]?(\d{13})',  # Unix timestamp with milliseconds (13位) 前缀 - 高优先级
        r'unix[_-]?(\d{10})',  # Unix timestamp (10位) 前缀 - 高优先级
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})[-_]?(\d{2})[-_]?(\d{2})[-_]?(\d{2})',  # YYYYMMDDHHMMSS
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',  # YYYYMMDD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                if 'unix' in pattern:  # Unix timestamp
                    timestamp_str = match.group(1)
                    
                    if len(timestamp_str) == 16:  # 16位时间戳，取前10位
                        unix_time = int(timestamp_str[:10])
                        return datetime.fromtimestamp(unix_time)
                    elif len(timestamp_str) == 13:  # 13位时间戳（毫秒）
                        unix_time = int(timestamp_str) / 1000
                        return datetime.fromtimestamp(unix_time)
                    elif len(timestamp_str) == 10:  # 10位时间戳（秒）
                        unix_time = int(timestamp_str)
                        return datetime.fromtimestamp(unix_time)
                elif len(match.groups()) == 6:  # YYYYMMDDHHMMSS
                    year, month, day, hour, minute, second = match.groups()
                    return datetime(int(year), int(month), int(day), 
                                       int(hour), int(minute), int(second))
                elif len(match.groups()) == 3:  # YYYYMMDD
                    year, month, day = match.groups()
                    return datetime(int(year), int(month), int(day))
            except (ValueError, OSError):
                continue
    
    return None


def get_image_metadata(image_path):
    """获取图片元数据"""
    try:
        image = Image.open(image_path)
        metadata = {
            'size': image.size,
            'format': image.format,
            'mode': image.mode,
            'file_size': os.path.getsize(image_path)
        }
        
        # 尝试获取EXIF数据
        try:
            exif_data = image.getexif()
            if exif_data:
                exif = {}
                for tag, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag, tag)
                    exif[tag_name] = value
                
                # 提取有用的EXIF信息
                if 'DateTime' in exif:
                    try:
                        metadata['datetime'] = datetime.strptime(exif['DateTime'], '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        pass
                
                metadata['exif'] = exif
        except AttributeError:
            # 旧版本PIL可能没有getexif方法
            pass
        
        return metadata
    except Exception as e:
        st.error(f"无法读取图片元数据: {e}")
        return None


def organize_images_by_timestamp(image_files):
    """根据时间戳整理图片"""
    image_data = []
    
    for img_path in image_files:
        if not os.path.exists(img_path):
            continue
            
        # 获取文件基本信息
        filename = os.path.basename(img_path)
        file_time = datetime.fromtimestamp(os.path.getmtime(img_path))
        
        # 尝试从文件名提取时间戳
        extracted_time = extract_timestamp_from_filename(filename)
        
        # 尝试从EXIF获取时间戳
        metadata = get_image_metadata(img_path)
        exif_time = metadata.get('datetime') if metadata else None
        
        # 选择最合适的时间戳
        if extracted_time:
            timestamp = extracted_time
            time_source = "文件名"
        elif exif_time:
            timestamp = exif_time
            time_source = "EXIF"
        else:
            timestamp = file_time
            time_source = "文件修改时间"
        
        image_data.append({
            'path': img_path,
            'filename': filename,
            'timestamp': timestamp,
            'time_source': time_source,
            'metadata': metadata
        })
    
    # 按时间戳排序
    image_data.sort(key=lambda x: x['timestamp'])
    
    return image_data


def show_single_image_preview(image_path, image_info=None):
    """显示单张图片预览"""
    if not os.path.exists(image_path):
        st.error(f"图片文件不存在: {image_path}")
        return
    
    try:
        # 显示图片
        image = Image.open(image_path)
        
        # 创建两列布局
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(image, caption=os.path.basename(image_path), use_container_width=True)
        
        with col2:
            st.subheader("📊 图片信息")
            
            # 基本信息
            st.write(f"**文件名**: {os.path.basename(image_path)}")
            st.write(f"**尺寸**: {image.size[0]} × {image.size[1]}")
            st.write(f"**格式**: {image.format}")
            st.write(f"**颜色模式**: {image.mode}")
            st.write(f"**文件大小**: {os.path.getsize(image_path):,} 字节")
            
            # 时间戳信息
            if image_info:
                st.write(f"**时间戳**: {image_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**时间来源**: {image_info['time_source']}")
                
                # EXIF信息（如果有）
                if image_info.get('metadata', {}).get('exif'):
                    with st.expander("📸 EXIF信息"):
                        exif = image_info['metadata']['exif']
                        for key, value in exif.items():
                            if isinstance(value, (str, int, float)):
                                st.write(f"**{key}**: {value}")
    
    except Exception as e:
        st.error(f"无法显示图片: {e}")


def show_timeline_preview(image_data):
    """显示基于时间轴的图片预览"""
    if not image_data:
        st.warning("没有可显示的图片")
        return
    
    st.subheader("📅 时间轴图片预览")
    
    # 创建时间轴
    timestamps = [img['timestamp'] for img in image_data]
    min_time = min(timestamps)
    max_time = max(timestamps)
    
    # 时间选择器
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.write(f"**开始时间**")
        st.write(min_time.strftime('%Y-%m-%d %H:%M:%S'))
    
    with col2:
        # 时间轴滑块
        if len(image_data) > 1:
            # 初始化滑块值
            if 'timeline_index' not in st.session_state:
                st.session_state.timeline_index = 0
            
            selected_index = st.slider(
                "拖动选择图片",
                min_value=0,
                max_value=len(image_data) - 1,
                value=st.session_state.timeline_index,
                format="图片 %d",
                key="timeline_slider"
            )
            
            # 更新session state
            st.session_state.timeline_index = selected_index
        else:
            selected_index = 0
            st.info("只有一张图片")
    
    with col3:
        st.write(f"**结束时间**")
        st.write(max_time.strftime('%Y-%m-%d %H:%M:%S'))
    
    # 显示选中的图片
    if 0 <= selected_index < len(image_data):
        selected_image = image_data[selected_index]
        
        # 图片信息栏
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("图片序号", f"{selected_index + 1}/{len(image_data)}")
        with col2:
            st.metric("时间", selected_image['timestamp'].strftime('%H:%M:%S'))
        with col3:
            st.metric("时间来源", selected_image['time_source'])
        with col4:
            if selected_image['metadata']:
                size = selected_image['metadata']['size']
                st.metric("尺寸", f"{size[0]}×{size[1]}")
        
        # 显示图片
        show_single_image_preview(selected_image['path'], selected_image)
        
        # 导航按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⬅️ 上一张", disabled=(selected_index == 0)):
                st.session_state.timeline_index = max(0, selected_index - 1)
                st.rerun()
        
        with col2:
            st.write(f"第 {selected_index + 1} 张，共 {len(image_data)} 张")
        
        with col3:
            if st.button("下一张 ➡️", disabled=(selected_index == len(image_data) - 1)):
                st.session_state.timeline_index = min(len(image_data) - 1, selected_index + 1)
                st.rerun()


def show_image_grid_preview(image_data, cols=4):
    """显示图片网格预览"""
    if not image_data:
        st.warning("没有可显示的图片")
        return
    
    st.subheader("🖼️ 图片网格预览")
    
    # 可选的列数调整
    cols = st.select_slider(
        "选择列数",
        options=[2, 3, 4, 5, 6],
        value=cols,
        key="grid_cols"
    )
    
    # 每页显示的图片数
    images_per_page = cols * 4  # 4行
    total_pages = (len(image_data) + images_per_page - 1) // images_per_page
    
    if total_pages > 1:
        page = st.selectbox(
            f"选择页面 (每页 {images_per_page} 张)",
            range(1, total_pages + 1),
            format_func=lambda x: f"第 {x} 页"
        )
        start_idx = (page - 1) * images_per_page
        end_idx = min(start_idx + images_per_page, len(image_data))
        page_images = image_data[start_idx:end_idx]
    else:
        page_images = image_data
        start_idx = 0
    
    # 创建网格布局
    for i in range(0, len(page_images), cols):
        columns = st.columns(cols)
        for j, col in enumerate(columns):
            if i + j < len(page_images):
                img_info = page_images[i + j]
                with col:
                    try:
                        image = Image.open(img_info['path'])
                        # 调整图片大小以适应网格
                        image.thumbnail((300, 300))
                        
                        # 创建可点击的图片
                        if st.button(
                            f"🔍 查看详情",
                            key=f"img_detail_{start_idx + i + j}",
                            help=f"点击查看 {img_info['filename']} 的详细信息",
                            use_container_width=True
                        ):
                            st.session_state.selected_image_index = start_idx + i + j
                            st.session_state.show_detail = True
                            st.rerun()
                        
                        st.image(image, caption=img_info['filename'], use_container_width=True)
                        st.caption(f"📅 {img_info['timestamp'].strftime('%m-%d %H:%M')}")
                        
                    except Exception as e:
                        st.error(f"无法加载图片: {e}")


def show_image_preview_interface(image_files):
    """显示图片预览界面"""
    if not image_files:
        st.warning("没有找到图片文件")
        return
    
    # 初始化session state
    if 'show_detail' not in st.session_state:
        st.session_state.show_detail = False
    if 'selected_image_index' not in st.session_state:
        st.session_state.selected_image_index = 0
    
    # 整理图片数据
    with st.spinner("正在分析图片时间戳..."):
        image_data = organize_images_by_timestamp(image_files)
    
    # 显示图片统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("图片总数", len(image_data))
    with col2:
        time_sources = [img['time_source'] for img in image_data]
        main_source = max(set(time_sources), key=time_sources.count)
        st.metric("主要时间来源", main_source)
    with col3:
        if image_data:
            time_span = max(img['timestamp'] for img in image_data) - min(img['timestamp'] for img in image_data)
            st.metric("时间跨度", f"{time_span.days}天")
    with col4:
        formats = [img['metadata']['format'] if img['metadata'] else 'Unknown' for img in image_data]
        main_format = max(set(formats), key=formats.count)
        st.metric("主要格式", main_format)
    
    # 预览模式选择
    preview_mode = st.radio(
        "🎨 选择预览模式",
        ["时间轴预览", "网格预览", "单张预览"],
        horizontal=True,
        help="选择不同的图片预览方式"
    )
    
    if preview_mode == "时间轴预览":
        show_timeline_preview(image_data)
    elif preview_mode == "网格预览":
        show_image_grid_preview(image_data)
    else:  # 单张预览
        # 图片选择器
        if len(image_data) > 1:
            selected_index = st.selectbox(
                "选择要预览的图片",
                range(len(image_data)),
                format_func=lambda x: f"{image_data[x]['filename']} ({image_data[x]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})"
            )
        else:
            selected_index = 0
        
        if 0 <= selected_index < len(image_data):
            show_single_image_preview(image_data[selected_index]['path'], image_data[selected_index])
    
    # 处理详情查看（从网格模式触发）
    if st.session_state.get('show_detail', False) and 'selected_image_index' in st.session_state:
        selected_index = st.session_state.selected_image_index
        if 0 <= selected_index < len(image_data):
            st.markdown("---")
            st.subheader("🔍 图片详情")
            show_single_image_preview(image_data[selected_index]['path'], image_data[selected_index])
            
            if st.button("❌ 关闭详情"):
                st.session_state.show_detail = False
                del st.session_state.selected_image_index
                st.rerun()


def create_image_timeline_chart(image_data):
    """创建图片时间轴图表"""
    if not image_data:
        return None
    
    # 准备数据
    timestamps = [img['timestamp'] for img in image_data]
    filenames = [img['filename'] for img in image_data]
    
    # 创建时间轴图表
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=[1] * len(timestamps),
        mode='markers+text',
        text=filenames,
        textposition='top center',
        marker=dict(
            size=12,
            color='blue',
            symbol='circle'
        ),
        hovertemplate='<b>%{text}</b><br>时间: %{x}<extra></extra>',
        name='图片'
    ))
    
    fig.update_layout(
        title='图片时间轴',
        xaxis_title='时间',
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0.5, 1.5]
        ),
        height=200,
        margin=dict(l=0, r=0, t=30, b=30)
    )
    
    return fig