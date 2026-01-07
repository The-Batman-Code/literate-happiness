# Production Coding Guidelines

## Context
B2B platform on Google Cloud Run/GKE. SQLAlchemy + Redis Cloud.  
**Package Manager**: `uv` | **DI**: `modern-di`

---

## Core Rules

1. **BE CRITICAL**: Challenge bad ideas. Point out flaws.
2. **THINK PERFORMANCE FIRST**: Avoid O(n²), use dict lookups over list loops, batch operations. Analyze complexity before coding.
3. **MODULAR**: Functions <50 lines, files <500 lines. Extract to `src/app/common/`.
4. **READ CONTEXT FIRST**: Use tools before editing.
5. **REPOSITORY PATTERN**: ALL database/Redis ops through repositories.
6. **ASK WHEN UNCLEAR**: Don't guess.
7. **EXPLAIN APPROACH**: Describe plan before implementing.
8. **ABSOLUTE IMPORTS**: `from src.app.X import Y` always.
9. **DUAL PYDANTIC**: `response_model=` AND return type.
10. **LOG CRITICAL OPS**: External calls, exceptions, state changes. Use `%s`, NOT f-strings.

---

## Performance Rules

### Avoid High Time Complexity

```python
# ❌ BAD - O(n²) nested loops
for user in users:
    for order in orders:  # Searching entire list each time
        if order.user_id == user.id:
            process(user, order)

# ✅ GOOD - O(n) with dict lookup
orders_by_user = {order.user_id: order for order in orders}
for user in users:
    if order := orders_by_user.get(user.id):  # O(1) lookup
        process(user, order)
```

### Use Set/Dict for Membership Tests

```python
# ❌ BAD - O(n) per check
user_ids = [1, 2, 3, 4, 5]
if user_id in user_ids:  # Scans entire list

# ✅ GOOD - O(1) per check
user_ids = {1, 2, 3, 4, 5}
if user_id in user_ids:  # Hash lookup
```

### Batch Database Operations

```python
# ❌ BAD - N queries
for user_id in user_ids:
    user = await repo.get_by_id(user_id)

# ✅ GOOD - 1 query
users = await repo.get_by_ids(user_ids)  # WHERE id IN (...)
```

### Avoid Repeated Calculations

```python
# ❌ BAD
for item in items:
    if expensive_function() > threshold:  # Called every iteration
        process(item)

# ✅ GOOD
result = expensive_function()  # Calculate once
for item in items:
    if result > threshold:
        process(item)
```

### Think Before Coding
1. What's the time complexity? O(n)? O(n²)?
2. Can I use a dict/set instead of nested loops?
3. Can I batch this operation?
4. Am I calculating the same thing repeatedly?

---

## Dependency Injection (`modern-di`)

```python
from modern_di import Group, Scope, providers

class AppDependencies(Group):
    # APP scope - once per app lifetime
    db_session = providers.Resource(Scope.APP, get_async_session)
    
    # REQUEST scope - per request
    user_repo = providers.Factory(Scope.REQUEST, UserRepository, session=db_session)
    user_service = providers.Factory(Scope.REQUEST, UserService, user_repo=user_repo)

# Usage in routes
from typing import cast

@router.post("")
async def create_user(data: UserCreate) -> UserResponse:
    service = cast(UserService, await AppDependencies.user_service.resolve())
    return await service.create_user(data)

# Lifespan (main.py)
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with Container(scope=Scope.APP) as container:
        await AppDependencies.db_session.async_resolve(container)
        yield
```

---

## Logging Standards

### Use %s Placeholders
```python
# ❌ WRONG - allocates memory always
logger.info(f"Processing {user_id}")

# ✅ CORRECT - lazy evaluation
logger.info("Processing %s", user_id)
```

### Patterns
```python
# Simple
logger.info("User created")

# Structured context
logger.bind(user_id=str(user_id)).info("Payment for: %s", user_id)

# Multiple logs same context
with logger.contextualize(request_id=req_id):
    logger.info("Started: %s", req_id)
    logger.info("Completed: %s", req_id)

# Exceptions - ALWAYS include error_type
try:
    operation()
except Exception as e:
    logger.bind(
        user_id=str(user_id),
        error_type=type(e).__name__,  # REQUIRED
    ).exception("Operation failed")
    raise ServiceException("Failed") from e
```

### When to Log
**ALWAYS**: External APIs (before/after/error), DB writes, exceptions, state changes, slow ops (>1s)  
**NEVER**: Loops, reads, helpers

---

## Repository Pattern

```python
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str) -> User:
        try:
            logger.bind(email=email).info("Creating user: %s", email)
            user = User(email=email)
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)
            return user
        except IntegrityError as e:
            if "unique constraint" in str(e).lower():
                raise ValueError("Email exists") from e
            raise
```

---

## Thread Safety & Locks

### Redis Lock (Cross-Container)
```python
lock_key = "user:create:%s" % email
try:
    async with redis_manager.lock(lock_key, timeout=10):
        user = await repo.get_by_email(email)
        if not user:
            user = await repo.create(email)
        return user
except LockError:
    raise ServiceException("Operation in progress")
```
**CRITICAL**: Keep <5s. Lock releases if timeout exceeded.

### Asyncio Lock (Single-Container)
```python
class SessionService:
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def update_state(self, data: dict):
        async with self._lock:
            self._state.update(data)
```

**Never nest locks**.

---

## Transactions

```python
async def create_user_with_profile(session: AsyncSession, email: str, data: dict):
    try:
        user = await UserRepository(session).create(email)
        profile = await ProfileRepository(session).create(user.id, data)
        await session.commit()
        
        await session.refresh(user)
        await session.refresh(profile)
        return user, profile
    except Exception as e:
        await session.rollback()
        logger.bind(error_type=type(e).__name__).exception("Transaction failed")
        raise ServiceException("Failed") from e
```

**Key**: Share `AsyncSession`. Always refresh after commit.

---

## FastAPI Patterns

```python
@router.post("", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate) -> UserResponse:
    try:
        logger.bind(email=data.email).info("Creating user: %s", data.email)
        service = cast(UserService, await AppDependencies.user_service.resolve())
        user = await service.create_user(data)
        logger.bind(user_id=str(user.id)).info("Created: %s", user.id)
        return user
    except ValueError as e:
        logger.warning("Validation failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.bind(error_type=type(e).__name__).exception("Failed")
        raise HTTPException(status_code=500, detail="Internal error") from e
```

---

## Database Optimization

```python
# N+1 Prevention
from sqlalchemy.orm import selectinload
users = await session.execute(
    select(User).options(selectinload(User.orders))
)

# Bulk operations
self.session.add_all([Item(**item) for item in items])
await self.session.flush()
```

---

## Async Patterns

```python
# Concurrent
user, orders = await asyncio.gather(
    user_service.get_user(id),
    order_service.get_orders(id),
)

# Timeout
result = await asyncio.wait_for(operation(), timeout=5.0)
```

---

## Timezone Handling

**Rule**: UTC everywhere.

```python
from datetime import datetime, timezone
utc_now = datetime.now(timezone.utc)

# Display to user
from zoneinfo import ZoneInfo
display = utc_datetime.astimezone(ZoneInfo(user.timezone))
```

---

## Key Reminders

✅ **DO**:
- Think performance: O(n) > O(n²), dict lookups, batch ops
- Repository pattern for data access
- %s placeholders in logs
- Log external APIs, exceptions, state changes
- `error_type` in exception logs
- `from e` to preserve chain
- `cast()` when resolving from container
- UTC in database

❌ **DON'T**:
- Nested loops when dict lookup works
- List membership tests (use set)
- Repeated calculations in loops
- f-strings in logs
- Missing logs on APIs/exceptions
- Relative imports
- Direct DB/Redis access
- Naive datetimes
- Nest locks

---

## Research Tools

**When to Research**:
- Unsure about library API/syntax
- ImportError or AttributeError
- Haven't used pattern in 6+ months
- Need current implementation examples

**Tools**:
- **Context 7 MCP**: Read project files, check existing patterns, verify imports
- **Web Search**: Current documentation, latest library versions, implementation examples

```python
# Example: Unsure about modern-di async patterns?
# 1. Search: "modern-di async resolve examples"
# 2. Check docs for Group, Scope, providers usage
# 3. Verify with Context 7 MCP in existing codebase
```

---

## Workflow

1. Read context with tools (Context 7 MCP)
2. Research if uncertain (web search for docs)
3. Analyze performance implications
4. Plan approach
5. Write code with logging
6. Add imports last