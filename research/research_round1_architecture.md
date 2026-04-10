# Round 1 Research: Architecture, DI, Concurrency & GUI Patterns

## Research Date: 2026-02-19
## Scope: Python Hexagonal Architecture, DDD, DI Containers, CustomTkinter MVVM, asyncio Structured Concurrency

---

## 1. Python Hexagonal Architecture & DDD Best Practices

### Key Findings

#### 1.1 Port/Adapter Boundary Rules
- **Primary ports** (driving) define application use cases and belong in the application layer.
- **Domain-driven secondary ports** (repositories, domain services) belong in the domain layer.
- **Infrastructure secondary ports** (email, messaging, external APIs) belong in the application layer.
- Port interfaces should use **domain language**, not technical terms, and follow Single Responsibility Principle.
- The domain layer **must not import anything** outside its own package — this is the cardinal rule of hexagonal architecture.

#### 1.2 Domain Model vs Persistence Model Separation
- In DDD, the domain model and persistence model should be **separated**. Using a single entity for both leads to a database-centric architecture.
- There can be multiple models optimized for different purposes: Domain (Entities, Aggregates, Value Objects), Persistence (ORM schemas, read/write models for CQRS).
- Over time, database changes should **not** require domain model changes.

#### 1.3 When Hexagonal Architecture is Overkill
- Hexagonal architecture should only be applied where there is **complex business logic**.
- CRUD-like modules should **not** use hexagonal architecture — it becomes overengineering.
- A practical project should mix architectural styles: complex modules get hexagonal, simple ones use plain MVC/CRUD.

#### 1.4 Rich Domain Model Principle
- Domain objects should follow the **rich domain model** principle: encapsulate data AND behaviors together.
- Anemic domain models (data-only entities with external service logic) are an anti-pattern in DDD.

### Relevance to This Project
- The project's `domain/entities/article.py` appears to be partially anemic — business logic scattered in use cases rather than entities.
- The domain layer imports infrastructure concerns in some places (observed in prior file reads).
- The architecture attempts hexagonal but may be over-applied to simple CRUD-like export operations.

---

## 2. Dependency Injection Patterns in Python

### Key Findings

#### 2.1 Container Pattern Best Practices
- The `dependency-injector` library provides `DeclarativeContainer` with `providers.Singleton`, `providers.Factory`, and `providers.Configuration`.
- Test override pattern: `with container.api_client.override(mock.Mock()): main()` — dependencies injected automatically.
- Key advantages: consolidated assembly, explicit dependency graph, easy mock injection.

#### 2.2 Container Initialization Anti-Pattern
- **Critical finding**: Containers that eagerly initialize all services (including external connections) at startup will block test suites.
- Best practice: Use **lazy initialization** — services should only be created when first accessed.
- For testing, the container should support `override()` to replace real services with mocks **before** any initialization occurs.

#### 2.3 Factory Fixtures for Testing
- Use **factory fixtures** with explicit dependency declaration to avoid circular dependencies.
- Mock at the **service boundary** with contract-based responses, not implementation details.
- `conftest.py` should provide session-scoped container fixtures that wire mocked adapters.

### Relevance to This Project
- **BUG-001 (P0)**: Container initialization blocks the test suite because it eagerly connects to external services (LLM APIs, etc.) during `__init__`.
- The container should use lazy `providers.Singleton` with deferred initialization, not eager construction.
- 186 tests are blocked because they import modules that trigger container initialization.

---

## 3. asyncio Structured Concurrency

### Key Findings

#### 3.1 TaskGroup (Python 3.11+) is the Standard
- `asyncio.TaskGroup` provides structured concurrency: all tasks within a block are completed or properly cancelled before the block exits.
- If any task fails, TaskGroup **cancels all remaining tasks** and raises an `ExceptionGroup`.
- This is **safer than `asyncio.gather()`** which can hide errors and leave orphan tasks.

#### 3.2 Key Best Practices
- Always use `async with asyncio.TaskGroup() as tg:` — never use TaskGroup without context manager.
- Handle `asyncio.CancelledError` in `try...finally` blocks for cleanup.
- Access task results via `.result()` **after** the `async with` block, not inside it.
- Use `asyncio.Semaphore` for backpressure control when spawning many concurrent tasks.
- Use `asyncio.timeout()` for structured timeout management (also introduced in 3.11).

#### 3.3 Migration from gather()
- Replace `await asyncio.gather(*coros, return_exceptions=True)` with TaskGroup + `except*` syntax.
- TaskGroup provides stronger safety guarantees for nested subtask scheduling.
- For new asyncio code, TaskGroup is generally preferred over gather.

### Relevance to This Project
- The project uses `asyncio.gather()` in multiple places — should migrate to `TaskGroup` for Python 3.14 compatibility.
- No structured concurrency patterns observed; task lifecycles are not well-managed.
- No backpressure mechanism when scraping/summarizing multiple articles concurrently.

---

## 4. CustomTkinter GUI Architecture

### Key Findings

#### 4.1 MVC/MVVM for Tkinter Applications
- Large Tkinter applications should use MVC or MVVM patterns to separate concerns.
- Recommended structure: one file for GUI (View), one for logic (Model/ViewModel), one for app entry point.
- Button commands and event handlers should delegate to a controller/viewmodel, not contain business logic.

#### 4.2 God Object Anti-Pattern
- A single file exceeding ~500 lines is a strong indicator of a God Object.
- Refactoring strategies: Extract Class (move related methods to new classes), Extract Interface, Delegate pattern.
- For GUI apps: split into Frame/Page classes, each managing a single logical section.

#### 4.3 CustomTkinter Specifics
- CustomTkinter provides modern widgets but does not enforce any architecture.
- Best practice: use composition — create reusable widget components as separate classes.
- Each major UI section (sidebar, content area, dialog) should be its own class inheriting from `CTkFrame`.

### Relevance to This Project
- **app.py is 113KB** — this is a severe God Object. It likely contains >3000 lines mixing view construction, event handling, business logic, and state management.
- The MVVM pattern is mentioned in architecture docs but not properly implemented.
- Refactoring into ~10-15 focused Frame/Component classes would dramatically improve maintainability.

---

## 5. AWS Best Practices for Hexagonal Architecture

### Key Findings
- AWS recommends: Write tests first (TDD), define domain behavior (BDD), automate testing and deployment.
- Use domain-driven design methodologies like **event storming** to model the business domain.
- Scale by decomposing into microservices and adopting CQRS with event-driven architecture.
- Project structure should **map directly** to hexagonal architecture concepts.

### Relevance to This Project
- No BDD/Gherkin tests exist for domain behavior validation.
- No event storming documentation for the article summarization domain.
- CQRS pattern could benefit the read-heavy article retrieval vs write-heavy summarization flow.

---

## Summary of Architecture Issues Found

| Issue | Severity | Category |
|-------|----------|----------|
| Container eager initialization blocks tests | P0 | DI/Testing |
| app.py 113KB God Object | P0 | GUI Architecture |
| Domain layer boundary violations | P1 | Hexagonal Architecture |
| No structured concurrency (TaskGroup) | P1 | Concurrency |
| Anemic domain model in some entities | P2 | DDD |
| No backpressure mechanism | P2 | Concurrency |
| Over-engineering in CRUD-like exporters | P3 | Architecture |
| No BDD/domain behavior tests | P3 | Testing |
