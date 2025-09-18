"""
创建测试数据集，将生成的测试图片添加到数据库中
"""

import sqlite3
import os
from datetime import datetime


def create_test_dataset():
    """创建测试数据集"""
    # 连接数据库
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    # 创建表（如果不存在）
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
    
    # 获取测试图片文件列表
    test_dir = "data/test_images"
    if not os.path.exists(test_dir):
        print(f"❌ 测试图片目录不存在: {test_dir}")
        return
    
    # 收集所有图片文件
    image_files = []
    for filename in os.listdir(test_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(test_dir, filename).replace('\\', '/')
            image_files.append(filepath)
    
    if not image_files:
        print("❌ 没有找到测试图片文件")
        return
    
    # 插入测试数据集
    dataset_name = "图片预览测试数据集"
    dataset_desc = """这是一个用于测试图片预览功能的数据集，包含以下类型的图片：
1. 按分钟间隔的序列图片 (10张)
2. 按小时间隔的图片 (6张)  
3. Unix时间戳命名的图片 (5张)
4. 按日期命名的图片 (7张)
5. 无时间戳的图片 (3张)

这些图片具有不同的时间戳格式，用于测试时间轴功能和单张预览功能。"""
    
    upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    file_paths_str = ",".join(image_files)
    
    # 检查是否已存在相同名称的数据集
    c.execute("SELECT id FROM datasets WHERE name = ?", (dataset_name,))
    existing = c.fetchone()
    
    if existing:
        # 更新现有数据集
        c.execute("""
            UPDATE datasets 
            SET description = ?, upload_time = ?, file_count = ?, file_paths = ?
            WHERE name = ?
        """, (dataset_desc, upload_time, len(image_files), file_paths_str, dataset_name))
        print(f"✅ 更新现有数据集: {dataset_name}")
        print(f"📊 文件数量: {len(image_files)}")
    else:
        # 插入新数据集
        c.execute("""
            INSERT INTO datasets (name, description, upload_time, file_count, file_paths)
            VALUES (?, ?, ?, ?, ?)
        """, (dataset_name, dataset_desc, upload_time, len(image_files), file_paths_str))
        print(f"✅ 创建新数据集: {dataset_name}")
        print(f"📊 文件数量: {len(image_files)}")
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"📁 图片文件列表:")
    for i, filepath in enumerate(image_files[:10], 1):  # 显示前10个文件
        print(f"  {i}. {os.path.basename(filepath)}")
    if len(image_files) > 10:
        print(f"  ... 还有 {len(image_files) - 10} 个文件")
    
    print(f"\\n🎉 测试数据集创建完成！")
    print(f"现在可以在应用的'数据浏览'页面中查看和测试图片预览功能。")


if __name__ == "__main__":
    create_test_dataset()