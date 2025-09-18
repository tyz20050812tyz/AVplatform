#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 兼容性包装函数
"""

import streamlit as st


def safe_button(label, key=None, help=None, **kwargs):
    """安全的按钮函数，自动处理 use_container_width 参数"""
    try:
        return st.button(label, key=key, help=help, use_container_width=kwargs.get('use_container_width', False))
    except TypeError:
        # 移除不支持的参数
        filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'use_container_width'}
        return st.button(label, key=key, help=help, **filtered_kwargs)

def safe_image(image, caption=None, **kwargs):
    """安全的图片显示函数，自动处理 use_container_width 参数"""
    try:
        return st.image(image, caption=caption, use_container_width=kwargs.get('use_container_width', False))
    except TypeError:
        # 移除不支持的参数
        filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'use_container_width'}
        return st.image(image, caption=caption, **filtered_kwargs)
