import sqlite3
import json
from datetime import datetime

class PerformanceDB:
    def __init__(self, db_path='performance_data.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 1. 绩效结果表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            period_type TEXT,
            employee_name TEXT NOT NULL,
            employee_id TEXT,
            email TEXT,
            department_l2 TEXT,
            department_l3 TEXT,
            department_l4 TEXT,
            total_score REAL,
            total_grade REAL,
            coefficient REAL,
            self_score REAL,
            manager_score REAL,
            manager_comment TEXT,
            dept_rank INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(period, employee_id)
        )
        ''')
        
        # 2. 考核指标表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            employee_name TEXT,
            indicator_module TEXT,
            indicator_name TEXT,
            weight REAL,
            target_value TEXT,
            actual_value TEXT,
            score REAL
        )
        ''')
        
        # 3. 面谈记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            employee_name TEXT,
            interviewer TEXT,
            interview_step TEXT,
            is_interviewed TEXT,
            employee_accept TEXT,
            feedback_content TEXT,
            is_feedback TEXT
        )
        ''')
        
        # 4. 考核方案表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessment_scheme (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            effective_period TEXT NOT NULL,
            scheme_name TEXT,
            department TEXT,
            position_type TEXT,
            indicator_config TEXT,
            weight_config TEXT,
            change_description TEXT,
            create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 5. 数据上传日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_upload_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            period TEXT,
            file_type TEXT,
            record_count INTEGER,
            uploader TEXT,
            status TEXT
        )
        ''')
        
        conn.commit()
        print("✓ 数据库初始化成功")
    
    def upgrade_table_structure(self):
        """升级表结构，添加缺失的字段"""
        cursor = self.conn.cursor()
        
        try:
            # 检查 performance_results 表的字段
            cursor.execute("PRAGMA table_info(performance_results)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # 如果缺少 coefficient 字段，则添加
            if 'coefficient' not in columns:
                print("检测到缺少 coefficient 字段，正在自动添加...")
                cursor.execute('ALTER TABLE performance_results ADD COLUMN coefficient REAL')
                self.conn.commit()
                print("✓ 成功添加 coefficient 字段")
            
            return True
        except Exception as e:
            print(f"✗ 表结构升级失败: {str(e)}")
            return False
        
    def get_all_periods(self):
        """获取所有考核周期"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT period FROM performance_results ORDER BY period DESC')
        return [row[0] for row in cursor.fetchall()]
    
    def get_periods_by_type(self, period_type=None):
        """
        获取指定类型的周期列表
        
        参数:
            period_type: "月度"/"季度"/"半年度"/"年度" 或 None(全部)
        
        返回:
            周期列表（按时间倒序）
        """
        cursor = self.conn.cursor()
        
        # 中文到英文的映射（数据库中存储的是英文）
        period_type_mapping = {
            "月度": "monthly",
            "季度": "quarterly",
            "半年度": "half_yearly",
            "年度": "yearly"
        }
        
        if period_type and period_type != "全部":
            # 将中文转换为英文
            english_type = period_type_mapping.get(period_type, period_type)
            
            cursor.execute('''
                SELECT DISTINCT period 
                FROM performance_results 
                WHERE period_type = ?
                ORDER BY period DESC
            ''', (english_type,))
        else:
            cursor.execute('''
                SELECT DISTINCT period 
                FROM performance_results 
                ORDER BY period DESC
            ''')
        
        return [row[0] for row in cursor.fetchall()]
    
    def get_all_employees(self, period=None):
        """获取所有员工"""
        cursor = self.conn.cursor()
        if period:
            cursor.execute('''
                SELECT DISTINCT employee_name, employee_id, department_l2, department_l4 
                FROM performance_results 
                WHERE period = ?
                ORDER BY employee_name
            ''', (period,))
        else:
            cursor.execute('''
                SELECT DISTINCT employee_name, employee_id, department_l2, department_l4 
                FROM performance_results 
                ORDER BY employee_name
            ''')
        return cursor.fetchall()
    
    def get_all_departments(self):
        """获取所有部门"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT department_l2, department_l4 
            FROM performance_results 
            WHERE department_l2 IS NOT NULL
            ORDER BY department_l2
        ''')
        return cursor.fetchall()
    
    def insert_performance_result(self, data):
        """插入绩效结果"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO performance_results 
            (period, period_type, employee_name, employee_id, email, 
             department_l2, department_l3, department_l4, 
             total_score, total_grade, coefficient, self_score, manager_score, manager_comment, dept_rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['period'], data.get('period_type'), data['employee_name'], 
            data['employee_id'], data.get('email'),
            data.get('department_l2'), data.get('department_l3'), data.get('department_l4'),
            data.get('total_score'), data.get('total_grade'), data.get('coefficient'),
            data.get('self_score'), data.get('manager_score'), 
            data.get('manager_comment'), data.get('dept_rank')
        ))
        self.conn.commit()
    
    def insert_indicator(self, data):
        """插入考核指标"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO performance_indicators 
            (period, employee_id, employee_name, indicator_module, indicator_name, 
             weight, target_value, actual_value, score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['period'], data['employee_id'], data['employee_name'],
            data.get('indicator_module'), data.get('indicator_name'),
            data.get('weight'), data.get('target_value'), 
            data.get('actual_value'), data.get('score')
        ))
        self.conn.commit()
    
    def insert_interview_record(self, data):
        """插入面谈记录"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO interview_records 
            (period, employee_id, employee_name, interviewer, interview_step,
             is_interviewed, employee_accept, feedback_content, is_feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['period'], data['employee_id'], data['employee_name'],
            data.get('interviewer'), data.get('interview_step'),
            data.get('is_interviewed'), data.get('employee_accept'),
            data.get('feedback_content'), data.get('is_feedback')
        ))
        self.conn.commit()
    
    def log_upload(self, period, file_type, record_count, uploader, status):
        """记录上传日志"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO data_upload_log (period, file_type, record_count, uploader, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (period, file_type, record_count, uploader, status))
        self.conn.commit()
    
    def get_employee_history(self, employee_id, period_type=None):
        """
        获取员工历史绩效
        
        参数:
            employee_id: 员工ID
            period_type: 周期类型筛选（"月度"/"季度"/"半年度"/"年度" 或 None）
        """
        cursor = self.conn.cursor()
        
        # 中文到英文的映射（数据库中存储的是英文）
        period_type_mapping = {
            "月度": "monthly",
            "季度": "quarterly",
            "半年度": "half_yearly",
            "年度": "yearly"
        }
        
        if period_type and period_type != "全部":
            # 将中文转换为英文
            english_type = period_type_mapping.get(period_type, period_type)
            
            cursor.execute('''
                SELECT * FROM performance_results 
                WHERE employee_id = ? AND period_type = ?
                ORDER BY period
            ''', (employee_id, english_type))
        else:
            cursor.execute('''
                SELECT * FROM performance_results 
                WHERE employee_id = ?
                ORDER BY period
            ''', (employee_id,))
        
        rows = cursor.fetchall()
        # 转换为字典列表
        return [dict(row) for row in rows]
    
    def get_employee_indicators(self, employee_id, period):
        """获取员工某期的考核指标"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM performance_indicators 
            WHERE employee_id = ? AND period = ?
            ORDER BY indicator_module, indicator_name
        ''', (employee_id, period))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_department_performance(self, period, department=None):
        """获取部门绩效数据"""
        cursor = self.conn.cursor()
        if department:
            cursor.execute('''
                SELECT * FROM performance_results 
                WHERE period = ? AND (department_l2 = ? OR department_l4 = ?)
                ORDER BY total_score DESC
            ''', (period, department, department))
        else:
            cursor.execute('''
                SELECT * FROM performance_results 
                WHERE period = ?
                ORDER BY total_score DESC
            ''', (period,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_interview_statistics(self, period):
        """获取面谈统计"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                interviewer,
                COUNT(*) as total_count,
                SUM(CASE WHEN is_interviewed = '是' THEN 1 ELSE 0 END) as interviewed_count
            FROM interview_records
            WHERE period = ? AND interviewer IS NOT NULL
            GROUP BY interviewer
        ''', (period,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_not_interviewed_employees(self, period):
        """获取未面谈员工"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT employee_name, employee_id, interviewer
            FROM interview_records
            WHERE period = ? AND is_interviewed = '否'
        ''', (period,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

if __name__ == '__main__':
    db = PerformanceDB()
    db.init_database()
    db.close()
