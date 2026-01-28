# GUI 架构重构指导文档

本文档提供微信文章总结器 GUI 的完整重构蓝图。

## 📊 现状分析

**当前问题**：
- `app.py` 达 228KB，包含 5900+ 行代码
- 视图逻辑与业务逻辑耦合严重
- 组件复用困难，维护成本高

**已完成重构**：
- ✅ 创建 `styles/` 模块（颜色、主题配置）
- ✅ 创建 `components/` 目录
- ✅ 新增 `GraphViewerComponent` 知识图谱查看器
- ✅ 已有 `viewmodels/` 目录（MVVM 模式部分实现）

## 🎯 重构目标

### 1. 目录结构规划

```
src/wechat_summarizer/presentation/gui/
├── app.py                      # 主应用入口（<1000行）
├── __init__.py
├── components/                 # UI 组件库
│   ├── __init__.py
│   ├── url_input.py            # URL 输入组件
│   ├── article_preview.py      # 文章预览组件
│   ├── summary_panel.py        # 摘要展示面板
│   ├── export_dialog.py        # 导出对话框
│   ├── settings_panel.py       # 设置面板
│   ├── graph_viewer.py         # 知识图谱查看器 ✅
│   ├── quality_indicator.py    # 摘要质量指示器
│   ├── progress_tracker.py     # 进度追踪组件
│   └── log_viewer.py           # 日志查看器
├── viewmodels/                 # MVVM 视图模型 ✅
│   ├── __init__.py
│   ├── base.py                 # 基础 ViewModel
│   ├── main_viewmodel.py
│   ├── article_viewmodel.py
│   ├── settings_viewmodel.py
│   ├── single_process_viewmodel.py
│   └── batch_process_viewmodel.py
├── styles/                     # 样式配置 ✅
│   ├── __init__.py
│   ├── colors.py               # 颜色配置
│   ├── fonts.py                # 字体配置
│   └── layouts.py              # 布局常量
├── utils/                      # GUI 工具 ✅
│   ├── __init__.py
│   ├── clipboard_detector.py
│   ├── i18n.py
│   ├── theme_manager.py
│   └── windows_integration.py
└── translations/               # 国际化翻译 ✅
    └── en.json
```

### 2. MVVM 架构设计

```
┌──────────────┐
│     View     │  ← 展示层（CustomTkinter 组件）
└──────────────┘
       ↕
┌──────────────┐
│  ViewModel   │  ← 视图逻辑层（状态管理、命令绑定）
└──────────────┘
       ↕
┌──────────────┐
│    Model     │  ← 业务逻辑层（Use Cases、Domain）
└──────────────┘
```

**职责划分**：
- **View**：纯UI渲染，接收用户输入，绑定 ViewModel 
- **ViewModel**：状态管理、数据转换、命令处理
- **Model**：业务逻辑、数据持久化、领域规则

## 🔨 重构步骤

### 阶段 1: 组件抽取（预计 3-5 天）

#### 1.1 URL 输入组件
```python
# components/url_input.py
class URLInputComponent:
    def __init__(self, master):
        self.frame = ctk.CTkFrame(master)
        self.entry = ctk.CTkEntry(...)
        self.submit_btn = ctk.CTkButton(...)
        
    def on_submit(self, callback):
        """绑定提交回调"""
        
    def get_url(self) -> str:
        """获取 URL"""
        
    def set_url(self, url: str):
        """设置 URL"""
```

#### 1.2 文章预览组件
```python
# components/article_preview.py
class ArticlePreviewComponent:
    def __init__(self, master):
        self.textbox = ctk.CTkTextbox(...)
        self.word_count_label = ctk.CTkLabel(...)
        
    def load_article(self, article: Article):
        """加载文章数据"""
        
    def clear(self):
        """清空预览"""
```

#### 1.3 摘要面板组件
```python
# components/summary_panel.py
class SummaryPanelComponent:
    def __init__(self, master):
        self.summary_text = ctk.CTkTextbox(...)
        self.key_points_frame = ctk.CTkFrame(...)
        self.tags_frame = ctk.CTkFrame(...)
        
    def display_summary(self, summary: Summary):
        """展示摘要"""
        
    def show_quality_score(self, score: float):
        """显示质量评分"""
```

### 阶段 2: ViewModel 完善（预计 2-3 天）

#### 2.1 增强事件系统
```python
# viewmodels/base.py
class BaseViewModel:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}
        self._state: dict[str, Any] = {}
        
    def subscribe(self, event: str, callback: Callable):
        """订阅事件"""
        
    def notify(self, event: str, data: Any):
        """通知订阅者"""
        
    def get_state(self, key: str) -> Any:
        """获取状态"""
        
    def set_state(self, key: str, value: Any):
        """设置状态并通知"""
```

#### 2.2 命令模式
```python
# viewmodels/commands.py
class Command(ABC):
    @abstractmethod
    async def execute(self) -> Any:
        pass
        
    @abstractmethod
    async def undo(self) -> None:
        pass

class FetchArticleCommand(Command):
    def __init__(self, url: str, use_case):
        self.url = url
        self.use_case = use_case
        
    async def execute(self):
        return await self.use_case.execute(self.url)
```

### 阶段 3: App.py 精简（预计 2-3 天）

```python
# app.py（重构后 <1000 行）
class ModernApp:
    def __init__(self):
        self.root = ctk.CTk()
        self._setup_window()
        self._init_viewmodels()
        self._create_layout()
        self._bind_events()
        
    def _setup_window(self):
        """窗口配置"""
        
    def _init_viewmodels(self):
        """初始化 ViewModels"""
        self.main_vm = MainViewModel()
        self.settings_vm = SettingsViewModel()
        
    def _create_layout(self):
        """创建布局（使用组件）"""
        self.url_input = URLInputComponent(self.content_frame)
        self.article_preview = ArticlePreviewComponent(self.content_frame)
        self.summary_panel = SummaryPanelComponent(self.content_frame)
        
    def _bind_events(self):
        """绑定事件"""
        self.main_vm.subscribe("article_fetched", self._on_article_fetched)
```

### 阶段 4: 新功能集成（预计 1-2 天）

1. **知识图谱可视化** ✅
   - 已完成 `GraphViewerComponent`
   - 支持力导向布局、节点交互

2. **摘要质量评分**
   - 创建 `QualityIndicatorComponent`
   - 显示评分饼图/雷达图

3. **RAG 检索预览**
   - 创建 `RAGPreviewComponent`
   - 显示相关文档片段

## 📐 设计原则

### 单一职责原则
- 每个组件只负责一个功能
- ViewModel 不直接操作 UI
- View 不包含业务逻辑

### 依赖倒置原则
- View 依赖 ViewModel 接口
- ViewModel 依赖 Use Case 接口
- 使用依赖注入

### 开闭原则
- 组件支持扩展（继承）
- 不修改现有组件代码

## 🧪 测试策略

### 组件测试
```python
# tests/gui/test_url_input.py
def test_url_input_validation():
    component = URLInputComponent(mock_master)
    component.set_url("invalid")
    assert component.validate() == False
```

### ViewModel 测试
```python
# tests/gui/test_main_viewmodel.py
async def test_fetch_article():
    vm = MainViewModel(mock_use_case)
    await vm.fetch_article("https://...")
    assert vm.get_state("article") is not None
```

## 🚀 迁移策略

### 增量迁移
1. **共存阶段**：新组件与旧代码共存
2. **逐步替换**：按模块逐步迁移
3. **弃用标记**：旧代码添加 `@deprecated`
4. **完全切换**：删除旧代码

### 向后兼容
- 保留现有 API
- 使用适配器模式
- 提供迁移工具

## 📝 编码规范

### 组件命名
- 组件类：`XxxComponent`
- ViewModel：`XxxViewModel`
- 事件：`on_xxx` 或 `xxx_changed`

### 文件组织
- 一个文件一个主类
- 相关辅助类放同文件
- 超过 500 行考虑拆分

### 注释要求
- 所有公开方法添加文档字符串
- 复杂逻辑添加行内注释
- 使用类型注解

## 🔗 参考资源

- [CustomTkinter 文档](https://customtkinter.tomschimansky.com/)
- [MVVM 模式详解](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93viewmodel)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**重构负责人**: AI Assistant  
**文档版本**: v1.0  
**更新日期**: 2026-01-27
