#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片显示功能
"""

import streamlit as st
import numpy as np
from PIL import Image
import os

def create_test_image():
    """创建测试图片"""
    # 创建一个简单的测试图片
    array = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    image = Image.fromarray(array)
    return image

def test_basic_image_display():
    """测试基本图片显示"""
    st.title("🖼️ 图片显示测试")
    
    # 创建测试图片
    test_image = create_test_image()
    
    st.subheader("1. 基本图片显示")
    try:
        st.image(test_image, caption="测试图片")
        st.success("✅ 基本图片显示正常")
    except Exception as e:
        st.error(f"❌ 基本图片显示失败: {e}")
    
    st.subheader("2. 带宽度设置的图片显示")
    try:
        st.image(test_image, caption="固定宽度图片", width=300)
        st.success("✅ 固定宽度图片显示正常")
    except Exception as e:
        st.error(f"❌ 固定宽度图片显示失败: {e}")
    
    st.subheader("3. 测试 use_container_width 参数")
    try:
        st.image(test_image, caption="容器宽度图片", use_container_width=True)
        st.success("✅ use_container_width 参数支持")
    except Exception as e:
        st.error(f"❌ use_container_width 参数不支持: {e}")
        # 降级到普通显示
        st.image(test_image, caption="容器宽度图片（降级）")
    
    st.subheader("4. 测试真实图片文件")
    # 查找项目中的测试图片
    test_paths = [
        "data/test_images",
        "datasets",
        "."
    ]
    
    found_images = []
    for path in test_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        found_images.append(os.path.join(root, file))
                        if len(found_images) >= 3:  # 只取前3张
                            break
                if len(found_images) >= 3:
                    break
    
    if found_images:
        st.write(f"找到 {len(found_images)} 张测试图片:")
        for img_path in found_images:
            try:
                st.write(f"**{os.path.basename(img_path)}**")
                st.image(img_path, caption=os.path.basename(img_path))
                st.success(f"✅ {img_path} 显示正常")
            except Exception as e:
                st.error(f"❌ {img_path} 显示失败: {e}")
    else:
        st.info("未找到测试图片文件")

if __name__ == "__main__":
    test_basic_image_display()