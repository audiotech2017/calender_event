# Events 日历展示应用 - 框架设计

## 项目概述

向老板展示每月工作成果的交互式日历应用。支持从 CSV/Excel 导入事件数据，以日历形式可视化展示，并提供多维度筛选功能。

---

## 一、输入数据规范

### 1.1 数据字段定义

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `project` | String | 是 | 项目名称 |
| `date_created` | Date | 是 | 事件创建日期 (YYYY-MM-DD) |
| `unique_key` | String | 是 | 唯一标识符 |
| `type` | String | 是 | 事件类型分类 |
| `short_desc` | String | 是 | 简短描述（日历上展示） |
| `desc_1` | String | 否 | 详细描述（弹窗/详情页展示） |

### 1.2 输入文件格式

**支持格式**: CSV, Excel (.xlsx, .xls)

**CSV 示例**:
```csv
project,date_created,unique_key,type,short_desc,desc_1
Project A,2025-03-15,EVT001,Feature,完成用户登录模块,实现了基于JWT的用户认证系统，支持OAuth2.0登录
Project B,2025-03-18,EVT002,Bugfix,修复支付接口问题,解决了支付宝回调验证失败的问题
Project A,2025-03-20,EVT003,Meeting,客户需求评审会议,与产品团队讨论Q2需求优先级
```

### 1.3 数据验证规则

- `date_created`: 必须是有效日期格式
- `unique_key`: 全局唯一，重复数据需提示
- `type`: 建议预定义类型（Feature/Bugfix/Meeting/Review/Other）
- 空值处理: `desc_1` 可为空，其他字段必填

---

## 二、系统架构

### 2.1 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Streamlit |
| 数据处理 | Pandas |
| 日历组件 | 自定义 HTML/CSS + Streamlit components |
| 图表库 | Plotly (可选，用于统计图表) |
| 文件解析 | pandas.read_csv / pandas.read_excel |

### 2.2 文件结构

```
calender_streamlist/
├── app.py                      # 主应用入口
├── components/
│   ├── __init__.py
│   ├── calendar_view.py        # 日历视图组件
│   ├── event_card.py           # 事件卡片组件
│   └── filters.py              # 筛选器组件
├── utils/
│   ├── __init__.py
│   ├── data_loader.py          # 数据加载与验证
│   ├── date_utils.py           # 日期处理工具
│   └── export.py               # 导出功能
├── styles/
│   └── calendar.css            # 自定义样式
├── config.py                   # 配置常量
└── requirements.txt            # 依赖列表
```

---

## 三、功能模块设计

### 3.1 模块架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        app.py (主入口)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  数据上传模块  │  │  筛选器模块   │  │  日历展示模块  │      │
│  │  data_loader │  │   filters    │  │ calendar_view │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Session State (数据缓存)                 │   │
│  │  - uploaded_data: DataFrame                          │   │
│  │  - filtered_data: DataFrame                          │   │
│  │  - selected_date: datetime                           │   │
│  │  - filters: dict                                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 数据流设计

```
用户上传文件 → 数据解析 → 数据验证 → Session State 存储
                                              ↓
用户设置筛选条件 → 数据过滤 → 更新 filtered_data
                                              ↓
日历渲染 ← 按月份分组 ← 按日期聚合事件
                                              ↓
用户点击日期 → 展示当日事件详情
```

---

## 四、界面设计

### 4.1 整体布局

```
┌─────────────────────────────────────────────────────────────────┐
│  📅 Events 日历展示应用                                    [?]  │
├────────────────┬──────────────────────────────────────────────┤
│                │                                              │
│  📤 数据上传    │           📊 日历视图                        │
│  ────────────  │                                              │
│  [选择文件]     │   ┌─────────────────────────────────────┐   │
│  CSV/Excel     │   │  ◀  2025年 3月  ▶                   │   │
│                │   │  日  一  二  三  四  五  六            │   │
│  ────────────  │   │  ─────────────────────────────────   │   │
│                │   │  26  27  28  29  30  31   1          │   │
│  🔍 筛选器      │   │   2   3   4   5   6   7   8          │   │
│  ────────────  │   │   9  10  11  12  13  14  15  ●        │   │
│  年份: [2025 ▼]│   │  16  17  18  19  20  21  22  ●        │   │
│  月份: [3月 ▼] │   │  23  24  25  26  27  28  29          │   │
│                │   │  30  31   1   2   3   4   5          │   │
│  Project:      │   └─────────────────────────────────────┘   │
│  [全部 ▼]      │                                              │
│                │   ● = 有事件的日期                            │
│  Type:         │                                              │
│  [全部 ▼]      │                                              │
│                │                                              │
│  ────────────  │                                              │
│                │                                              │
│  📈 统计概览    │                                              │
│  ────────────  │                                              │
│  本月事件: 15  │                                              │
│  Project A: 8  │                                              │
│  Project B: 7  │                                              │
│                │                                              │
└────────────────┴──────────────────────────────────────────────┘
```

### 4.2 日历单元格设计

```
┌─────────────────┐
│  15             │  ← 日期数字
│  ─────────────  │
│  🟦 用户登录     │  ← short_desc (截断显示)
│  🟥 支付接口     │  ← 不同颜色代表不同 type
│  +2 more...     │  ← 超出显示数量时提示
└─────────────────┘
```

### 4.3 事件详情弹窗

```
┌─────────────────────────────────────┐
│  📋 2025-03-15 事件详情         [×] │
├─────────────────────────────────────┤
│                                     │
│  🟦 用户登录模块                      │
│  Project: Project A                 │
│  Type: Feature                      │
│  Key: EVT001                        │
│  ─────────────────────────────────  │
│  实现了基于JWT的用户认证系统，支持     │
│  OAuth2.0登录，包含用户注册、登录、    │
│  密码重置等功能。                     │
│                                     │
│  [复制]  [编辑]  [删除]              │
│                                     │
├─────────────────────────────────────┤
│  🟥 支付接口修复                      │
│  Project: Project B                 │
│  ...                                │
└─────────────────────────────────────┘
```

---

## 五、核心组件设计

### 5.1 数据上传组件 (data_loader.py)

```python
class DataLoader:
    """数据加载与验证"""
    
    REQUIRED_COLUMNS = ['project', 'date_created', 'unique_key', 'type', 'short_desc']
    
    @staticmethod
    def load_file(uploaded_file) -> pd.DataFrame:
        """加载 CSV/Excel 文件"""
        pass
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> tuple[bool, list]:
        """验证数据完整性"""
        pass
    
    @staticmethod
    def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
        """解析日期字段"""
        pass
```

### 5.2 筛选器组件 (filters.py)

```python
class EventFilters:
    """事件筛选器"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.available_years = self._get_years()
        self.available_projects = self._get_projects()
        self.available_types = self._get_types()
    
    def render_year_selector(self) -> int:
        """渲染年份选择器"""
        pass
    
    def render_month_selector(self) -> int:
        """渲染月份选择器"""
        pass
    
    def render_project_selector(self) -> list:
        """渲染项目多选器"""
        pass
    
    def render_type_selector(self) -> list:
        """渲染类型多选器"""
        pass
    
    def apply_filters(self, filters: dict) -> pd.DataFrame:
        """应用筛选条件"""
        pass
```

### 5.3 日历视图组件 (calendar_view.py)

```python
class CalendarView:
    """日历视图渲染"""
    
    def __init__(self, year: int, month: int, events_df: pd.DataFrame):
        self.year = year
        self.month = month
        self.events = events_df
    
    def render_calendar(self) -> str:
        """渲染完整日历 HTML"""
        pass
    
    def _render_day_cell(self, date: datetime, events: list) -> str:
        """渲染单个日期单元格"""
        pass
    
    def _get_events_for_date(self, date: datetime) -> list:
        """获取指定日期的事件"""
        pass
    
    def _get_event_color(self, event_type: str) -> str:
        """根据类型返回颜色"""
        pass
```

### 5.4 事件卡片组件 (event_card.py)

```python
class EventCard:
    """事件卡片展示"""
    
    TYPE_COLORS = {
        'Feature': '#3B82F6',    # 蓝色
        'Bugfix': '#EF4444',     # 红色
        'Meeting': '#10B981',    # 绿色
        'Review': '#F59E0B',     # 橙色
        'Other': '#6B7280'       # 灰色
    }
    
    @classmethod
    def render_compact(cls, event: dict) -> str:
        """渲染紧凑卡片（日历内）"""
        pass
    
    @classmethod
    def render_detail(cls, event: dict) -> str:
        """渲染详情卡片（弹窗内）"""
        pass
```

---

## 六、配置常量

```python
# config.py

# 类型颜色映射
TYPE_COLORS = {
    'Feature': '#3B82F6',
    'Bugfix': '#EF4444',
    'Meeting': '#10B981',
    'Review': '#F59E0B',
    'Other': '#6B7280'
}

# 日历显示配置
CALENDAR_CONFIG = {
    'max_events_per_day': 3,      # 每天最多显示事件数
    'short_desc_max_length': 15,  # 短描述最大字符数
    'week_start': 'Sunday',       # 周起始日
}

# 文件上传配置
UPLOAD_CONFIG = {
    'max_file_size_mb': 10,
    'allowed_extensions': ['.csv', '.xlsx', '.xls'],
}

# 日期格式
DATE_FORMAT = '%Y-%m-%d'
DISPLAY_DATE_FORMAT = '%Y年%m月%d日'
```

---

## 七、交互流程

### 7.1 用户使用流程

```
1. 打开应用
   ↓
2. 上传 CSV/Excel 文件
   ↓
3. 数据验证与预览
   ↓
4. 设置筛选条件（年份/月份/项目/类型）
   ↓
5. 查看日历展示
   ↓
6. 点击日期查看详情
   ↓
7. 导出报告（可选）
```

### 7.2 状态管理

```python
# Session State 结构
{
    'uploaded_data': DataFrame,      # 原始上传数据
    'filtered_data': DataFrame,      # 筛选后数据
    'current_year': int,             # 当前选中年份
    'current_month': int,            # 当前选中月份
    'selected_filters': {            # 筛选条件
        'projects': list,
        'types': list
    },
    'selected_date': datetime,       # 选中的日期
    'show_detail_modal': bool        # 是否显示详情弹窗
}
```

---

## 八、扩展功能规划

### 8.1 Phase 1 - MVP (当前设计)
- [x] 文件上传 (CSV/Excel)
- [x] 日历展示
- [x] 基础筛选 (年份/月份/项目/类型)
- [x] 事件详情查看

### 8.2 Phase 2 - 增强功能
- [ ] 事件编辑/删除
- [ ] 新增事件
- [ ] 拖拽调整日期
- [ ] 周视图/列表视图切换

### 8.3 Phase 3 - 高级功能
- [ ] 数据统计图表
- [ ] 工作量趋势分析
- [ ] 导出 PDF 报告
- [ ] 数据持久化 (数据库)

---

## 九、技术难点与解决方案

### 9.1 日历渲染
**难点**: Streamlit 原生不支持复杂日历组件
**方案**: 使用 `st.components.v1.html` 渲染自定义 HTML/CSS 日历

### 9.2 日期筛选性能
**难点**: 大数据量时筛选可能卡顿
**方案**: 使用 Pandas 向量化操作，避免循环

### 9.3 移动端适配
**难点**: 日历在手机上显示困难
**方案**: 检测屏幕宽度，小屏时切换为列表视图

---

## 十、待确认问题

1. **日期字段格式**: 是否统一为 `YYYY-MM-DD`？
2. **Type 预定义值**: 是否需要固定类型列表？
3. **多语言**: 是否需要中英文切换？
4. **权限控制**: 是否需要登录/权限管理？
5. **数据持久化**: 是否需要保存上传的历史数据？

---

*设计版本: v1.0*  
*创建时间: 2026-03-23*  
*设计状态: 框架完成，待开发*
