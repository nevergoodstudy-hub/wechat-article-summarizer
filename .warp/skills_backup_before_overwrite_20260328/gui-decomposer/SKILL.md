---
name: gui-decomposer
description: "Decompose the 113KB GUI app.py God Object into modular components. Use this skill to fix P0-2: split app.py into CTkFrame subclasses (sidebar, article list, summarization, export, settings), CTkToplevel dialogs, MVVM ViewModels, reusable widgets, and a pub/sub event bus. Each extracted file should be <400 lines."
---

# GUI God Object Decomposer — P0-2 Fix

Split `src/wechat_summarizer/presentation/gui/app.py` (113KB, ~3000+ lines) into 10-15 modular component files using MVVM + event bus pattern.

## Audit Reference
- Issue: DEEP_AUDIT_ISSUES.md → P0-2
- Fix plan: DEEP_AUDIT_IMPROVEMENTS.md → 方案 P0-2

## Target Directory Structure

```
src/wechat_summarizer/presentation/gui/
├── __init__.py
├── app.py                  # Keep as thin entry point (<100 lines)
├── main_window.py          # MainWindow coordinator (~200 lines)
├── event_bus.py            # Pub/sub event bus
├── frames/
│   ├── __init__.py
│   ├── sidebar_frame.py    # Navigation sidebar (~150 lines)
│   ├── article_list_frame.py  # Article list + CRUD (~300 lines)
│   ├── article_detail_frame.py # Article detail view (~200 lines)
│   ├── summarization_frame.py  # Summary controls (~250 lines)
│   ├── export_frame.py     # Export panel (~200 lines)
│   ├── settings_frame.py   # Settings panel (~300 lines)
│   └── progress_overlay.py # Progress indicators (~100 lines)
├── dialogs/
│   ├── __init__.py
│   ├── api_key_dialog.py   # API key configuration
│   ├── export_dialog.py    # Export confirmation
│   └── about_dialog.py     # About dialog
├── viewmodels/
│   ├── __init__.py
│   ├── article_viewmodel.py    # Article list state + logic
│   ├── summary_viewmodel.py    # Summarization state + logic
│   └── settings_viewmodel.py   # Settings state + logic
└── widgets/
    ├── __init__.py
    ├── article_card.py     # Article card component
    ├── llm_selector.py     # LLM provider selector
    └── url_input.py        # URL input with validation
```

## Step-by-Step Execution

### Step 1: Read and analyze app.py
1. Read the full `app.py` file
2. Identify method clusters by responsibility:
   - Navigation/sidebar methods
   - Article list management methods
   - Summarization control methods
   - Export methods
   - Settings/configuration methods
   - Dialog/popup methods
   - State management / data binding
3. Map each method to its target component

### Step 2: Create the event bus
Create `event_bus.py` first — this enables component communication:

```python
from typing import Callable, Any
from collections import defaultdict

class GUIEventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        self._handlers[event].append(handler)

    def publish(self, event: str, **data: Any) -> None:
        for handler in self._handlers[event]:
            handler(**data)

    def unsubscribe(self, event: str, handler: Callable) -> None:
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)
```

### Step 3: Extract components incrementally
For EACH extraction:
1. Create the new file with the class
2. Move relevant methods from app.py to the new class
3. Update imports in app.py
4. Replace moved code with delegation to the new component
5. Test that the GUI still launches

Extraction order (least dependencies first):
1. `progress_overlay.py` — standalone progress indicator
2. `event_bus.py` — no dependencies
3. `widgets/` — small reusable components
4. `dialogs/` — standalone popup windows
5. `frames/sidebar_frame.py` — navigation
6. `frames/article_list_frame.py` — article management
7. `frames/summarization_frame.py` — summary controls
8. `frames/export_frame.py` — export controls
9. `frames/settings_frame.py` — settings panel
10. `viewmodels/` — extract business logic from frames
11. `main_window.py` — final coordinator

### Step 4: Create MainWindow coordinator
The final app.py / main_window.py should be a thin orchestrator:

```python
import customtkinter as ctk
from .event_bus import GUIEventBus
from .frames.sidebar_frame import SidebarFrame
from .frames.article_list_frame import ArticleListFrame

class MainWindow(ctk.CTk):
    def __init__(self, container):
        super().__init__()
        self.title("WeChat Article Summarizer")
        self.event_bus = GUIEventBus()

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = SidebarFrame(self, self.event_bus)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ArticleListFrame(self, self.event_bus, container)
        self.content.grid(row=0, column=1, sticky="nsew")

        # Wire events
        self.event_bus.subscribe("navigate", self._on_navigate)
```

### Step 5: Frame pattern template
Each frame follows this pattern:

```python
import customtkinter as ctk
from ..event_bus import GUIEventBus

class ArticleListFrame(ctk.CTkFrame):
    def __init__(self, parent, event_bus: GUIEventBus, container):
        super().__init__(parent)
        self.event_bus = event_bus
        self.container = container
        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        # Widget construction only
        ...

    def _bind_events(self):
        self.event_bus.subscribe("article_added", self._on_article_added)
        ...

    def _on_article_added(self, **data):
        # Handle event
        ...
```

## Validation
1. After each extraction: `python -m wechat_summarizer gui` should launch without errors
2. All extracted files < 400 lines
3. `main_window.py` < 200 lines
4. No circular imports: `python -c "from wechat_summarizer.presentation.gui.main_window import MainWindow"`
5. Zero `grep -rn "from.*app import" src/wechat_summarizer/presentation/gui/frames/` hits (frames don't import app.py)

## Key Principles
- **Mediator pattern**: MainWindow is the only class that knows about all frames
- **Event bus**: Frames communicate via events, not direct references
- **ViewModel separation**: Business logic in viewmodels, not in frames
- **No circular imports**: Dependency flows: app → main_window → frames → widgets
- **Incremental**: Extract one component at a time, test after each
