#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络存储配置模块
支持将数据存储到指定的网络位置
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

class NetworkStorageConfig:
    """网络存储配置类"""
    
    def __init__(self):
        self.config_file = Path("config/network_storage.json")
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认配置
        return {
            "enabled": False,
            "storage_type": "local",  # local, network_share, ftp
            "storage_path": "",
            "server_config": {},
            "central_server": {
                "enabled": False,
                "host": "",
                "port": 8501
            }
        }
    
    def save_config(self):
        """保存配置"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def set_central_server(self, host: str, port: int = 8501):
        """设置中央服务器"""
        self.config["central_server"] = {
            "enabled": True,
            "host": host,
            "port": port
        }
        self.save_config()
    
    def set_network_storage(self, storage_path: str, storage_type: str = "network_share"):
        """设置网络存储路径"""
        self.config.update({
            "enabled": True,
            "storage_type": storage_type,
            "storage_path": storage_path
        })
        self.save_config()
    
    def get_storage_path(self, subpath: str = "") -> str:
        """获取存储路径"""
        if self.config["enabled"] and self.config["storage_path"]:
            base_path = Path(self.config["storage_path"])
        else:
            base_path = Path(".")
        
        if subpath:
            return str(base_path / subpath)
        return str(base_path)
    
    def get_data_path(self) -> str:
        """获取数据存储路径"""
        return self.get_storage_path("data")
    
    def get_datasets_path(self) -> str:
        """获取数据集存储路径"""
        return self.get_storage_path("datasets")
    
    def get_database_path(self) -> str:
        """获取数据库路径"""
        return self.get_storage_path("data.db")
    
    def is_central_server_mode(self) -> bool:
        """是否为中央服务器模式"""
        return self.config["central_server"]["enabled"]
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return self.config["central_server"]

# 全局配置实例
network_config = NetworkStorageConfig()

def get_storage_path(subpath: str = "") -> str:
    """获取存储路径的便捷函数"""
    return network_config.get_storage_path(subpath)

def ensure_storage_directory(path: str):
    """确保存储目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)

def copy_to_central_storage(local_path: str, relative_path: str) -> str:
    """将文件复制到中央存储"""
    if not network_config.config["enabled"]:
        return local_path
    
    try:
        central_path = network_config.get_storage_path(relative_path)
        ensure_storage_directory(os.path.dirname(central_path))
        shutil.copy2(local_path, central_path)
        return central_path
    except Exception as e:
        print(f"复制到中央存储失败: {e}")
        return local_path