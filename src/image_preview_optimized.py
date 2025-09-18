"""
优化版图片预览功能模块
专注于性能优化：缓存、延迟加载、智能采样
"""

import streamlit as st
import os
import re
from datetime import datetime
from PIL import Image, ExifTags
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import hashlib
from functools import lru_cache
import threading
import time


# 缓存配置
CACHE_SIZE = 100  # 最大缓存图片数量
THUMBNAIL_SIZE = (200, 200)  # 缩略图尺寸
MAX_PREVIEW_SIZE = (800, 600)  # 预览图最大尺寸


@lru_cache(maxsize=200)
def extract_timestamp_from_filename(filename):
    """从文件名中提取时间戳（带缓存）"""
    # 常见的时间戳格式模式（按优先级排序）
    patterns = [
        r'unix[_-]?(\d{16})',  # 16位时间戳（需要取前10位） - 最高优先级
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


class ImageCache:
    """图片缓存管理器"""
    
    def __init__(self, max_size=CACHE_SIZE):
        self.max_size = max_size
        self.cache = {}
        self.access_time = {}
        
    def _evict_oldest(self):
        """清理最久未使用的缓存"""
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_time.keys(), key=lambda k: self.access_time[k])
            del self.cache[oldest_key]
            del self.access_time[oldest_key]
    
    def get_thumbnail(self, image_path):
        """获取缩略图（带缓存）"""
        cache_key = f"thumb_{image_path}"
        current_time = time.time()
        
        if cache_key in self.cache:
            self.access_time[cache_key] = current_time
            return self.cache[cache_key]
        
        try:
            # 创建缩略图
            with Image.open(image_path) as img:
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                # 转换为RGB避免显示问题
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                self._evict_oldest()
                self.cache[cache_key] = img.copy()
                self.access_time[cache_key] = current_time
                
                return self.cache[cache_key]
        except Exception as e:
            st.error(f"创建缩略图失败: {e}")
            return None
    
    def get_preview(self, image_path):
        """获取预览图（带缓存）"""
        cache_key = f"preview_{image_path}"
        current_time = time.time()
        
        if cache_key in self.cache:
            self.access_time[cache_key] = current_time
            return self.cache[cache_key]
        
        try:
            with Image.open(image_path) as img:
                # 限制预览图大小
                img.thumbnail(MAX_PREVIEW_SIZE, Image.Resampling.LANCZOS)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                self._evict_oldest()
                self.cache[cache_key] = img.copy()
                self.access_time[cache_key] = current_time
                
                return self.cache[cache_key]
        except Exception as e:
            st.error(f"创建预览图失败: {e}")
            return None


# 全局图片缓存
image_cache = ImageCache()


@st.cache_data(ttl=300)  # 缓存5分钟
def get_basic_image_info(image_path):
    """获取基本图片信息（轻量级，带缓存）"""
    try:
        if not os.path.exists(image_path):
            return None
        
        # 只获取基本信息，不打开图片
        file_size = os.path.getsize(image_path)
        file_time = datetime.fromtimestamp(os.path.getmtime(image_path))
        filename = os.path.basename(image_path)
        
        # 从文件名提取时间戳
        extracted_time = extract_timestamp_from_filename(filename)
        
        # 选择时间戳
        if extracted_time:
            timestamp = extracted_time
            time_source = "文件名"
        else:
            timestamp = file_time
            time_source = "文件修改时间"
        
        return {
            'path': image_path,
            'filename': filename,
            'timestamp': timestamp,
            'time_source': time_source,
            'file_size': file_size,
            'format': os.path.splitext(filename)[1].upper().replace('.', ''),
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def organize_images_fast(image_files):
    """快速整理图片（只获取基本信息）"""
    image_data = []
    
    # 使用进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(image_files)
    for i, img_path in enumerate(image_files):
        # 更新进度
        progress = (i + 1) / total_files
        progress_bar.progress(progress)
        status_text.text(f"处理图片 {i + 1}/{total_files}: {os.path.basename(img_path)}")
        
        info = get_basic_image_info(img_path)
        if info:
            image_data.append(info)
    
    # 清理进度显示
    progress_bar.empty()
    status_text.empty()
    
    # 按时间戳排序
    image_data.sort(key=lambda x: x['timestamp'])
    
    return image_data


def show_optimized_grid_preview(image_data, cols=4):
    """优化版网格预览（延迟加载）"""
    if not image_data:
        st.warning("没有可显示的图片")
        return
    
    st.subheader("🖼️ 优化网格预览")
    
    # 可选的列数调整
    cols = st.select_slider(
        "选择列数",
        options=[2, 3, 4, 5, 6],
        value=cols,
        key="grid_cols_opt"
    )
    
    # 每页显示的图片数（减少以提高性能）
    images_per_page = cols * 3  # 3行而不是4行
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
                        # 使用缓存的缩略图
                        thumbnail = image_cache.get_thumbnail(img_info['path'])
                        
                        if thumbnail:
                            # 显示基本信息（不需要打开完整图片）
                            st.write(f"**{img_info['filename'][:20]}...**" if len(img_info['filename']) > 20 else f"**{img_info['filename']}**")
                            st.write(f"📅 {img_info['timestamp'].strftime('%m-%d %H:%M')}")
                            st.write(f"📁 {img_info['file_size'] // 1024} KB")
                            
                            # 创建可点击的查看按钮
                            if st.button(
                                f"🔍 查看",
                                key=f"opt_img_detail_{start_idx + i + j}",
                                help=f"点击查看 {img_info['filename']}"
                            ):
                                st.session_state.selected_image_index = start_idx + i + j
                                st.session_state.show_detail = True
                                st.rerun()
                        else:
                            st.error("无法加载图片")
                        
                    except Exception as e:
                        st.error(f"加载失败: {e}")


def show_optimized_single_preview(image_path, image_info=None):
    """优化版单张图片预览"""
    if not os.path.exists(image_path):
        st.error(f"图片文件不存在: {image_path}")
        return
    
    try:
        # 使用缓存的预览图
        preview_image = image_cache.get_preview(image_path)
        
        if not preview_image:
            st.error("无法加载图片预览")
            return
        
        # 创建两列布局
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(preview_image, caption=os.path.basename(image_path))
        
        with col2:
            st.subheader("📊 图片信息")
            
            # 基本信息
            st.write(f"**文件名**: {os.path.basename(image_path)}")
            
            if image_info:
                st.write(f"**尺寸**: {preview_image.size[0]} × {preview_image.size[1]}")
                st.write(f"**格式**: {image_info['format']}")
                st.write(f"**文件大小**: {image_info['file_size']:,} 字节")
                st.write(f"**时间戳**: {image_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**时间来源**: {image_info['time_source']}")
            
            # 延迟加载详细EXIF信息
            if st.button("📸 加载EXIF信息"):
                with st.spinner("正在加载EXIF信息..."):
                    try:
                        with Image.open(image_path) as full_image:
                            exif_data = full_image.getexif()
                            if exif_data:
                                st.write("**EXIF信息**:")
                                for tag, value in exif_data.items():
                                    tag_name = ExifTags.TAGS.get(tag, tag)
                                    if isinstance(value, (str, int, float)) and len(str(value)) < 100:
                                        st.write(f"**{tag_name}**: {value}")
                            else:
                                st.info("此图片没有EXIF信息")
                    except Exception as e:
                        st.error(f"无法读取EXIF信息: {e}")
    
    except Exception as e:
        st.error(f"无法显示图片: {e}")


def show_optimized_timeline_preview(image_data):
    """优化版时间轴预览"""
    if not image_data:
        st.warning("没有可显示的图片")
        return
    
    st.subheader("📅 优化时间轴预览")
    
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
            if 'timeline_index_opt' not in st.session_state:
                st.session_state.timeline_index_opt = 0
            
            selected_index = st.slider(
                "拖动选择图片",
                min_value=0,
                max_value=len(image_data) - 1,
                value=st.session_state.timeline_index_opt,
                format="图片 %d",
                key="timeline_slider_opt"
            )
            
            # 更新session state
            st.session_state.timeline_index_opt = selected_index
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
            st.metric("文件大小", f"{selected_image['file_size'] // 1024} KB")
        
        # 显示图片（使用优化预览）
        show_optimized_single_preview(selected_image['path'], selected_image)
        
        # 导航按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⬅️ 上一张", disabled=(selected_index == 0)):
                st.session_state.timeline_index_opt = max(0, selected_index - 1)
                st.rerun()
        
        with col2:
            st.write(f"第 {selected_index + 1} 张，共 {len(image_data)} 张")
        
        with col3:
            if st.button("下一张 ➡️", disabled=(selected_index == len(image_data) - 1)):
                st.session_state.timeline_index_opt = min(len(image_data) - 1, selected_index + 1)
                st.rerun()


def show_optimized_image_preview_interface(image_files):
    """优化版图片预览界面"""
    if not image_files:
        st.warning("没有找到图片文件")
        return
    
    # 初始化session state
    if 'show_detail_opt' not in st.session_state:
        st.session_state.show_detail_opt = False
    if 'selected_image_index_opt' not in st.session_state:
        st.session_state.selected_image_index_opt = 0
    
    # 性能提示
    if len(image_files) > 50:
        st.info(f"🚀 检测到 {len(image_files)} 张图片，已启用性能优化模式")
    
    # 快速整理图片数据
    with st.spinner("正在快速分析图片..."):
        image_data = organize_images_fast(image_files)
    
    # 显示图片统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("图片总数", len(image_data))
    with col2:
        time_sources = [img['time_source'] for img in image_data]
        main_source = max(set(time_sources), key=time_sources.count) if time_sources else "未知"
        st.metric("主要时间来源", main_source)
    with col3:
        if image_data:
            time_span = max(img['timestamp'] for img in image_data) - min(img['timestamp'] for img in image_data)
            st.metric("时间跨度", f"{time_span.days}天")
    with col4:
        formats = [img['format'] for img in image_data]
        main_format = max(set(formats), key=formats.count) if formats else "未知"
        st.metric("主要格式", main_format)
    
    # 预览模式选择
    preview_mode = st.radio(
        "🎨 选择预览模式",
        ["优化时间轴", "优化网格", "优化单张"],
        horizontal=True,
        help="优化版本，性能更好"
    )
    
    if preview_mode == "优化时间轴":
        show_optimized_timeline_preview(image_data)
    elif preview_mode == "优化网格":
        show_optimized_grid_preview(image_data)
    else:  # 优化单张预览
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
            show_optimized_single_preview(image_data[selected_index]['path'], image_data[selected_index])
    
    # 处理详情查看（从网格模式触发）
    if st.session_state.get('show_detail_opt', False) and 'selected_image_index_opt' in st.session_state:
        selected_index = st.session_state.selected_image_index_opt
        if 0 <= selected_index < len(image_data):
            st.markdown("---")
            st.subheader("🔍 图片详情")
            show_optimized_single_preview(image_data[selected_index]['path'], image_data[selected_index])
            
            if st.button("❌ 关闭详情"):
                st.session_state.show_detail_opt = False
                del st.session_state.selected_image_index_opt
                st.rerun()
    
    # 缓存统计
    with st.expander("📊 性能统计"):
        st.write(f"**缓存状态**: {len(image_cache.cache)}/{image_cache.max_size} 张图片已缓存")
        st.write(f"**处理模式**: 性能优化模式")
        st.write(f"**缩略图尺寸**: {THUMBNAIL_SIZE[0]}x{THUMBNAIL_SIZE[1]}")
        st.write(f"**预览图限制**: {MAX_PREVIEW_SIZE[0]}x{MAX_PREVIEW_SIZE[1]}")