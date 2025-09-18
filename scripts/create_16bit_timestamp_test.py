"""
创建16位时间戳测试图片
"""

import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime


def create_test_image_with_16bit_timestamp():
    """创建带16位时间戳的测试图片"""
    
    # 您提供的16位时间戳
    timestamp_16bit = "1501822123278663"
    
    # 计算对应的实际时间（后10位）
    unix_timestamp = int(timestamp_16bit[-10:])  # 2123278663
    actual_time = datetime.fromtimestamp(unix_timestamp)
    
    # 创建测试目录
    test_dir = "data/test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建测试图片
    filename = f"unix_{timestamp_16bit}.png"
    filepath = os.path.join(test_dir, filename)
    
    # 创建800x600的图片
    image = Image.new('RGB', (800, 600), (100, 150, 200))
    draw = ImageDraw.Draw(image)
    
    # 尝试使用系统字体
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_medium = ImageFont.truetype("arial.ttf", 32)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 绘制背景矩形
    draw.rectangle([50, 150, 750, 450], fill=(255, 255, 255, 200))
    
    # 绘制标题
    title = "16位时间戳测试图片"
    title_bbox = draw.textbbox((0, 0), title, font=font_large)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (800 - title_width) // 2
    draw.text((title_x, 180), title, fill=(0, 0, 0), font=font_large)
    
    # 绘制原始时间戳
    original_text = f"原始时间戳: {timestamp_16bit}"
    draw.text((80, 250), original_text, fill=(0, 0, 0), font=font_medium)
    
    # 绘制后10位
    extracted_text = f"后10位: {timestamp_16bit[-10:]}"
    draw.text((80, 290), extracted_text, fill=(0, 0, 0), font=font_medium)
    
    # 绘制解析后的时间
    time_text = f"解析时间: {actual_time.strftime('%Y-%m-%d %H:%M:%S')}"
    draw.text((80, 330), time_text, fill=(0, 0, 0), font=font_medium)
    
    # 绘制文件名
    file_text = f"文件名: {filename}"
    draw.text((80, 370), file_text, fill=(0, 100, 0), font=font_small)
    
    # 保存图片
    image.save(filepath)
    
    print(f"✅ 创建16位时间戳测试图片:")
    print(f"   文件: {filename}")
    print(f"   路径: {filepath}")
    print(f"   原始时间戳: {timestamp_16bit}")
    print(f"   后10位: {timestamp_16bit[-10:]}")
    print(f"   解析时间: {actual_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return filepath


def add_to_test_dataset():
    """将新图片添加到测试数据集"""
    import sqlite3
    
    # 创建测试图片
    new_image_path = create_test_image_with_16bit_timestamp()
    
    # 更新数据库
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    # 查找图片预览测试数据集
    c.execute("SELECT id, file_paths FROM datasets WHERE name = ?", ("图片预览测试数据集",))
    result = c.fetchone()
    
    if result:
        dataset_id, existing_paths = result
        
        # 添加新图片路径
        if existing_paths:
            updated_paths = existing_paths + "," + new_image_path.replace('\\', '/')
        else:
            updated_paths = new_image_path.replace('\\', '/')
        
        # 计算新的文件数量
        file_count = len(updated_paths.split(","))
        
        # 更新数据库
        c.execute("""
            UPDATE datasets 
            SET file_paths = ?, file_count = ?, upload_time = ?
            WHERE id = ?
        """, (updated_paths, file_count, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), dataset_id))
        
        conn.commit()
        print(f"✅ 已将16位时间戳图片添加到测试数据集")
        print(f"   数据集文件总数: {file_count}")
    else:
        print("❌ 未找到图片预览测试数据集")
    
    conn.close()


def main():
    """主函数"""
    print("🚀 创建16位时间戳测试图片")
    print("=" * 50)
    
    add_to_test_dataset()
    
    print("=" * 50)
    print("🎉 完成！您现在可以在应用中测试16位时间戳解析功能了")
    print("💡 在'数据浏览'页面选择'图片预览测试数据集'查看效果")


if __name__ == "__main__":
    main()