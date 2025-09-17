import sqlite3

conn = sqlite3.connect('data.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print('数据库表:', [t[0] for t in tables])

if 'users' in [t[0] for t in tables]:
    c.execute("SELECT username, email FROM users")
    users = c.fetchall()
    print('用户列表:', users)

conn.close()