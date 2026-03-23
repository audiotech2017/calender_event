# Events 日历展示应用 - 数据结构规范

## 一、输入数据 Schema

### 1.1 字段定义

```json
{
  "project": {
    "type": "string",
    "required": true,
    "description": "项目名称，用于分类和筛选",
    "example": "Project A",
    "constraints": {
      "max_length": 100,
      "not_empty": true
    }
  },
  "date_created": {
    "type": "date",
    "required": true,
    "description": "事件创建日期",
    "example": "2025-03-15",
    "formats": ["YYYY-MM-DD", "YYYY/MM/DD", "DD-MM-YYYY"],
    "constraints": {
      "valid_date": true,
      "not_future": false
    }
  },
  "unique_key": {
    "type": "string",
    "required": true,
    "description": "全局唯一标识符",
    "example": "EVT001",
    "constraints": {
      "unique": true,
      "max_length": 50
    }
  },
  "type": {
    "type": "string",
    "required": true,
    "description": "事件类型分类",
    "example": "Feature",
    "enum": ["Feature", "Bugfix", "Meeting", "Review", "Other"],
    "constraints": {
      "case_sensitive": false
    }
  },
  "short_desc": {
    "type": "string",
    "required": true,
    "description": "简短描述，日历上展示",
    "example": "完成用户登录模块",
    "constraints": {
      "max_length": 50,
      "not_empty": true
    }
  },
  "desc_1": {
    "type": "string",
    "required": false,
    "description": "详细描述，弹窗中展示",
    "example": "实现了基于JWT的用户认证系统...",
    "constraints": {
      "max_length": 1000
    },
    "default": ""
  }
}
```

### 1.2 CSV 格式示例

```csv
project,date_created,unique_key,type,short_desc,desc_1
Project A,2025-03-15,EVT001,Feature,完成用户登录模块,实现了基于JWT的用户认证系统，支持OAuth2.0登录
Project B,2025-03-18,EVT002,Bugfix,修复支付接口问题,解决了支付宝回调验证失败的问题
Project A,2025-03-20,EVT003,Meeting,客户需求评审会议,与产品团队讨论Q2需求优先级
Project C,2025-03-22,Feature,新增报表功能,开发了月度销售统计报表，支持导出Excel
Project A,2025-03-25,Review,代码审查,对订单模块进行代码审查，发现3个潜在问题
```

### 1.3 Excel 格式要求

- **Sheet 名称**: 任意（读取第一个 sheet）
- **表头**: 必须在第一行
- **列顺序**: 不固定，按字段名匹配
- **数据行**: 从第二行开始

## 二、内部数据结构

### 2.1 DataFrame Schema

```python
import pandas as pd
from datetime import datetime

# 内部数据格式
events_df = pd.DataFrame({
    'project': pd.Series(dtype='str'),           # 项目名称
    'date_created': pd.Series(dtype='datetime64[ns]'),  # 日期
    'unique_key': pd.Series(dtype='str'),        # 唯一键
    'type': pd.Series(dtype='str'),              # 类型
    'short_desc': pd.Series(dtype='str'),        # 短描述
    'desc_1': pd.Series(dtype='str'),            # 详细描述
    'year': pd.Series(dtype='int'),              # 年份（派生）
    'month': pd.Series(dtype='int'),             # 月份（派生）
    'day': pd.Series(dtype='int'),               # 日期（派生）
    'type_color': pd.Series(dtype='str')         # 类型颜色（派生）
})
```

### 2.2 Event 对象 (Python Dict)

```python
event = {
    # 原始字段
    'project': 'Project A',
    'date_created': datetime(2025, 3, 15),
    'unique_key': 'EVT001',
    'type': 'Feature',
    'short_desc': '完成用户登录模块',
    'desc_1': '实现了基于JWT的用户认证系统...',
    
    # 派生字段
    'year': 2025,
    'month': 3,
    'day': 15,
    'type_color': '#3B82F6',
    'weekday': 5,  # 0=周一, 6=周日
    'week_of_month': 3
}
```

### 2.3 日历单元格数据结构

```python
calendar_cell = {
    'date': datetime(2025, 3, 15),
    'year': 2025,
    'month': 3,
    'day': 15,
    'weekday': 5,           # 星期几
    'is_current_month': True,  # 是否当前月份
    'is_today': False,      # 是否今天
    'events': [             # 当日事件列表
        {
            'unique_key': 'EVT001',
            'short_desc': '完成用户登录模块',
            'type': 'Feature',
            'color': '#3B82F6',
            'project': 'Project A'
        },
        # ... 更多事件
    ],
    'event_count': 3,       # 事件总数
    'has_more': True        # 是否还有更多（超出显示限制）
}
```

## 三、筛选条件数据结构

```python
filters = {
    'year': 2025,                    # 选中年份
    'month': 3,                      # 选中月份
    'projects': ['Project A', 'Project B'],  # 选中项目（空列表=全部）
    'types': ['Feature', 'Bugfix'],  # 选中类型（空列表=全部）
    'date_range': {                  # 日期范围（可选）
        'start': datetime(2025, 3, 1),
        'end': datetime(2025, 3, 31)
    }
}
```

## 四、统计数据结构

```python
statistics = {
    'total_events': 15,              # 总事件数
    'filtered_events': 8,            # 筛选后事件数
    'by_project': {                  # 按项目统计
        'Project A': {'count': 5, 'percentage': 62.5},
        'Project B': {'count': 3, 'percentage': 37.5}
    },
    'by_type': {                     # 按类型统计
        'Feature': {'count': 3, 'percentage': 37.5, 'color': '#3B82F6'},
        'Bugfix': {'count': 2, 'percentage': 25.0, 'color': '#EF4444'},
        'Meeting': {'count': 2, 'percentage': 25.0, 'color': '#10B981'},
        'Review': {'count': 1, 'percentage': 12.5, 'color': '#F59E0B'}
    },
    'by_date': {                     # 按日期统计
        '2025-03-15': 2,
        '2025-03-18': 1,
        # ...
    },
    'daily_average': 2.5             # 日均事件数
}
```

## 五、Session State 结构

```python
session_state = {
    # 数据存储
    'raw_data': pd.DataFrame,        # 原始上传数据
    'processed_data': pd.DataFrame,  # 处理后数据（含派生字段）
    'filtered_data': pd.DataFrame,   # 筛选后数据
    
    # 筛选状态
    'current_year': 2025,
    'current_month': 3,
    'selected_projects': [],
    'selected_types': [],
    
    # UI 状态
    'selected_date': datetime,       # 选中的日期（用于弹窗）
    'show_detail_modal': False,      # 是否显示详情弹窗
    'modal_events': [],              # 弹窗中展示的事件
    
    # 文件信息
    'uploaded_filename': 'events.csv',
    'upload_time': datetime,
    
    # 错误信息
    'validation_errors': [],
    'last_error': None
}
```

## 六、导出数据结构

### 6.1 CSV 导出格式

```csv
project,date_created,unique_key,type,short_desc,desc_1,year,month
Project A,2025-03-15,EVT001,Feature,完成用户登录模块,实现了...,2025,3
Project B,2025-03-18,EVT002,Bugfix,修复支付接口问题,解决了...,2025,3
```

### 6.2 JSON 导出格式

```json
{
  "export_info": {
    "export_time": "2025-03-23T21:30:00",
    "total_events": 15,
    "filter_applied": true,
    "filters": {
      "year": 2025,
      "month": 3,
      "projects": ["Project A", "Project B"],
      "types": ["Feature", "Bugfix"]
    }
  },
  "events": [
    {
      "project": "Project A",
      "date_created": "2025-03-15",
      "unique_key": "EVT001",
      "type": "Feature",
      "short_desc": "完成用户登录模块",
      "desc_1": "实现了基于JWT的用户认证系统..."
    }
  ],
  "statistics": {
    "by_project": {...},
    "by_type": {...}
  }
}
```

## 七、类型颜色映射

```python
TYPE_COLOR_MAP = {
    'Feature': {
        'bg': '#DBEAFE',      # 浅蓝背景
        'border': '#3B82F6',  # 蓝色边框
        'text': '#1E40AF'     # 深蓝文字
    },
    'Bugfix': {
        'bg': '#FEE2E2',      # 浅红背景
        'border': '#EF4444',  # 红色边框
        'text': '#991B1B'     # 深红文字
    },
    'Meeting': {
        'bg': '#D1FAE5',      # 浅绿背景
        'border': '#10B981',  # 绿色边框
        'text': '#065F46'     # 深绿文字
    },
    'Review': {
        'bg': '#FEF3C7',      # 浅黄背景
        'border': '#F59E0B',  # 橙色边框
        'text': '#92400E'     # 深橙文字
    },
    'Other': {
        'bg': '#F3F4F6',      # 浅灰背景
        'border': '#6B7280',  # 灰色边框
        'text': '#374151'     # 深灰文字
    }
}
```

## 八、数据验证规则

```python
VALIDATION_RULES = {
    'project': {
        'required': True,
        'type': 'string',
        'min_length': 1,
        'max_length': 100
    },
    'date_created': {
        'required': True,
        'type': 'date',
        'formats': ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y'],
        'valid_range': {
            'min': '2000-01-01',
            'max': '2099-12-31'
        }
    },
    'unique_key': {
        'required': True,
        'type': 'string',
        'unique': True,
        'max_length': 50
    },
    'type': {
        'required': True,
        'type': 'string',
        'valid_values': ['Feature', 'Bugfix', 'Meeting', 'Review', 'Other'],
        'case_sensitive': False
    },
    'short_desc': {
        'required': True,
        'type': 'string',
        'min_length': 1,
        'max_length': 50
    },
    'desc_1': {
        'required': False,
        'type': 'string',
        'max_length': 1000,
        'default': ''
    }
}
```

---

*数据结构版本: v1.0*  
*创建时间: 2026-03-23*
