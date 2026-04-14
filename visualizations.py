import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

class PerformanceVisualizer:
    """绩效数据可视化类"""
    
    # 美柚风格颜色配置
    COLORS = {
        'primary': '#FF6B9A',      # 主粉色
        'primary_light': '#FFB3D4', # 浅粉色
        'primary_lighter': '#FFE5ED', # 极浅粉
        'secondary': '#60A5FA',     # 柔和蓝
        'success': '#34D399',       # 柔和绿
        'warning': '#FBBF24',       # 柔和黄
        'error': '#F87171',         # 柔和红
        'gray': '#525252',          # 深灰
        'gray_light': '#A3A3A3',    # 浅灰
        
        # 多色方案（用于多系列图表）
        'palette': ['#FF6B9A', '#FFB3D4', '#60A5FA', '#34D399', '#FBBF24', '#F87171'],
        
        # 顺序色（用于热力图、渐变）
        'sequential': ['#FFF5F8', '#FFE5ED', '#FFCCE0', '#FFB3D4', '#FF8AB8', '#FF6B9A', '#E6548A', '#CC3D7A'],
    }
    
    # 图表通用布局配置
    LAYOUT_CONFIG = {
        'font': {
            'family': '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif',
            'size': 13,
            'color': '#525252'
        },
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'margin': {'t': 40, 'r': 20, 'b': 40, 'l': 60},
        'hovermode': 'closest',
        'hoverlabel': {
            'bgcolor': 'white',
            'bordercolor': '#FFB3D4',
            'font': {'size': 13, 'color': '#525252'}
        },
        'xaxis': {
            'gridcolor': '#F5F5F5',
            'gridwidth': 1,
            'showgrid': True,
            'zeroline': False,
            'linecolor': '#E8E8E8',
        },
        'yaxis': {
            'gridcolor': '#F5F5F5',
            'gridwidth': 1,
            'showgrid': True,
            'zeroline': False,
            'linecolor': '#E8E8E8',
        },
        'legend': {
            'bgcolor': 'rgba(255,255,255,0.9)',
            'bordercolor': '#E8E8E8',
            'borderwidth': 1,
            'font': {'size': 12}
        }
    }
    
    @staticmethod
    def create_score_trend_chart(history_data):
        """创建总分趋势图"""
        # 确保数据是列表格式
        if not history_data:
            return None
        
        # 转换为DataFrame并确保数据类型正确
        df = pd.DataFrame(history_data)
        
        if df.empty:
            return None
        
        # 确保所有字段都是正确的数据类型
        if 'period' in df.columns:
            df['period'] = df['period'].astype(str)
        if 'total_score' in df.columns:
            df['total_score'] = pd.to_numeric(df['total_score'], errors='coerce')
        if 'self_score' in df.columns:
            df['self_score'] = pd.to_numeric(df['self_score'], errors='coerce')
        if 'manager_score' in df.columns:
            df['manager_score'] = pd.to_numeric(df['manager_score'], errors='coerce')
        
        df = df.sort_values('period')
        
        fig = go.Figure()
        
        # 总分折线
        fig.add_trace(go.Scatter(
            x=df['period'].tolist(),
            y=df['total_score'].tolist(),
            mode='lines+markers',
            name='总分',
            line=dict(color='#2E86DE', width=3),
            marker=dict(size=10, color='#2E86DE'),
            hovertemplate='<b>%{x}</b><br>总分: %{y:.2f}<extra></extra>'
        ))
        
        # 自评分折线
        if 'self_score' in df.columns and df['self_score'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['period'].tolist(),
                y=df['self_score'].tolist(),
                mode='lines+markers',
                name='自评',
                line=dict(color='#54A0FF', width=2, dash='dot'),
                marker=dict(size=8, color='#54A0FF'),
                hovertemplate='<b>%{x}</b><br>自评: %{y:.2f}<extra></extra>'
            ))
        
        # 上级评分折线
        if 'manager_score' in df.columns and df['manager_score'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['period'].tolist(),
                y=df['manager_score'].tolist(),
                mode='lines+markers',
                name='上级评',
                line=dict(color='#48DBFB', width=2, dash='dot'),
                marker=dict(size=8, color='#48DBFB'),
                hovertemplate='<b>%{x}</b><br>上级评: %{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title='绩效分数趋势',
            xaxis_title='考核周期',
            yaxis_title='分数',
            hovermode='x unified',
            height=400,
            template='plotly_white',
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def create_rank_trend_chart(history_data):
        """创建排名趋势图"""
        if not history_data:
            return None
            
        df = pd.DataFrame(history_data)
        
        if df.empty or 'dept_rank' not in df.columns:
            return None
        
        # 确保数据类型正确
        df['period'] = df['period'].astype(str)
        df['dept_rank'] = pd.to_numeric(df['dept_rank'], errors='coerce')
        
        df = df.sort_values('period')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['period'].tolist(),
            y=df['dept_rank'].tolist(),
            mode='lines+markers',
            name='部门排名',
            line=dict(color='#EE5A6F', width=3),
            marker=dict(size=12, color='#EE5A6F'),
            hovertemplate='<b>%{x}</b><br>排名: 第%{y}名<extra></extra>'
        ))
        
        fig.update_layout(
            title='部门排名变化',
            xaxis_title='考核周期',
            yaxis_title='排名',
            yaxis=dict(autorange='reversed'),  # 排名越小越好，所以反转y轴
            hovermode='x unified',
            height=300,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_coefficient_trend_chart(history_data):
        """创建系数趋势图"""
        if not history_data:
            return None
        
        # 转换为DataFrame并确保数据类型正确
        df = pd.DataFrame(history_data)
        
        if df.empty or 'coefficient' not in df.columns:
            return None
        
        # 过滤掉没有系数的记录
        df = df[df['coefficient'].notna()]
        
        if df.empty:
            return None
        
        # 确保数据类型正确
        df['period'] = df['period'].astype(str)
        df['coefficient'] = pd.to_numeric(df['coefficient'], errors='coerce')
        
        df = df.sort_values('period')
        
        fig = go.Figure()
        
        # 系数折线
        fig.add_trace(go.Scatter(
            x=df['period'].tolist(),
            y=df['coefficient'].tolist(),
            mode='lines+markers',
            name='绩效系数',
            line=dict(color='#6C5CE7', width=3),
            marker=dict(size=12, color='#6C5CE7'),
            hovertemplate='<b>%{x}</b><br>系数: %{y:.2f}<extra></extra>'
        ))
        
        # 添加基准线（系数=1.0）
        fig.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="gray",
            annotation_text="基准线 (1.0)",
            annotation_position="right"
        )
        
        fig.update_layout(
            title='绩效系数趋势',
            xaxis_title='考核周期',
            yaxis_title='系数',
            hovermode='x unified',
            height=350,
            template='plotly_white',
            yaxis=dict(range=[0.5, 1.5])  # 通常系数在0.5-1.5之间
        )
        
        return fig
    
    @staticmethod
    def create_radar_chart(indicators_data, period):
        """创建雷达图：显示各项指标得分"""
        if not indicators_data:
            return None
            
        df = pd.DataFrame(indicators_data)
        
        if df.empty:
            return None
        
        # 确保数据类型正确
        if 'indicator_module' in df.columns:
            df['indicator_module'] = df['indicator_module'].astype(str)
        if 'score' in df.columns:
            df['score'] = pd.to_numeric(df['score'], errors='coerce')
        
        # 按模块分组聚合（取平均分）
        df_agg = df.groupby('indicator_module')['score'].mean().reset_index()
        
        categories = df_agg['indicator_module'].tolist()
        values = df_agg['score'].tolist()
        
        # 闭合雷达图
        categories = categories + [categories[0]]
        values = values + [values[0]]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=str(period),
            line=dict(color='#10AC84', width=2),
            fillcolor='rgba(16, 172, 132, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            title='考核模块得分分布',
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_indicator_detail_chart(indicators_data):
        """创建指标明细柱状图"""
        if not indicators_data:
            return None
            
        df = pd.DataFrame(indicators_data)
        
        if df.empty:
            return None
        
        # 确保数据类型正确
        if 'indicator_name' in df.columns:
            df['indicator_name'] = df['indicator_name'].astype(str)
        if 'score' in df.columns:
            df['score'] = pd.to_numeric(df['score'], errors='coerce')
        if 'weight' in df.columns:
            df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
        
        # 按得分排序
        df = df.sort_values('score', ascending=True)
        
        # 根据得分设置颜色
        colors = ['#EE5A6F' if x < 80 else '#FFA502' if x < 90 else '#1DD1A1' 
                  for x in df['score']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df['indicator_name'].tolist(),
            x=df['score'].tolist(),
            orientation='h',
            marker=dict(color=colors),
            text=df['score'].round(2).tolist(),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>得分: %{x:.2f}<br>权重: %{customdata}%<extra></extra>',
            customdata=df['weight'].tolist()
        ))
        
        fig.update_layout(
            title='各项指标得分明细',
            xaxis_title='得分',
            yaxis_title='',
            height=max(400, len(df) * 30),
            template='plotly_white',
            xaxis=dict(range=[0, 105])
        )
        
        return fig
    
    @staticmethod
    def create_department_distribution(dept_data):
        """创建部门分数分布直方图"""
        if not dept_data:
            return None
            
        df = pd.DataFrame(dept_data)
        
        if df.empty:
            return None
        
        # 确保数据类型正确
        if 'total_score' in df.columns:
            df['total_score'] = pd.to_numeric(df['total_score'], errors='coerce')
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=df['total_score'].tolist(),
            nbinsx=10,
            marker=dict(
                color='#5F27CD',
                line=dict(color='white', width=1)
            ),
            hovertemplate='分数区间: %{x}<br>人数: %{y}<extra></extra>'
        ))
        
        # 添加平均分线
        avg_score = df['total_score'].mean()
        fig.add_vline(
            x=avg_score,
            line_dash="dash",
            line_color="red",
            annotation_text=f"平均分: {avg_score:.1f}",
            annotation_position="top"
        )
        
        fig.update_layout(
            title='部门绩效分数分布',
            xaxis_title='分数',
            yaxis_title='人数',
            height=400,
            template='plotly_white',
            bargap=0.1
        )
        
        return fig
    
    @staticmethod
    def create_department_ranking(dept_data):
        """创建部门排名表"""
        df = pd.DataFrame(dept_data)
        
        if df.empty:
            return None
        
        # 选择需要的列并排序
        # 检查是否有系数字段
        if 'coefficient' in df.columns:
            df_display = df[['dept_rank', 'employee_name', 'total_score', 'coefficient', 'manager_comment']].copy()
            df_display['coefficient'] = df_display['coefficient'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
            df_display = df_display.sort_values('dept_rank')
            df_display.columns = ['排名', '姓名', '总分', '系数', '上级评语']
        else:
            df_display = df[['dept_rank', 'employee_name', 'total_score', 'manager_comment']].copy()
            df_display = df_display.sort_values('dept_rank')
            df_display.columns = ['排名', '姓名', '总分', '上级评语']
        
        # 根据分数设置颜色
        colors = []
        for score in df_display['总分']:
            if score >= 90:
                colors.append('#D1F2EB')  # 优秀-绿色
            elif score >= 80:
                colors.append('#FCF3CF')  # 良好-黄色
            else:
                colors.append('#FADBD8')  # 需关注-红色
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df_display.columns),
                fill_color='#5F27CD',
                font=dict(color='white', size=13),
                align='left',
                height=35
            ),
            cells=dict(
                values=[df_display[col] for col in df_display.columns],
                fill_color=[colors],
                align='left',
                height=30,
                font=dict(size=12)
            )
        )])
        
        fig.update_layout(
            title='部门绩效排名',
            height=max(400, len(df_display) * 35 + 100),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        return fig
    
    @staticmethod
    def create_interview_completion_chart(interview_stats):
        """创建面谈完成情况图"""
        if not interview_stats:
            return None
            
        df = pd.DataFrame(interview_stats)
        
        if df.empty:
            return None
        
        # 确保数据类型正确
        if 'interviewer' in df.columns:
            df['interviewer'] = df['interviewer'].astype(str)
        if 'total_count' in df.columns:
            df['total_count'] = pd.to_numeric(df['total_count'], errors='coerce')
        if 'interviewed_count' in df.columns:
            df['interviewed_count'] = pd.to_numeric(df['interviewed_count'], errors='coerce')
        
        df['completion_rate'] = (df['interviewed_count'] / df['total_count'] * 100).round(1)
        df = df.sort_values('completion_rate')
        
        # 根据完成率设置颜色
        colors = ['#EE5A6F' if x < 50 else '#FFA502' if x < 80 else '#1DD1A1' 
                  for x in df['completion_rate']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df['interviewer'].tolist(),
            x=df['completion_rate'].tolist(),
            orientation='h',
            marker=dict(color=colors),
            text=[f"{rate}% ({int(row['interviewed_count'])}/{int(row['total_count'])})" 
                  for rate, (_, row) in zip(df['completion_rate'], df.iterrows())],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>完成率: %{x:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title='各上级绩效面谈完成情况',
            xaxis_title='完成率 (%)',
            yaxis_title='',
            height=max(300, len(df) * 40),
            template='plotly_white',
            xaxis=dict(range=[0, 110])
        )
        
        return fig
    
    @staticmethod
    def create_score_comparison(periods_data):
        """创建多周期对比图"""
        if not periods_data or len(periods_data) < 2:
            return None
        
        df = pd.DataFrame(periods_data)
        df = df.sort_values('period')
        
        fig = go.Figure()
        
        # 箱型图显示每期分数分布
        for period in df['period'].unique():
            period_scores = df[df['period'] == period]['total_score']
            
            fig.add_trace(go.Box(
                y=period_scores,
                name=period,
                boxmean='sd'
            ))
        
        fig.update_layout(
            title='各周期分数分布对比',
            yaxis_title='分数',
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_department_rank_distribution(dept_data, highlight_employee_id, highlight_name):
        """创建部门排名分布图，突出显示指定员工"""
        if not dept_data:
            return None
        
        df = pd.DataFrame(dept_data)
        df = df.sort_values('dept_rank')
        
        # 创建颜色：高亮指定员工
        colors = ['#EE5A6F' if row['employee_id'] == highlight_employee_id else '#5F27CD' 
                  for _, row in df.iterrows()]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['employee_name'],
            y=df['total_score'],
            marker=dict(color=colors),
            text=df['total_score'].round(2),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>总分: %{y:.2f}<br>排名: 第%{customdata}名<extra></extra>',
            customdata=df['dept_rank']
        ))
        
        # 添加平均分线
        avg_score = df['total_score'].mean()
        fig.add_hline(
            y=avg_score,
            line_dash="dash",
            line_color="green",
            annotation_text=f"部门平均分: {avg_score:.1f}",
            annotation_position="top right"
        )
        
        fig.update_layout(
            title=f'部门排名分布 (共{len(df)}人，{highlight_name}标红)',
            xaxis_title='',
            yaxis_title='总分',
            height=400,
            template='plotly_white',
            xaxis=dict(tickangle=-45)
        )
        
        return fig
    
    @staticmethod
    def create_multi_indicator_trend(all_indicators, selected_indicators):
        """创建多指标趋势对比图"""
        if not all_indicators or not selected_indicators:
            return None
        
        df = pd.DataFrame(all_indicators)
        df_filtered = df[df['indicator_name'].isin(selected_indicators)]
        
        if df_filtered.empty:
            return None
        
        fig = go.Figure()
        
        # 为每个指标创建一条线
        colors = ['#2E86DE', '#EE5A6F', '#1DD1A1', '#FFA502', '#5F27CD', 
                  '#48DBFB', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        for i, indicator in enumerate(selected_indicators):
            df_ind = df_filtered[df_filtered['indicator_name'] == indicator].sort_values('period')
            
            fig.add_trace(go.Scatter(
                x=df_ind['period'],
                y=df_ind['score'],
                mode='lines+markers',
                name=indicator,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>周期: %{x}<br>得分: %{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title='指标得分趋势对比',
            xaxis_title='考核周期',
            yaxis_title='得分',
            height=450,
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )
        
        return fig
    
    @staticmethod
    def create_module_trend_chart(df_module):
        """创建模块得分趋势图"""
        if df_module.empty:
            return None
        
        fig = go.Figure()
        
        modules = df_module['indicator_module'].unique()
        colors = {'定量指标': '#2E86DE', '定性指标': '#1DD1A1', '考核指标': '#FFA502'}
        
        for module in modules:
            df_m = df_module[df_module['indicator_module'] == module].sort_values('period')
            
            fig.add_trace(go.Scatter(
                x=df_m['period'],
                y=df_m['score'],
                mode='lines+markers',
                name=module,
                line=dict(color=colors.get(module, '#5F27CD'), width=3),
                marker=dict(size=10),
                fill='tonexty' if module != modules[0] else None,
                hovertemplate='<b>%{fullData.name}</b><br>周期: %{x}<br>平均分: %{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title='各考核模块得分趋势',
            xaxis_title='考核周期',
            yaxis_title='平均得分',
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    # ==================== 高级分析图表 ====================
    
    @staticmethod
    def create_indicator_avg_chart(indicator_stats):
        """创建指标平均分柱状图"""
        if not indicator_stats:
            return None
        
        df = pd.DataFrame(indicator_stats)
        df = df.sort_values('avg_score', ascending=True)
        
        # 根据平均分设置颜色
        colors = []
        for score in df['avg_score']:
            if score >= 90:
                colors.append('#1DD1A1')  # 绿色-偏高
            elif score >= 80:
                colors.append('#54A0FF')  # 蓝色-正常
            else:
                colors.append('#FFA502')  # 橙色-偏低
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df['indicator_name'].tolist(),
            x=df['avg_score'].tolist(),
            orientation='h',
            marker=dict(color=colors),
            text=df['avg_score'].round(2).tolist(),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>平均分: %{x:.2f}<br>权重: %{customdata:.1f}%<extra></extra>',
            customdata=df['avg_weight'].tolist()
        ))
        
        # 添加基准线
        fig.add_vline(x=85, line_dash="dash", line_color="gray", 
                     annotation_text="基准线(85分)", annotation_position="top")
        
        fig.update_layout(
            title='指标平均分分布',
            xaxis_title='平均分',
            yaxis_title='',
            height=max(400, len(df) * 30),
            template='plotly_white',
            xaxis=dict(range=[0, 105])
        )
        
        return fig
    
    @staticmethod
    def create_indicator_std_chart(indicator_stats):
        """创建指标区分度（标准差）柱状图"""
        if not indicator_stats:
            return None
        
        df = pd.DataFrame(indicator_stats)
        df = df.sort_values('std_score', ascending=True)
        
        # 根据标准差设置颜色和标签
        colors = []
        labels = []
        for std in df['std_score']:
            if std < 5:
                colors.append('#EE5A6F')  # 红色-区分度不足
                labels.append('区分度不足')
            elif std > 10:
                colors.append('#1DD1A1')  # 绿色-区分度较高
                labels.append('区分度较高')
            else:
                colors.append('#FFA502')  # 橙色-区分度一般
                labels.append('区分度一般')
        
        df['label'] = labels
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df['indicator_name'].tolist(),
            x=df['std_score'].tolist(),
            orientation='h',
            marker=dict(color=colors),
            text=df['std_score'].round(2).tolist(),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>标准差: %{x:.2f}<br>%{customdata}<extra></extra>',
            customdata=df['label'].tolist()
        ))
        
        # 添加参考线
        fig.add_vline(x=5, line_dash="dash", line_color="red", 
                     annotation_text="区分度不足", annotation_position="top")
        fig.add_vline(x=10, line_dash="dash", line_color="green", 
                     annotation_text="区分度较高", annotation_position="top")
        
        fig.update_layout(
            title='指标区分度分析（标准差）',
            xaxis_title='标准差',
            yaxis_title='',
            height=max(400, len(df) * 30),
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_department_comparison_chart(dept_stats):
        """创建部门对比柱状图"""
        if not dept_stats:
            return None
        
        df = pd.DataFrame(dept_stats)
        df = df.sort_values('avg_score', ascending=True)
        
        fig = go.Figure()
        
        # 平均分
        fig.add_trace(go.Bar(
            name='平均分',
            y=df['department'].tolist(),
            x=df['avg_score'].tolist(),
            orientation='h',
            marker=dict(color='#5F27CD'),
            text=df['avg_score'].round(2).tolist(),
            textposition='outside'
        ))
        
        # 优秀率
        fig.add_trace(go.Bar(
            name='优秀率(%)',
            y=df['department'].tolist(),
            x=df['excellent_rate'].tolist(),
            orientation='h',
            marker=dict(color='#1DD1A1'),
            text=[f"{x:.1f}%" for x in df['excellent_rate']],
            textposition='outside'
        ))
        
        fig.update_layout(
            title='部门绩效对比',
            xaxis_title='',
            yaxis_title='',
            height=max(400, len(df) * 50),
            template='plotly_white',
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    @staticmethod
    def create_correlation_chart(correlations):
        """创建指标相关性分析图"""
        if not correlations:
            return None
        
        df = pd.DataFrame(correlations)
        df = df.sort_values('correlation', ascending=True)
        
        # 根据相关系数设置颜色
        colors = []
        for corr in df['correlation']:
            if abs(corr) >= 0.7:
                colors.append('#5F27CD')  # 紫色-强相关
            elif abs(corr) >= 0.4:
                colors.append('#54A0FF')  # 蓝色-中等相关
            else:
                colors.append('#95A5A6')  # 灰色-弱相关
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df['indicator_name'].tolist(),
            x=df['correlation'].tolist(),
            orientation='h',
            marker=dict(color=colors),
            text=df['correlation'].round(3).tolist(),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>相关系数: %{x:.3f}<extra></extra>'
        ))
        
        # 添加参考线
        fig.add_vline(x=0.7, line_dash="dash", line_color="purple", 
                     annotation_text="强相关", annotation_position="top")
        fig.add_vline(x=0.4, line_dash="dash", line_color="blue", 
                     annotation_text="中等相关", annotation_position="top")
        fig.add_vline(x=-0.4, line_dash="dash", line_color="blue")
        fig.add_vline(x=-0.7, line_dash="dash", line_color="purple")
        
        fig.update_layout(
            title='指标与总分的相关性分析',
            xaxis_title='相关系数（皮尔逊）',
            yaxis_title='',
            height=max(400, len(df) * 30),
            template='plotly_white',
            xaxis=dict(range=[-1, 1])
        )
        
        return fig
    
    # ==================== 面谈质量分析图表 ====================
    
    @staticmethod
    def create_interview_trend_chart(trend_data):
        """创建面谈完成率趋势图（多条线对比上级）"""
        if not trend_data:
            return None
        
        df = pd.DataFrame(trend_data)
        
        if df.empty:
            return None
        
        fig = go.Figure()
        
        # 为每个上级创建一条折线
        interviewers = df['interviewer'].unique()
        
        # 定义颜色
        colors = ['#5F27CD', '#1DD1A1', '#FF6B6B', '#4ECDC4', '#FFA502', 
                 '#48DBF8', '#EE5A6F', '#B8E994', '#F8A5C2', '#786FA6']
        
        for i, interviewer in enumerate(interviewers):
            interviewer_data = df[df['interviewer'] == interviewer].sort_values('period')
            
            color = colors[i % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=interviewer_data['period'].tolist(),
                y=interviewer_data['completion_rate'].tolist(),
                mode='lines+markers',
                name=interviewer,
                line=dict(color=color, width=3),
                marker=dict(size=10, color=color),
                hovertemplate=(
                    '<b>%{fullData.name}</b><br>' +
                    '周期: %{x}<br>' +
                    '完成率: %{y:.1f}%<br>' +
                    '已完成: %{customdata[0]}人<br>' +
                    '未完成: %{customdata[1]}人<br>' +
                    '<extra></extra>'
                ),
                customdata=interviewer_data[['completed_count', 'uncompleted_count']].values
            ))
        
        fig.update_layout(
            title='部门面谈完成率趋势对比（按上级）',
            xaxis_title='考核周期',
            yaxis_title='完成率 (%)',
            height=500,
            template='plotly_white',
            hovermode='x unified',
            yaxis=dict(range=[0, 105]),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 添加目标线
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="green",
            annotation_text="目标线 (80%)",
            annotation_position="right"
        )
        
        return fig
    
    @staticmethod
    def create_quality_score_chart(quality_data):
        """创建上级面谈质量分柱状图"""
        if not quality_data:
            return None
        
        df = pd.DataFrame(quality_data)
        
        # 按质量分排序
        df = df.sort_values('quality_score', ascending=True)
        
        # 根据质量分设置颜色
        colors = []
        for score in df['quality_score']:
            if score >= 75:
                colors.append('#1DD1A1')  # 高质量-绿色
            elif score >= 50:
                colors.append('#FFA502')  # 中等-橙色
            else:
                colors.append('#EE5A6F')  # 低质量-红色
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df['interviewer'].tolist(),
            x=df['quality_score'].tolist(),
            orientation='h',
            marker=dict(color=colors),
            text=df['quality_score'].round(1).tolist(),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>质量分: %{x:.1f}<extra></extra>'
        ))
        
        # 添加参考线
        fig.add_vline(x=75, line_dash="dash", line_color="green", 
                     annotation_text="高质量", annotation_position="top")
        fig.add_vline(x=50, line_dash="dash", line_color="orange", 
                     annotation_text="中等", annotation_position="top")
        
        fig.update_layout(
            title='上级面谈质量分对比',
            xaxis_title='平均质量分',
            yaxis_title='',
            height=max(400, len(df) * 40),
            template='plotly_white',
            xaxis=dict(range=[0, 105])
        )
        
        return fig
    
    @staticmethod
    def create_quality_distribution_chart(quality_data):
        """创建质量分布饼图"""
        if not quality_data:
            return None
        
        df = pd.DataFrame(quality_data)
        
        # 统计各质量等级数量
        quality_counts = df['quality_level'].value_counts()
        
        colors = {
            '高质量': '#1DD1A1',
            '中等': '#FFA502',
            '低质量': '#EE5A6F',
            '无效': '#95A5A6'
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=quality_counts.index.tolist(),
            values=quality_counts.values.tolist(),
            marker=dict(colors=[colors.get(label, '#95A5A6') for label in quality_counts.index]),
            hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>',
            textinfo='label+percent'
        )])
        
        fig.update_layout(
            title='面谈质量分布',
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_interviewer_ranking_chart(rankings):
        """创建上级排名对比图"""
        if not rankings:
            return None
        
        df = pd.DataFrame(rankings)
        df = df.sort_values('completion_rate', ascending=True)
        
        fig = go.Figure()
        
        # 完成率柱
        fig.add_trace(go.Bar(
            name='完成率',
            y=df['interviewer'].tolist(),
            x=df['completion_rate'].tolist(),
            orientation='h',
            marker=dict(color='#5F27CD'),
            text=[f"{x:.1f}%" for x in df['completion_rate']],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>完成率: %{x:.1f}%<extra></extra>'
        ))
        
        # 质量分柱
        fig.add_trace(go.Bar(
            name='质量分',
            y=df['interviewer'].tolist(),
            x=df['avg_quality_score'].tolist(),
            orientation='h',
            marker=dict(color='#1DD1A1'),
            text=[f"{x:.0f}" for x in df['avg_quality_score']],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>质量分: %{x:.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='上级综合表现排名（完成率 vs 质量分）',
            xaxis_title='',
            yaxis_title='',
            height=max(400, len(df) * 50),
            template='plotly_white',
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    # ==================== 绩效分布监控可视化 ====================
    
    @staticmethod
    def create_score_distribution_histogram(distribution_data, show_avg=False, avg_distribution_data=None):
        """
        创建分数分布直方图
        
        参数:
            distribution_data: 当前周期分布数据
            show_avg: 是否显示平均分布对比
            avg_distribution_data: 平均分布数据（用于对比）
        """
        if not distribution_data:
            return None
        
        fig = go.Figure()
        
        # 当前周期分布
        scores = distribution_data['scores']
        fig.add_trace(go.Histogram(
            x=scores,
            name='当前周期',
            marker_color='#3498db',
            opacity=0.75,
            xbins=dict(
                start=60,
                end=100,
                size=5
            ),
            hovertemplate='分数段: %{x}<br>人数: %{y}<extra></extra>'
        ))
        
        # 如果有平均分布数据，添加对比
        if show_avg and avg_distribution_data:
            avg_scores = avg_distribution_data['avg_scores']
            fig.add_trace(go.Histogram(
                x=avg_scores,
                name='平均分布（最近6期）',
                marker_color='#e74c3c',
                opacity=0.6,
                xbins=dict(
                    start=60,
                    end=100,
                    size=5
                ),
                hovertemplate='分数段: %{x}<br>人数: %{y}<extra></extra>'
            ))
        
        # 添加参考线
        fig.add_vline(x=90, line_dash="dash", line_color="green", 
                     annotation_text="优秀线(90)", annotation_position="top")
        fig.add_vline(x=80, line_dash="dash", line_color="orange", 
                     annotation_text="良好线(80)", annotation_position="top")
        fig.add_vline(x=70, line_dash="dash", line_color="red", 
                     annotation_text="及格线(70)", annotation_position="top")
        
        # 添加平均分线
        avg = distribution_data['avg_score']
        fig.add_vline(x=avg, line_dash="solid", line_color="purple", line_width=2,
                     annotation_text=f"平均分({avg:.1f})", annotation_position="top")
        
        fig.update_layout(
            title='绩效分数分布直方图',
            xaxis_title='分数',
            yaxis_title='人数',
            height=500,
            template='plotly_white',
            barmode='overlay' if show_avg else 'stack',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    @staticmethod
    def create_interval_ratio_chart(distribution_data, comparison_data=None):
        """
        创建区间占比堆叠柱状图
        
        参数:
            distribution_data: 当前分布数据
            comparison_data: 对比数据（可选，如平均分布）
        """
        if not distribution_data:
            return None
        
        intervals = ['≥90 (高绩效)', '80-90 (良好)', '70-80 (待提升)', '<70 (需关注)']
        colors = ['#1DD1A1', '#54A0FF', '#FFA502', '#EE5A6F']
        
        fig = go.Figure()
        
        # 当前周期
        ratios = distribution_data['ratios']
        fig.add_trace(go.Bar(
            name='当前周期',
            x=['当前周期'],
            y=[ratios[intervals[0]]],
            text=[f"{ratios[intervals[0]]:.1f}%"],
            textposition='inside',
            marker_color=colors[0],
            hovertemplate='≥90 (高绩效): %{y:.1f}%<extra></extra>',
            showlegend=True,
            legendgroup='intervals'
        ))
        
        for i in range(1, len(intervals)):
            fig.add_trace(go.Bar(
                name=intervals[i] if i == 1 else '',
                x=['当前周期'],
                y=[ratios[intervals[i]]],
                text=[f"{ratios[intervals[i]]:.1f}%"],
                textposition='inside',
                marker_color=colors[i],
                hovertemplate=f'{intervals[i]}: %{{y:.1f}}%<extra></extra>',
                showlegend=(i == 1),
                legendgroup='intervals'
            ))
        
        # 如果有对比数据
        if comparison_data:
            comp_ratios = comparison_data['ratios']
            for i, interval in enumerate(intervals):
                fig.add_trace(go.Bar(
                    name=interval if i == 0 else '',
                    x=['平均分布'],
                    y=[comp_ratios[interval]],
                    text=[f"{comp_ratios[interval]:.1f}%"],
                    textposition='inside',
                    marker_color=colors[i],
                    hovertemplate=f'{interval}: %{{y:.1f}}%<extra></extra>',
                    showlegend=False,
                    legendgroup='intervals'
                ))
        
        # 添加参考线
        fig.add_hline(y=40, line_dash="dash", line_color="red", 
                     annotation_text="高分警戒线(40%)", annotation_position="right")
        
        fig.update_layout(
            title='绩效分数区间占比对比',
            xaxis_title='',
            yaxis_title='占比 (%)',
            height=500,
            template='plotly_white',
            barmode='stack',
            yaxis=dict(range=[0, 105])
        )
        
        return fig
    
    @staticmethod
    def create_health_gauge_chart(health_score, health_level):
        """
        创建健康度仪表盘
        
        参数:
            health_score: 健康度分数（0-100）
            health_level: 健康等级（优秀/良好/一般/需改进）
        """
        # 颜色映射
        color_map = {
            '优秀': '#1DD1A1',
            '良好': '#54A0FF',
            '一般': '#FFA502',
            '需改进': '#EE5A6F'
        }
        
        color = color_map.get(health_level, '#95A5A6')
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"分布健康度<br><span style='font-size:0.6em'>{health_level}</span>"},
            number={'suffix': "分"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 60], 'color': '#FFE5E5'},
                    {'range': [60, 75], 'color': '#FFF4E5'},
                    {'range': [75, 90], 'color': '#E5F5FF'},
                    {'range': [90, 100], 'color': '#E5FFE5'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 60
                }
            }
        ))
        
        fig.update_layout(
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_department_comparison_chart(dept_distribution_data):
        """
        创建部门分数对比图
        
        参数:
            dept_distribution_data: 部门分布数据
        """
        if not dept_distribution_data:
            return None
        
        departments = dept_distribution_data['departments']
        
        dept_names = [d.get('department', '') for d in departments]
        avg_scores = [d.get('avg_score', 0) for d in departments]
        std_scores = [d.get('std_score', 0) for d in departments]
        
        fig = go.Figure()
        
        # 平均分柱状图
        fig.add_trace(go.Bar(
            name='平均分',
            x=dept_names,
            y=avg_scores,
            text=[f"{score:.1f}" for score in avg_scores],
            textposition='outside',
            marker_color='#FF6B9A',  # 使用粉色
            hovertemplate='<b>%{x}</b><br>平均分: %{y:.2f}<extra></extra>'
        ))
        
        # 标准差折线图
        fig.add_trace(go.Scatter(
            name='标准差',
            x=dept_names,
            y=std_scores,
            mode='lines+markers',
            yaxis='y2',
            line=dict(color='#60A5FA', width=2),  # 使用柔和蓝
            marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>标准差: %{y:.2f}<extra></extra>'
        ))
        
        # 添加参考线
        fig.add_hline(y=85, line_dash="dash", line_color="#34D399",  # 使用柔和绿
                     annotation_text="优秀线", annotation_position="right")
        
        fig.update_layout(
            title='部门绩效对比（平均分 + 标准差）',
            xaxis_title='部门',
            yaxis_title='平均分',
            yaxis2=dict(
                title='标准差',
                overlaying='y',
                side='right',
                range=[0, max(std_scores) * 1.5] if std_scores and max(std_scores) > 0 else [0, 15]
            ),
            height=500,
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    @staticmethod
    def create_department_interval_heatmap(dept_distribution_data):
        """
        创建部门区间分布热力图
        
        参数:
            dept_distribution_data: 部门分布数据
        """
        if not dept_distribution_data:
            return None
        
        departments = dept_distribution_data['departments']
        
        dept_names = [d['department'] for d in departments]
        intervals = ['≥90 (高绩效)', '80-90 (良好)', '70-80 (待提升)', '<70 (需关注)']
        
        # 构建热力图数据
        z_data = []
        for interval in intervals:
            row = [d['ratios'][interval] for d in departments]
            z_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=dept_names,
            y=intervals,
            colorscale='RdYlGn',
            reversescale=False,
            text=[[f"{val:.1f}%" for val in row] for row in z_data],
            texttemplate='%{text}',
            textfont={"size": 10},
            hovertemplate='<b>%{x}</b><br>%{y}: %{z:.1f}%<extra></extra>',
            colorbar=dict(title="占比 (%)")
        ))
        
        fig.update_layout(
            title='部门区间分布热力图',
            xaxis_title='部门',
            yaxis_title='分数区间',
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_forced_distribution_comparison(fit_analysis):
        """
        创建强制分布适配对比图
        
        参数:
            fit_analysis: 强制分布适配分析结果
        """
        if not fit_analysis:
            return None
        
        levels = ['A', 'B', 'B-', 'C']
        target_counts = [fit_analysis['target_counts'][level] for level in levels]
        
        # 统计自然分布（基于natural_level）
        simulated_levels = fit_analysis['simulated_levels']
        natural_counts = {'A': 0, 'B': 0, 'B-': 0, 'C': 0}
        for sim in simulated_levels:
            if sim['natural_level']:
                natural_counts[sim['natural_level']] += 1
        
        natural_counts_list = [natural_counts[level] for level in levels]
        
        fig = go.Figure()
        
        # 目标分布
        fig.add_trace(go.Bar(
            name='目标分布（强制）',
            x=levels,
            y=target_counts,
            text=[f"{count}人" for count in target_counts],
            textposition='outside',
            marker_color='#3498db',
            hovertemplate='<b>等级 %{x}</b><br>目标人数: %{y}<extra></extra>'
        ))
        
        # 自然分布
        fig.add_trace(go.Bar(
            name='自然分布（基于分数）',
            x=levels,
            y=natural_counts_list,
            text=[f"{count}人" for count in natural_counts_list],
            textposition='outside',
            marker_color='#e74c3c',
            hovertemplate='<b>等级 %{x}</b><br>自然人数: %{y}<extra></extra>'
        ))
        
        # 添加匹配率标注
        match_ratio = fit_analysis['match_ratio']
        
        # 颜色映射
        color_mapping = {
            'success': '#1DD1A1',
            'info': '#54A0FF',
            'warning': '#FFA502',
            'error': '#EE5A6F'
        }
        
        bg_color = color_mapping.get(fit_analysis['fit_color'], '#54A0FF')
        
        fig.add_annotation(
            text=f"匹配率: {match_ratio:.1f}%<br>{fit_analysis['fit_status']}",
            xref="paper", yref="paper",
            x=0.95, y=0.95,
            showarrow=False,
            bgcolor=bg_color,
            font=dict(size=14, color='white'),
            borderpad=10
        )
        
        fig.update_layout(
            title='强制分布 vs 自然分布对比',
            xaxis_title='绩效等级',
            yaxis_title='人数',
            height=500,
            template='plotly_white',
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig

if __name__ == '__main__':
    # 测试代码
    pass
