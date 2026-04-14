#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周期筛选诊断和修复脚本
用于检查和修复数据库中的period_type字段
"""
import sys
import sqlite3

print("=" * 80)
print("周期筛选诊断和修复工具")
print("=" * 80)

# 连接数据库
try:
    conn = sqlite3.connect('performance_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    print("✅ 成功连接到数据库")
except Exception as e:
    print(f"❌ 连接数据库失败: {e}")
    sys.exit(1)

# 1. 检查所有周期及其类型
print("\n" + "=" * 80)
print("步骤1：检查数据库中的周期数据")
print("=" * 80)

cursor.execute('''
    SELECT DISTINCT period, period_type, COUNT(*) as count
    FROM performance_results
    GROUP BY period, period_type
    ORDER BY period DESC
''')

rows = cursor.fetchall()

if not rows:
    print("⚠️ 数据库中没有数据")
    conn.close()
    sys.exit(0)

print(f"\n找到 {len(rows)} 个周期：\n")
print(f"{'周期':<30} {'类型':<15} {'人数':<10}")
print("-" * 60)

problem_periods = []
for row in rows:
    period = row['period']
    period_type = row['period_type']
    count = row['count']
    
    # 检查period_type是否为None或空
    if not period_type:
        problem_periods.append(period)
        print(f"{period:<30} {'❌ NULL/空':<15} {count:<10}")
    else:
        print(f"{period:<30} {period_type:<15} {count:<10}")

# 2. 检查具体员工的数据
print("\n" + "=" * 80)
print("步骤2：检查方飞龙(2833)的数据")
print("=" * 80)

cursor.execute('''
    SELECT period, period_type, total_score
    FROM performance_results
    WHERE employee_id = '2833'
    ORDER BY period DESC
''')

rows = cursor.fetchall()

if rows:
    print(f"\n找到 {len(rows)} 条记录：\n")
    print(f"{'周期':<30} {'类型':<15} {'分数':<10}")
    print("-" * 60)
    
    for row in rows:
        period = row['period']
        period_type = row['period_type'] or '❌ NULL'
        score = row['total_score'] or 'N/A'
        print(f"{period:<30} {period_type:<15} {score:<10}")
    
    # 统计各类型数量
    print("\n类型统计：")
    cursor.execute('''
        SELECT period_type, COUNT(*) as count
        FROM performance_results
        WHERE employee_id = '2833'
        GROUP BY period_type
    ''')
    type_stats = cursor.fetchall()
    for row in type_stats:
        ptype = row['period_type'] or 'NULL/空'
        count = row['count']
        print(f"  {ptype}: {count}条")
else:
    print("\n⚠️ 未找到方飞龙的数据")

# 3. 如果发现问题，提供修复选项
if problem_periods:
    print("\n" + "=" * 80)
    print("步骤3：发现period_type为空的周期")
    print("=" * 80)
    print(f"\n以下 {len(problem_periods)} 个周期的period_type为空：")
    for p in problem_periods:
        print(f"  - {p}")
    
    print("\n是否自动修复这些周期的period_type？")
    print("修复规则：")
    print("  - 包含'月度' → monthly")
    print("  - 包含'季度' 或 'Q' → quarterly")
    print("  - 包含'半年' → half_yearly")
    print("  - 包含'年度' → yearly")
    
    response = input("\n输入 'yes' 开始修复，其他键退出: ").strip().lower()
    
    if response == 'yes':
        print("\n开始修复...")
        fixed_count = 0
        
        for period in problem_periods:
            # 判断周期类型
            if '月度' in period:
                new_type = 'monthly'
            elif '季度' in period or 'Q' in period.upper():
                new_type = 'quarterly'
            elif '半年' in period:
                new_type = 'half_yearly'
            elif '年度' in period:
                new_type = 'yearly'
            else:
                print(f"  ⚠️ 无法判断类型: {period}")
                continue
            
            try:
                cursor.execute('''
                    UPDATE performance_results
                    SET period_type = ?
                    WHERE period = ? AND period_type IS NULL
                ''', (new_type, period))
                
                affected = cursor.rowcount
                print(f"  ✅ {period} → {new_type} ({affected}条记录)")
                fixed_count += affected
            except Exception as e:
                print(f"  ❌ 修复失败 {period}: {e}")
        
        # 提交更改
        conn.commit()
        print(f"\n✅ 修复完成！共修复 {fixed_count} 条记录")
        print("请重启系统以使更改生效")
    else:
        print("\n取消修复")
else:
    print("\n" + "=" * 80)
    print("✅ 所有周期的period_type都已正确设置")
    print("=" * 80)

# 4. 最终验证
print("\n" + "=" * 80)
print("步骤4：最终验证")
print("=" * 80)

cursor.execute('''
    SELECT 
        SUM(CASE WHEN period_type IS NULL THEN 1 ELSE 0 END) as null_count,
        SUM(CASE WHEN period_type = 'monthly' THEN 1 ELSE 0 END) as monthly_count,
        SUM(CASE WHEN period_type = 'quarterly' THEN 1 ELSE 0 END) as quarterly_count,
        SUM(CASE WHEN period_type = 'half_yearly' THEN 1 ELSE 0 END) as half_yearly_count,
        SUM(CASE WHEN period_type = 'yearly' THEN 1 ELSE 0 END) as yearly_count
    FROM performance_results
''')

stats = cursor.fetchone()

print("\n数据库整体统计：")
print(f"  NULL/空: {stats['null_count']}条")
print(f"  月度 (monthly): {stats['monthly_count']}条")
print(f"  季度 (quarterly): {stats['quarterly_count']}条")
print(f"  半年度 (half_yearly): {stats['half_yearly_count']}条")
print(f"  年度 (yearly): {stats['yearly_count']}条")

if stats['null_count'] == 0:
    print("\n✅ 所有记录的period_type都已正确设置！")
else:
    print(f"\n⚠️ 仍有 {stats['null_count']} 条记录的period_type为空")

conn.close()

print("\n" + "=" * 80)
print("✅ 诊断完成")
print("=" * 80)
