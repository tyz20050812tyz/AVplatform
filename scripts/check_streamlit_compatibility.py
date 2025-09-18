#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 兼容性检查和修复脚本
"""

import streamlit as st
import sys
import pkg_resources

def check_streamlit_version():
    """检查 Streamlit 版本"""
    try:
        version = pkg_resources.get_distribution("streamlit").version
        print(f"✅ Streamlit 版本: {version}")
        
        # 检查关键功能支持
        major, minor, patch = version.split('.')[:3]
        major, minor = int(major), int(minor)
        
        features = {
            "use_container_width": (1, 0, 0),  # 从 1.0.0 开始支持
            "st.columns": (0, 68, 0),  # 从 0.68.0 开始支持
            "st.tabs": (1, 10, 0),     # 从 1.10.0 开始支持
        }
        
        print("\n🔍 功能支持检查:")
        for feature, (req_major, req_minor, req_patch) in features.items():
            if (major, minor) >= (req_major, req_minor):
                print(f"✅ {feature}: 支持")
            else:
                print(f"❌ {feature}: 不支持 (需要 {req_major}.{req_minor}.{req_patch}+)")
        
        return version, (major, minor)
        
    except Exception as e:
        print(f"❌ 无法获取 Streamlit 版本: {e}")
        return None, None

def test_streamlit_features():
    """测试 Streamlit 功能"""
    print("\n🧪 测试 Streamlit 功能:")
    
    try:
        # 测试基本功能
        st.title("兼容性测试")
        print("✅ st.title: 正常")
        
        # 测试列功能
        col1, col2 = st.columns(2)
        with col1:
            st.write("测试列1")
        with col2:
            st.write("测试列2")
        print("✅ st.columns: 正常")
        
        # 测试按钮
        try:
            st.button("测试按钮", use_container_width=True)
            print("✅ use_container_width 参数: 支持")
        except TypeError:
            st.button("测试按钮")
            print("⚠️ use_container_width 参数: 不支持")
        
        # 测试图片显示
        import numpy as np
        from PIL import Image
        test_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        test_image = Image.fromarray(test_array)
        
        try:
            st.image(test_image, caption="测试图片", use_container_width=True)
            print("✅ st.image use_container_width: 支持")
        except TypeError:
            st.image(test_image, caption="测试图片")
            print("⚠️ st.image use_container_width: 不支持")
            
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")

def create_compatibility_wrapper():
    """创建兼容性包装函数"""
    wrapper_code = '''
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
'''
    
    with open('src/streamlit_compat.py', 'w', encoding='utf-8') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""\nStreamlit 兼容性包装函数\n"""\n\n')
        f.write('import streamlit as st\n\n')
        f.write(wrapper_code)
    
    print("✅ 兼容性包装函数已创建: src/streamlit_compat.py")

def main():
    """主函数"""
    print("🔍 Streamlit 兼容性检查")
    print("=" * 40)
    
    # 检查版本
    version, version_tuple = check_streamlit_version()
    
    if not version:
        print("❌ 无法检查版本，请确保 Streamlit 已安装")
        return
    
    # 如果版本较老，提供升级建议
    if version_tuple and version_tuple < (1, 0):
        print(f"\n⚠️ 建议升级 Streamlit:")
        print(f"   当前版本: {version}")
        print(f"   建议版本: 1.20.0+")
        print(f"   升级命令: pip install streamlit>=1.20.0")
    
    # 创建兼容性包装
    create_compatibility_wrapper()
    
    print(f"\n💡 使用建议:")
    print(f"   1. 如果遇到参数不支持的错误，请升级 Streamlit")
    print(f"   2. 或者使用创建的兼容性包装函数")
    print(f"   3. 移除代码中的 use_container_width 参数")

if __name__ == "__main__":
    main()