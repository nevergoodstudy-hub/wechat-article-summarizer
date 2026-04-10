---
name: asyncio-taskgroup-migration
description: "Migrate all asyncio.gather() calls to asyncio.TaskGroup for structured concurrency. Use this skill to fix P1-2: replace gather with TaskGroup context managers, add Semaphore-based backpressure for concurrent operations, and use except* for ExceptionGroup handling. Targets Python 3.11+ structured concurrency patterns."
---

# asyncio.gather → TaskGroup Migration — P1-2 Fix

Replace all `asyncio.gather()` usage with `asyncio.TaskGroup` for proper structured concurrency, error propagation, and task lifecycle management.

## Audit Reference
- Issue: DEEP_AUDIT_ISSUES.md → P1-2
- Fix plan: DEEP_AUDIT_IMPROVEMENTS.md → 方案 P1-2
- Research: research_round1_architecture.md → Section 3

## Step-by-Step Execution

### Step 1: Find all asyncio.gather usage
```powershell
grep -rn "asyncio\.gather" src/
```

### Step 2: Migrate each usage
For each `asyncio.gather()` call, apply the appropriate pattern:

**Pattern A: Simple concurrent tasks**
```python
# Before:
results = await asyncio.gather(task1(), task2(), task3())

# After:
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(task1())
    t2 = tg.create_task(task2())
    t3 = tg.create_task(task3())
results = [t1.result(), t2.result(), t3.result()]
```

**Pattern B: Dynamic task list with error tolerance**
```python
# Before:
results = await asyncio.gather(*[process(url) for url in urls], return_exceptions=True)

# After:
results = []
try:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(process(url)) for url in urls]
    results = [t.result() for t in tasks]
except* Exception as eg:
    # Handle partial failures
    for t in tasks:
        if t.done() and not t.cancelled():
            try:
                results.append(t.result())
            except Exception:
                results.append(None)
```

**Pattern C: With backpressure (Semaphore)**
```python
# For concurrent scraping/API calls — limit concurrency:
semaphore = asyncio.Semaphore(5)  # max 5 concurrent

async def limited_task(url):
    async with semaphore:
        return await scrape(url)

async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(limited_task(url)) for url in urls]
results = [t.result() for t in tasks]
```

### Step 3: Add timeout support
Where applicable, wrap TaskGroup with `asyncio.timeout()`:
```python
async with asyncio.timeout(60):
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(scrape(url)) for url in urls]
```

### Step 4: Update error handling
Replace `if isinstance(result, Exception)` patterns with `except*` syntax:
```python
try:
    async with asyncio.TaskGroup() as tg:
        ...
except* ValueError as eg:
    for exc in eg.exceptions:
        logger.error(f"Validation error: {exc}")
except* httpx.HTTPError as eg:
    for exc in eg.exceptions:
        logger.error(f"HTTP error: {exc}")
```

## Key Files to Check
- Scraper orchestration (concurrent URL fetching)
- Batch summarization (concurrent LLM calls)
- Export operations (concurrent file writes)
- MCP server (concurrent tool execution)
- Any module importing `asyncio.gather`

## Validation
1. `grep -rn "asyncio\.gather" src/` returns ZERO results
2. All existing async tests still pass
3. Concurrent operations still work correctly
4. Error handling works: one failed task doesn't leave others orphaned
