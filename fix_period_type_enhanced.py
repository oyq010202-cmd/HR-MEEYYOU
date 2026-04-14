#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周期类型修复工具 - 增强版
支持修复 NULL、空值和 unknown 类型
"""
import sys
import sqlite3
import re

print("=" * 80)
print("周期类型修复工具 - 增强版")
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

def smart_detect_period_type(period):
    """
    智能识别周期类型
    
    规则：
    1. 包含"月度" → monthly
    2. 包含"季度"或"Q"或"q" → quarterly
    3. 包含"半年" → half_yearly
    4. 包含"年度" → yearly
    5. 格式为"XX年XX月"（只有年月，无其他）→ monthly
    6. 包含"Q1"/"Q2"/"Q3"/"Q4" → quarterly
    """
    period = str(period).strip()
    
    # 明确包含周期类型关键词
    if '月度' in period:
        return 'monthly'
    elif '季度' in period or 'Q' in period.upper():
        return 'quarterly'
    elif '半年' in period:
        return 'half_yearly'
    elif '年度' in period:
        return 'yearly'
    
    # 智能判断：检查是否为"年月"格式
    # 例如: "26年2月", "2026年1月", "25年12月"
    month_pattern = r'^\d{2,4}年\d{1,2}月$'
    if re.match(month_pattern, period):
        return 'monthly'
    
    # 检查是否包含季度标识
    quarter_patterns = [r'Q[1-4]', r'q[1-4]', r'第[一二三四]季度']
    for pattern in quarter_patterns:
        if re.search(pattern, period):
            return 'quarterly'
    
    return None

# 1. 检查所有周期
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
print(f"{'周期':<35} {'当前类型':<20} {'人数':<10} {'建议类型':<15}")
print("-" * 85)

problem_periods = []
for row in rows:
    period = row['period']
    current_type = row['period_type'] or 'NULL'
    count = row['count']
    
    # 智能检测应该是什么类型
    suggested_type = smart_detect_period_type(period)
    
    # 判断是否需要修复
    needs_fix = False
    if not row['period_type'] or row['period_type'] == 'unknown':
        needs_fix = True
        problem_periods.append((period, suggested_type))
    
    # 显示
    status = "❌ 需修复" if needs_fix else "✅ 正常"
    suggested_display = suggested_type if suggested_type else "无法判断"
    
    print(f"{period:<35} {current_type:<20} {count:<10} {suggested_display:<15} {status}")

# 2. 检查具体员工
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
    print(f"{'周期':<35} {'类型':<20} {'分数':<10}")
    print("-" * 70)
    
    for row in rows:
        period = row['period']
        period_type = row['period_type'] or 'NULL'
        score = row['total_score'] or 'N/A'
        
        status = "❌" if (not row['period_type'] or row['period_type'] == 'unknown') else "✅"
        print(f"{period:<35} {period_type:<20} {score:<10} {status}")

# 3. 修复
if problem_periods:
    print("\n" + "=" * 80)
    print("步骤3：发现需要修复的周期")
    print("=" * 80)
    print(f"\n以下 {len(problem_periods)} 个周期需要修复：\n")
    
    for period, suggested_type in problem_periods:
        if suggested_type:
            print(f"  📝 {period:<35} → {suggested_type}")
        else:
            print(f"  ⚠️ {period:<35} → 无法自动判断类型")
    
    print("\n是否开始修复？")
    response = input("输入 'yes' 开始修复，其他键退出: ").strip().lower()
    
    if response == 'yes':
        print("\n开始修复...")
        fixed_count = 0
        failed_count = 0
        
        for period, suggested_type in problem_periods:
            if not suggested_type:
                print(f"  ⚠️ 跳过（无法判断）: {period}")
                failed_count += 1
                continue
            
            try:
                # 修复NULL和unknown两种情况
                cursor.execute('''
                    UPDATE performance_results
                    SET period_type = ?
                    WHERE period = ? AND (period_type IS NULL OR period_type = 'unknown')
                ''', (suggested_type, period))
                
                affected = cursor.rowcount
                if affected > 0:
                    print(f"  ✅ {period:<35} → {suggested_type:<15} ({affected}条记录)")
                    fixed_count += affected
                else:
                    print(f"  ⚠️ {period:<35} → 没有记录被修复")
            except Exception as e:
                print(f"  ❌ 修复失败 {period}: {e}")
                failed_count += 1
        
        # 提交更改
        if fixed_count > 0:
            conn.commit()
            print(f"\n✅ 修复完成！共修复 {fixed_count} 条记录")
            if failed_count > 0:
                print(f"⚠️ {failed_count} 个周期无法自动修复，请手动处理")
            print("\n🔄 请重启系统以使更改生效！")
        else:
            print("\n⚠️ 没有记录被修复")
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
        SUM(CASE WHEN period_type IS NULL OR period_type = 'unknown' THEN 1 ELSE 0 END) as problem_count,
        SUM(CASE WHEN period_type = 'monthly' THEN 1 ELSE 0 END) as monthly_count,
        SUM(CASE WHEN period_type = 'quarterly' THEN 1 ELSE 0 END) as quarterly_count,
        SUM(CASE WHEN period_type = 'half_yearly' THEN 1 ELSE 0 END) as half_yearly_count,
        SUM(CASE WHEN period_type = 'yearly' THEN 1 ELSE 0 END) as yearly_count
    FROM performance_results
''')

stats = cursor.fetchone()

print("\n数据库整体统计：")
print(f"  ❌ NULL/unknown: {stats['problem_count']}条")
print(f"  ✅ 月度 (monthly): {stats['monthly_count']}条")
print(f"  ✅ 季度 (quarterly): {stats['quarterly_count']}条")
print(f"  ✅ 半年度 (half_yearly): {stats['half_yearly_count']}条")
print(f"  ✅ 年度 (yearly): {stats['yearly_count']}条")

if stats['problem_count'] == 0:
    print("\n" + "🎉" * 40)
    print("✅ 所有记录的period_type都已正确设置！")
    print("🎉" * 40)
    print("\n下一步：")
    print("1. 关闭此窗口")
    print("2. 重启系统（Ctrl+C → run.bat）")
    print("3. 测试员工绩效追踪的周期筛选功能")
else:
    print(f"\n⚠️ 仍有 {stats['problem_count']} 条记录需要处理")
    print("建议：检查这些记录的周期名称格式是否正确")

conn.close()

print("\n" + "=" * 80)
print("✅ 诊断完成")
print("=" * 80)
