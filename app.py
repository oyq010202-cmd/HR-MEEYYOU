import streamlit as st
import pandas as pd
from datetime import datetime
import os
import tempfile
import base64

from database import PerformanceDB
from data_processor import DataProcessor
from visualizations import PerformanceVisualizer

# 页面配置
st.set_page_config(
    page_title="绩效考核管理系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS - 美柚数据平台设计规范 v1.0（参考OE系统）
st.markdown("""
<style>
/* ==================== 颜色体系 - 严格按照 80-90% 中性色 + 5-10% 品牌粉 ==================== */

:root {
    /* 品牌粉（仅用于强调） */
    --brand-pink: #DD5F87;
    --brand-pink-light: #F0A8BF;
    --brand-pink-lighter: #FFE8F0;
    --brand-pink-dark: #C54D75;
    
    /* 中性色（主导） */
    --gray-bg: #F5F6F8;
    --gray-card: #FFFFFF;
    --gray-border: #E2E8F0;
    --gray-border-light: #EDF0F3;
    --gray-hover: #F8F9FA;
    
    /* 文字色 */
    --text-primary: #2D3748;
    --text-secondary: #718096;
    --text-tertiary: #A0AEC0;
    --text-placeholder: #CBD5E0;
    
    /* 功能色 */
    --success: #10B981;
    --success-bg: #D1FAE5;
    --warning: #F59E0B;
    --warning-bg: #FEF3C7;
    --error: #EF4444;
    --error-bg: #FEE2E2;
    --info: #6366F1;
    --info-bg: #E0E7FF;
}

/* ==================== 侧边栏样式（参考OE系统）==================== */

[data-testid="stSidebar"] {
    background-color: white !important;
    border-right: 1px solid var(--gray-border);
    padding-top: 0 !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem !important;     /* 减少: 20px → 0.5rem (8px) */
}

/* Logo区域 */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    margin-bottom: 8px;
}

.sidebar-logo-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    overflow: hidden;
}

.sidebar-logo-icon img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.sidebar-logo-text {
    font-size: 18px;                    /* Logo文字 - 最大 */
    font-weight: 600;
    color: var(--text-primary);
}

/* 导航菜单项 */
[data-testid="stSidebar"] .element-container {
    margin-bottom: 4px;
}

/* 导航分组标题 */
.sidebar-section {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 16px 20px 8px 20px;
    margin-top: 12px;
}

/* Radio按钮样式（用作导航） */
[data-testid="stSidebar"] .row-widget.stRadio > div {
    gap: 4px;
}

[data-testid="stSidebar"] .row-widget.stRadio > div > label {
    background-color: transparent;
    padding: 10px 16px;
    border-radius: 8px;
    transition: all 0.2s ease;
    cursor: pointer;
    font-size: 14px;
    color: var(--text-secondary);
    font-weight: 400;
}

[data-testid="stSidebar"] .row-widget.stRadio > div > label:hover {
    background-color: var(--gray-hover);
    color: var(--text-primary);
}

/* 选中态 - 浅粉色背景 */
[data-testid="stSidebar"] .row-widget.stRadio > div > label[data-baseweb="radio"] > div:first-child {
    display: none;
}

[data-testid="stSidebar"] .row-widget.stRadio > div > label > div {
    padding-left: 0;
}

/* 使用粉色背景表示选中 */
[data-testid="stSidebar"] .row-widget.stRadio input:checked + div {
    background-color: var(--brand-pink-lighter) !important;
    color: var(--brand-pink) !important;
    font-weight: 500;
}

/* 侧边栏底部版本信息 */
.sidebar-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    padding: 16px 20px;
    font-size: 11px;
    color: var(--text-tertiary);
    border-top: 1px solid var(--gray-border-light);
    background: white;
}

/* ==================== 全局样式 ==================== */

.main {
    background-color: var(--gray-bg);
}

.main .block-container {
    padding-top: 1rem !important;           /* 强制减少顶部间距 */
    padding-bottom: 2rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 1400px;
}

/* 进一步减少顶部空白 */
[data-testid="stAppViewContainer"] .main .block-container {
    padding-top: 1rem !important;
}

section[data-testid="stSidebar"] + section .main .block-container {
    padding-top: 1rem !important;
}

/* ==================== Header 区域（参考OE）==================== */

.page-header {
    margin-bottom: 20px;
    margin-top: 0 !important;
    padding-top: 0 !important;
}

.page-title {
    font-size: 24px;                    /* 增大: 20px → 24px */
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 6px 0;
    letter-spacing: -0.01em;
}

.page-subtitle {
    font-size: 14px;                    /* 增大: 13px → 14px */
    font-weight: 400;
    color: var(--text-secondary);
    margin: 0 0 20px 0;
    line-height: 1.6;
}

.main-header {
    font-size: 24px;                    /* 增大: 20px → 24px */
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 6px 0 !important;
    padding-top: 0 !important;
    letter-spacing: -0.01em;
}

.main-subtitle {
    font-size: 14px;                    /* 增大: 13px → 14px */
    font-weight: 400;
    color: var(--text-secondary);
    margin-bottom: 20px;
    line-height: 1.6;
}

.main-subtitle {
    font-size: 13px;
    font-weight: 400;
    color: var(--text-secondary);
    margin-bottom: 24px;
    line-height: 1.6;
}

/* ==================== 筛选器区域（参考OE）==================== */

.filter-section {
    background: white;
    border: 1px solid var(--gray-border);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 24px;
}

/* ==================== KPI卡片（参考OE）==================== */

/* KPI卡片容器 */
.kpi-card {
    background: var(--gray-card);
    border: 1px solid var(--gray-border);
    border-radius: 10px;
    padding: 20px;
    transition: all 0.2s ease;
}

.kpi-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    border-color: var(--gray-border);
}

/* KPI标题 */
.kpi-title {
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 12px;
    font-weight: 400;
}

/* KPI数值 - 大且显眼 */
.kpi-value {
    font-size: 36px;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.2;
    margin-bottom: 4px;
}

.kpi-unit {
    font-size: 14px;
    color: var(--text-tertiary);
    margin-left: 4px;
}

/* KPI对比数据 */
.kpi-compare {
    display: flex;
    gap: 16px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--gray-border-light);
}

.kpi-compare-item {
    font-size: 12px;
    color: var(--text-secondary);
}

.kpi-compare-value {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 500;
}

.kpi-compare-value.positive {
    background: var(--success-bg);
    color: var(--success);
}

.kpi-compare-value.negative {
    background: var(--error-bg);
    color: var(--error);
}

/* KPI目标 */
.kpi-target {
    font-size: 12px;
    margin-top: 8px;
    color: var(--text-secondary);
}

.kpi-target-value {
    color: var(--text-primary);
    font-weight: 500;
}

.kpi-target-gap {
    color: var(--error);
    font-weight: 500;
}

/* ==================== 卡片系统 ==================== */

.data-card {
    background: var(--gray-card);
    border: 1px solid var(--gray-border);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    transition: all 0.2s ease;
}

.data-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 6px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}

.card-subtitle {
    font-size: 12px;
    font-weight: 400;
    color: var(--text-secondary);
    margin: 0 0 16px 0;
    line-height: 1.5;
}

/* ==================== 上传组件 ==================== */

.upload-zone {
    background: var(--gray-bg);
    border: 1.5px dashed var(--gray-border);
    border-radius: 8px;
    padding: 28px;
    text-align: center;
    transition: all 0.2s ease;
    cursor: pointer;
}

.upload-zone:hover {
    border-color: var(--brand-pink-light);
    background: var(--brand-pink-lighter);
}

.upload-zone-icon {
    font-size: 32px;
    color: var(--text-tertiary);
    margin-bottom: 10px;
}

.upload-zone-text {
    font-size: 13px;
    color: var(--text-secondary);
    margin: 6px 0 4px 0;
}

.upload-zone-hint {
    font-size: 11px;
    color: var(--text-tertiary);
}

/* 状态徽章 */
.status-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
}

.status-badge.success {
    background: var(--success-bg);
    color: var(--success);
}

.status-badge.pending {
    background: var(--warning-bg);
    color: var(--warning);
}

/* ==================== 指标卡片 ==================== */

.metric-card {
    background: var(--gray-card);
    border: 1px solid var(--gray-border);
    border-radius: 8px;
    padding: 16px;
    transition: all 0.2s ease;
}

.metric-card:hover {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.metric-label {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}

.metric-value {
    font-size: 24px;
    font-weight: 600;
    color: var(--brand-pink);
    line-height: 1.2;
    margin-bottom: 2px;
}

.metric-unit {
    font-size: 12px;
    font-weight: 400;
    color: var(--text-tertiary);
}

[data-testid="stMetricValue"] {
    font-size: 24px !important;
    font-weight: 600 !important;
    color: var(--brand-pink) !important;
}

[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ==================== 按钮系统 ==================== */

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--brand-pink) 0%, var(--brand-pink-dark) 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    box-shadow: 0 2px 4px rgba(221, 95, 135, 0.12);
    transition: all 0.2s ease;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(221, 95, 135, 0.18);
}

.stButton > button[kind="primary"]:disabled {
    background: var(--gray-border);
    color: var(--text-tertiary);
    box-shadow: none;
    cursor: not-allowed;
}

/* ==================== 表格 ==================== */

.dataframe {
    border: 1px solid var(--gray-border) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    font-size: 13px !important;
}

.dataframe thead tr {
    background: var(--gray-bg) !important;
}

.dataframe thead th {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    padding: 10px 14px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid var(--gray-border) !important;
}

.dataframe tbody td {
    font-size: 13px !important;
    color: var(--text-primary) !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid var(--gray-border-light) !important;
}

.dataframe tbody tr:hover {
    background: var(--gray-hover) !important;
}

.dataframe tbody tr:last-child td {
    border-bottom: none !important;
}

/* ==================== Tab系统 ==================== */

.stTabs [data-baseweb="tab-list"] {
    gap: 28px;
    border-bottom: 1px solid var(--gray-border);
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    padding: 0;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
    background: transparent;
    border: none;
}

.stTabs [aria-selected="true"] {
    color: var(--brand-pink) !important;
    font-weight: 600 !important;
    border-bottom: 2px solid var(--brand-pink) !important;
}

/* ==================== 表单元素 ==================== */

.stSelectbox > div > div,
.stTextInput > div > div > input {
    border-radius: 8px;
    border: 1px solid var(--gray-border);
    font-size: 13px;
}

.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {
    border-color: var(--brand-pink) !important;
    box-shadow: 0 0 0 3px var(--brand-pink-lighter) !important;
}

/* ==================== 消息提示 ==================== */

.success-box {
    background: var(--success-bg);
    border-left: 3px solid var(--success);
    padding: 14px 18px;
    border-radius: 8px;
    margin: 16px 0;
}

.warning-box {
    background: var(--warning-bg);
    border-left: 3px solid var(--warning);
    padding: 14px 18px;
    border-radius: 8px;
    margin: 16px 0;
}

.danger-box {
    background: var(--error-bg);
    border-left: 3px solid var(--error);
    padding: 14px 18px;
    border-radius: 8px;
    margin: 16px 0;
}

.stSuccess {
    background-color: var(--success-bg) !important;
    border-left-color: var(--success) !important;
}

.stWarning {
    background-color: var(--warning-bg) !important;
    border-left-color: var(--warning) !important;
}

.stError {
    background-color: var(--error-bg) !important;
    border-left-color: var(--error) !important;
}

.stInfo {
    background-color: var(--info-bg) !important;
    border-left-color: var(--info) !important;
}

/* ==================== 间距系统 ==================== */

.element-container {
    margin-bottom: 24px;
}

h1, h2, h3 {
    margin-top: 24px;
    margin-bottom: 12px;
    color: var(--text-primary);
    font-weight: 600;
}

.element-container p {
    line-height: 1.6;
    color: var(--text-primary);
}

hr {
    border: none;
    border-top: 1px solid var(--gray-border);
    margin: 24px 0;
}

/* ==================== 其他 ==================== */

.streamlit-expanderHeader {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}

[data-testid="stFileUploader"] {
    border: none;
    padding: 0;
}

[data-testid="stFileUploader"] > div {
    background: transparent;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# 初始化数据库
@st.cache_resource
def init_database():
    db = PerformanceDB('performance_data.db')
    db.init_database()
    db.connect()
    return db

db = init_database()
processor = DataProcessor(db)
visualizer = PerformanceVisualizer()

# 侧边栏导航 - 参考OE系统风格
# 添加CSS减少侧边栏顶部间距
st.sidebar.markdown("""
<style>
    /* 减少侧边栏顶部padding */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }
    /* Logo区域向上移 */
    .logo-container {
        margin-top: -20px !important;
    }
</style>
""", unsafe_allow_html=True)

# Logo区域 - 修复模糊和间距问题
st.sidebar.markdown("""
<style>
.logo-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px 24px 20px;
}
.logo-container img {
    width: 44px !important;
    height: 44px !important;
    border-radius: 8px;
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
}
</style>
""", unsafe_allow_html=True)

# 使用HTML布局显示Logo
try:
    import base64
    with open('meiyou_logo.png', 'rb') as f:
        logo_data = base64.b64encode(f.read()).decode()
    
    st.sidebar.markdown(f"""
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_data}" alt="美柚Logo">
        <div style="font-size:18px;font-weight:600;color:#2D3748;">绩效考核管理系统</div>
    </div>
    """, unsafe_allow_html=True)
except:
    # 备用方案
    col1, col2 = st.sidebar.columns([1, 4], gap="small")
    with col1:
        st.image('meiyou_logo.png', width=44)
    with col2:
        st.markdown('<div style="font-size:18px;font-weight:600;color:#2D3748;padding-top:10px;">绩效考核管理系统</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

# 导航分组
st.sidebar.markdown('<div class="sidebar-section">数据管理</div>', unsafe_allow_html=True)

menu = st.sidebar.radio(
    "导航菜单",
    ["📤 数据上传", "🗄️ 数据管理"],
    index=0,
    label_visibility="collapsed"
)

st.sidebar.markdown('<div class="sidebar-section">效能分析</div>', unsafe_allow_html=True)

if menu in ["📤 数据上传", "🗄️ 数据管理"]:
    analysis_menu = st.sidebar.radio(
        "分析菜单",
        ["👤 员工绩效追踪", "📈 部门绩效分析", "📊 绩效分布监控", "💬 面谈质量监控"],
        index=None,
        label_visibility="collapsed"
    )
    if analysis_menu:
        menu = analysis_menu

st.sidebar.markdown('<div class="sidebar-section">高级功能</div>', unsafe_allow_html=True)

if menu in ["📤 数据上传", "🗄️ 数据管理", "👤 员工绩效追踪", "📈 部门绩效分析", "📊 绩效分布监控", "💬 面谈质量监控"]:
    advanced_menu = st.sidebar.radio(
        "高级菜单",
        ["🔄 考核方案管理", "🔍 智能查询", "📊 高级分析"],
        index=None,
        label_visibility="collapsed"
    )
    if advanced_menu:
        menu = advanced_menu

# 底部版本信息
st.sidebar.markdown("""
<div class="sidebar-footer">
    版本 v1.0.0
</div>
""", unsafe_allow_html=True)

# ==================== 页面1: 数据上传 ====================
if menu == "📤 数据上传":
    # 使用CSS控制顶部空白（不用div）
    st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:first-child {
            padding-top: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header区域 - 标题+描述（增加底部间距）
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">📊 数据上传中心</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">导入绩效考核数据，系统将自动识别周期并生成分析报告</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 核心功能区 - 卡片网格布局
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.markdown("""
        <div class="data-card">
            <div style="margin-bottom: 14px;">
                <div class="card-title">📄 绩效结果文件</div>
                <div class="card-subtitle">包含员工总分、等级、排名等绩效结果数据</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        results_file = st.file_uploader(
            "选择文件",
            type=['xlsx'],
            key='results_file',
            label_visibility="collapsed",
            help="支持格式：xlsx"
        )
        
        if results_file:
            st.markdown('<div class="status-badge success">✓ 已选择</div>', unsafe_allow_html=True)
        else:
            st.caption("支持格式：.xlsx")
    
    with col2:
        st.markdown("""
        <div class="data-card">
            <div style="margin-bottom: 14px;">
                <div class="card-title">📊 指标评价文件</div>
                <div class="card-subtitle">包含各考核指标的详细分数数据</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        indicators_file = st.file_uploader(
            "选择文件",
            type=['xlsx'],
            key='indicators_file',
            label_visibility="collapsed",
            help="支持格式：xlsx"
        )
        
        if indicators_file:
            st.markdown('<div class="status-badge success">✓ 已选择</div>', unsafe_allow_html=True)
        else:
            st.caption("支持格式：.xlsx")
    
    # 高级选项
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    
    with st.expander("⚙️ 高级选项", expanded=False):
        manual_period = st.text_input(
            "手动指定考核周期",
            placeholder="例如：2026年2月月度考核",
            help="留空则自动从文件中识别",
            label_visibility="visible"
        )
    
    # 操作区 - 右对齐
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2.5, 0.8, 0.7])
    
    with col3:
        process_button = st.button(
            "🚀 开始处理", 
            type="primary",
            use_container_width=True,
            disabled=not (results_file and indicators_file)
        )
    
    # 处理数据逻辑
    if process_button:
        if results_file and indicators_file:
            with st.spinner("正在处理数据..."):
                # 保存上传的文件
                temp_dir = tempfile.gettempdir()
                results_path = os.path.join(temp_dir, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                indicators_path = os.path.join(temp_dir, f"indicators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                
                with open(results_path, 'wb') as f:
                    f.write(results_file.getvalue())
                
                with open(indicators_path, 'wb') as f:
                    f.write(indicators_file.getvalue())
                
                period = manual_period if manual_period else None
                
                # 处理绩效结果
                result1 = processor.process_performance_results(results_path, period)
                
                # 处理指标信息
                result2 = processor.process_indicator_info(indicators_path, period)
                
                # 清理临时文件
                os.remove(results_path)
                os.remove(indicators_path)
                
                # 显示结果
                if result1['success'] and result2['success']:
                    st.markdown(f"""
                    <div class="success-box">
                        <div style="font-size:14px; font-weight:600; margin-bottom:8px;">✅ 数据导入成功</div>
                        <div style="font-size:12px; line-height:1.6; color:#718096;">
                            <div>考核周期：{result1['period']}</div>
                            <div>绩效结果：{result1['records']} 条</div>
                            <div>考核指标：{result2['records']} 条</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # KPI概览区
                    stats = processor.get_summary_stats(result1['period'])
                    if stats:
                        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
                        st.markdown("""
                        <div class="data-card">
                            <div class="card-title">📊 数据概览</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("总人数", f"{stats['total_employees']}")
                        with col2:
                            st.metric("平均分", f"{stats['avg_score']:.2f}")
                        with col3:
                            st.metric("优秀人数", f"{stats['excellent_count']}", 
                                     delta=f"{stats['excellent_count']/stats['total_employees']*100:.1f}%")
                        with col4:
                            st.metric("需关注", f"{stats['need_attention_count']}", 
                                     delta=f"{stats['need_attention_count']/stats['total_employees']*100:.1f}%",
                                     delta_color="inverse")
                else:
                    error_msg = result1.get('message', '') + ' ' + result2.get('message', '')
                    st.markdown(f"""
                    <div class="danger-box">
                        <div style="font-size:14px; font-weight:600; margin-bottom:8px;">❌ 数据导入失败</div>
                        <div style="font-size:12px; color:#718096;">{error_msg}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # 数据区 - 上传历史表格
    st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="data-card">
        <div class="card-title">📜 上传历史记录</div>
    </div>
    """, unsafe_allow_html=True)
    
    cursor = db.conn.cursor()
    cursor.execute('''
        SELECT upload_time, period, file_type, record_count, status
        FROM data_upload_log
        ORDER BY upload_time DESC
        LIMIT 10
    ''')
    history = cursor.fetchall()
    
    if history:
        df_history = pd.DataFrame(history, columns=['上传时间', '考核周期', '文件类型', '记录数', '状态'])
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("暂无上传记录")

# ==================== 页面2: 员工绩效追踪 ====================
elif menu == "👤 员工绩效追踪":
    # Header区域
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">👤 员工绩效追踪</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">查看员工历史绩效趋势，分析个人成长轨迹</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取所有员工
    employees = db.get_all_employees()
    
    if not employees:
        st.warning("⚠️ 暂无数据，请先上传绩效数据")
    else:
        # 筛选器区域 - 白色卡片
        st.markdown("""
        <div class="data-card" style="margin-bottom: 24px;">
            <div class="card-title">🔍 筛选条件</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 先选择部门，再选择员工
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 获取所有部门
            departments = db.get_all_departments()
            dept_options = ["全部部门"] + sorted(list(set([row[0] for row in departments if row[0]])))
            selected_dept = st.selectbox("📂 选择部门", dept_options)
        
        with col2:
            # 根据部门筛选员工
            if selected_dept == "全部部门":
                filtered_employees = employees
            else:
                filtered_employees = [emp for emp in employees if emp[2] == selected_dept]
            
            employee_options = {f"{row[0]} ({row[1]})": row[1] for row in filtered_employees}
            selected_employee = st.selectbox(
                "👤 选择员工",
                options=list(employee_options.keys()) if employee_options else ["无员工"]
            )
        
        with col3:
            # 周期类型筛选
            period_type_filter = st.selectbox(
                "📅 周期类型",
                ["全部", "月度", "季度", "半年度", "年度"]
            )
        
        if selected_employee and selected_employee != "无员工":
            employee_id = employee_options[selected_employee]
            employee_name = selected_employee.split(' (')[0]
            
            # 获取员工历史数据
            history = db.get_employee_history(employee_id)
            
            # 根据周期类型筛选
            if period_type_filter != "全部":
                # 建立中文到英文的映射
                period_type_mapping = {
                    "月度": "monthly",
                    "季度": "quarterly",
                    "半年度": "half_yearly",
                    "年度": "yearly"
                }
                
                # 获取对应的英文类型
                target_type = period_type_mapping.get(period_type_filter)
                
                # 根据period_type字段筛选
                if target_type:
                    history = [h for h in history if h.get('period_type') == target_type]
            
            if history:
                st.markdown(f"### {employee_name} 的绩效记录")
                
                # 基本信息卡片
                latest = history[-1]
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("最新总分", f"{latest['total_score']:.2f}" if latest['total_score'] else "N/A")
                with col2:
                    # 显示系数
                    if latest.get('coefficient'):
                        st.metric("绩效系数", f"{latest['coefficient']:.2f}")
                    else:
                        st.metric("绩效系数", "N/A")
                with col3:
                    st.metric("部门排名", f"第 {int(latest['dept_rank'])} 名" if latest['dept_rank'] else "N/A")
                with col4:
                    st.metric("所属部门", latest['department_l2'] or "未知")
                with col5:
                    # 识别周期类型
                    period_count_by_type = {}
                    for h in history:
                        if '月度' in h['period']:
                            period_count_by_type['月度'] = period_count_by_type.get('月度', 0) + 1
                        elif '季度' in h['period'] or 'Q' in h['period']:
                            period_count_by_type['季度'] = period_count_by_type.get('季度', 0) + 1
                    period_summary = ', '.join([f"{k}×{v}" for k, v in period_count_by_type.items()])
                    st.metric("参与周期", period_summary or f"{len(history)}期")
                with col5:
                    # 趋势指示
                    if len(history) >= 2:
                        trend = latest['total_score'] - history[-2]['total_score']
                        st.metric("变化趋势", f"{trend:+.2f}分")
                    else:
                        st.metric("变化趋势", "首期")
                
                st.markdown("---")
                
                # 可视化部分
                col1, col2 = st.columns(2)
                
                with col1:
                    # 分数趋势图
                    fig_score = visualizer.create_score_trend_chart(history)
                    if fig_score:
                        st.plotly_chart(fig_score, use_container_width=True)
                
                with col2:
                    # 排名趋势图
                    fig_rank = visualizer.create_rank_trend_chart(history)
                    if fig_rank:
                        st.plotly_chart(fig_rank, use_container_width=True)
                
                # 系数趋势图（单独一行）
                fig_coefficient = visualizer.create_coefficient_trend_chart(history)
                if fig_coefficient:
                    st.plotly_chart(fig_coefficient, use_container_width=True)
                else:
                    st.info("💡 **提示**: 系统未检测到系数数据。如需查看系数趋势，请确保从北森导出时包含\"最终系数\"字段。")
                
                st.markdown("---")
                
                # 上级评语
                st.markdown("---")
                st.subheader("💬 上级评价历史")
                
                for record in reversed(history):
                    if record.get('manager_comment'):
                        st.markdown(f"""
                        <div class="success-box">
                            <strong>{record['period']}</strong><br>
                            {record['manager_comment']}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info(f"该员工在「{period_type_filter}」类型下暂无数据")

# ==================== 页面3: 部门绩效分析 ====================
elif menu == "📈 部门绩效分析":
    # Header区域
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">📈 部门绩效分析</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">对比部门绩效表现，识别优势与改进空间</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取所有周期
    periods = db.get_all_periods()
    
    if not periods:
        st.warning("⚠️ 暂无数据，请先上传绩效数据")
    else:
        # 筛选器区域 - 白色卡片
        st.markdown("""
        <div class="data-card" style="margin-bottom: 24px;">
            <div class="card-title">🔍 筛选条件</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 周期和部门选择
        col1, col2 = st.columns(2)
        
        with col1:
            selected_period = st.selectbox("选择考核周期", periods)
        
        with col2:
            departments = db.get_all_departments()
            dept_options = ["全部"] + [f"{row[0]} - {row[1]}" if row[1] else row[0] for row in departments]
            selected_dept = st.selectbox("选择部门", dept_options)
        
        if selected_period:
            # 获取部门数据
            dept_filter = None if selected_dept == "全部" else selected_dept.split(' - ')[0]
            dept_data = db.get_department_performance(selected_period, dept_filter)
            
            if dept_data:
                df_dept = pd.DataFrame(dept_data)
                
                # 统计指标
                st.subheader("📊 整体概览")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                total_count = len(df_dept)
                avg_score = df_dept['total_score'].mean()
                excellent_count = len(df_dept[df_dept['total_score'] >= 90])
                good_count = len(df_dept[(df_dept['total_score'] >= 80) & (df_dept['total_score'] < 90)])
                need_attention = len(df_dept[df_dept['total_score'] < 80])
                
                with col1:
                    st.metric("参与人数", total_count)
                with col2:
                    st.metric("平均分", f"{avg_score:.2f}")
                with col3:
                    st.metric("优秀 (≥90)", f"{excellent_count} ({excellent_count/total_count*100:.1f}%)")
                with col4:
                    st.metric("良好 (80-90)", f"{good_count} ({good_count/total_count*100:.1f}%)")
                with col5:
                    st.metric("需关注 (<80)", f"{need_attention} ({need_attention/total_count*100:.1f}%)")
                
                st.markdown("---")
                
                # 排名表（占满宽度）
                fig_rank = visualizer.create_department_ranking(dept_data)
                if fig_rank:
                    st.plotly_chart(fig_rank, use_container_width=True)
                
                # 优秀员工和需关注员工
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("⭐ 优秀员工 (≥90分)")
                    excellent = df_dept[df_dept['total_score'] >= 90].sort_values('total_score', ascending=False)
                    if not excellent.empty:
                        for _, row in excellent.iterrows():
                            st.markdown(f"""
                            <div class="success-box">
                                <strong>{row['employee_name']}</strong> - {row['total_score']:.2f}分 (第{row['dept_rank']}名)<br>
                                <small>{row['manager_comment'] if row['manager_comment'] else '暂无评语'}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("本期暂无优秀员工")
                
                with col2:
                    st.subheader("⚠️ 需关注员工 (<80分)")
                    need_att = df_dept[df_dept['total_score'] < 80].sort_values('total_score')
                    if not need_att.empty:
                        for _, row in need_att.iterrows():
                            st.markdown(f"""
                            <div class="warning-box">
                                <strong>{row['employee_name']}</strong> - {row['total_score']:.2f}分 (第{row['dept_rank']}名)<br>
                                <small>{row['manager_comment'] if row['manager_comment'] else '暂无评语'}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("✅ 本期无需特别关注的员工")

# ==================== 页面4: 面谈质量监控（重构升级版） ====================
elif menu == "💬 面谈质量监控":
    # Header区域
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">💬 面谈质量监控与分析</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">从完成率到质量管理：趋势分析 + 质量评估 + 风险预警</p>
    </div>
    """, unsafe_allow_html=True)
    
    periods = db.get_all_periods()
    
    if not periods:
        st.warning("⚠️ 暂无数据，请先上传绩效数据")
    else:
        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 上级趋势分析",
            "🎯 面谈质量分析", 
            "⚠️ 风险预警",
            "🏆 上级排名"
        ])
        
        # ==================== Tab1: 上级维度趋势分析 ====================
        with tab1:
            st.markdown("""
            <div class="data-card" style="margin-bottom: 20px;">
                <div class="card-title">📈 上级面谈完成率趋势</div>
                <div class="card-subtitle">观察不同上级的面谈执行趋势，识别持续优秀/持续落后的管理者</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 筛选器
            col1, col2 = st.columns(2)
            
            with col1:
                # 获取所有上级
                cursor = db.conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT interviewer 
                    FROM interview_records 
                    WHERE interviewer IS NOT NULL AND interviewer != '未知'
                    ORDER BY interviewer
                ''')
                supervisors = [row[0] for row in cursor.fetchall()]
                
                if supervisors:
                    # 添加"全部对比"选项
                    supervisor_options = ["📊 全部上级对比"] + supervisors
                    selected_option = st.selectbox("👤 选择上级", supervisor_options)
                    
                    # 如果选择"全部对比"，传None；否则传选中的上级
                    selected_supervisor = None if selected_option == "📊 全部上级对比" else selected_option
                else:
                    st.warning("暂无上级数据")
                    selected_supervisor = None
                    supervisors = []
            
            with col2:
                # 周期范围选择
                max_periods = min(len(periods), 12)
                period_count = st.slider("📅 显示最近几期", 3, max_periods, 6)
            
            if supervisors:  # 只要有上级数据就可以分析
                with st.spinner('正在分析面谈趋势...'):
                    # 获取趋势数据
                    recent_periods = periods[-period_count:]
                    trend_data = processor.get_interview_trend_by_supervisor(
                        selected_supervisor,  # None表示所有上级对比
                        recent_periods
                    )
                    
                    if trend_data:
                        # 统计卡片
                        df_trend = pd.DataFrame(trend_data)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            avg_rate = df_trend['completion_rate'].mean()
                            label = "整体平均完成率" if not selected_supervisor else f"{selected_supervisor}团队完成率"
                            st.metric(label, f"{avg_rate:.1f}%")
                        
                        with col2:
                            if selected_supervisor:
                                total_employees = df_trend['total_count'].sum() // len(recent_periods)
                                st.metric("负责人数", total_employees)
                            else:
                                interviewers = df_trend['interviewer'].nunique()
                                st.metric("上级人数", interviewers)
                        
                        with col3:
                            latest_period_data = df_trend[df_trend['period'] == recent_periods[-1]]
                            latest_avg = latest_period_data['completion_rate'].mean()
                            st.metric("最新周期完成率", f"{latest_avg:.1f}%")
                        
                        with col4:
                            # 计算趋势（最新vs前一期）
                            if len(recent_periods) >= 2:
                                prev_period_data = df_trend[df_trend['period'] == recent_periods[-2]]
                                prev_avg = prev_period_data['completion_rate'].mean()
                                trend_change = latest_avg - prev_avg
                                st.metric("环比变化", f"{trend_change:+.1f}%")
                            else:
                                st.metric("环比变化", "N/A")
                        
                        st.markdown("---")
                        
                        # 趋势图
                        fig_trend = visualizer.create_interview_trend_chart(trend_data)
                        if fig_trend:
                            st.plotly_chart(fig_trend, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 关键洞察
                        st.markdown("### 💡 关键洞察")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 🌟 持续优秀上级")
                            # 找出平均完成率最高的3位
                            interviewer_avg = df_trend.groupby('interviewer')['completion_rate'].mean().sort_values(ascending=False)
                            for i, (interviewer, rate) in enumerate(interviewer_avg.head(3).items(), 1):
                                st.success(f"{i}. **{interviewer}**: 平均完成率 {rate:.1f}%")
                        
                        with col2:
                            st.markdown("#### ⚠️ 需要改进上级")
                            # 找出平均完成率最低的3位
                            for i, (interviewer, rate) in enumerate(interviewer_avg.tail(3).items(), 1):
                                st.warning(f"{i}. **{interviewer}**: 平均完成率 {rate:.1f}%")
                        
                        # 详细数据表
                        st.markdown("---")
                        st.markdown("### 📋 详细数据")
                        
                        # 转换为透视表格式
                        pivot_data = df_trend.pivot(
                            index='interviewer', 
                            columns='period', 
                            values='completion_rate'
                        ).round(1)
                        
                        # 添加平均值列
                        pivot_data['平均完成率'] = pivot_data.mean(axis=1).round(1)
                        
                        # 按平均完成率排序
                        pivot_data = pivot_data.sort_values('平均完成率', ascending=False)
                        
                        st.dataframe(pivot_data, use_container_width=True)
                    else:
                        st.warning("⚠️ 暂无面谈趋势数据")
        
        # ==================== Tab2: 面谈质量分析 ====================
        with tab2:
            st.markdown("### 🎯 面谈内容质量分析")
            st.info("💡 **分析目标**：评估面谈内容的深度和质量，识别敷衍面谈行为")
            
            # 周期选择
            selected_period = st.selectbox("📅 选择考核周期", periods, key="quality_period")
            
            if selected_period:
                with st.spinner('正在分析面谈质量...'):
                    # 获取质量数据
                    quality_data = processor.analyze_interview_quality(selected_period)
                    
                    if quality_data:
                        df_quality = pd.DataFrame(quality_data)
                        
                        # 统计卡片
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            avg_score = df_quality['quality_score'].mean()
                            st.metric("平均质量分", f"{avg_score:.1f}")
                        
                        with col2:
                            high_quality = len(df_quality[df_quality['quality_level'] == '高质量'])
                            st.metric("高质量面谈", f"{high_quality}人")
                        
                        with col3:
                            low_quality = len(df_quality[df_quality['quality_level'] == '低质量'])
                            low_rate = (low_quality / len(df_quality) * 100) if len(df_quality) > 0 else 0
                            st.metric("低质量面谈", f"{low_quality}人 ({low_rate:.1f}%)")
                        
                        with col4:
                            invalid = len(df_quality[df_quality['quality_level'] == '无效'])
                            st.metric("无效面谈", f"{invalid}人")
                        
                        # 预警
                        if low_rate > 30:
                            st.error(f"🚨 **警告**: 低质量面谈占比{low_rate:.1f}%，超过30%阈值！")
                        
                        st.markdown("---")
                        
                        # 可视化
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # 按上级统计质量分
                            interviewer_quality = df_quality.groupby('interviewer')['quality_score'].mean().reset_index()
                            interviewer_quality.columns = ['interviewer', 'quality_score']
                            
                            fig_quality = visualizer.create_quality_score_chart(
                                interviewer_quality.to_dict('records')
                            )
                            if fig_quality:
                                st.plotly_chart(fig_quality, use_container_width=True)
                        
                        with col2:
                            # 质量分布饼图
                            fig_dist = visualizer.create_quality_distribution_chart(
                                quality_data
                            )
                            if fig_dist:
                                st.plotly_chart(fig_dist, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 问题标记
                        st.markdown("### ⚠️ 质量问题标记")
                        
                        # 找出质量分明显偏低的上级
                        interviewer_avg = df_quality.groupby('interviewer')['quality_score'].mean()
                        overall_avg = df_quality['quality_score'].mean()
                        
                        low_performers = interviewer_avg[interviewer_avg < overall_avg * 0.7].sort_values()
                        
                        if len(low_performers) > 0:
                            st.warning(f"发现 {len(low_performers)} 位上级的面谈质量明显偏低：")
                            for interviewer, score in low_performers.items():
                                st.markdown(f"- **{interviewer}**: 平均质量分 {score:.1f} （整体平均 {overall_avg:.1f}）")
                        else:
                            st.success("✅ 所有上级的面谈质量均达标")
                        
                        # 低质量面谈详情
                        st.markdown("---")
                        st.markdown("### 📋 低质量面谈详情")
                        
                        low_quality_records = df_quality[
                            (df_quality['quality_level'] == '低质量') | 
                            (df_quality['quality_level'] == '无效')
                        ]
                        
                        if not low_quality_records.empty:
                            df_display = low_quality_records[[
                                'employee_name', 'interviewer', 'quality_level', 
                                'quality_score', 'feedback_content'
                            ]]
                            df_display.columns = ['员工', '上级', '质量等级', '质量分', '面谈内容']
                            
                            # 限制面谈内容显示长度
                            df_display['面谈内容'] = df_display['面谈内容'].apply(
                                lambda x: str(x)[:50] + '...' if pd.notna(x) and len(str(x)) > 50 else str(x)
                            )
                            
                            st.dataframe(df_display, use_container_width=True, height=300)
                        else:
                            st.success("✅ 没有低质量面谈记录")
                    else:
                        st.warning("⚠️ 该周期暂无面谈质量数据")
        
        # ==================== Tab3: 风险预警 ====================
        with tab3:
            st.markdown("### ⚠️ 连续未面谈员工预警")
            st.info("💡 **分析目标**：识别被长期忽视的员工，防止管理盲区")
            
            # 阈值设置
            col1, col2 = st.columns(2)
            
            with col1:
                period_count = st.slider("📅 检查最近几期", 3, min(len(periods), 12), 6, key="risk_periods")
            
            with col2:
                threshold = st.slider("⚠️ 连续未面谈阈值", 2, 5, 3)
            
            with st.spinner('正在识别风险员工...'):
                # 获取风险员工
                recent_periods = periods[-period_count:]
                risk_employees = processor.get_continuous_uninterviewed_employees(
                    recent_periods, 
                    threshold
                )
                
                if risk_employees:
                    # 统计
                    st.error(f"🚨 发现 **{len(risk_employees)}** 名员工连续{threshold}期未完成面谈！")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("风险员工总数", len(risk_employees))
                    
                    with col2:
                        depts = set([emp['department'] for emp in risk_employees if emp['department']])
                        st.metric("涉及部门", len(depts))
                    
                    with col3:
                        interviewers = set([emp['interviewer'] for emp in risk_employees if emp['interviewer']])
                        st.metric("涉及上级", len(interviewers))
                    
                    st.markdown("---")
                    
                    # 风险员工列表
                    st.markdown("### 📋 风险员工详情")
                    
                    df_risk = pd.DataFrame(risk_employees)
                    df_risk['未面谈周期'] = df_risk['uninterviewed_periods'].apply(lambda x: ', '.join(x))
                    
                    df_display = df_risk[[
                        'employee_name', 'department', 'interviewer', 
                        'consecutive_count', '未面谈周期'
                    ]]
                    df_display.columns = ['员工', '部门', '直接上级', '连续未面谈期数', '未面谈周期']
                    
                    # 按连续期数排序
                    df_display = df_display.sort_values('连续未面谈期数', ascending=False)
                    
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        height=400
                    )
                    
                    # 按上级统计
                    st.markdown("---")
                    st.markdown("### 📊 按上级统计风险人数")
                    
                    interviewer_risk = df_risk.groupby('interviewer').size().reset_index()
                    interviewer_risk.columns = ['上级', '风险员工数']
                    interviewer_risk = interviewer_risk.sort_values('风险员工数', ascending=False)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.dataframe(interviewer_risk, use_container_width=True)
                    
                    with col2:
                        # 找出风险最高的上级
                        top_risk = interviewer_risk.iloc[0]
                        st.error(f"""
                        **⚠️ 风险最高上级**
                        
                        {top_risk['上级']}
                        
                        风险员工: {top_risk['风险员工数']}人
                        """)
                else:
                    st.success(f"✅ 没有发现连续{threshold}期未面谈的员工！")
        
        # ==================== Tab4: 上级排名 ====================
        with tab4:
            st.markdown("### 🏆 上级面谈执行排名")
            st.info("💡 **分析目标**：综合评估上级的面谈执行力，找出最佳实践和问题管理者")
            
            # 周期选择
            selected_period = st.selectbox("📅 选择考核周期", periods, key="ranking_period")
            
            if selected_period:
                with st.spinner('正在计算排名...'):
                    # 获取排名数据
                    rankings = processor.get_interviewer_rankings(selected_period)
                    
                    if rankings:
                        # Top/Bottom展示
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 🥇 Top 3 最佳上级")
                            for i, rank in enumerate(rankings[:3], 1):
                                st.success(f"""
                                **{i}. {rank['interviewer']}**
                                - 完成率: {rank['completion_rate']:.1f}%
                                - 质量分: {rank['avg_quality_score']:.0f}
                                - 负责人数: {rank['total_count']}人
                                """)
                        
                        with col2:
                            st.markdown("#### ⚠️ Bottom 3 需改进上级")
                            for i, rank in enumerate(rankings[-3:][::-1], 1):
                                st.warning(f"""
                                **{i}. {rank['interviewer']}**
                                - 完成率: {rank['completion_rate']:.1f}%
                                - 质量分: {rank['avg_quality_score']:.0f}
                                - 低质量数: {rank['low_quality_count']}人
                                """)
                        
                        st.markdown("---")
                        
                        # 综合排名图表
                        fig_ranking = visualizer.create_interviewer_ranking_chart(rankings)
                        if fig_ranking:
                            st.plotly_chart(fig_ranking, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 详细排名表
                        st.markdown("### 📋 详细排名数据")
                        
                        df_ranking = pd.DataFrame(rankings)
                        df_display = df_ranking[[
                            'interviewer', 'total_count', 'completed_count', 
                            'completion_rate', 'avg_quality_score', 'low_quality_count'
                        ]]
                        df_display.columns = [
                            '上级', '负责人数', '已完成', 
                            '完成率(%)', '平均质量分', '低质量数'
                        ]
                        
                        # 格式化
                        df_display['完成率(%)'] = df_display['完成率(%)'].round(1)
                        df_display['平均质量分'] = df_display['平均质量分'].round(1)
                        
                        st.dataframe(df_display, use_container_width=True)
                        
                        # 导出
                        csv = df_display.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 导出排名数据",
                            data=csv,
                            file_name=f"interviewer_ranking_{selected_period}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("⚠️ 该周期暂无上级排名数据")

# ==================== 页面5: 考核方案管理 ====================
elif menu == "🔄 考核方案管理":
    # Header区域
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">🔄 考核方案管理</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">记录和跟踪考核方案变更历史</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 添加方案变更", "📜 变更历史"])
    
    with tab1:
        st.markdown("""
        <div class="data-card" style="margin-bottom: 20px;">
            <div class="card-title">添加新的考核方案变更</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            effective_period = st.text_input("生效周期", placeholder="例如: 2026年3月")
            scheme_name = st.text_input("方案名称", placeholder="例如: Q1考核方案调整")
        
        with col2:
            department = st.text_input("适用部门", placeholder="例如: 客服部")
            position_type = st.text_input("岗位类型", placeholder="例如: 运营支持")
        
        change_description = st.text_area(
            "变更说明",
            placeholder="请描述本次考核方案的主要变更内容...",
            height=100
        )
        
        st.subheader("指标配置")
        indicator_config = st.text_area(
            "指标配置（JSON格式）",
            placeholder='{"响应时长": 10, "满意度": 10, "转化率": 8}',
            height=100
        )
        
        if st.button("💾 保存方案", type="primary"):
            if effective_period and scheme_name:
                cursor = db.conn.cursor()
                cursor.execute('''
                    INSERT INTO assessment_scheme 
                    (effective_period, scheme_name, department, position_type, 
                     indicator_config, change_description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (effective_period, scheme_name, department, position_type, 
                      indicator_config, change_description))
                db.conn.commit()
                
                st.success("✅ 方案已保存")
            else:
                st.warning("⚠️ 请填写必填项")
    
    with tab2:
        st.subheader("考核方案变更历史")
        
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT effective_period, scheme_name, department, change_description, create_date
            FROM assessment_scheme
            ORDER BY create_date DESC
        ''')
        schemes = cursor.fetchall()
        
        if schemes:
            for scheme in schemes:
                st.markdown(f"""
                <div class="success-box">
                    <h4>{scheme[1]}</h4>
                    <p><strong>生效周期:</strong> {scheme[0]} | <strong>部门:</strong> {scheme[2] or '全部'}</p>
                    <p><strong>变更说明:</strong> {scheme[3] or '无'}</p>
                    <p><small>创建时间: {scheme[4]}</small></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无方案变更记录")

# ==================== 页面6: 智能查询 ====================
elif menu == "🔍 智能查询":
    # Header区域
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">🔍 智能查询中心</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">多维度组合查询，快速定位目标数据</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 筛选器区域 - 白色卡片
    st.markdown("""
    <div class="data-card" style="margin-bottom: 24px;">
        <div class="card-title">🔍 高级筛选</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("员工姓名/工号", placeholder="输入姓名或工号")
    
    with col2:
        periods = db.get_all_periods()
        period_filter = st.multiselect("考核周期", periods if periods else [])
    
    with col3:
        score_range = st.slider("分数范围", 0, 100, (70, 100))
    
    if st.button("🔍 查询", type="primary"):
        cursor = db.conn.cursor()
        
        # 构建SQL查询
        query = "SELECT * FROM performance_results WHERE 1=1"
        params = []
        
        if search_name:
            query += " AND (employee_name LIKE ? OR employee_id LIKE ?)"
            params.extend([f"%{search_name}%", f"%{search_name}%"])
        
        if period_filter:
            query += f" AND period IN ({','.join(['?']*len(period_filter))})"
            params.extend(period_filter)
        
        query += " AND total_score BETWEEN ? AND ?"
        params.extend([score_range[0], score_range[1]])
        
        query += " ORDER BY period DESC, total_score DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if results:
            st.success(f"✅ 找到 {len(results)} 条记录")
            
            df_results = pd.DataFrame(results)
            df_display = df_results[['period', 'employee_name', 'employee_id', 
                                     'department_l2', 'total_score', 'dept_rank']]
            df_display.columns = ['考核周期', '姓名', '工号', '部门', '总分', '排名']
            
            st.dataframe(df_display, use_container_width=True)
            
            # 导出功能
            csv = df_display.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 导出查询结果",
                data=csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("未找到符合条件的记录")

# ==================== 页面6: 绩效分布监控 ====================
elif menu == "📊 绩效分布监控":
    # Header区域
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">📊 绩效分布监控</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">实时监控分数分布健康度，提前预警调整压力</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取所有周期
    periods = db.get_all_periods()
    
    if not periods:
        st.warning("⚠️ 暂无数据，请先上传绩效数据")
    else:
        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 当前周期分布",
            "📊 多周期平均分布",
            "🏢 部门分布对比",
            "⚖️ 强制分布适配"
        ])
        
        # ==================== Tab1: 当前周期分布 ====================
        with tab1:
            # 筛选器 - 白色卡片
            st.markdown("""
            <div class="data-card" style="margin-bottom: 24px;">
                <div class="card-title">🔍 筛选条件</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 筛选条件
            col1, col2 = st.columns(2)
            
            with col1:
                selected_period = st.selectbox("📅 考核周期", periods, key="dist_period")
            
            with col2:
                # 获取部门列表
                cursor = db.conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT department_l2
                    FROM performance_results
                    WHERE department_l2 IS NOT NULL
                    ORDER BY department_l2
                ''')
                departments = ["全部"] + [row[0] for row in cursor.fetchall()]
                selected_dept = st.selectbox("🏢 部门", departments, key="dist_dept")
            
            if selected_period:
                with st.spinner('正在分析分数分布...'):
                    # 获取分布数据（支持部门筛选）
                    dist_data = processor.get_score_distribution(selected_period, department=selected_dept)
                    
                    if dist_data:
                        # 健康度分析
                        health_analysis = processor.analyze_distribution_health(dist_data)
                        
                        # 顶部指标卡片
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            st.metric("参与人数", dist_data['total_count'])
                        
                        with col2:
                            st.metric("平均分", f"{dist_data['avg_score']:.2f}")
                        
                        with col3:
                            st.metric("标准差", f"{dist_data['std_score']:.2f}")
                        
                        with col4:
                            st.metric("最高分", f"{dist_data['max_score']:.1f}")
                        
                        with col5:
                            st.metric("最低分", f"{dist_data['min_score']:.1f}")
                        
                        st.markdown("---")
                        
                        # 健康度仪表盘 + 分布图
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            # 健康度仪表盘
                            gauge_fig = visualizer.create_health_gauge_chart(
                                health_analysis['health_score'],
                                health_analysis['health_level']
                            )
                            if gauge_fig:
                                st.plotly_chart(gauge_fig, use_container_width=True)
                        
                        with col2:
                            # 区间占比图
                            ratio_fig = visualizer.create_interval_ratio_chart(dist_data)
                            if ratio_fig:
                                st.plotly_chart(ratio_fig, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 分数分布直方图
                        hist_fig = visualizer.create_score_distribution_histogram(dist_data)
                        if hist_fig:
                            st.plotly_chart(hist_fig, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 健康度分析报告
                        st.markdown("### 📋 分布健康度分析报告")
                        
                        # 显示健康度等级
                        if health_analysis['health_color'] == 'success':
                            st.success(f"**健康度评分：{health_analysis['health_score']}分 ({health_analysis['health_level']})**")
                        elif health_analysis['health_color'] == 'info':
                            st.info(f"**健康度评分：{health_analysis['health_score']}分 ({health_analysis['health_level']})**")
                        elif health_analysis['health_color'] == 'warning':
                            st.warning(f"**健康度评分：{health_analysis['health_score']}分 ({health_analysis['health_level']})**")
                        else:
                            st.error(f"**健康度评分：{health_analysis['health_score']}分 ({health_analysis['health_level']})**")
                        
                        # 显示完整分析报告
                        st.markdown(health_analysis['summary'])
                        
                        # 详细数据表
                        st.markdown("---")
                        st.markdown("### 📊 区间分布详细数据")
                        
                        dist_df = pd.DataFrame({
                            '分数区间': list(dist_data['distribution'].keys()),
                            '人数': list(dist_data['distribution'].values()),
                            '占比': [f"{dist_data['ratios'][k]:.1f}%" for k in dist_data['distribution'].keys()]
                        })
                        
                        st.dataframe(dist_df, use_container_width=True)
                    else:
                        st.warning("⚠️ 该周期暂无绩效数据")
        
        # ==================== Tab2: 多周期平均分布 ====================
        with tab2:
            st.markdown("### 📊 多周期平均绩效分布（模拟年度评分基础）")
            st.info("💡 **分析目标**：基于员工最近N期平均分，提前预判年度绩效格局")
            
            # 配置区
            col1, col2, col3 = st.columns(3)
            
            with col1:
                n_periods = st.slider("📅 选择周期数", 3, 12, 6, help="计算员工最近N期的平均分")
            
            with col2:
                st.markdown(f"**分析范围**：最近 {n_periods} 期")
                if len(periods) >= n_periods:
                    st.success(f"✅ 数据充足（共{len(periods)}期）")
                else:
                    st.warning(f"⚠️ 数据不足（仅{len(periods)}期）")
            
            with col3:
                # 部门筛选
                cursor = db.conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT department_l2
                    FROM performance_results
                    WHERE department_l2 IS NOT NULL
                    ORDER BY department_l2
                ''')
                departments_avg = ["全部"] + [row[0] for row in cursor.fetchall()]
                selected_dept_avg = st.selectbox("🏢 选择部门", departments_avg, key="avg_dept")
            
            with st.spinner('正在计算多周期平均分布...'):
                # 获取平均分布（支持部门筛选）
                avg_dist_data = processor.get_avg_score_distribution(
                    periods=None, 
                    n_periods=n_periods,
                    department=selected_dept_avg
                )
                
                if avg_dist_data:
                    # 健康度分析
                    avg_health = processor.analyze_distribution_health(avg_dist_data)
                    
                    # 顶部指标
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("统计周期数", avg_dist_data['period_count'])
                    
                    with col2:
                        st.metric("员工人数", avg_dist_data['total_count'])
                    
                    with col3:
                        st.metric("平均分", f"{avg_dist_data['avg_score']:.2f}")
                    
                    with col4:
                        st.metric("标准差", f"{avg_dist_data['std_score']:.2f}")
                    
                    st.markdown("---")
                    
                    # 对比图：当前 vs 平均
                    current_dist = processor.get_score_distribution(periods[-1], department=selected_dept_avg)
                    
                    if current_dist:
                        # 双图对比
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📈 分数分布对比")
                            hist_fig = visualizer.create_score_distribution_histogram(
                                current_dist, 
                                show_avg=True, 
                                avg_distribution_data=avg_dist_data
                            )
                            if hist_fig:
                                st.plotly_chart(hist_fig, use_container_width=True)
                        
                        with col2:
                            st.markdown("#### 📊 区间占比对比")
                            ratio_fig = visualizer.create_interval_ratio_chart(
                                current_dist,
                                comparison_data=avg_dist_data
                            )
                            if ratio_fig:
                                st.plotly_chart(ratio_fig, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # 健康度分析
                    st.markdown("### 📋 平均分布健康度分析")
                    
                    if avg_health['health_color'] == 'success':
                        st.success(f"**健康度评分：{avg_health['health_score']}分 ({avg_health['health_level']})**")
                    elif avg_health['health_color'] == 'info':
                        st.info(f"**健康度评分：{avg_health['health_score']}分 ({avg_health['health_level']})**")
                    elif avg_health['health_color'] == 'warning':
                        st.warning(f"**健康度评分：{avg_health['health_score']}分 ({avg_health['health_level']})**")
                    else:
                        st.error(f"**健康度评分：{avg_health['health_score']}分 ({avg_health['health_level']})**")
                    
                    st.markdown(avg_health['summary'])
                    
                    # 高分/低分人员清单
                    st.markdown("---")
                    st.markdown("### 👥 关键人员清单")
                    
                    col1, col2 = st.columns(2)
                    
                    employee_data = avg_dist_data['employee_data']
                    sorted_employees = sorted(employee_data, key=lambda x: x['avg_score'], reverse=True)
                    
                    with col1:
                        st.markdown("#### 🌟 高分人员 (平均分≥90)")
                        high_performers = [e for e in sorted_employees if e['avg_score'] >= 90]
                        if high_performers:
                            high_df = pd.DataFrame(high_performers)[['employee_name', 'avg_score', 'department_l2']]
                            high_df.columns = ['姓名', '平均分', '部门']
                            high_df['平均分'] = high_df['平均分'].round(2)
                            st.dataframe(high_df, use_container_width=True)
                        else:
                            st.info("暂无平均分≥90的员工")
                    
                    with col2:
                        st.markdown("#### ⚠️ 低分人员 (平均分<70)")
                        low_performers = [e for e in sorted_employees if e['avg_score'] < 70]
                        if low_performers:
                            low_df = pd.DataFrame(low_performers)[['employee_name', 'avg_score', 'department_l2']]
                            low_df.columns = ['姓名', '平均分', '部门']
                            low_df['平均分'] = low_df['平均分'].round(2)
                            st.dataframe(low_df, use_container_width=True)
                        else:
                            st.info("暂无平均分<70的员工")
                else:
                    st.warning("⚠️ 暂无足够数据计算平均分布")
        
        # ==================== Tab3: 部门分布对比 ====================
        with tab3:
            st.markdown("### 🏢 部门绩效分布对比分析")
            st.info("💡 **分析目标**：识别评分偏松/偏严的部门，发现区分度最好的部门")
            
            # 选择周期
            selected_period_dept = st.selectbox("📅 选择考核周期", periods, key="dept_dist_period")
            
            if selected_period_dept:
                with st.spinner('正在分析部门分布...'):
                    dept_dist = processor.get_department_distribution(selected_period_dept)
                    
                    if dept_dist and dept_dist['departments']:
                        departments = dept_dist['departments']
                        
                        # 顶部统计
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("部门数量", len(departments))
                        
                        with col2:
                            avg_scores = [d['avg_score'] for d in departments]
                            st.metric("全局平均分", f"{sum(avg_scores)/len(avg_scores):.2f}")
                        
                        with col3:
                            std_scores = [d['std_score'] for d in departments]
                            st.metric("平均标准差", f"{sum(std_scores)/len(std_scores):.2f}")
                        
                        st.markdown("---")
                        
                        # 部门对比图
                        dept_comp_fig = visualizer.create_department_comparison_chart(dept_dist)
                        if dept_comp_fig:
                            st.plotly_chart(dept_comp_fig, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 部门区间分布热力图
                        dept_heatmap = visualizer.create_department_interval_heatmap(dept_dist)
                        if dept_heatmap:
                            st.plotly_chart(dept_heatmap, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 部门分析洞察
                        st.markdown("### 💡 部门分析洞察")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 🌟 评分最严格的部门")
                            # 平均分最低的3个部门
                            strict_depts = sorted(departments, key=lambda x: x['avg_score'])[:3]
                            for i, dept in enumerate(strict_depts, 1):
                                st.success(f"{i}. **{dept['department']}**: 平均 {dept['avg_score']:.2f}分")
                        
                        with col2:
                            st.markdown("#### ⚠️ 评分偏宽松的部门")
                            # 平均分最高的3个部门
                            lenient_depts = sorted(departments, key=lambda x: x['avg_score'], reverse=True)[:3]
                            for i, dept in enumerate(lenient_depts, 1):
                                st.warning(f"{i}. **{dept['department']}**: 平均 {dept['avg_score']:.2f}分")
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 🎯 区分度最好的部门")
                            # 标准差最大的3个部门
                            best_diff = sorted(departments, key=lambda x: x['std_score'], reverse=True)[:3]
                            for i, dept in enumerate(best_diff, 1):
                                st.info(f"{i}. **{dept['department']}**: 标准差 {dept['std_score']:.2f}")
                        
                        with col2:
                            st.markdown("#### ⚠️ 区分度不足的部门")
                            # 标准差最小的3个部门
                            poor_diff = sorted(departments, key=lambda x: x['std_score'])[:3]
                            for i, dept in enumerate(poor_diff, 1):
                                st.warning(f"{i}. **{dept['department']}**: 标准差 {dept['std_score']:.2f}")
                        
                        # 详细数据表
                        st.markdown("---")
                        st.markdown("### 📊 部门详细数据")
                        
                        dept_df = pd.DataFrame([{
                            '部门': d['department'],
                            '人数': d['total_count'],
                            '平均分': round(d['avg_score'], 2),
                            '标准差': round(d['std_score'], 2),
                            '最高分': round(d['max_score'], 2),
                            '最低分': round(d['min_score'], 2),
                            '≥90占比': f"{d['ratios']['≥90 (高绩效)']:.1f}%",
                            '<70占比': f"{d['ratios']['<70 (需关注)']:.1f}%"
                        } for d in departments])
                        
                        st.dataframe(dept_df, use_container_width=True)
                    else:
                        st.warning("⚠️ 该周期暂无部门数据")
        
        # ==================== Tab4: 强制分布适配分析 ====================
        with tab4:
            st.markdown("### ⚖️ 强制分布适配分析（年度预判）")
            st.info("💡 **分析目标**：提前判断当前分数分布能否自然满足强制分布要求")
            
            # 配置区 - 第一行：年份和周期选择
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # 获取所有可用年份
                cursor = db.conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT period 
                    FROM performance_results 
                    ORDER BY period DESC
                ''')
                all_periods = [row[0] for row in cursor.fetchall()]
                
                # 提取年份（从周期中提取，如"2026年3月"→"2026"）
                available_years = sorted(list(set([
                    period.split('年')[0] + '年' if '年' in period else period[:4] 
                    for period in all_periods
                ])), reverse=True)
                
                # 添加"全部年份"选项
                year_options = ["全部年份"] + available_years
                selected_year = st.selectbox("📅 选择年份", year_options, key="forced_year")
            
            with col2:
                n_periods_forced = st.slider("📊 基于最近N期平均分", 3, 12, 6, key="forced_periods")
                
                # 显示实际会使用的周期数
                if selected_year != "全部年份":
                    year_periods = [p for p in all_periods if p.startswith(selected_year.replace('年', ''))]
                    actual_n = min(n_periods_forced, len(year_periods))
                    if actual_n < n_periods_forced:
                        st.caption(f"⚠️ {selected_year}只有{actual_n}期数据")
                else:
                    st.caption(f"将使用最近{n_periods_forced}期")
            
            with col3:
                # 部门筛选
                cursor.execute('''
                    SELECT DISTINCT department_l2
                    FROM performance_results
                    WHERE department_l2 IS NOT NULL
                    ORDER BY department_l2
                ''')
                departments_forced = ["全部"] + [row[0] for row in cursor.fetchall()]
                selected_dept_forced = st.selectbox("🏢 选择部门", departments_forced, key="forced_dept")
            
            # 配置区 - 第二行：目标比例
            st.markdown("**目标比例配置**（可调整）")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                a_ratio = st.number_input("A级占比 (%)", 0, 100, 20, step=5)
            
            with col2:
                b_ratio = st.number_input("B级占比 (%)", 0, 100, 50, step=5)
            
            with col3:
                b_minus_ratio = st.number_input("B-级占比 (%)", 0, 100, 20, step=5)
            
            with col4:
                c_ratio = st.number_input("C级占比 (%)", 0, 100, 10, step=5)
            
            total_ratio = a_ratio + b_ratio + b_minus_ratio + c_ratio
            
            if total_ratio != 100:
                st.error(f"⚠️ 比例总和必须为100%，当前为 {total_ratio}%")
            else:
                st.success(f"✅ 比例配置有效：A{a_ratio}% + B{b_ratio}% + B-{b_minus_ratio}% + C{c_ratio}% = 100%")
                
                with st.spinner('正在分析强制分布适配度...'):
                    # 获取平均分布（支持年份和部门筛选）
                    avg_dist_forced = processor.get_avg_score_distribution(
                        periods=None, 
                        n_periods=n_periods_forced,
                        department=selected_dept_forced,
                        year=selected_year if selected_year != "全部年份" else None
                    )
                    
                    if avg_dist_forced:
                        # 强制分布适配分析
                        target_ratios = {
                            'A': a_ratio,
                            'B': b_ratio,
                            'B-': b_minus_ratio,
                            'C': c_ratio
                        }
                        
                        fit_analysis = processor.analyze_forced_distribution(avg_dist_forced, target_ratios)
                        
                        if fit_analysis:
                            # 顶部指标
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("统计周期", f"最近{n_periods_forced}期")
                            
                            with col2:
                                st.metric("总人数", fit_analysis['total_count'])
                            
                            with col3:
                                st.metric("匹配率", f"{fit_analysis['match_ratio']:.1f}%")
                            
                            with col4:
                                st.metric("不匹配人数", fit_analysis['mismatch_count'])
                            
                            st.markdown("---")
                            
                            # 适配结论
                            if fit_analysis['fit_color'] == 'success':
                                st.success(f"### {fit_analysis['fit_message']}")
                            elif fit_analysis['fit_color'] == 'info':
                                st.info(f"### {fit_analysis['fit_message']}")
                            else:
                                st.warning(f"### {fit_analysis['fit_message']}")
                            
                            st.markdown("---")
                            
                            # 对比图
                            forced_comp_fig = visualizer.create_forced_distribution_comparison(fit_analysis)
                            if forced_comp_fig:
                                st.plotly_chart(forced_comp_fig, use_container_width=True)
                            
                            st.markdown("---")
                            
                            # 等级分配详情
                            st.markdown("### 📊 等级分配详细数据")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 目标分配（强制比例）")
                                target_df = pd.DataFrame({
                                    '等级': ['A', 'B', 'B-', 'C'],
                                    '目标人数': [fit_analysis['target_counts'][level] for level in ['A', 'B', 'B-', 'C']],
                                    '目标占比': [f"{target_ratios[level]}%" for level in ['A', 'B', 'B-', 'C']]
                                })
                                st.dataframe(target_df, use_container_width=True, hide_index=True)
                            
                            with col2:
                                st.markdown("#### 自然分布（基于分数）")
                                simulated_levels = fit_analysis['simulated_levels']
                                natural_counts = {'A': 0, 'B': 0, 'B-': 0, 'C': 0, None: 0}
                                for sim in simulated_levels:
                                    level = sim.get('natural_level')
                                    if level in natural_counts:
                                        natural_counts[level] += 1
                                
                                total = fit_analysis['total_count']
                                natural_df = pd.DataFrame({
                                    '等级': ['A', 'B', 'B-', 'C'],
                                    '自然人数': [natural_counts.get(level, 0) for level in ['A', 'B', 'B-', 'C']],
                                    '自然占比': [f"{natural_counts.get(level, 0)/total*100:.1f}%" if total > 0 else "0%" for level in ['A', 'B', 'B-', 'C']]
                                })
                                st.dataframe(natural_df, use_container_width=True, hide_index=True)
                            
                            # 不匹配员工示例
                            if fit_analysis['mismatch_count'] > 0:
                                st.markdown("---")
                                st.markdown("### ⚠️ 需要调整的员工示例（前10个）")
                                
                                mismatch_df = pd.DataFrame(fit_analysis['mismatch_examples'])
                                if not mismatch_df.empty:
                                    mismatch_df = mismatch_df[['employee_name', 'avg_score', 'natural_level', 'simulated_level']]
                                    mismatch_df.columns = ['姓名', '平均分', '自然等级', '强制等级']
                                    mismatch_df['平均分'] = mismatch_df['平均分'].round(2)
                                    st.dataframe(mismatch_df, use_container_width=True)
                                    
                                    st.caption("💡 **说明**：这些员工的自然等级（基于分数）与强制分布要求的等级不一致，年底可能需要调整")
                        else:
                            st.error("⚠️ 适配分析失败")
                    else:
                        st.warning("⚠️ 暂无足够数据进行适配分析")

# ==================== 页面7: 高级分析中心 ====================
elif menu == "📊 高级分析":
    # Header区域
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">📊 高级分析中心</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">数据驱动的管理决策支持</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取所有周期
    periods = db.get_all_periods()
    
    if not periods:
        st.warning("⚠️ 暂无数据，请先上传绩效数据")
    else:
        # 筛选器区域 - 白色卡片
        st.markdown("""
        <div class="data-card" style="margin-bottom: 24px;">
            <div class="card-title">🔍 筛选条件</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 周期选择
        selected_period = st.selectbox(
            "📅 选择考核周期",
            periods,
            index=0
        )
        
        if selected_period:
            # 创建三个标签页
            tab1, tab2, tab3 = st.tabs([
                "🔬 指标拆解分析", 
                "📊 部门/岗位对比", 
                "🔗 指标贡献分析"
            ])
            
            # ==================== Tab1: 指标拆解分析 ====================
            with tab1:
                st.markdown("### 🔬 指标拆解分析")
                st.info("💡 **分析目标**：找出区分度不足的指标、发现评分偏高/偏低的问题")
                
                with st.spinner('正在分析指标数据...'):
                    # 计算指标统计数据
                    indicator_stats = processor.analyze_indicators(selected_period)
                    
                    if indicator_stats:
                        # 显示统计信息
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("分析指标数", len(indicator_stats))
                        with col2:
                            avg_std = sum([s['std_score'] for s in indicator_stats]) / len(indicator_stats)
                            st.metric("平均标准差", f"{avg_std:.2f}")
                        with col3:
                            low_distinction = len([s for s in indicator_stats if s['std_score'] < 5])
                            st.metric("区分度不足", low_distinction)
                        with col4:
                            high_avg = len([s for s in indicator_stats if s['avg_score'] > 90])
                            st.metric("评分偏高", high_avg)
                        
                        st.markdown("---")
                        
                        # 可视化部分
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # 平均分柱状图
                            fig_avg = visualizer.create_indicator_avg_chart(indicator_stats)
                            if fig_avg:
                                st.plotly_chart(fig_avg, use_container_width=True)
                        
                        with col2:
                            # 标准差柱状图
                            fig_std = visualizer.create_indicator_std_chart(indicator_stats)
                            if fig_std:
                                st.plotly_chart(fig_std, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 生成智能结论
                        st.markdown("### 🤖 智能分析结论")
                        insights = processor.generate_indicator_insights(indicator_stats)
                        
                        if insights:
                            # 按类型分组显示
                            warnings = [i for i in insights if i['severity'] == 'warning']
                            successes = [i for i in insights if i['severity'] == 'success']
                            infos = [i for i in insights if i['severity'] == 'info']
                            
                            if warnings:
                                st.markdown("#### ⚠️ 需要关注的问题")
                                for insight in warnings[:5]:  # 只显示前5个
                                    st.warning(f"**{insight['type']}**: {insight['message']}")
                            
                            if successes:
                                st.markdown("#### ✅ 表现良好的指标")
                                for insight in successes[:3]:
                                    st.success(f"**{insight['type']}**: {insight['message']}")
                            
                            if infos:
                                st.markdown("#### 💡 其他观察")
                                for insight in infos[:3]:
                                    st.info(f"**{insight['type']}**: {insight['message']}")
                        
                        st.markdown("---")
                        
                        # 详细数据表格
                        st.markdown("### 📋 详细统计数据")
                        df_stats = pd.DataFrame(indicator_stats)
                        df_display = df_stats[['indicator_name', 'avg_score', 'std_score', 
                                              'max_score', 'min_score', 'sample_count']]
                        df_display.columns = ['指标名称', '平均分', '标准差', '最高分', '最低分', '样本数']
                        
                        # 设置数值格式
                        df_display['平均分'] = df_display['平均分'].round(2)
                        df_display['标准差'] = df_display['标准差'].round(2)
                        
                        st.dataframe(df_display, use_container_width=True, height=400)
                        
                        # 导出功能
                        csv = df_display.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 导出分析结果",
                            data=csv,
                            file_name=f"indicator_analysis_{selected_period}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("⚠️ 该周期暂无足够的指标数据进行分析")
            
            # ==================== Tab2: 部门/岗位对比 ====================
            with tab2:
                st.markdown("### 📊 部门对比分析")
                st.info("💡 **分析目标**：识别各部门绩效差异，找出表现突出和需要改进的部门")
                
                with st.spinner('正在分析部门数据...'):
                    # 部门对比分析
                    dept_stats = processor.analyze_departments(selected_period)
                    
                    if dept_stats:
                        # 整体统计
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("参与部门数", len(dept_stats))
                        with col2:
                            avg_dept_score = sum([d['avg_score'] for d in dept_stats]) / len(dept_stats)
                            st.metric("部门平均分", f"{avg_dept_score:.2f}")
                        with col3:
                            max_dept = max(dept_stats, key=lambda x: x['avg_score'])
                            st.metric("最高分部门", f"{max_dept['department'][:6]}... ({max_dept['avg_score']:.1f})")
                        
                        st.markdown("---")
                        
                        # 部门对比图
                        dept_dist_for_chart = {'departments': dept_stats, 'period': selected_period}
                        fig_dept = visualizer.create_department_comparison_chart(dept_dist_for_chart)
                        if fig_dept:
                            st.plotly_chart(fig_dept, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 详细数据表
                        st.markdown("### 📋 部门详细数据")
                        df_dept = pd.DataFrame(dept_stats)
                        df_dept_display = df_dept[['department', 'total_count', 'avg_score', 
                                                   'excellent_rate', 'need_attention_rate']]
                        df_dept_display.columns = ['部门', '人数', '平均分', '优秀率(%)', '需关注率(%)']
                        df_dept_display['平均分'] = df_dept_display['平均分'].round(2)
                        df_dept_display['优秀率(%)'] = df_dept_display['优秀率(%)'].round(1)
                        df_dept_display['需关注率(%)'] = df_dept_display['需关注率(%)'].round(1)
                        
                        st.dataframe(df_dept_display, use_container_width=True)
                        
                        # 关键洞察
                        st.markdown("### 💡 关键洞察")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 🏆 表现突出部门")
                            top_depts = sorted(dept_stats, key=lambda x: x['avg_score'], reverse=True)[:3]
                            for i, dept in enumerate(top_depts, 1):
                                st.success(f"{i}. **{dept['department']}**: 平均分{dept['avg_score']:.2f}，优秀率{dept['excellent_rate']:.1f}%")
                        
                        with col2:
                            st.markdown("#### ⚠️ 需要改进部门")
                            bottom_depts = sorted(dept_stats, key=lambda x: x['avg_score'])[:3]
                            for i, dept in enumerate(bottom_depts, 1):
                                st.warning(f"{i}. **{dept['department']}**: 平均分{dept['avg_score']:.2f}，需关注率{dept['need_attention_rate']:.1f}%")
                    else:
                        st.warning("⚠️ 该周期暂无部门数据")
            
            # ==================== Tab3: 指标贡献分析 ====================
            with tab3:
                st.markdown("### 🔗 指标贡献分析")
                st.info("💡 **分析目标**：识别哪些指标对总分影响最大，指导考核方案优化")
                
                with st.spinner('正在计算指标相关性...'):
                    # 计算相关系数
                    correlations = processor.calculate_indicator_correlations(selected_period)
                    
                    if correlations:
                        # 统计信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("分析指标数", len(correlations))
                        with col2:
                            strong_corr = len([c for c in correlations if abs(c['correlation']) >= 0.7])
                            st.metric("强相关指标", strong_corr)
                        with col3:
                            weak_corr = len([c for c in correlations if abs(c['correlation']) < 0.4])
                            st.metric("弱相关指标", weak_corr)
                        
                        st.markdown("---")
                        
                        # 相关性图表
                        fig_corr = visualizer.create_correlation_chart(correlations)
                        if fig_corr:
                            st.plotly_chart(fig_corr, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # 关键发现
                        st.markdown("### 🎯 关键发现")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 💪 高影响力指标")
                            st.caption("这些指标对总分影响最大，应该重点关注")
                            high_impact = [c for c in correlations if abs(c['correlation']) >= 0.7][:5]
                            if high_impact:
                                for c in high_impact:
                                    st.success(f"**{c['indicator_name']}**: 相关系数 {c['correlation']:.3f}")
                            else:
                                st.info("暂无强相关指标")
                        
                        with col2:
                            st.markdown("#### 🔍 低影响力指标")
                            st.caption("这些指标对总分影响较小，可能需要重新评估")
                            low_impact = [c for c in correlations if abs(c['correlation']) < 0.3][:5]
                            if low_impact:
                                for c in low_impact:
                                    st.warning(f"**{c['indicator_name']}**: 相关系数 {c['correlation']:.3f}")
                            else:
                                st.info("所有指标都有一定影响力")
                        
                        st.markdown("---")
                        
                        # 详细数据表
                        st.markdown("### 📋 相关性详细数据")
                        df_corr = pd.DataFrame(correlations)
                        df_corr['abs_correlation'] = df_corr['correlation'].abs()
                        df_corr = df_corr.sort_values('abs_correlation', ascending=False)
                        
                        df_corr_display = df_corr[['indicator_name', 'correlation', 'sample_count']]
                        df_corr_display.columns = ['指标名称', '相关系数', '样本数']
                        df_corr_display['相关系数'] = df_corr_display['相关系数'].round(3)
                        
                        st.dataframe(df_corr_display, use_container_width=True, height=400)
                        
                        # 建议
                        st.markdown("### 💡 优化建议")
                        st.info("""
                        **基于相关性分析的建议**：
                        
                        1. **强相关指标（≥0.7）**：这些指标对总分影响最大，应该：
                           - 保持或提高权重
                           - 加强这些指标的管理和追踪
                           - 在绩效沟通中重点关注
                        
                        2. **弱相关指标（<0.3）**：这些指标对总分影响较小，建议：
                           - 重新评估指标的合理性
                           - 考虑是否需要调整评分标准
                           - 或者从考核体系中移除
                        
                        3. **负相关指标**：如果出现负相关（得分越高总分越低），需要：
                           - 检查指标定义是否合理
                           - 检查数据录入是否有误
                           - 重新审视指标与绩效的关系
                        """)
                    else:
                        # 检查是否有指标数据
                        cursor = db.conn.cursor()
                        cursor.execute('''
                            SELECT COUNT(*) as indicator_count
                            FROM performance_indicators
                            WHERE period = ?
                        ''', (selected_period,))
                        indicator_count = cursor.fetchone()[0]
                        
                        cursor.execute('''
                            SELECT COUNT(*) as employee_count
                            FROM performance_results
                            WHERE period = ?
                        ''', (selected_period,))
                        employee_count = cursor.fetchone()[0]
                        
                        if indicator_count == 0:
                            st.error(f"""
                            ⚠️ **该周期缺少指标数据**
                            
                            当前状态：
                            - 员工数：{employee_count} 人
                            - 指标数据：0 条 ❌
                            
                            **问题原因**：
                            上传的Excel文件中只包含总分，没有包含各个指标的详细分数。
                            
                            **解决方法**：
                            1. 确保Excel文件中包含指标列（如：结果导向、用户体验、问题解决等）
                            2. 每个员工都要有各个指标的分数，不能只有总分
                            3. 重新上传包含完整指标数据的Excel文件
                            
                            **需要的数据格式示例**：
                            ```
                            员工姓名 | 结果导向 | 用户体验 | 问题解决 | ... | 总分
                            --------|---------|---------|---------|-----|----
                            张三    | 95      | 92      | 88      | ... | 91.7
                            李四    | 88      | 85      | 90      | ... | 87.7
                            ```
                            """)
                        else:
                            st.warning(f"""
                            ⚠️ **数据量不足，无法进行相关性分析**
                            
                            当前状态：
                            - 员工数：{employee_count} 人
                            - 指标数据：{indicator_count} 条
                            
                            **最低要求**：
                            - 每个指标至少需要 **3个员工** 的数据
                            - 建议至少 **5个员工** 才能得到准确的相关性分析
                            
                            **建议**：
                            增加参与考核的员工人数，或等待积累更多数据后再进行分析。
                            """)

# ==================== 页面8: 数据管理 ====================
elif menu == "🗄️ 数据管理":
    # Header区域
    st.markdown("""
    <div class="page-header" style="margin-bottom: 32px; margin-top: -100px;">
        <h1 class="page-title">🗄️ 数据库管理</h1>
        <p class="page-subtitle" style="margin-bottom: 0;">数据概览、删除、备份与恢复</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 数据概览", "🗑️ 删除数据", "💾 备份与恢复"])
    
    with tab1:
        st.markdown("""
        <div class="data-card" style="margin-bottom: 20px;">
            <div class="card-title">📊 数据库概览</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 获取所有周期
        periods = db.get_all_periods()
        
        if periods:
            st.success(f"✅ 数据库中共有 {len(periods)} 个考核周期的数据")
            
            # 显示每个周期的详细信息
            for period in periods:
                with st.expander(f"📅 {period}", expanded=False):
                    stats = processor.get_summary_stats(period)
                    if stats:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("员工数", stats['total_employees'])
                        with col2:
                            st.metric("平均分", f"{stats['avg_score']:.2f}")
                        with col3:
                            st.metric("最高分", f"{stats['max_score']:.2f}")
                        with col4:
                            st.metric("最低分", f"{stats['min_score']:.2f}")
                        
                        # 查看该周期的员工列表
                        cursor = db.conn.cursor()
                        cursor.execute('''
                            SELECT employee_name, employee_id, total_score, dept_rank
                            FROM performance_results
                            WHERE period = ?
                            ORDER BY total_score DESC
                            LIMIT 10
                        ''', (period,))
                        top_employees = cursor.fetchall()
                        
                        if top_employees:
                            st.write("**前10名员工：**")
                            df_top = pd.DataFrame(
                                [dict(row) for row in top_employees],
                                columns=['employee_name', 'employee_id', 'total_score', 'dept_rank']
                            )
                            df_top.columns = ['姓名', '工号', '总分', '排名']
                            st.dataframe(df_top, use_container_width=True)
        else:
            st.info("📭 数据库为空，请先上传数据")
        
        # 数据库文件信息
        st.markdown("---")
        st.subheader("💾 数据库文件信息")
        
        import os
        db_file = 'performance_data.db'
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file) / 1024  # KB
            st.info(f"📁 文件大小: {file_size:.2f} KB\n\n📍 文件位置: {os.path.abspath(db_file)}")
        else:
            st.warning("数据库文件不存在")
    
    with tab2:
        st.subheader("🗑️ 删除数据")
        
        st.warning("⚠️ **警告**: 删除操作不可恢复！请谨慎操作。")
        
        periods = db.get_all_periods()
        
        if periods:
            # 删除指定周期
            st.markdown("### 删除指定周期")
            
            selected_period = st.selectbox(
                "选择要删除的考核周期",
                periods,
                key="delete_period"
            )
            
            if selected_period:
                # 显示该周期的数据量
                cursor = db.conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM performance_results WHERE period = ?', (selected_period,))
                count = cursor.fetchone()[0]
                
                st.info(f"📊 该周期共有 **{count}** 名员工的数据")
                
                # 确认删除
                confirm_text = st.text_input(
                    f"请输入 \"{selected_period}\" 以确认删除",
                    key="confirm_delete_period"
                )
                
                if st.button("🗑️ 确认删除该周期", type="primary", key="btn_delete_period"):
                    if confirm_text == selected_period:
                        try:
                            # 删除相关数据
                            cursor.execute('DELETE FROM performance_results WHERE period = ?', (selected_period,))
                            cursor.execute('DELETE FROM performance_indicators WHERE period = ?', (selected_period,))
                            cursor.execute('DELETE FROM interview_records WHERE period = ?', (selected_period,))
                            db.conn.commit()
                            
                            st.success(f"✅ 已成功删除 {selected_period} 的所有数据！")
                            st.info("💡 请刷新页面查看更新后的数据")
                            
                        except Exception as e:
                            st.error(f"❌ 删除失败: {str(e)}")
                    else:
                        st.error("⚠️ 输入的周期名称不正确，删除已取消")
            
            # 清空所有数据
            st.markdown("---")
            st.markdown("### 🚨 清空所有数据")
            
            st.error("⚠️ **危险操作**: 此操作将删除数据库中的所有数据！")
            
            confirm_clear = st.text_input(
                "请输入 \"CLEAR ALL DATA\" 以确认清空",
                key="confirm_clear_all"
            )
            
            if st.button("🗑️ 清空所有数据", type="secondary", key="btn_clear_all"):
                if confirm_clear == "CLEAR ALL DATA":
                    try:
                        cursor = db.conn.cursor()
                        cursor.execute('DELETE FROM performance_results')
                        cursor.execute('DELETE FROM performance_indicators')
                        cursor.execute('DELETE FROM interview_records')
                        cursor.execute('DELETE FROM assessment_scheme')
                        cursor.execute('DELETE FROM data_upload_log')
                        db.conn.commit()
                        
                        st.success("✅ 已清空所有数据！")
                        st.info("💡 请刷新页面")
                        
                    except Exception as e:
                        st.error(f"❌ 清空失败: {str(e)}")
                else:
                    st.error("⚠️ 确认文本不正确，操作已取消")
        else:
            st.info("📭 数据库为空，无需删除")
    
    with tab3:
        st.subheader("💾 备份与恢复")
        
        import shutil
        
        # 表结构升级（新增）
        st.markdown("### 🔧 表结构升级")
        st.info("💡 如果遇到字段缺失错误（如coefficient），点击下方按钮升级表结构")
        
        if st.button("🔧 升级表结构", key="btn_upgrade_structure"):
            try:
                result = db.upgrade_table_structure()
                if result:
                    st.success("✅ 表结构升级成功！现在可以导入包含系数的数据了。")
                else:
                    st.warning("⚠️ 表结构已是最新，无需升级")
            except Exception as e:
                st.error(f"❌ 升级失败: {str(e)}")
        
        st.markdown("---")
        
        # 备份数据库
        st.markdown("### 📤 备份数据库")
        st.info("💡 备份会将当前数据库复制到带时间戳的文件")
        
        if st.button("💾 创建备份", key="btn_backup"):
            try:
                backup_name = f"performance_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy('performance_data.db', backup_name)
                
                st.success(f"✅ 备份成功！")
                st.info(f"📁 备份文件: {backup_name}")
                
                # 提供下载
                with open(backup_name, 'rb') as f:
                    st.download_button(
                        label="📥 下载备份文件",
                        data=f,
                        file_name=backup_name,
                        mime="application/octet-stream"
                    )
            except Exception as e:
                st.error(f"❌ 备份失败: {str(e)}")
        
        # 查看备份文件列表
        st.markdown("---")
        st.markdown("### 📋 本地备份文件")
        
        import glob
        backup_files = glob.glob("performance_data_backup_*.db")
        
        if backup_files:
            backup_files.sort(reverse=True)  # 最新的在前
            
            for backup in backup_files[:5]:  # 只显示最近5个
                file_size = os.path.getsize(backup) / 1024
                file_time = os.path.getmtime(backup)
                from datetime import datetime
                time_str = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"📁 {backup}")
                with col2:
                    st.text(f"{file_size:.1f} KB")
                with col3:
                    st.text(time_str)
        else:
            st.info("暂无本地备份文件")
        
        # 恢复数据库
        st.markdown("---")
        st.markdown("### 📥 恢复数据库")
        
        st.warning("⚠️ **警告**: 恢复会覆盖当前数据库！")
        
        uploaded_backup = st.file_uploader(
            "选择备份文件 (.db)",
            type=['db'],
            key="restore_file"
        )
        
        if uploaded_backup:
            st.info(f"已选择文件: {uploaded_backup.name}")
            
            if st.button("🔄 恢复数据库", type="primary", key="btn_restore"):
                try:
                    # 先备份当前数据库
                    current_backup = f"performance_data_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    shutil.copy('performance_data.db', current_backup)
                    
                    # 恢复上传的备份
                    with open('performance_data.db', 'wb') as f:
                        f.write(uploaded_backup.getvalue())
                    
                    st.success("✅ 数据库恢复成功！")
                    st.info(f"💡 原数据库已备份为: {current_backup}")
                    st.warning("⚠️ 请刷新页面以加载新数据")
                    
                except Exception as e:
                    st.error(f"❌ 恢复失败: {str(e)}")

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #95a5a6; padding: 1rem;'>
    <p>绩效考核管理系统 v1.0 | 数据本地存储，安全可靠</p>
</div>
""", unsafe_allow_html=True)
