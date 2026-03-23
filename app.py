import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import calendar
import sqlite3

# ============== 配置常量 ==============

TYPE_COLOR_MAP = {
    'Feature': {'bg': '#DBEAFE', 'border': '#3B82F6', 'text': '#1E40AF'},
    'Bugfix': {'bg': '#FEE2E2', 'border': '#EF4444', 'text': '#991B1B'},
    'Meeting': {'bg': '#D1FAE5', 'border': '#10B981', 'text': '#065F46'},
    'Review': {'bg': '#FEF3C7', 'border': '#F59E0B', 'text': '#92400E'},
    'Other': {'bg': '#F3F4F6', 'border': '#6B7280', 'text': '#374151'}
}

DEFAULT_TYPES = ['Feature', 'Bugfix', 'Meeting', 'Review', 'Other']
DB_PATH = 'events.db'

# ============== 数据库操作 ==============

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_key TEXT UNIQUE NOT NULL,
                project TEXT NOT NULL,
                date_created TEXT NOT NULL,
                type TEXT NOT NULL,
                short_desc TEXT NOT NULL,
                desc_1 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_types (
                type_name TEXT PRIMARY KEY,
                bg_color TEXT DEFAULT '#F3F4F6',
                border_color TEXT DEFAULT '#6B7280',
                text_color TEXT DEFAULT '#374151'
            )
        ''')
        
        # 插入默认类型
        for t in DEFAULT_TYPES:
            colors = TYPE_COLOR_MAP.get(t, TYPE_COLOR_MAP['Other'])
            cursor.execute('''
                INSERT OR IGNORE INTO custom_types (type_name, bg_color, border_color, text_color)
                VALUES (?, ?, ?, ?)
            ''', (t, colors['bg'], colors['border'], colors['text']))
        
        conn.commit()
        conn.close()
    
    def get_all_events(self) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query('SELECT * FROM events ORDER BY date_created DESC', conn)
        conn.close()
        return df
    
    def get_events_by_month(self, year: int, month: int) -> pd.DataFrame:
        conn = self.get_connection()
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        df = pd.read_sql_query('''
            SELECT * FROM events 
            WHERE date_created >= ? AND date_created < ?
            ORDER BY date_created
        ''', conn, params=(start_date, end_date))
        conn.close()
        return df
    
    def add_event(self, event: Dict) -> tuple[bool, str]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO events (unique_key, project, date_created, type, short_desc, desc_1)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (event['unique_key'], event['project'], event['date_created'],
                  event['type'], event['short_desc'], event.get('desc_1', '')))
            conn.commit()
            conn.close()
            return True, "添加成功"
        except sqlite3.IntegrityError:
            return False, f"唯一键 '{event['unique_key']}' 已存在"
    
    def update_event(self, unique_key: str, event: Dict) -> tuple[bool, str]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE events SET project=?, date_created=?, type=?, short_desc=?, desc_1=?
                WHERE unique_key=?
            ''', (event['project'], event['date_created'], event['type'],
                  event['short_desc'], event.get('desc_1', ''), unique_key))
            conn.commit()
            conn.close()
            return True, "更新成功"
        except Exception as e:
            return False, str(e)
    
    def delete_event(self, unique_key: str) -> tuple[bool, str]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM events WHERE unique_key=?', (unique_key,))
            conn.commit()
            conn.close()
            return True, "删除成功"
        except Exception as e:
            return False, str(e)
    
    def get_all_types(self) -> List[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT type_name FROM custom_types ORDER BY type_name')
        types = [row[0] for row in cursor.fetchall()]
        conn.close()
        return types
    
    def add_custom_type(self, type_name: str, colors: Dict) -> tuple[bool, str]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO custom_types (type_name, bg_color, border_color, text_color)
                VALUES (?, ?, ?, ?)
            ''', (type_name, colors['bg'], colors['border'], colors['text']))
            conn.commit()
            conn.close()
            return True, "添加成功"
        except sqlite3.IntegrityError:
            return False, f"类型 '{type_name}' 已存在"
    
    def get_type_colors(self) -> Dict[str, Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT type_name, bg_color, border_color, text_color FROM custom_types')
        colors = {}
        for row in cursor.fetchall():
            colors[row[0]] = {'bg': row[1], 'border': row[2], 'text': row[3]}
        conn.close()
        return colors

# ============== 数据加载 ==============

def load_file(uploaded_file) -> pd.DataFrame:
    file_name = uploaded_file.name.lower()
    if file_name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif file_name.endswith(('.xlsx', '.xls')):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("不支持的文件格式")

def validate_data(df: pd.DataFrame) -> tuple[bool, List[str]]:
    required = ['project', 'date_created', 'unique_key', 'type', 'short_desc']
    errors = []
    
    missing_cols = [col for col in required if col not in df.columns]
    if missing_cols:
        errors.append(f"缺少字段: {', '.join(missing_cols)}")
        return False, errors
    
    for col in required:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            errors.append(f"'{col}' 有 {null_count} 个空值")
    
    duplicates = df[df.duplicated(subset=['unique_key'], keep=False)]
    if not duplicates.empty:
        errors.append(f"唯一键重复: {', '.join(duplicates['unique_key'].unique()[:3])}")
    
    return len(errors) == 0, errors

# ============== 日历渲染 ==============

def render_calendar_html(year: int, month: int, events_df: pd.DataFrame, type_colors: Dict) -> str:
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    events_by_date = {}
    if not events_df.empty:
        for _, row in events_df.iterrows():
            date_str = row['date_created']
            if date_str not in events_by_date:
                events_by_date[date_str] = []
            events_by_date[date_str].append(row.to_dict())
    
    week_days = ['日', '一', '二', '三', '四', '五', '六']
    today = datetime.now().strftime('%Y-%m-%d')
    
    css = """
    <style>
    .cal-container { font-family: -apple-system, BlinkMacSystemFont, sans-serif; width: 100%; }
    .cal-header { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin-bottom: 4px; }
    .weekday-h { text-align: center; padding: 8px; font-weight: 600; color: #6B7280; font-size: 14px; }
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
    .cal-cell { min-height: 90px; border: 1px solid #E5E7EB; padding: 4px; background: white; }
    .cal-cell:hover { background: #F9FAFB; border-color: #3B82F6; }
    .cal-cell.other { background: #F9FAFB; color: #9CA3AF; }
    .cal-cell.today { border-color: #3B82F6; border-width: 2px; }
    .cell-date { font-size: 13px; font-weight: 500; margin-bottom: 3px; }
    .cell-events { display: flex; flex-direction: column; gap: 2px; }
    .evt-badge { font-size: 10px; padding: 2px 4px; border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-left: 3px solid; cursor: pointer; }
    .evt-badge:hover { opacity: 0.8; }
    .evt-more { font-size: 9px; color: #6B7280; text-align: center; }
    </style>
    """
    
    html = f'{css}<div class="cal-container">'
    html += '<div class="cal-header">' + ''.join([f'<div class="weekday-h">{d}</div>' for d in week_days]) + '</div>'
    html += '<div class="cal-grid">'
    
    for week in month_days:
        for day in week:
            if day == 0:
                html += '<div class="cal-cell other"></div>'
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                cell_class = "cal-cell"
                if date_str == today:
                    cell_class += " today"
                
                events = events_by_date.get(date_str, [])
                html += f'<div class="{cell_class}"><div class="cell-date">{day}</div><div class="cell-events">'
                
                for event in events[:3]:
                    evt_type = event.get('type', 'Other')
                    colors = type_colors.get(evt_type, TYPE_COLOR_MAP['Other'])
                    desc = event.get('short_desc', '')[:15]
                    project = event.get('project', 'Unknown')
                    long_desc = event.get('desc_1', '无详细描述')
                    
                    # 使用title属性实现tooltip
                    tooltip_content = f"项目: {project}\n类型: {evt_type}\n描述: {long_desc}"
                    html += f'<div class="evt-badge" style="background:{colors["bg"]};color:{colors["text"]};border-color:{colors["border"]}" title="{tooltip_content}">{desc}</div>'
                
                if len(events) > 3:
                    html += f'<div class="evt-more">+{len(events)-3} more</div>'
                
                html += '</div></div>'
    
    html += '</div></div>'
    return html

# ============== Session State ==============

def init_session():
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    if 'year' not in st.session_state:
        st.session_state.year = datetime.now().year
    if 'month' not in st.session_state:
        st.session_state.month = datetime.now().month
    if 'sel_projects' not in st.session_state:
        st.session_state.sel_projects = []
    if 'sel_types' not in st.session_state:
        st.session_state.sel_types = []
    if 'sample_loaded' not in st.session_state:
        st.session_state.sample_loaded = False

# ============== 模拟数据 ==============

def load_sample_data(db: Database):
    """加载模拟数据"""
    sample_data = [
        # 2026年1月数据
        {"unique_key": "EVT001", "project": "Project Alpha", "date_created": "2026-01-02", "type": "Feature", "short_desc": "项目初始化", "desc_1": "搭建项目基础架构和开发环境"},
        {"unique_key": "EVT002", "project": "Project Beta", "date_created": "2026-01-05", "type": "Meeting", "short_desc": "项目启动会议", "desc_1": "确定项目目标和技术方案"},
        {"unique_key": "EVT003", "project": "Project Gamma", "date_created": "2026-01-05", "type": "Feature", "short_desc": "技术栈选择", "desc_1": "确定项目技术栈和架构"},
        {"unique_key": "EVT004", "project": "Project Alpha", "date_created": "2026-01-08", "type": "Feature", "short_desc": "数据库设计", "desc_1": "设计数据库表结构和关系"},
        {"unique_key": "EVT005", "project": "Project Beta", "date_created": "2026-01-10", "type": "Bugfix", "short_desc": "环境配置问题", "desc_1": "解决开发环境依赖冲突"},
        {"unique_key": "EVT006", "project": "Project Gamma", "date_created": "2026-01-10", "type": "Review", "short_desc": "需求分析", "desc_1": "分析项目需求和功能点"},
        {"unique_key": "EVT007", "project": "Project Alpha", "date_created": "2026-01-12", "type": "Meeting", "short_desc": "需求文档评审", "desc_1": "评审产品需求文档"},
        {"unique_key": "EVT008", "project": "Project Beta", "date_created": "2026-01-15", "type": "Feature", "short_desc": "API接口设计", "desc_1": "设计RESTful API接口规范"},
        {"unique_key": "EVT009", "project": "Project Gamma", "date_created": "2026-01-15", "type": "Bugfix", "short_desc": "网络配置", "desc_1": "配置网络环境和防火墙"},
        {"unique_key": "EVT010", "project": "Project Alpha", "date_created": "2026-01-18", "type": "Meeting", "short_desc": "技术方案讨论", "desc_1": "讨论核心功能实现方案"},
        {"unique_key": "EVT011", "project": "Project Beta", "date_created": "2026-01-20", "type": "Bugfix", "short_desc": "依赖包版本问题", "desc_1": "修复依赖包版本不兼容问题"},
        {"unique_key": "EVT012", "project": "Project Gamma", "date_created": "2026-01-22", "type": "Feature", "short_desc": "前端框架搭建", "desc_1": "搭建前端项目框架"},
        {"unique_key": "EVT013", "project": "Project Alpha", "date_created": "2026-01-25", "type": "Review", "short_desc": "技术方案评审", "desc_1": "评审技术实现方案"},
        {"unique_key": "EVT014", "project": "Project Beta", "date_created": "2026-01-25", "type": "Feature", "short_desc": "用户模块开发", "desc_1": "实现用户注册登录功能"},
        {"unique_key": "EVT015", "project": "Project Gamma", "date_created": "2026-01-28", "type": "Meeting", "short_desc": "进度同步会", "desc_1": "总结1月工作进度"},
        {"unique_key": "EVT016", "project": "Project Alpha", "date_created": "2026-01-30", "type": "Bugfix", "short_desc": "代码规范检查", "desc_1": "检查代码规范和质量"},
        
        # 2026年2月数据
        {"unique_key": "EVT017", "project": "Project Alpha", "date_created": "2026-02-02", "type": "Feature", "short_desc": "产品模块开发", "desc_1": "实现产品管理功能"},
        {"unique_key": "EVT018", "project": "Project Beta", "date_created": "2026-02-05", "type": "Bugfix", "short_desc": "数据库连接问题", "desc_1": "修复数据库连接池配置"},
        {"unique_key": "EVT019", "project": "Project Gamma", "date_created": "2026-02-05", "type": "Meeting", "short_desc": "需求变更讨论", "desc_1": "讨论产品需求变更"},
        {"unique_key": "EVT020", "project": "Project Alpha", "date_created": "2026-02-08", "type": "Feature", "short_desc": "订单模块开发", "desc_1": "实现订单创建和管理功能"},
        {"unique_key": "EVT021", "project": "Project Beta", "date_created": "2026-02-10", "type": "Review", "short_desc": "代码审查", "desc_1": "审查用户模块代码"},
        {"unique_key": "EVT022", "project": "Project Gamma", "date_created": "2026-02-12", "type": "Feature", "short_desc": "支付集成", "desc_1": "集成第三方支付接口"},
        {"unique_key": "EVT023", "project": "Project Alpha", "date_created": "2026-02-12", "type": "Bugfix", "short_desc": "前端样式问题", "desc_1": "修复页面响应式布局问题"},
        {"unique_key": "EVT024", "project": "Project Beta", "date_created": "2026-02-15", "type": "Meeting", "short_desc": "测试计划讨论", "desc_1": "制定测试计划和测试用例"},
        {"unique_key": "EVT025", "project": "Project Gamma", "date_created": "2026-02-18", "type": "Feature", "short_desc": "报表功能开发", "desc_1": "实现数据报表生成功能"},
        {"unique_key": "EVT026", "project": "Project Alpha", "date_created": "2026-02-20", "type": "Review", "short_desc": "安全审查", "desc_1": "审查系统安全漏洞"},
        {"unique_key": "EVT027", "project": "Project Beta", "date_created": "2026-02-22", "type": "Bugfix", "short_desc": "性能优化", "desc_1": "优化系统性能和响应速度"},
        {"unique_key": "EVT028", "project": "Project Gamma", "date_created": "2026-02-25", "type": "Feature", "short_desc": "缓存机制实现", "desc_1": "实现系统缓存机制"},
        {"unique_key": "EVT029", "project": "Project Alpha", "date_created": "2026-02-28", "type": "Meeting", "short_desc": "月度总结会议", "desc_1": "总结2月工作成果"},
        {"unique_key": "EVT030", "project": "Project Beta", "date_created": "2026-02-28", "type": "Review", "short_desc": "测试结果分析", "desc_1": "分析测试结果和问题"},
        
        # 2026年3月数据
        {"unique_key": "EVT031", "project": "Project Alpha", "date_created": "2026-03-02", "type": "Feature", "short_desc": "完成用户认证模块", "desc_1": "实现了基于JWT的用户登录系统，支持邮箱和密码登录"},
        {"unique_key": "EVT032", "project": "Project Beta", "date_created": "2026-03-05", "type": "Bugfix", "short_desc": "修复首页加载慢问题", "desc_1": "优化了数据库查询，添加了Redis缓存"},
        {"unique_key": "EVT033", "project": "Project Gamma", "date_created": "2026-03-05", "type": "Feature", "short_desc": "消息队列集成", "desc_1": "集成消息队列系统"},
        {"unique_key": "EVT034", "project": "Project Alpha", "date_created": "2026-03-06", "type": "Meeting", "short_desc": "客户需求评审会议", "desc_1": "与产品团队讨论Q2需求优先级"},
        {"unique_key": "EVT035", "project": "Project Beta", "date_created": "2026-03-08", "type": "Feature", "short_desc": "新增数据导出功能", "desc_1": "支持Excel和CSV格式导出"},
        {"unique_key": "EVT036", "project": "Project Gamma", "date_created": "2026-03-10", "type": "Review", "short_desc": "代码审查-订单模块", "desc_1": "对订单处理流程进行代码审查"},
        {"unique_key": "EVT037", "project": "Project Alpha", "date_created": "2026-03-12", "type": "Bugfix", "short_desc": "修复支付回调异常", "desc_1": "解决了支付宝和微信支付回调偶尔失败的问题"},
        {"unique_key": "EVT038", "project": "Project Beta", "date_created": "2026-03-12", "type": "Feature", "short_desc": "完成权限管理系统", "desc_1": "实现了基于RBAC的权限控制"},
        {"unique_key": "EVT039", "project": "Project Gamma", "date_created": "2026-03-15", "type": "Meeting", "short_desc": "技术架构评审", "desc_1": "讨论微服务拆分方案"},
        {"unique_key": "EVT040", "project": "Project Alpha", "date_created": "2026-03-17", "type": "Feature", "short_desc": "新增消息推送功能", "desc_1": "集成极光推送，支持iOS和Android"},
        {"unique_key": "EVT041", "project": "Project Beta", "date_created": "2026-03-18", "type": "Bugfix", "short_desc": "修复内存泄漏问题", "desc_1": "定位并修复了用户会话缓存导致的内存泄漏"},
        {"unique_key": "EVT042", "project": "Project Gamma", "date_created": "2026-03-20", "type": "Review", "short_desc": "安全漏洞扫描", "desc_1": "使用OWASP工具进行安全扫描"},
        {"unique_key": "EVT043", "project": "Project Alpha", "date_created": "2026-03-21", "type": "Feature", "short_desc": "完成报表统计模块", "desc_1": "新增销售报表、用户增长报表"},
        {"unique_key": "EVT044", "project": "Project Beta", "date_created": "2026-03-21", "type": "Bugfix", "short_desc": "修复文件上传漏洞", "desc_1": "限制了上传文件类型和大小"},
        {"unique_key": "EVT045", "project": "Project Gamma", "date_created": "2026-03-23", "type": "Meeting", "short_desc": "项目进度同步会", "desc_1": "汇报本月完成情况"},
        {"unique_key": "EVT046", "project": "Project Alpha", "date_created": "2026-03-25", "type": "Feature", "short_desc": "优化搜索功能", "desc_1": "接入Elasticsearch，搜索速度提升10倍"},
        {"unique_key": "EVT047", "project": "Project Beta", "date_created": "2026-03-26", "type": "Other", "short_desc": "文档更新-API文档", "desc_1": "更新了Swagger文档"},
        {"unique_key": "EVT048", "project": "Project Gamma", "date_created": "2026-03-27", "type": "Review", "short_desc": "性能测试报告", "desc_1": "完成压力测试，支持10000并发"},
        {"unique_key": "EVT049", "project": "Project Alpha", "date_created": "2026-03-28", "type": "Meeting", "short_desc": "客户演示准备", "desc_1": "准备产品演示材料"},
        {"unique_key": "EVT050", "project": "Project Beta", "date_created": "2026-03-30", "type": "Feature", "short_desc": "完成移动端适配", "desc_1": "响应式布局优化"},
        {"unique_key": "EVT051", "project": "Project Gamma", "date_created": "2026-03-31", "type": "Bugfix", "short_desc": "修复数据同步延迟", "desc_1": "数据同步延迟从5分钟降至30秒"},
        {"unique_key": "EVT052", "project": "Project Alpha", "date_created": "2026-03-31", "type": "Review", "short_desc": "项目总结", "desc_1": "总结Q1项目成果"},
    ]
    
    success_count = 0
    for event in sample_data:
        ok, _ = db.add_event(event)
        if ok:
            success_count += 1
    
    return success_count

def clear_all_data(db: Database):
    """清空所有数据"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM events')
        conn.commit()
        conn.close()
        return True, "所有数据已清空"
    except Exception as e:
        return False, str(e)

# ============== 主界面 ==============

def main():
    st.set_page_config(page_title="Events 日历", page_icon="📅", layout="wide")
    st.title("📅 Events 日历展示应用")
    
    init_session()
    db = st.session_state.db
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 控制面板")
        
        # 模拟数据
        st.subheader("🎮 快速开始")
        all_events = db.get_all_events()
        
        if all_events.empty:
            st.info("数据库为空，可以加载模拟数据体验功能")
            if st.button("🚀 加载模拟数据", type="primary", use_container_width=True):
                count = load_sample_data(db)
                st.session_state.sample_loaded = True
                st.success(f"已加载 {count} 条模拟数据")
                st.rerun()
        else:
            st.success(f"当前有 {len(all_events)} 条数据")
            
            # 显示是否为模拟数据
            sample_keys = [f"EVT{i:03d}" for i in range(1, 21)]
            is_sample = all(evt in all_events['unique_key'].values for evt in sample_keys[:5])
            
            if is_sample:
                st.caption("✨ 当前为模拟数据")
            
            if st.button("🗑️ 一键清空所有数据", type="secondary", use_container_width=True):
                st.session_state.confirm_clear = True
                st.rerun()
            
            if st.session_state.get('confirm_clear', False):
                st.warning("⚠️ 确定要清空所有数据吗？")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ 确认清空", type="primary", use_container_width=True):
                        ok, msg = clear_all_data(db)
                        if ok:
                            st.session_state.sel_projects = []
                            st.session_state.sel_types = []
                            st.session_state.confirm_clear = False
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                with c2:
                    if st.button("❌ 取消", use_container_width=True):
                        st.session_state.confirm_clear = False
                        st.rerun()
        
        st.divider()
        
        # 上传
        st.subheader("📤 数据上传")
        uploaded = st.file_uploader("选择文件", type=['csv', 'xlsx', 'xls'])
        if uploaded:
            try:
                df = load_file(uploaded)
                valid, errors = validate_data(df)
                if not valid:
                    st.error("验证失败:")
                    for e in errors:
                        st.write(f"- {e}")
                else:
                    st.dataframe(df.head(3), use_container_width=True)
                    if st.button("✅ 导入", type="primary"):
                        df['date_created'] = pd.to_datetime(df['date_created']).dt.strftime('%Y-%m-%d')
                        success = error = 0
                        for _, row in df.iterrows():
                            ok, _ = db.add_event({
                                'unique_key': str(row['unique_key']),
                                'project': str(row['project']),
                                'date_created': str(row['date_created']),
                                'type': str(row['type']),
                                'short_desc': str(row['short_desc']),
                                'desc_1': str(row.get('desc_1', ''))
                            })
                            if ok:
                                success += 1
                            else:
                                error += 1
                        st.success(f"导入: {success}成功, {error}失败")
                        st.rerun()
            except Exception as e:
                st.error(f"读取失败: {e}")
        
        st.divider()
        
        # 筛选
        st.subheader("🔍 筛选")
        all_events = db.get_all_events()
        
        if all_events.empty:
            st.info("暂无数据")
            return
        
        if not all_events.empty:
            years = sorted(all_events['date_created'].str[:4].unique(), reverse=True)
            y = st.selectbox("年份", years, index=0)
            st.session_state.year = int(y)
            
            m = st.selectbox("月份", range(1, 13), format_func=lambda x: f"{x}月", index=st.session_state.month-1)
            st.session_state.month = m
            
            projects = sorted(all_events['project'].unique())
            st.session_state.sel_projects = st.multiselect("Project", projects, st.session_state.sel_projects)
            
            types = db.get_all_types()
            st.session_state.sel_types = st.multiselect("Type", types, st.session_state.sel_types)
        
        st.divider()
        
        # 统计
        st.subheader("📈 统计")
        events = db.get_events_by_month(st.session_state.year, st.session_state.month)
        if st.session_state.sel_projects:
            events = events[events['project'].isin(st.session_state.sel_projects)]
        if st.session_state.sel_types:
            events = events[events['type'].isin(st.session_state.sel_types)]
        
        if not events.empty:
            st.metric("本月事件", len(events))
            st.write("**项目分布**")
            for proj, cnt in events['project'].value_counts().head(5).items():
                st.write(f"- {proj}: {cnt}")
            st.write("**类型分布**")
            colors = db.get_type_colors()
            for t, cnt in events['type'].value_counts().items():
                c = colors.get(t, TYPE_COLOR_MAP['Other'])['border']
                st.markdown(f"<span style='color:{c}'>●</span> {t}: {cnt}", unsafe_allow_html=True)
        else:
            st.info("无数据")
        
        # 导出
        if not events.empty and st.button("📥 导出CSV"):
            csv = events.to_csv(index=False)
            st.download_button("下载", csv, f"events_{st.session_state.year}_{st.session_state.month}.csv", "text/csv")
    
    # 主内容 - 日历
    st.subheader("📅 日历视图")
    
    # 导航
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if st.button("◀ 上月"):
            if st.session_state.month == 1:
                st.session_state.month = 12
                st.session_state.year -= 1
            else:
                st.session_state.month -= 1
            st.rerun()
    with c2:
        st.markdown(f"<h3 style='text-align:center'>{st.session_state.year}年 {st.session_state.month}月</h3>", unsafe_allow_html=True)
    with c3:
        if st.button("下月 ▶"):
            if st.session_state.month == 12:
                st.session_state.month = 1
                st.session_state.year += 1
            else:
                st.session_state.month += 1
            st.rerun()
    
    # 日历
    events = db.get_events_by_month(st.session_state.year, st.session_state.month)
    if st.session_state.sel_projects:
        events = events[events['project'].isin(st.session_state.sel_projects)]
    if st.session_state.sel_types:
        events = events[events['type'].isin(st.session_state.sel_types)]
    
    colors = db.get_type_colors()
    
    if events.empty:
        st.info("本月暂无事件数据")
        # 显示空日历
        cal_html = render_calendar_html(st.session_state.year, st.session_state.month, events, colors)
        st.components.v1.html(cal_html, height=550)
    else:
        cal_html = render_calendar_html(st.session_state.year, st.session_state.month, events, colors)
        st.components.v1.html(cal_html, height=550)
    
    # 事件管理
    st.divider()
    st.subheader("📝 事件管理")
    
    tab_view, tab_add = st.tabs(["📋 查看/编辑", "➕ 添加事件"])
    
    with tab_view:
        if events.empty:
            st.info("当前筛选条件下无事件")
        else:
            for _, evt in events.iterrows():
                with st.expander(f"{evt['date_created']} | {evt['short_desc']} ({evt['type']})"):
                    st.write(f"**Project:** {evt['project']}")
                    st.write(f"**Type:** {evt['type']}")
                    st.write(f"**Key:** {evt['unique_key']}")
                    st.write(f"**描述:** {evt['desc_1'] or '无'}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✏️ 编辑", key=f"edit_{evt['unique_key']}"):
                            st.session_state.edit_key = evt['unique_key']
                            st.rerun()
                    with c2:
                        if st.button("🗑️ 删除", key=f"del_{evt['unique_key']}"):
                            ok, msg = db.delete_event(evt['unique_key'])
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
    
    with tab_add:
        # 使用session state存储表单数据
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'key': f"EVT{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'proj': '',
                'date': datetime.now(),
                'evt_type': '',
                'short': '',
                'desc': ''
            }
        
        with st.form("add_event"):
            key = st.text_input("唯一键 *", value=st.session_state.form_data['key'])
            proj = st.text_input("Project *", value=st.session_state.form_data['proj'])
            date = st.date_input("日期 *", value=st.session_state.form_data['date'])
            all_types = db.get_all_types()
            evt_type = st.selectbox("Type *", all_types, index=all_types.index(st.session_state.form_data['evt_type']) if st.session_state.form_data['evt_type'] in all_types else 0)
            short = st.text_input("简短描述 *", max_chars=50, value=st.session_state.form_data['short'])
            desc = st.text_area("详细描述", max_chars=1000, value=st.session_state.form_data['desc'])
            
            if st.form_submit_button("✅ 保存", type="primary"):
                if all([key, proj, evt_type, short]):
                    ok, msg = db.add_event({
                        'unique_key': key, 'project': proj,
                        'date_created': date.strftime('%Y-%m-%d'),
                        'type': evt_type, 'short_desc': short, 'desc_1': desc
                    })
                    if ok:
                        st.success(msg)
                        # 清空表单数据
                        st.session_state.form_data = {
                            'key': f"EVT{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            'proj': '',
                            'date': datetime.now(),
                            'evt_type': '',
                            'short': '',
                            'desc': ''
                        }
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("请填写必填项")

if __name__ == "__main__":
    main()
