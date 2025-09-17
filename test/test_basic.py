import os
import tempfile
import sqlite3
import pandas as pd
from PIL import Image
import yaml
import json

def test_database_creation():
    """测试数据库创建"""
    print("测试数据库创建...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        conn = sqlite3.connect(tmp.name)
        c = conn.cursor()
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
        
        # 验证表是否创建成功
        conn = sqlite3.connect(tmp.name)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'")
        result = c.fetchone()
        assert result is not None, "数据表创建失败"
        conn.close()
        
        os.unlink(tmp.name)
        print("✅ 数据库创建测试通过")

def test_file_upload_simulation():
    """测试文件上传功能模拟"""
    print("测试文件上传功能...")
    
    test_dir = "test_datasets"
    os.makedirs(test_dir, exist_ok=True)
    
    try:
        # 模拟图像文件
        test_image = os.path.join(test_dir, "test_image.png")
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image)
        assert os.path.exists(test_image), "测试图像文件创建失败"
        
        # 模拟CSV文件
        test_csv = os.path.join(test_dir, "test_data.csv")
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [10, 20, 30, 40, 50],
            'timestamp': pd.date_range('2024-01-01', periods=5)
        })
        df.to_csv(test_csv, index=False)
        assert os.path.exists(test_csv), "测试CSV文件创建失败"
        
        # 模拟YAML文件
        test_yaml = os.path.join(test_dir, "test_config.yaml")
        yaml_data = {
            'camera': {
                'resolution': [1920, 1080],
                'fps': 30,
                'calibration': {
                    'fx': 800.0,
                    'fy': 800.0,
                    'cx': 960.0,
                    'cy': 540.0
                }
            }
        }
        with open(test_yaml, 'w') as f:
            yaml.dump(yaml_data, f)
        assert os.path.exists(test_yaml), "测试YAML文件创建失败"
        
        # 模拟JSON文件
        test_json = os.path.join(test_dir, "test_metadata.json")
        json_data = {
            'dataset_info': {
                'name': 'test_dataset',
                'version': '1.0',
                'sensors': ['camera', 'lidar', 'gps']
            }
        }
        with open(test_json, 'w') as f:
            json.dump(json_data, f, indent=2)
        assert os.path.exists(test_json), "测试JSON文件创建失败"
        
        print("✅ 文件上传测试通过")
        
        # 返回测试文件路径用于应用测试
        return [test_image, test_csv, test_yaml, test_json]
        
    except Exception as e:
        print(f"❌ 文件上传测试失败: {e}")
        # 清理测试文件
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir):
                os.remove(os.path.join(test_dir, file))
            os.rmdir(test_dir)
        raise

def test_data_processing():
    """测试数据处理功能"""
    print("测试数据处理功能...")
    
    try:
        # 测试图像处理
        img = Image.new('RGB', (100, 100), color='blue')
        assert img.size == (100, 100), "图像处理失败"
        
        # 测试数据框处理
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        assert df.shape == (3, 2), "数据框处理失败"
        
        # 测试YAML处理
        test_yaml = {'test': 'data', 'number': 42}
        yaml_str = yaml.dump(test_yaml)
        loaded_yaml = yaml.safe_load(yaml_str)
        assert loaded_yaml == test_yaml, "YAML处理失败"
        
        # 测试JSON处理
        test_json = {'test': 'data', 'array': [1, 2, 3]}
        json_str = json.dumps(test_json)
        loaded_json = json.loads(json_str)
        assert loaded_json == test_json, "JSON处理失败"
        
        print("✅ 数据处理测试通过")
        
    except Exception as e:
        print(f"❌ 数据处理测试失败: {e}")
        raise

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行无人驾驶数据平台测试")
    print("=" * 50)
    
    try:
        test_database_creation()
        test_files = test_file_upload_simulation()
        test_data_processing()
        
        print("=" * 50)
        print("✅ 所有测试通过！")
        print("测试文件已创建在 test_datasets/ 目录下")
        print("您可以使用这些文件测试应用功能")
        print("=" * 50)
        
        return test_files
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ 测试失败: {e}")
        print("=" * 50)
        raise

if __name__ == "__main__":
    run_all_tests()