#!/usr/bin/env python3
"""
简单的PCD文件上传和可视化测试工具
"""
import streamlit as st
import os
import shutil
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="PCD文件上传测试",
    page_icon="📤",
    layout="wide"
)

def main():
    """主函数"""
    st.title("📤 PCD文件上传测试工具")
    st.markdown("这个工具可以帮助您测试PCD文件的上传和存储功能")
    st.markdown("---")
    
    # 文件上传
    st.subheader("📁 上传PCD文件")
    uploaded_file = st.file_uploader(
        "选择PCD文件",
        type=['pcd'],
        help="请选择一个PCD格式的点云文件"
    )
    
    if uploaded_file is not None:
        # 显示文件信息
        st.success(f"✅ 文件上传成功: {uploaded_file.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("文件名", uploaded_file.name)
        with col2:
            st.metric("文件大小", f"{uploaded_file.size:,} bytes")
        
        # 保存文件
        if st.button("💾 保存文件到测试目录", type="primary"):
            try:
                # 创建测试目录
                test_dir = "data/temp_pointclouds"
                os.makedirs(test_dir, exist_ok=True)
                
                # 生成唯一文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"uploaded_{timestamp}_{uploaded_file.name}"
                file_path = os.path.join(test_dir, filename)
                
                # 保存文件
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                st.success(f"✅ 文件已保存: {file_path}")
                st.success(f"📁 文件大小: {os.path.getsize(file_path):,} bytes")
                
                # 显示测试说明
                st.markdown("---")
                st.subheader("🔍 测试说明")
                st.info(f"""
                文件已成功上传并保存到: `{file_path}`
                
                现在您可以：
                1. 在主应用程序中创建一个包含此文件的数据集
                2. 使用数据可视化功能查看点云
                3. 或者运行专门的测试应用: `streamlit run test_pcd_streamlit.py`
                """)
                
                # 提供直接可视化选项
                if st.button("🚀 立即测试可视化"):
                    st.markdown("---")
                    st.subheader("🌌 点云可视化测试")
                    
                    # 导入可视化功能
                    import sys
                    sys.path.append('src')
                    
                    try:
                        from main import load_point_cloud, visualize_single_pointcloud
                        
                        # 尝试加载和可视化
                        with st.spinner("正在加载点云数据..."):
                            points, colors = load_point_cloud(file_path)
                        
                        if points is not None:
                            st.success(f"✅ 点云加载成功: {len(points):,} 个点")
                            
                            # 显示基本统计
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("点数量", f"{len(points):,}")
                            with col2:
                                st.metric("有颜色", "是" if colors is not None else "否")
                            with col3:
                                st.metric("数据维度", f"{points.shape}")
                            
                            # 调用可视化函数
                            visualize_single_pointcloud(file_path)
                        else:
                            st.error("❌ 点云加载失败")
                    
                    except Exception as e:
                        st.error(f"❌ 可视化测试失败: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                
            except Exception as e:
                st.error(f"❌ 文件保存失败: {str(e)}")
    
    else:
        st.info("💡 请选择一个PCD文件进行上传测试")
    
    # 显示现有测试文件
    st.markdown("---")
    st.subheader("📋 现有测试文件")
    
    test_dir = "data/temp_pointclouds"
    if os.path.exists(test_dir):
        files = [f for f in os.listdir(test_dir) if f.endswith('.pcd')]
        if files:
            st.write("**可用的PCD测试文件:**")
            for file in files:
                file_path = os.path.join(test_dir, file)
                file_size = os.path.getsize(file_path)
                st.write(f"- `{file}` ({file_size:,} bytes)")
        else:
            st.info("暂无测试文件")
    else:
        st.info("测试目录不存在")

if __name__ == "__main__":
    main()