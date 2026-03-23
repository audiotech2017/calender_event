# Events 日历展示应用 - 开发文档

## 项目概述

向老板展示每月工作成果的交互式日历应用。支持从 CSV/Excel 导入事件数据，以日历形式可视化展示，并提供多维度筛选、增删改查和数据持久化功能。

***

## 开发时间线

| 阶段 | 时间 | 内容 |
|------|------|------|
| 需求确认 | 2026-03-23 21:22 | 确认功能需求和技术方案 |
| 框架设计 | 2026-03-23 21:26 | 完成系统架构和交互设计 |
| 功能开发 | 2026-03-23 21:40 | 完成核心功能开发 |
| 模拟数据 | 2026-03-23 21:44 | 添加20条模拟数据和一键清空功能 |
| 文档汇总 | 2026-03-23 22:00 | 整理开发文档 |

---

## 需求分析

### 原始需求
- 输入：CSV/Excel 文件，包含 project / date_created / unique_key / type / short_desc / desc_1
- 输出：交互式日历表
- 筛选：年份、月份、project、type
- 展示：short_desc 在日历上展示

### 扩展需求（开发中确认）
- Type 类型可自定义，默认5种
- 日期格式统一为 YYYY-MM-DD
- 周起始日为周日
- 支持新增、编辑、删除事件
- SQLite 数据持久化
- 一键加载/清空模拟数据

---

## 技术架构

### 技术栈
| 组件 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Streamlit | >=1.28.0 |
| 数据处理 | Pandas | >=2.0.0 |
| 数据库 | SQLite | 内置 |
| Excel解析 | openpyxl | >=3.1.0 |

### 文件结构
```
calender_streamlist/
├── app.py              # 主应用 (26KB, ~600行)
├── requirements.txt    # 依赖列表
├── DESIGN.md          # 设计文档
├── INTERACTION.md     # 交互流程
└── DATA_SCHEMA.md     # 数据结构
```

***

## 数据库设计

### events 表
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_key TEXT UNIQUE NOT NULL,
    project TEXT NOT NULL,
    date_created TEXT NOT NULL,
    type TEXT NOT NULL,
    short_desc TEXT NOT NULL,
    desc_1 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### custom_types 表
```sql
CREATE TABLE custom_types (
    type_name TEXT PRIMARY KEY,
    bg_color TEXT DEFAULT '#F3F4F6',
    border_color TEXT DEFAULT '#6B7280',
    text_color TEXT DEFAULT '#374151'
);
```

***

## 核心功能实现

### 1. 数据库操作类 (Database)

```python
class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        # 创建表结构
        # 插入默认类型颜色
    
    def get_all_events(self) -> pd.DataFrame:
        # 获取所有事件
    
    def get_events_by_month(self, year: int, month: int) -> pd.DataFrame:
        # 按月筛选事件
    
    def add_event(self, event: Dict) -> tuple[bool, str]:
        # 添加事件，处理唯一键冲突
    
    def update_event(self, unique_key: str, event: Dict) -> tuple[bool, str]:
        # 更新事件
    
    def delete_event(self, unique_key: str) -> tuple[bool, str]:
        # 删除事件
```

***

### 2. 数据验证

```python
def validate_data(df: pd.DataFrame) -> tuple[bool, List[str]]:
    required = ['project', 'date_created', 'unique_key', 'type', 'short_desc']
    
    # 检查必需字段
    missing_cols = [col for col in required if col not in df.columns]
    
    # 检查空值
    for col in required:
        null_count = df[col].isnull().sum()
    
    # 检查唯一键重复
    duplicates = df[df.duplicated(subset=['unique_key'], keep=False)]
    
    return len(errors) == 0, errors
```

***

### 3. 日历渲染

```python
def render_calendar_html(year: int, month: int, events_df: pd.DataFrame, type_colors: Dict) -> str:
    cal = calendar.Calendar(firstweekday=6)  # 周日开始
    month_days = cal.monthdayscalendar(year, month)
    
    # 按日期分组事件
    events_by_date = {}
    for _, row in events_df.iterrows():
        date_str = row['date_created']
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(row.to_dict())
    
    # 生成 HTML + CSS
    # 每天最多显示3个事件
    # 不同类型不同颜色
```

***

### 4. 模拟数据加载

```python
def load_sample_data(db: Database):
    sample_data = [
        {"unique_key": "EVT001", "project": "Project Alpha", 
         "date_created": "2025-03-03", "type": "Feature", 
         "short_desc": "完成用户认证模块", "desc_1": "实现了基于JWT..."},
        # ... 共20条
    ]
    
    success_count = 0
    for event in sample_data:
        ok, _ = db.add_event(event)
        if ok:
            success_count += 1
    
    return success_count
```

### 5. 一键清空

```python
def clear_all_data(db: Database):
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

***

## 界面布局

### 侧边栏（控制面板）
```
┌─────────────────────────────┐
│  ⚙️ 控制面板                 │
├─────────────────────────────┤
│  🎮 快速开始                 │
│  当前有 20 条数据            │
│  ✨ 当前为模拟数据           │
│  [🗑️ 一键清空所有数据]       │
├─────────────────────────────┤
│  📤 数据上传                 │
│  [文件选择]                  │
│  [✅ 导入]                   │
├─────────────────────────────┤
│  🔍 筛选                     │
│  年份: [2025 ▼]              │
│  月份: [3月 ▼]               │
│  Project: [多选]             │
│  Type: [多选]                │
├─────────────────────────────┤
│  📈 统计                     │
│  本月事件: 20                │
│  Project A: 8                │
│  ● Feature: 6                │
│  ● Bugfix: 4                 │
├─────────────────────────────┤
│  [📥 导出CSV]                │
└─────────────────────────────┘
```

### 主内容区
```
┌─────────────────────────────────────────────────────────────┐
│  📅 日历视图                                                 │
│  [◀ 上月]    2025年 3月    [下月 ▶]                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  日   一   二   三   四   五   六                    │   │
│  │  ────────────────────────────────────────────────  │   │
│  │  26  27  28   1    2   [3]   4                     │   │
│  │            🟦用户认证                               │   │
│  │   5   6   7   8   9  10  11                        │   │
│  │  🟥首页修复 🟩需求评审 🟦数据导出                    │   │
│  │  ...                                               │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  📝 事件管理                                                 │
│  [📋 查看/编辑] [➕ 添加事件]                                │
└─────────────────────────────────────────────────────────────┘
```

***

## 类型颜色映射

| 类型 | 背景色 | 边框色 | 文字色 |
|------|--------|--------|--------|
| Feature | #DBEAFE (浅蓝) | #3B82F6 (蓝) | #1E40AF (深蓝) |
| Bugfix | #FEE2E2 (浅红) | #EF4444 (红) | #991B1B (深红) |
| Meeting | #D1FAE5 (浅绿) | #10B981 (绿) | #065F46 (深绿) |
| Review | #FEF3C7 (浅黄) | #F59E0B (橙) | #92400E (深橙) |
| Other | #F3F4F6 (浅灰) | #6B7280 (灰) | #374151 (深灰) |

***

## 代码统计

| 指标    | 数值            |
| ----- | ------------- |
| 总代码行数 | \~650行        |
| 函数数量  | 12个           |
| 类数量   | 1个 (Database) |
| 数据库表  | 2个            |
| 模拟数据  | 52条           |

***

## 模拟数据结构

### 数据分布
- **时间范围**: 2025年3月1日 - 3月31日
- **项目数量**: 3个 (Project Alpha/Beta/Gamma)
- **事件总数**: 20条
- **类型分布**:
  - Feature: 6条
  - Bugfix: 4条
  - Meeting: 4条
  - Review: 4条
  - Other: 2条

### 示例数据
```csv
project,date_created,unique_key,type,short_desc,desc_1
Project Alpha,2025-03-03,EVT001,Feature,完成用户认证模块,实现了基于JWT的用户登录系统...
Project Alpha,2025-03-05,EVT002,Bugfix,修复首页加载慢问题,优化了数据库查询...
Project Beta,2025-03-06,EVT003,Meeting,客户需求评审会议,与产品团队讨论Q2需求...
```

---

## 开发要点

### 1. Streamlit 限制与解决方案

**限制**: 原生不支持复杂日历组件
**方案**: 使用 `st.components.v1.html` 渲染自定义 HTML/CSS

**限制**: 无法直接处理日历单元格点击
**方案**: 通过 `st.expander` 和事件列表实现详情查看

### 2. 数据验证策略

- 前端: Streamlit 表单验证（必填项）
- 后端: 数据库唯一键约束
- 导入: Pandas 数据清洗和验证

### 3. 性能优化

- 按月查询数据库，避免全表扫描
- 使用 Pandas 向量化操作处理数据
- 日历渲染使用纯 HTML/CSS，无 JavaScript

---

## 使用说明

### 首次使用
1. 运行 `streamlit run app.py`
2. 点击 **"🚀 加载模拟数据"**
3. 查看日历效果

### 导入真实数据
1. 准备 CSV/Excel 文件
2. 点击 **"📤 数据上传"** 选择文件
3. 预览数据后点击 **"✅ 导入"**

### 管理事件
- **添加**: 切换到 **"➕ 添加事件"** 标签页
- **编辑/删除**: 在 **"📋 查看/编辑"** 标签页展开事件

### 清空数据
1. 点击 **"🗑️ 一键清空所有数据"**
2. 确认清空操作

---

## 后续优化建议

1. **周视图/列表视图切换**: 增加不同展示模式
2. **拖拽调整日期**: 支持可视化调整事件日期
3. **批量导入/导出**: 支持更多格式（JSON, PDF报告）
4. **用户认证**: 多用户支持和权限管理
5. **数据备份**: 自动备份和恢复功能
6. **图表统计**: 工作量趋势分析图表

---

*开发完成时间: 2026-03-23*  
*版本: v1.0*  
*开发者: Claw*
