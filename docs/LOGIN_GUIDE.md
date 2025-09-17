# 🔐 登录系统使用指南

## 功能概述

为无人驾驶数据管理平台添加了完整的用户认证系统，包括：

- 🔑 **用户登录** - 安全的密码验证
- 📝 **用户注册** - 支持新用户注册
- 🎫 **会话管理** - 自动会话过期和令牌管理
- 🔒 **安全特性** - 密码哈希、登录限制、账户锁定

## 快速开始

### 1. 测试核心功能（无需Streamlit）

```bash
# 测试认证功能
python test_auth.py

# 命令行登录演示
python demo_login.py
```

### 2. 启动完整Web应用（需要Streamlit）

```bash
# 安装Streamlit
pip install streamlit

# 启动应用
streamlit run main.py
```

## 默认账户

系统会自动创建默认管理员账户：

- **用户名**: `admin`
- **密码**: `admin123`
- **邮箱**: `admin@platform.com`

⚠️ **安全提示**: 首次登录后建议立即修改默认密码

## 功能特性

### 🔒 安全特性

1. **密码安全**
   - 使用PBKDF2算法进行密码哈希
   - 随机盐值防止彩虹表攻击
   - 密码强度验证（至少6位，包含字母和数字）

2. **登录保护**
   - 失败登录次数限制（最多5次）
   - 账户自动锁定机制（锁定1小时）
   - 会话超时管理（24小时）

3. **输入验证**
   - 用户名格式验证（3-20位字母数字下划线）
   - 邮箱格式验证
   - 防止重复注册

### 🎫 会话管理

- 自动生成安全会话令牌
- 会话过期自动清理
- 多设备登录支持
- 安全退出登录

## 数据库结构

### 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_login TEXT,
    is_active INTEGER DEFAULT 1,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TEXT
);
```

### 会话表 (user_sessions)
```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## 集成说明

### 在现有页面中添加认证

```python
from auth import check_authentication, show_auth_page

def your_page_function():
    # 检查用户是否已登录
    if not check_authentication():
        show_auth_page()
        return
    
    # 已登录用户的页面内容
    st.write("欢迎使用数据管理平台！")
```

### 获取当前用户信息

```python
if 'user' in st.session_state:
    current_user = st.session_state.user
    username = current_user['username']
    email = current_user['email']
```

## 测试结果

✅ **所有核心功能已验证**：

- 数据库初始化 ✅
- 用户注册 ✅ 
- 用户登录 ✅
- 密码验证 ✅
- 会话管理 ✅
- 输入验证 ✅
- 安全特性 ✅

## 用户体验

### 登录界面特性

- 🎨 美观的用户界面
- 📱 响应式设计
- 🔄 实时表单验证
- 💡 友好的错误提示
- 🎯 简洁的操作流程

### 安全提示

- 密码强度指示
- 登录失败提醒
- 账户锁定通知
- 会话过期提醒

## 故障排除

### 常见问题

1. **Streamlit未安装**
   ```bash
   pip install streamlit
   ```

2. **数据库权限问题**
   - 确保当前目录可写
   - 检查data.db文件权限

3. **会话失效**
   - 重新登录即可
   - 检查系统时间是否正确

### 调试模式

运行测试脚本查看详细信息：
```bash
python test_auth.py
```

## 后续扩展

可以考虑添加的功能：

- 🔄 密码重置功能
- 👥 用户权限管理
- 📊 登录日志记录
- 🔔 邮箱验证功能
- 🌐 OAuth第三方登录

---

💡 **提示**: 登录系统已完全集成到主应用中，用户必须登录后才能访问数据管理功能。