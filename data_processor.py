import pandas as pd
import numpy as np
from database import PerformanceDB
import re
import tempfile
import os

class DataProcessor:
    def __init__(self, db):
        self.db = db
    
    def parse_period(self, period_str):
        """解析考核周期，判断是月度还是季度"""
        if '月度' in period_str:
            return 'monthly'
        elif '季度' in period_str or 'Q' in period_str:
            return 'quarterly'
        return 'unknown'
    
    def process_performance_results(self, file_path, period=None):
        """处理绩效结果导出文件"""
        try:
            # 自动升级表结构（添加缺失的字段）
            self.db.upgrade_table_structure()
            
            df = pd.read_excel(file_path)
            
            # 自动识别考核周期
            if period is None:
                period = df['绩效活动'].dropna().iloc[0] if '绩效活动' in df.columns else None
            
            if not period:
                raise ValueError("无法识别考核周期")
            
            period_type = self.parse_period(period)
            
            # 数据清洗：找到实际的数据行（跳过表头说明行）
            # 识别标志：工号列应该是数字
            if '工号' in df.columns:
                df = df[pd.notna(df['工号'])]
            
            processed_records = []
            interview_records = []
            
            # 按员工分组处理（每个员工可能有多行：自评、上级评）
            current_employee = None
            employee_data = {}
            
            for idx, row in df.iterrows():
                # 如果是新员工行（有员工姓名和工号）
                if pd.notna(row.get('员工')) and pd.notna(row.get('工号')):
                    # 保存上一个员工的数据
                    if current_employee and employee_data:
                        processed_records.append(employee_data)
                    
                    # 开始新员工
                    current_employee = row['员工']
                    
                    # ==================== 读取直接上级 ====================
                    # 优先从"直接上级"列读取（新模板）
                    direct_supervisor = None
                    if '直接上级' in df.columns:
                        direct_supervisor = row.get('直接上级')
                    
                    # 如果没有"直接上级"列，尝试其他可能的列名
                    if pd.isna(direct_supervisor) or direct_supervisor is None:
                        direct_supervisor = row.get('自定义模块')  # 旧格式兼容
                    
                    # ==================== 读取或构建部门信息 ====================
                    # 优先使用真实的部门字段
                    department_l2 = None
                    department_l3 = None
                    department_l4 = None
                    
                    # 尝试读取部门字段（如果Excel中有的话）
                    if '部门' in df.columns:
                        department_l2 = row.get('部门')
                    elif '二级部门' in df.columns:
                        department_l2 = row.get('二级部门')
                    elif 'department_l2' in df.columns:
                        department_l2 = row.get('department_l2')
                    
                    # 如果没有部门字段，使用直接上级作为虚拟部门
                    if pd.isna(department_l2) or department_l2 is None:
                        if pd.notna(direct_supervisor):
                            department_l2 = f"{direct_supervisor}组"  # 例如："蔺瑶组"
                        else:
                            department_l2 = "未知部门"
                    
                    employee_data = {
                        'period': period,
                        'period_type': period_type,
                        'employee_name': row['员工'],
                        'employee_id': str(int(row['工号'])),
                        'email': row.get('邮箱'),
                        'total_score': row.get('总分'),
                        'total_grade': row.get('总等级'),
                        'coefficient': row.get('最终系数'),  # 读取系数
                        'department_l2': department_l2,  # 使用构建好的部门
                        'department_l3': department_l3,
                        'department_l4': department_l4,
                        'self_score': None,
                        'manager_score': None,
                        'manager_comment': None
                    }
                    
                    # ==================== 面谈信息提取（支持新旧两种格式） ====================
                    # 新格式：清晰的列名
                    is_interviewed = None
                    employee_accept = None
                    feedback_content = None
                    interviewer = None
                    
                    # 优先使用新格式的列名
                    if '【面谈】\n直接上级是否进行面谈' in df.columns:
                        is_interviewed = row.get('【面谈】\n直接上级是否进行面谈')
                    elif '【面谈】直接上级是否进行面谈' in df.columns:  # 可能没有换行符
                        is_interviewed = row.get('【面谈】直接上级是否进行面谈')
                    else:
                        # 兼容旧格式
                        is_interviewed = row.get('Unnamed: 10')
                    
                    if '【面谈】\n员工是否接受该绩效结果' in df.columns:
                        employee_accept = row.get('【面谈】\n员工是否接受该绩效结果')
                    elif '【面谈】员工是否接受该绩效结果' in df.columns:
                        employee_accept = row.get('【面谈】员工是否接受该绩效结果')
                    else:
                        # 兼容旧格式
                        employee_accept = row.get('Unnamed: 11') or row.get('Unnamed: 16')
                    
                    if '【面谈】\n面谈反馈内容' in df.columns:
                        feedback_content = row.get('【面谈】\n面谈反馈内容')
                    elif '【面谈】面谈反馈内容' in df.columns:
                        feedback_content = row.get('【面谈】面谈反馈内容')
                    else:
                        # 兼容旧格式
                        feedback_content = row.get('Unnamed: 12')
                    
                    # ==================== 面谈人使用之前读取的direct_supervisor ====================
                    # 注意：direct_supervisor在前面已经读取过了（第59-67行）
                    # 这里直接使用，不需要重新读取
                    interviewer = direct_supervisor if pd.notna(direct_supervisor) else '未知'
                    
                    # 如果有面谈记录，保存
                    if pd.notna(is_interviewed) or pd.notna(feedback_content):
                        interview_records.append({
                            'period': period,
                            'employee_id': employee_data['employee_id'],
                            'employee_name': employee_data['employee_name'],
                            'interviewer': interviewer,
                            'is_interviewed': '是' if is_interviewed == '是' else '否',
                            'employee_accept': '是' if employee_accept == '是' else '否',
                            'feedback_content': feedback_content if pd.notna(feedback_content) else None
                        })
                
                # ==================== 评语信息提取（支持新旧两种格式） ====================
                manager_comment = None
                employee_comment = None
                
                # 优先使用新格式
                if '直接上级总评语' in df.columns:
                    manager_comment = row.get('直接上级总评语')
                if '员工总评语' in df.columns:
                    employee_comment = row.get('员工总评语')
                
                # 如果新格式存在且有数据，直接使用
                if pd.notna(manager_comment) and current_employee:
                    employee_data['manager_comment'] = manager_comment
                
                # 兼容旧格式的评价信息
                if not manager_comment or pd.isna(manager_comment):
                    evaluator = row.get('总评')
                    evaluator_role = row.get('Unnamed: 18')
                    evaluation_score = row.get('Unnamed: 19')
                    evaluation_comment = row.get('Unnamed: 20')
                    
                    if pd.notna(evaluator) and evaluator != '评价人' and current_employee:
                        if evaluator_role == '员工本人':
                            employee_data['self_score'] = pd.to_numeric(evaluation_score, errors='coerce')
                        elif evaluator_role == '直接上级':
                            employee_data['manager_score'] = pd.to_numeric(evaluation_score, errors='coerce')
                            if pd.notna(evaluation_comment):
                                employee_data['manager_comment'] = evaluation_comment
            
            # 保存最后一个员工
            if current_employee and employee_data:
                processed_records.append(employee_data)
            
            # 计算部门排名（按总分降序）
            # 先按部门分组，再计算排名
            df_results = pd.DataFrame(processed_records)
            if not df_results.empty and 'total_score' in df_results.columns:
                # 暂时不分部门，全局排名（后续可以根据部门字段优化）
                df_results['dept_rank'] = df_results['total_score'].rank(ascending=False, method='min')
                
                # 更新processed_records
                for i, row in df_results.iterrows():
                    processed_records[i]['dept_rank'] = int(row['dept_rank'])
            
            # 存入数据库
            for record in processed_records:
                self.db.insert_performance_result(record)
            
            for interview in interview_records:
                self.db.insert_interview_record(interview)
            
            # 记录日志
            self.db.log_upload(period, '绩效结果导出', len(processed_records), 'System', '成功')
            
            return {
                'success': True,
                'period': period,
                'records': len(processed_records),
                'message': f'成功导入 {len(processed_records)} 条绩效结果'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'导入失败: {str(e)}'
            }
    
    def process_indicator_info(self, file_path, period=None):
        """处理指标评价信息导出文件"""
        try:
            df = pd.read_excel(file_path)
            
            # 自动识别考核周期
            if period is None:
                period = df['绩效活动'].dropna().iloc[0] if '绩效活动' in df.columns else None
            
            if not period:
                raise ValueError("无法识别考核周期")
            
            # 数据清洗：跳过表头行
            if '工号' in df.columns:
                df = df[pd.notna(df['工号'])]
            
            processed_indicators = []
            
            # 同时更新performance_results表中的部门信息
            employee_departments = {}
            
            for idx, row in df.iterrows():
                employee_id = str(int(row['工号'])) if pd.notna(row.get('工号')) else None
                employee_name = row.get('员工')
                
                if not employee_id or not employee_name:
                    continue
                
                # 收集部门信息
                if employee_id not in employee_departments:
                    employee_departments[employee_id] = {
                        'department_l2': row.get('二级组织'),
                        'department_l3': row.get('三级组织'),
                        'department_l4': row.get('四级组织')
                    }
                
                # 处理权重（可能是百分比字符串）
                weight = row.get('权重')
                if pd.notna(weight):
                    if isinstance(weight, str):
                        weight = float(weight.replace('%', '')) if '%' in weight else float(weight)
                    else:
                        weight = float(weight) if weight > 1 else float(weight) * 100
                
                indicator_data = {
                    'period': period,
                    'employee_id': employee_id,
                    'employee_name': employee_name,
                    'indicator_module': row.get('绩效模块'),
                    'indicator_name': row.get('考核项名称'),
                    'weight': weight,
                    'target_value': str(row.get('目标值')) if pd.notna(row.get('目标值')) else None,
                    'actual_value': str(row.get('完成值')) if pd.notna(row.get('完成值')) else None,
                    'score': row.get('考核项得分')
                }
                
                processed_indicators.append(indicator_data)
            
            # 存入数据库
            for indicator in processed_indicators:
                self.db.insert_indicator(indicator)
            
            # 更新部门信息到performance_results表
            cursor = self.db.conn.cursor()
            for emp_id, dept_info in employee_departments.items():
                cursor.execute('''
                    UPDATE performance_results 
                    SET department_l2 = ?, department_l3 = ?, department_l4 = ?
                    WHERE employee_id = ? AND period = ?
                ''', (
                    dept_info['department_l2'],
                    dept_info['department_l3'],
                    dept_info['department_l4'],
                    emp_id,
                    period
                ))
            self.db.conn.commit()
            
            # 重新计算部门排名（按部门）
            self._recalculate_dept_rank(period)
            
            # 记录日志
            self.db.log_upload(period, '指标评价信息导出', len(processed_indicators), 'System', '成功')
            
            return {
                'success': True,
                'period': period,
                'records': len(processed_indicators),
                'message': f'成功导入 {len(processed_indicators)} 条考核指标'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'导入失败: {str(e)}'
            }
    
    def _recalculate_dept_rank(self, period):
        """重新计算部门排名"""
        cursor = self.db.conn.cursor()
        
        # 获取所有部门
        cursor.execute('''
            SELECT DISTINCT department_l2, department_l4 
            FROM performance_results 
            WHERE period = ? AND department_l2 IS NOT NULL
        ''', (period,))
        departments = cursor.fetchall()
        
        # 为每个部门计算排名
        for dept in departments:
            dept_l2, dept_l4 = dept[0], dept[1]
            
            # 获取该部门所有员工，按总分排序
            cursor.execute('''
                SELECT employee_id, total_score
                FROM performance_results 
                WHERE period = ? AND department_l2 = ? AND department_l4 = ?
                ORDER BY total_score DESC
            ''', (period, dept_l2, dept_l4))
            
            employees = cursor.fetchall()
            
            # 更新排名
            for rank, (emp_id, score) in enumerate(employees, 1):
                cursor.execute('''
                    UPDATE performance_results 
                    SET dept_rank = ?
                    WHERE period = ? AND employee_id = ?
                ''', (rank, period, emp_id))
        
        self.db.conn.commit()
    
    def get_summary_stats(self, period):
        """获取某期的汇总统计"""
        cursor = self.db.conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_employees,
                AVG(total_score) as avg_score,
                MAX(total_score) as max_score,
                MIN(total_score) as min_score,
                COUNT(CASE WHEN total_score >= 90 THEN 1 END) as excellent_count,
                COUNT(CASE WHEN total_score < 80 THEN 1 END) as need_attention_count
            FROM performance_results
            WHERE period = ?
        ''', (period,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # ==================== 高级分析方法 ====================
    
    def analyze_indicators(self, period):
        """指标拆解分析：计算每个指标的统计数据"""
        cursor = self.db.conn.cursor()
        
        # 直接查询所有指标数据，用Pandas计算统计量
        cursor.execute('''
            SELECT indicator_name, score, weight
            FROM performance_indicators
            WHERE period = ?
        ''', (period,))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        # 按指标分组计算统计量
        stats = df.groupby('indicator_name').agg({
            'score': ['mean', 'std', 'max', 'min', 'count'],
            'weight': 'mean'
        }).reset_index()
        
        # 重命名列
        stats.columns = ['indicator_name', 'avg_score', 'std_score', 'max_score', 
                        'min_score', 'sample_count', 'avg_weight']
        
        # 过滤样本数过少的指标
        stats = stats[stats['sample_count'] >= 3]
        
        # 填充NaN（标准差为0的情况）
        stats['std_score'] = stats['std_score'].fillna(0)
        
        # 排序：按标准差降序
        stats = stats.sort_values('std_score', ascending=False)
        
        return stats.to_dict('records')
    
    def generate_indicator_insights(self, indicator_stats):
        """生成指标分析结论"""
        insights = []
        
        for stat in indicator_stats:
            name = stat['indicator_name']
            avg = stat['avg_score']
            std = stat['std_score']
            
            # 区分度分析
            if std < 5:
                insights.append({
                    'indicator': name,
                    'type': '区分度不足',
                    'message': f'"{name}"标准差仅{std:.2f}，区分度不足，建议优化评分标准或加大权重差异',
                    'severity': 'warning'
                })
            elif std > 10:
                insights.append({
                    'indicator': name,
                    'type': '区分度较高',
                    'message': f'"{name}"标准差为{std:.2f}，区分度较高，能有效区分员工表现',
                    'severity': 'success'
                })
            
            # 评分水平分析
            if avg > 90:
                insights.append({
                    'indicator': name,
                    'type': '评分偏高',
                    'message': f'"{name}"平均分{avg:.2f}，评分偏高，可能存在评分宽松问题',
                    'severity': 'info'
                })
            elif avg < 70:
                insights.append({
                    'indicator': name,
                    'type': '评分偏低',
                    'message': f'"{name}"平均分{avg:.2f}，评分偏低，建议检查目标设定是否合理',
                    'severity': 'warning'
                })
        
        return insights
    
    def analyze_departments(self, period):
        """部门对比分析"""
        cursor = self.db.conn.cursor()
        
        # 先获取基础聚合数据
        cursor.execute('''
            SELECT 
                department_l2 as department,
                COUNT(*) as total_count,
                AVG(total_score) as avg_score,
                COUNT(CASE WHEN total_score >= 90 THEN 1 END) as excellent_count,
                COUNT(CASE WHEN total_score < 80 THEN 1 END) as need_attention_count
            FROM performance_results
            WHERE period = ? AND department_l2 IS NOT NULL
            GROUP BY department_l2
            HAVING COUNT(*) >= 2
            ORDER BY avg_score DESC
        ''', (period,))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        # 为每个部门计算标准差（需要原始分数数据）
        for d in data:
            dept_name = d['department']
            
            # 获取该部门的所有分数
            cursor.execute('''
                SELECT total_score
                FROM performance_results
                WHERE period = ? AND department_l2 = ? AND total_score IS NOT NULL
            ''', (period, dept_name))
            
            scores = [row[0] for row in cursor.fetchall()]
            
            # 计算标准差
            if len(scores) > 1:
                df_scores = pd.Series(scores)
                std_value = df_scores.std()
                d['std_score'] = float(std_value) if pd.notna(std_value) else 0.0
            else:
                d['std_score'] = 0.0
            
            # 计算百分比
            d['excellent_rate'] = (d['excellent_count'] / d['total_count'] * 100) if d['total_count'] > 0 else 0
            d['need_attention_rate'] = (d['need_attention_count'] / d['total_count'] * 100) if d['total_count'] > 0 else 0
        
        return data
    
    def calculate_indicator_correlations(self, period):
        """计算指标与总分的相关系数"""
        cursor = self.db.conn.cursor()
        
        # 获取所有员工的指标得分和总分
        cursor.execute('''
            SELECT 
                pi.employee_id,
                pi.indicator_name,
                pi.score as indicator_score,
                pr.total_score
            FROM performance_indicators pi
            JOIN performance_results pr 
                ON pi.employee_id = pr.employee_id AND pi.period = pr.period
            WHERE pi.period = ?
        ''', (period,))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        # 按指标计算与总分的相关系数
        correlations = []
        for indicator in df['indicator_name'].unique():
            df_ind = df[df['indicator_name'] == indicator]
            
            # 需要至少3个样本才能计算相关系数（已降低要求）
            if len(df_ind) < 3:
                continue
            
            try:
                corr = df_ind['indicator_score'].corr(df_ind['total_score'])
                if pd.notna(corr):  # 排除NaN
                    correlations.append({
                        'indicator_name': indicator,
                        'correlation': corr,
                        'sample_count': len(df_ind)
                    })
            except:
                continue
        
        # 按相关系数绝对值排序
        correlations = sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True)
        
        return correlations

    # ==================== 面谈质量分析方法 ====================
    
    def get_interview_trend_by_supervisor(self, supervisor, periods=None):
        """
        按上级分析面谈完成率趋势（支持单个上级或查看其下属）
        
        参数:
            supervisor: 上级名称（如果为None，则返回所有上级的对比）
            periods: 周期列表（None表示最近6期）
        
        返回:
            每个上级在各个周期的完成率数据
        """
        cursor = self.db.conn.cursor()
        
        # 如果没有指定周期，获取最近6期
        if periods is None:
            cursor.execute('''
                SELECT DISTINCT period 
                FROM interview_records 
                ORDER BY period DESC 
                LIMIT 6
            ''')
            periods = [row[0] for row in cursor.fetchall()]
            periods.reverse()  # 按时间正序
        
        if not periods:
            return []
        
        # 获取面谈记录
        if supervisor:
            # 查询特定上级的面谈记录
            cursor.execute('''
                SELECT 
                    ir.period,
                    ir.interviewer,
                    ir.employee_name,
                    ir.is_interviewed,
                    ir.feedback_content
                FROM interview_records ir
                WHERE ir.interviewer = ?
                ORDER BY ir.period
            ''', (supervisor,))
        else:
            # 查询所有上级的面谈记录
            cursor.execute('''
                SELECT 
                    ir.period,
                    ir.interviewer,
                    ir.employee_name,
                    ir.is_interviewed,
                    ir.feedback_content
                FROM interview_records ir
                WHERE ir.interviewer IS NOT NULL AND ir.interviewer != '未知'
                ORDER BY ir.period, ir.interviewer
            ''')
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        # 判断是否真正完成面谈（特殊规则）
        def is_really_interviewed(row):
            # 面谈状态为"否"
            if row['is_interviewed'] != '是':
                return False
            
            feedback = row.get('feedback_content')
            # 面谈内容为空
            if pd.isna(feedback) or feedback is None:
                return False
            
            feedback_str = str(feedback).strip()
            # 面谈内容为"无"、"无填写"等
            if feedback_str in ['无', '无填写', '']:
                return False
            
            # 面谈内容长度<5
            if len(feedback_str) < 5:
                return False
            
            return True
        
        df['really_interviewed'] = df.apply(is_really_interviewed, axis=1)
        
        # 按上级和周期分组统计
        result = []
        for interviewer in df['interviewer'].unique():
            if pd.isna(interviewer) or interviewer == '未知':
                continue
            
            interviewer_data = df[df['interviewer'] == interviewer]
            
            for period in periods:
                period_data = interviewer_data[interviewer_data['period'] == period]
                
                if len(period_data) == 0:
                    continue
                
                total = len(period_data)
                completed = period_data['really_interviewed'].sum()
                rate = (completed / total * 100) if total > 0 else 0
                
                result.append({
                    'period': period,
                    'interviewer': interviewer,
                    'total_count': total,
                    'completed_count': int(completed),
                    'uncompleted_count': total - int(completed),
                    'completion_rate': rate
                })
        
        return result
    
    def get_interview_trend_by_department(self, department, periods=None):
        """
        部门维度的面谈完成率趋势
        
        参数:
            department: 部门名称
            periods: 周期列表（None表示最近6期）
        
        返回:
            每个上级在各个周期的完成率数据
        """
        cursor = self.db.conn.cursor()
        
        # 如果没有指定周期，获取最近6期
        if periods is None:
            cursor.execute('''
                SELECT DISTINCT period 
                FROM interview_records 
                ORDER BY period DESC 
                LIMIT 6
            ''')
            periods = [row[0] for row in cursor.fetchall()]
            periods.reverse()  # 按时间正序
        
        if not periods:
            return []
        
        # 获取该部门在这些周期的所有面谈记录
        # 需要关联performance_results获取部门信息
        cursor.execute('''
            SELECT 
                ir.period,
                ir.interviewer,
                ir.employee_name,
                ir.is_interviewed,
                ir.feedback_content,
                pr.department_l2
            FROM interview_records ir
            LEFT JOIN performance_results pr 
                ON ir.employee_id = pr.employee_id AND ir.period = pr.period
            WHERE pr.department_l2 = ?
            ORDER BY ir.period, ir.interviewer
        ''', (department,))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        # 判断是否真正完成面谈（特殊规则）
        def is_really_interviewed(row):
            # 面谈状态为"否"
            if row['is_interviewed'] != '是':
                return False
            
            feedback = row.get('feedback_content')
            # 面谈内容为空
            if pd.isna(feedback) or feedback is None:
                return False
            
            feedback_str = str(feedback).strip()
            # 面谈内容为"无"、"无填写"等
            if feedback_str in ['无', '无填写', '']:
                return False
            
            # 面谈内容长度<5
            if len(feedback_str) < 5:
                return False
            
            return True
        
        df['really_interviewed'] = df.apply(is_really_interviewed, axis=1)
        
        # 按上级和周期分组统计
        result = []
        for interviewer in df['interviewer'].unique():
            if pd.isna(interviewer) or interviewer == '未知':
                continue
            
            interviewer_data = df[df['interviewer'] == interviewer]
            
            for period in periods:
                period_data = interviewer_data[interviewer_data['period'] == period]
                
                if len(period_data) == 0:
                    continue
                
                total = len(period_data)
                completed = period_data['really_interviewed'].sum()
                rate = (completed / total * 100) if total > 0 else 0
                
                result.append({
                    'period': period,
                    'interviewer': interviewer,
                    'total_count': total,
                    'completed_count': int(completed),
                    'uncompleted_count': total - int(completed),
                    'completion_rate': rate
                })
        
        return result
    
    def analyze_interview_quality(self, period, department=None):
        """
        面谈内容质量分析
        
        参数:
            period: 考核周期
            department: 部门（可选）
        
        返回:
            每条面谈的质量评分和统计
        """
        cursor = self.db.conn.cursor()
        
        # 构建查询
        if department:
            cursor.execute('''
                SELECT 
                    ir.employee_name,
                    ir.interviewer,
                    ir.feedback_content,
                    pr.department_l2
                FROM interview_records ir
                LEFT JOIN performance_results pr 
                    ON ir.employee_id = pr.employee_id AND ir.period = pr.period
                WHERE ir.period = ? AND pr.department_l2 = ?
            ''', (period, department))
        else:
            cursor.execute('''
                SELECT 
                    ir.employee_name,
                    ir.interviewer,
                    ir.feedback_content,
                    pr.department_l2
                FROM interview_records ir
                LEFT JOIN performance_results pr 
                    ON ir.employee_id = pr.employee_id AND ir.period = pr.period
                WHERE ir.period = ?
            ''', (period,))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return []
        
        # 计算质量分
        quality_keywords = ['改进', '目标', '问题', '计划', '提升', '优化', '建议', '发展']
        
        def calculate_quality_score(feedback):
            if pd.isna(feedback) or feedback is None:
                return 0, '无内容'
            
            feedback_str = str(feedback).strip()
            
            # 无效内容
            if feedback_str in ['无', '无填写', ''] or len(feedback_str) < 5:
                return 0, '无效'
            
            score = 0
            quality_level = ''
            
            # 基础分：根据长度
            length = len(feedback_str)
            if length < 10:
                score = 30
                quality_level = '低质量'
            elif length < 50:
                score = 60
                quality_level = '中等'
            else:
                score = 80
                quality_level = '高质量'
            
            # 关键词加分
            keyword_count = sum([1 for kw in quality_keywords if kw in feedback_str])
            score += min(keyword_count * 5, 20)  # 最多加20分
            
            # 重新评级
            if score >= 75:
                quality_level = '高质量'
            elif score >= 50:
                quality_level = '中等'
            else:
                quality_level = '低质量'
            
            return score, quality_level
        
        # 计算每条记录的质量分
        for item in data:
            score, level = calculate_quality_score(item['feedback_content'])
            item['quality_score'] = score
            item['quality_level'] = level
        
        return data
    
    def get_continuous_uninterviewed_employees(self, periods=None, threshold=3):
        """
        识别连续未面谈的员工
        
        参数:
            periods: 周期列表（None表示最近6期）
            threshold: 连续未面谈阈值（默认3期）
        
        返回:
            连续未面谈员工列表
        """
        cursor = self.db.conn.cursor()
        
        # 如果没有指定周期，获取最近6期
        if periods is None:
            cursor.execute('''
                SELECT DISTINCT period 
                FROM interview_records 
                ORDER BY period DESC 
                LIMIT 6
            ''')
            periods = [row[0] for row in cursor.fetchall()]
            periods.reverse()  # 按时间正序
        
        if not periods or len(periods) < threshold:
            return []
        
        # 获取所有员工的面谈记录
        cursor.execute('''
            SELECT 
                ir.employee_id,
                ir.employee_name,
                ir.period,
                ir.is_interviewed,
                ir.feedback_content,
                ir.interviewer,
                pr.department_l2
            FROM interview_records ir
            LEFT JOIN performance_results pr 
                ON ir.employee_id = pr.employee_id AND ir.period = pr.period
            ORDER BY ir.employee_id, ir.period
        ''')
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        # 判断是否真正完成面谈
        def is_really_interviewed(row):
            if row['is_interviewed'] != '是':
                return False
            
            feedback = row.get('feedback_content')
            if pd.isna(feedback) or feedback is None:
                return False
            
            feedback_str = str(feedback).strip()
            if feedback_str in ['无', '无填写', ''] or len(feedback_str) < 5:
                return False
            
            return True
        
        df['really_interviewed'] = df.apply(is_really_interviewed, axis=1)
        
        # 按员工分组，检查连续未面谈
        risk_employees = []
        
        for employee_id in df['employee_id'].unique():
            emp_data = df[df['employee_id'] == employee_id].sort_values('period')
            
            # 只检查最近的几期
            recent_periods = emp_data[emp_data['period'].isin(periods)]
            
            if len(recent_periods) < threshold:
                continue
            
            # 检查最近threshold期是否都未面谈
            latest_records = recent_periods.tail(threshold)
            
            if not latest_records['really_interviewed'].any():
                # 连续未面谈
                risk_employees.append({
                    'employee_id': employee_id,
                    'employee_name': latest_records.iloc[0]['employee_name'],
                    'department': latest_records.iloc[0]['department_l2'],
                    'interviewer': latest_records.iloc[0]['interviewer'],
                    'uninterviewed_periods': latest_records['period'].tolist(),
                    'consecutive_count': len(latest_records)
                })
        
        return risk_employees
    
    def get_interviewer_rankings(self, period):
        """
        获取上级面谈排名
        
        参数:
            period: 考核周期
        
        返回:
            上级排名数据（完成率、质量分等）
        """
        cursor = self.db.conn.cursor()
        
        cursor.execute('''
            SELECT 
                ir.interviewer,
                ir.employee_name,
                ir.is_interviewed,
                ir.feedback_content,
                pr.department_l2
            FROM interview_records ir
            LEFT JOIN performance_results pr 
                ON ir.employee_id = pr.employee_id AND ir.period = pr.period
            WHERE ir.period = ?
        ''', (period,))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        # 判断真正完成
        def is_really_interviewed(row):
            if row['is_interviewed'] != '是':
                return False
            feedback = row.get('feedback_content')
            if pd.isna(feedback) or feedback is None:
                return False
            feedback_str = str(feedback).strip()
            if feedback_str in ['无', '无填写', ''] or len(feedback_str) < 5:
                return False
            return True
        
        df['really_interviewed'] = df.apply(is_really_interviewed, axis=1)
        
        # 计算质量分
        quality_keywords = ['改进', '目标', '问题', '计划', '提升', '优化', '建议', '发展']
        
        def calculate_quality_score(feedback):
            if pd.isna(feedback) or feedback is None:
                return 0
            feedback_str = str(feedback).strip()
            if feedback_str in ['无', '无填写', ''] or len(feedback_str) < 5:
                return 0
            
            score = 0
            length = len(feedback_str)
            if length < 10:
                score = 30
            elif length < 50:
                score = 60
            else:
                score = 80
            
            keyword_count = sum([1 for kw in quality_keywords if kw in feedback_str])
            score += min(keyword_count * 5, 20)
            
            return score
        
        df['quality_score'] = df['feedback_content'].apply(calculate_quality_score)
        
        # 按上级分组统计
        rankings = []
        for interviewer in df['interviewer'].unique():
            if pd.isna(interviewer) or interviewer == '未知':
                continue
            
            interviewer_data = df[df['interviewer'] == interviewer]
            total = len(interviewer_data)
            completed = interviewer_data['really_interviewed'].sum()
            avg_quality = interviewer_data['quality_score'].mean()
            
            rankings.append({
                'interviewer': interviewer,
                'total_count': total,
                'completed_count': int(completed),
                'completion_rate': (completed / total * 100) if total > 0 else 0,
                'avg_quality_score': avg_quality,
                'low_quality_count': len(interviewer_data[interviewer_data['quality_score'] < 50]),
                'department': interviewer_data.iloc[0]['department_l2'] if 'department_l2' in interviewer_data.columns else None
            })
        
        # 按完成率排序
        rankings = sorted(rankings, key=lambda x: x['completion_rate'], reverse=True)
        
        return rankings
    
    # ==================== 绩效分级与分布监控模块 ====================
    
    def get_performance_level(self, score, period_type):
        """
        获取绩效等级（严格遵循分数边界）
        
        参数:
            score: 分数
            period_type: 周期类型（monthly/quarterly/half_yearly/yearly）
        
        返回:
            等级字符串，如果是非年度则返回None
        
        规则:
            - 非年度（月度/季度/半年度）：不生成等级，返回None
            - 年度：
                * A: [90, 100]
                * B: (80, 90)
                * B-: [70, 80]
                * C: [0, 70)
        
        边界规则:
            * 90 → A
            * 80 → B-
            * 70 → B-
            * <70 → C
        """
        # 非年度不生成等级
        if period_type != 'yearly':
            return None
        
        # 年度才生成等级
        if pd.isna(score):
            return None
        
        score = float(score)
        
        # 严格按边界判断
        if score >= 90:
            return 'A'
        elif score >= 80:  # (80, 90)，但80本身归到B-
            if score == 80:
                return 'B-'
            else:
                return 'B'
        elif score >= 70:  # [70, 80]
            return 'B-'
        else:  # [0, 70)
            return 'C'
    
    def get_score_interval(self, score):
        """
        获取分数所在区间（用于分析，不区分周期类型）
        
        辅助区间（仅用于分析）:
            * ≥90 → 高绩效
            * 80–90 → 良好
            * 70–80 → 待提升
            * <70 → 需关注
        """
        if pd.isna(score):
            return None
        
        score = float(score)
        
        if score >= 90:
            return '≥90 (高绩效)'
        elif score >= 80:
            return '80-90 (良好)'
        elif score >= 70:
            return '70-80 (待提升)'
        else:
            return '<70 (需关注)'
    
    def get_score_distribution(self, period, department=None):
        """
        获取当前周期的分数分布
        
        参数:
            period: 考核周期
            department: 部门名称（可选，None表示全部）
        
        返回:
            分布统计数据
        """
        cursor = self.db.conn.cursor()
        
        if department and department != "全部":
            cursor.execute('''
                SELECT total_score, employee_name, department_l2
                FROM performance_results
                WHERE period = ? AND total_score IS NOT NULL AND department_l2 = ?
                ORDER BY total_score DESC
            ''', (period, department))
        else:
            cursor.execute('''
                SELECT total_score, employee_name, department_l2
                FROM performance_results
                WHERE period = ? AND total_score IS NOT NULL
                ORDER BY total_score DESC
            ''', (period,))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        # 添加分数区间
        df['interval'] = df['total_score'].apply(self.get_score_interval)
        
        # 统计各区间人数
        distribution = {
            '≥90 (高绩效)': 0,
            '80-90 (良好)': 0,
            '70-80 (待提升)': 0,
            '<70 (需关注)': 0
        }
        
        interval_counts = df['interval'].value_counts()
        for interval, count in interval_counts.items():
            distribution[interval] = int(count)
        
        total = len(df)
        
        return {
            'period': period,
            'department': department if department else '全部',
            'total_count': total,
            'distribution': distribution,
            'ratios': {k: (v / total * 100 if total > 0 else 0) for k, v in distribution.items()},
            'scores': df['total_score'].tolist(),
            'avg_score': float(df['total_score'].mean()),
            'std_score': float(df['total_score'].std()),
            'max_score': float(df['total_score'].max()),
            'min_score': float(df['total_score'].min()),
            'data': data
        }
    
    def get_avg_score_distribution(self, periods=None, n_periods=6, department=None):
        """
        获取多周期平均分分布（用于模拟年度评分基础）
        
        参数:
            periods: 周期列表（None表示最近N期）
            n_periods: 最近几期（默认6期）
            department: 部门名称（可选，None表示全部）
        
        返回:
            基于员工平均分的分布统计
        """
        cursor = self.db.conn.cursor()
        
        # 如果没有指定周期，获取最近N期
        if periods is None:
            cursor.execute('''
                SELECT DISTINCT period 
                FROM performance_results 
                ORDER BY period DESC 
                LIMIT ?
            ''', (n_periods,))
            periods = [row[0] for row in cursor.fetchall()]
        
        if not periods:
            return None
        
        # 获取这些周期的所有数据
        placeholders = ','.join(['?'] * len(periods))
        
        if department and department != "全部":
            cursor.execute(f'''
                SELECT employee_id, employee_name, department_l2, period, total_score
                FROM performance_results
                WHERE period IN ({placeholders}) AND total_score IS NOT NULL AND department_l2 = ?
            ''', (*periods, department))
        else:
            cursor.execute(f'''
                SELECT employee_id, employee_name, department_l2, period, total_score
                FROM performance_results
                WHERE period IN ({placeholders}) AND total_score IS NOT NULL
            ''', periods)
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        # 按员工分组计算平均分
        employee_avg = df.groupby(['employee_id', 'employee_name', 'department_l2']).agg({
            'total_score': 'mean'
        }).reset_index()
        
        employee_avg.columns = ['employee_id', 'employee_name', 'department_l2', 'avg_score']
        
        # 添加分数区间
        employee_avg['interval'] = employee_avg['avg_score'].apply(self.get_score_interval)
        
        # 统计各区间人数
        distribution = {
            '≥90 (高绩效)': 0,
            '80-90 (良好)': 0,
            '70-80 (待提升)': 0,
            '<70 (需关注)': 0
        }
        
        interval_counts = employee_avg['interval'].value_counts()
        for interval, count in interval_counts.items():
            distribution[interval] = int(count)
        
        total = len(employee_avg)
        
        return {
            'periods': periods,
            'period_count': len(periods),
            'department': department if department else '全部',
            'total_count': total,
            'distribution': distribution,
            'ratios': {k: (v / total * 100 if total > 0 else 0) for k, v in distribution.items()},
            'avg_scores': employee_avg['avg_score'].tolist(),
            'avg_score': float(employee_avg['avg_score'].mean()),
            'std_score': float(employee_avg['avg_score'].std()),
            'max_score': float(employee_avg['avg_score'].max()),
            'min_score': float(employee_avg['avg_score'].min()),
            'employee_data': employee_avg.to_dict('records')
        }
    
    def analyze_distribution_health(self, distribution_data):
        """
        分析分布健康度
        
        参数:
            distribution_data: get_score_distribution或get_avg_score_distribution的返回值
        
        返回:
            健康度分析结果
        """
        if not distribution_data:
            return None
        
        ratios = distribution_data['ratios']
        avg_score = distribution_data['avg_score']
        std_score = distribution_data['std_score']
        
        issues = []
        suggestions = []
        health_score = 100  # 满分100
        
        # 1. ≥90 占比 > 40% → 高分过多
        if ratios['≥90 (高绩效)'] > 40:
            issues.append(f"⚠️ 高分（≥90）占比过高: {ratios['≥90 (高绩效)']:.1f}% (建议<40%)")
            suggestions.append("评分标准可能偏宽松，建议提高评分严格度")
            health_score -= 15
        
        # 2. 80–90 占比 > 60% → 分数集中
        if ratios['80-90 (良好)'] > 60:
            issues.append(f"⚠️ 分数集中在80-90: {ratios['80-90 (良好)']:.1f}% (建议<60%)")
            suggestions.append("区分度不足，建议拉开优秀与普通的差距")
            health_score -= 20
        
        # 3. <70 占比 < 5% → 低分过少
        if ratios['<70 (需关注)'] < 5:
            issues.append(f"⚠️ 低分（<70）占比过少: {ratios['<70 (需关注)']:.1f}% (建议>5%)")
            suggestions.append("缺乏淘汰空间，建议识别并标记待改进员工")
            health_score -= 10
        
        # 4. 标准差 < 5 → 未有效拉开差距
        if std_score < 5:
            issues.append(f"⚠️ 标准差过小: {std_score:.2f} (建议>5)")
            suggestions.append("分数差距过小，未能有效区分绩效差异")
            health_score -= 15
        
        # 5. 平均分过高或过低
        if avg_score > 88:
            issues.append(f"⚠️ 平均分过高: {avg_score:.2f} (建议85-88)")
            suggestions.append("整体评分偏高，建议适当收紧评分标准")
            health_score -= 10
        elif avg_score < 75:
            issues.append(f"⚠️ 平均分过低: {avg_score:.2f} (建议80-85)")
            suggestions.append("整体评分偏低，可能影响员工士气")
            health_score -= 10
        
        # 健康等级
        if health_score >= 90:
            health_level = "优秀"
            health_color = "success"
        elif health_score >= 75:
            health_level = "良好"
            health_color = "info"
        elif health_score >= 60:
            health_level = "一般"
            health_color = "warning"
        else:
            health_level = "需改进"
            health_color = "error"
        
        return {
            'health_score': max(0, health_score),
            'health_level': health_level,
            'health_color': health_color,
            'avg_score': avg_score,
            'std_score': std_score,
            'issues': issues,
            'suggestions': suggestions,
            'summary': self._generate_health_summary(health_level, issues, suggestions)
        }
    
    def _generate_health_summary(self, level, issues, suggestions):
        """生成健康度总结"""
        if level == "优秀":
            summary = "✅ **分布健康度优秀**\n\n绩效分数分布合理，区分度良好，符合正态分布预期。"
        elif level == "良好":
            summary = "✔️ **分布健康度良好**\n\n绩效分数分布基本合理，存在小幅优化空间。"
        elif level == "一般":
            summary = "⚠️ **分布健康度一般**\n\n绩效分数分布存在一定问题，建议关注以下方面："
        else:
            summary = "❌ **分布健康度需改进**\n\n绩效分数分布存在明显问题，需要重点优化："
        
        if issues:
            summary += "\n\n**发现的问题：**\n"
            for issue in issues:
                summary += f"- {issue}\n"
        
        if suggestions:
            summary += "\n**改进建议：**\n"
            for suggestion in suggestions:
                summary += f"- {suggestion}\n"
        
        return summary
    
    def get_department_distribution(self, period):
        """
        获取部门分数分布对比
        
        参数:
            period: 考核周期
        
        返回:
            各部门的分布统计
        """
        cursor = self.db.conn.cursor()
        
        cursor.execute('''
            SELECT department_l2, total_score, employee_name
            FROM performance_results
            WHERE period = ? AND total_score IS NOT NULL AND department_l2 IS NOT NULL
            ORDER BY department_l2, total_score DESC
        ''', (period,))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        # 添加分数区间
        df['interval'] = df['total_score'].apply(self.get_score_interval)
        
        # 按部门分组统计
        dept_stats = []
        
        for dept in df['department_l2'].unique():
            dept_data = df[df['department_l2'] == dept]
            
            # 统计各区间
            distribution = {
                '≥90 (高绩效)': 0,
                '80-90 (良好)': 0,
                '70-80 (待提升)': 0,
                '<70 (需关注)': 0
            }
            
            interval_counts = dept_data['interval'].value_counts()
            for interval, count in interval_counts.items():
                distribution[interval] = int(count)
            
            total = len(dept_data)
            
            # 计算标准差（处理NaN和小样本）
            std_value = dept_data['total_score'].std()
            std_score = float(std_value) if pd.notna(std_value) else 0.0
            
            dept_stats.append({
                'department': dept,
                'total_count': total,
                'avg_score': float(dept_data['total_score'].mean()),
                'std_score': std_score,
                'max_score': float(dept_data['total_score'].max()),
                'min_score': float(dept_data['total_score'].min()),
                'distribution': distribution,
                'ratios': {k: (v / total * 100 if total > 0 else 0) for k, v in distribution.items()}
            })
        
        # 按平均分排序
        dept_stats.sort(key=lambda x: x['avg_score'], reverse=True)
        
        return {
            'period': period,
            'departments': dept_stats
        }
    
    def analyze_forced_distribution(self, avg_score_data, target_ratios=None):
        """
        强制分布适配分析
        
        参数:
            avg_score_data: get_avg_score_distribution的返回值
            target_ratios: 目标比例字典，默认 {'A': 20, 'B': 50, 'B-': 20, 'C': 10}
        
        返回:
            适配分析结果
        """
        if not avg_score_data:
            return None
        
        # 默认目标比例
        if target_ratios is None:
            target_ratios = {
                'A': 20,   # 20%
                'B': 50,   # 50%
                'B-': 20,  # 20%
                'C': 10    # 10%
            }
        
        employee_data = avg_score_data['employee_data']
        total_count = avg_score_data['total_count']
        
        # 基于平均分排序
        sorted_employees = sorted(employee_data, key=lambda x: x['avg_score'], reverse=True)
        
        # 计算目标人数
        target_counts = {
            'A': int(total_count * target_ratios['A'] / 100),
            'B': int(total_count * target_ratios['B'] / 100),
            'B-': int(total_count * target_ratios['B-'] / 100),
            'C': int(total_count * target_ratios['C'] / 100)
        }
        
        # 调整确保总数一致
        diff = total_count - sum(target_counts.values())
        if diff > 0:
            target_counts['B'] += diff
        
        # 模拟分配等级
        simulated_levels = []
        current_idx = 0
        
        for level in ['A', 'B', 'B-', 'C']:
            count = target_counts[level]
            for i in range(count):
                if current_idx < len(sorted_employees):
                    emp = sorted_employees[current_idx]
                    simulated_levels.append({
                        'employee_name': emp['employee_name'],
                        'avg_score': emp['avg_score'],
                        'simulated_level': level,
                        'natural_level': self.get_performance_level(emp['avg_score'], 'yearly')
                    })
                    current_idx += 1
        
        # 分析适配度
        matches = 0
        mismatches = []
        
        for sim in simulated_levels:
            if sim['simulated_level'] == sim['natural_level']:
                matches += 1
            else:
                mismatches.append(sim)
        
        match_ratio = (matches / total_count * 100) if total_count > 0 else 0
        
        # 判断适配情况
        if match_ratio >= 80:
            fit_status = "自然满足"
            fit_color = "success"
            fit_message = "✅ 当前分数分布可自然满足强制分布要求，无需大幅调整"
        elif match_ratio >= 60:
            fit_status = "基本适配"
            fit_color = "info"
            fit_message = "⚠️ 需要适当调整部分员工等级，但幅度较小"
        else:
            fit_status = "需要调整"
            fit_color = "warning"
            fit_message = "❌ 分数分布与强制分布差异较大，年底需要显著调整"
        
        return {
            'target_ratios': target_ratios,
            'target_counts': target_counts,
            'total_count': total_count,
            'match_ratio': match_ratio,
            'fit_status': fit_status,
            'fit_color': fit_color,
            'fit_message': fit_message,
            'simulated_levels': simulated_levels,
            'mismatch_count': len(mismatches),
            'mismatch_examples': mismatches[:10]  # 只返回前10个不匹配的例子
        }

if __name__ == '__main__':
    # 测试代码
    db = PerformanceDB()
    db.connect()
    processor = DataProcessor(db)
    
    # 测试处理文件
    result1 = processor.process_performance_results(
        '/mnt/user-data/uploads/_2026年2月月度考核_绩效结果导出.xlsx'
    )
    print(result1)
    
    result2 = processor.process_indicator_info(
        '/mnt/user-data/uploads/_2026年2月月度考核_指标评价信息导出.xlsx'
    )
    print(result2)
    
    db.close()
