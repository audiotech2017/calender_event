# Events 日历展示应用 - 完整源代码

---

## 依赖导入

```python
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import calendar
import sqlite3
```

---

## 配置常量

```python
TYPE_COLOR_MAP = {
    'Feature': {'bg': '#DBEAFE', 'border': '#3B82F6', 'text': '#1E40AF'},
    'Bugfix': {'bg': '#FEE2E2', 'border': '#EF4444', 'text': '#991B1B'},
    'Meeting': {'bg': '#D1FAE5', 'border': '#10B981', 'text': '#065F46'},
    'Review': {'bg': '#FEF3C7', 'border': '#F59E0B', 'text': '#92400E'},
    'Other': {'bg': '#F3F4F6', 'border': '#6B7280', 'text': '#374151'}
}

DEFAULT_TYPES = ['Feature', 'Bugfix', 'Meeting', 'Review', 'Other']
DB_PATH = 'events.db'
```

---

## 数据库操作类

```python
class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建 events 表
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
        
        # 创建 custom_types 表
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
        """获取所有事件"""
        conn = self.get_connection()
        df = pd.read_sql_query('SELECT * FROM events ORDER BY date_created DESC', conn)
        conn.close()
        return df
    
    def get_events_by_month(self, year: int, month: int) -> pd.DataFrame:
        """获取指定月份的事件"""
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
        """添加事件"""
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
        """更新事件"""
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
        """删除事件"""
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
        """获取所有类型"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT type_name FROM custom_types ORDER BY type_name')
        types = [row[0] for row in cursor.fetchall()]
        conn.close()
        return types
    
    def add_custom_type(self, type_name: str, colors: Dict) -> tuple[bool, str]:
        """添加自定义类型"""
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
        """获取所有类型的颜色配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT type_name, bg_color, border_color, text_color FROM custom_types')
        colors = {}
        for row in cursor.fetchall():
            colors[row[0]] = {'bg': row[1], 'border': row[2], 'text': row[3]}
        conn.close()
        return colors
```

---

## 数据加载与验证

```python
def load_file(uploaded_file) -> pd.DataFrame:
    """加载 CSV/Excel 文件"""
    file_name = uploaded_file.name.lower()
    if file_name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif file_name.endswith(('.xlsx', '.xls')):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("不支持的文件格式")

def validate_data(df: pd.DataFrame) -> tuple[bool, List[str]]:
    """验证数据完整性"""
    required = ['project', 'date_created', 'unique_key', 'type', 'short_desc']
    errors = []
    
    # 检查必需字段
    missing_cols = [col for col in required if col not in df.columns]
    if missing_cols:
        errors.append(f"缺少字段: {', '.join(missing_cols)}")
        return False, errors
    
    # 检查空值
    for col in required:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            errors.append(f"'{col}' 有 {null_count} 个空值")
    
    # 检查唯一键重复
    duplicates = df[df.duplicated(subset=['unique_key'], keep=False)]
    if not duplicates.empty:
        errors.append(f"唯一键重复: {', '.join(duplicates['unique_key'].unique()[:3])}")
    
    return len(errors) == 0, errors
```

---

## 日历渲染

```python
def render_calendar_html(year: int, month: int, events_df: pd.DataFrame, type_colors: Dict) -> str:
    """渲染日历 HTML"""
    cal = calendar.Calendar(firstweekday=6)  # 周日开始
    month_days = cal.monthdayscalendar(year, month)
    
    # 按日期分组事件
    events_by_date = {}
    if not events_df.empty:
        for _, row in events_df.iterrows():
            date_str = row['date_created']
            if date_str not in events_by_date:
                events_by_date[date_str] = []
            events_by_date[date_str].append(row.to_dict())
    
    week_days = ['日', '一', '二', '三', '四', '五', '六']
    today = datetime.now().strftime('%Y-%m-%d')
    
    # CSS 样式
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
    .evt-badge { font-size: 10px; padding: 2px 4px; border-radius: 3px; 
                 white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
                 border-left: 3px solid; cursor: pointer; }
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
                
                # 显示最多3个事件
                for event in events[:3]:
                    evt_type = event.get('type', 'Other')
                    colors = type_colors.get(evt_type, TYPE_COLOR_MAP['Other'])
                    desc = event.get('short_desc', '')[:15]
                    html += f'<div class="evt-badge" style="background:{colors["bg"]};color:{colors["text"]};border-color:{colors["border"]}">{desc}</div>'
                
                # 更多事件提示
                if len(events) > 3:
                    html += f'<div class="evt-more">+{len(events)-3} more</div>'
                
                html += '</div></div>'
    
    html += '</div></div>'
    return html
```

---

## Session State 管理

```python
def init_session():
    """初始化会话状态"""
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
```

---

## 模拟数据

```python
def load_sample_data(db: Database):
    """加载52条模拟数据（2025年1-3月）"""
    sample_data = [
        {"unique_key": "EVT001", "project": "Project Alpha", 
         "date_created": "2025-01-02", "type": "Feature", 
         "short_desc": "项目初始化", "desc_1": "搭建项目基础架构和开发环境"},
        # ... 共52条数据，覆盖3个月
        {"unique_key": "EVT052", "project": "Project Alpha", 
         "date_created": "2025-03-31", "type": "Review", 
         "short_desc": "项目总结", "desc_1": "总结Q1项目成果"},
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
```

---

## 主界面

```python
def main():
    st.set_page_config(page_title="Events 日历", page_icon="📅", layout="wide")
    st.title("📅 Events 日历展示应用")
    
    init_session()
    db = st.session_state.db
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 控制面板")
        
        # 快速开始 - 加载/清空模拟数据
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
            # 检测是否为模拟数据
            sample_keys = [f"EVT{i:03d}" for i in range(1, 21)]
            is_sample = all(evt in all_events['unique_key'].values for evt in sample_keys[:5])
            if is_sample:
                st.caption("✨ 当前为模拟数据")
            
            if st.button("🗑️ 一键清空所有数据", type="secondary", use_container_width=True):
                st.session_state.confirm_clear = True
                st.rerun()
            
            # 确认清空对话框
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
                with c2:
                    if st.button("❌ 取消", use_container_width=True):
                        st.session_state.confirm_clear = False
                        st.rerun()
        
        st.divider()
        
        # 数据上传
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
        
        # 筛选器
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
        
        # 统计概览
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
    
    # 主内容区 - 日历视图
    st.subheader("📅 日历视图")
    
    # 月份导航
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
    
    # 渲染日历
    events = db.get_events_by_month(st.session_state.year, st.session_state.month)
    if st.session_state.sel_projects:
        events = events[events['project'].isin(st.session_state.sel_projects)]
    if st.session_state.sel_types:
        events = events[events['type'].isin(st.session_state.sel_types)]
    
    colors = db.get_type_colors()
    
    if events.empty:
        st.info("本月暂无事件数据")
    
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
        with st.form("add_event"):
            key = st.text_input("唯一键 *", value=f"EVT{datetime.now().strftime('%Y%m%d%H%M%S')}")
            proj = st.text_input("Project *")
            date = st.date_input("日期 *", value=datetime.now())
            all_types = db.get_all_types()
            evt_type = st.selectbox("Type *", all_types)
            short = st.text_input("简短描述 *", max_chars=50)
            desc = st.text_area("详细描述", max_chars=1000)
            
            if st.form_submit_button("✅ 保存", type="primary"):
                if all([key, proj, evt_type, short]):
                    ok, msg = db.add_event({
                        'unique_key': key, 'project': proj,
                        'date_created': date.strftime('%Y-%m-%d'),
                        'type': evt_type, 'short_desc': short, 'desc_1': desc
                    })
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("请填写必填项")

if __name__ == "__main__":
    main()
```

---

## 代码统计

| 指标 | 数值 |
|------|------|
| 总代码行数 | ~650行 |
| 函数数量 | 12个 |
| 类数量 | 1个 (Database) |
| 数据库表 | 2个 |
| 模拟数据 | 52条 |

---

## 依赖列表 (requirements.txt)

```
streamlit>=1.28.0
pandas>=2.0.0
openpyxl>=3.1.0
```

