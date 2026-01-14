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
10. **LOG CRITICAL OPS**: External calls, exceptions, state changes. Use `{}`, NOT f-strings.

---

## Performance Rules

### Avoid High Time Complexity
```python
# ❌ BAD - O(n²)
for user in users:
    for order in orders:
        if order.user_id == user.id:
            process(user, order)

# ✅ GOOD - O(n)
orders_by_user = {order.user_id: order for order in orders}
for user in users:
    if order := orders_by_user.get(user.id):
        process(user, order)
```

### Use Set/Dict for Membership
```python
# ❌ BAD - O(n)
if user_id in user_ids_list:

# ✅ GOOD - O(1)
if user_id in user_ids_set:
```

### Batch Operations
```python
# ❌ BAD - N queries
for user_id in user_ids:
    user = await repo.get_by_id(user_id)

# ✅ GOOD - 1 query
users = await repo.get_by_ids(user_ids)
```

### Think Before Coding
1. What's the time complexity?
2. Can I use dict/set instead of loops?
3. Can I batch this?
4. Am I recalculating unnecessarily?

---

## Dependency Injection (modern-di)

```python
from modern_di import Group, Scope, providers

class AppDependencies(Group):
    # APP scope - once per app lifetime
    db_session = providers.Resource(Scope.APP, get_async_session)
    
    # REQUEST scope - per request
    user_repo = providers.Factory(Scope.REQUEST, UserRepository, session=db_session)
    user_service = providers.Factory(Scope.REQUEST, UserService, user_repo=user_repo)
```

### Usage in Routes
```python
from typing import cast

@router.post("")
async def create_user(data: UserCreate) -> UserResponse:
    service = cast(UserService, await container.resolve_provider(AppDependencies.user_service))
    return await service.create_user(data)
```

### Lifespan (main.py)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with Container(scope=Scope.APP) as container:
        await container.resolve_provider(AppDependencies.db_session)
        yield
```

---

## Logging Standards

### Use {} Placeholders (Loguru)
```python
# ❌ WRONG - allocates memory always
logger.info(f"Processing {user_id}")

# ✅ CORRECT - lazy evaluation
logger.info("Processing {}", user_id)
```

### Patterns
```python
# Simple
logger.info("User created")

# Structured context
logger.bind(user_id=str(user_id)).info("Payment for: {}", user_id)

# Multiple logs same context
with logger.contextualize(request_id=req_id):
    logger.info("Started: {}", req_id)
    logger.info("Completed: {}", req_id)

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
- **ALWAYS**: External APIs (before/after/error), DB writes, exceptions, state changes, slow ops (>1s)
- **NEVER**: Loops, reads, helpers

---

## Security Rules

**CRITICAL**: Follow OWASP Top 10 guidelines. Prevent injection, broken auth, XSS, CSRF, security misconfigurations.

### Rate Limiting
```python
from slowapi import Limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest):
    ...
```

### Input Validation
```python
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",  # Reject unexpected fields
    )
```

### SQL Injection Prevention
```python
# ✅ GOOD - Parameterized (ORM does this)
user = await session.execute(
    select(User).where(User.email == email)
)

# ❌ NEVER
query = f"SELECT * FROM users WHERE email = '{email}'"
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # NOT "*"
    allow_credentials=True,
)
```

### API Keys & Secrets
```python
# ❌ WRONG
API_KEY = "sk-1234567890"

# ✅ CORRECT
from src.app.core.config import settings
api_key = settings.external_api.key.get_secret_value()
```

**NEVER**: Hard-code secrets, commit `.env`, log PII, use `allow_origins=["*"]`, build SQL with strings

**ALWAYS**: Use env vars, rotate keys, `SecretStr` in Pydantic, parameterized queries

---

## Repository Pattern

```python
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str) -> User:
        try:
            logger.bind(email=email).info("Creating user: {}", email)
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
lock_key = f"user:create:{email}"
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
        logger.bind(email=data.email).info("Creating user: {}", data.email)
        service = cast(UserService, await container.resolve_provider(AppDependencies.user_service))
        user = await service.create_user(data)
        logger.bind(user_id=str(user.id)).info("Created: {}", user.id)
        return user
    except ValueError as e:
        logger.warning("Validation failed: {}", str(e))
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

### ✅ DO
- Follow OWASP Top 10
- Think performance: O(n) > O(n²), dict lookups, batch ops
- Repository pattern for data access
- {} placeholders in logs
- Log external APIs, exceptions, state changes
- `error_type` in exception logs
- `from e` to preserve chain
- `cast()` when resolving from container
- UTC in database
- Rate limit public endpoints
- Pydantic validation with `extra="forbid"`
- Environment variables for secrets
- Parameterized queries

### ❌ DON'T
- Nested loops when dict works
- List membership tests (use set)
- Repeated calculations in loops
- f-strings in logs
- Missing logs on APIs/exceptions
- Relative imports
- Direct DB/Redis access
- Naive datetimes
- Nest locks
- Hard-code secrets
- Log PII (passwords, tokens)
- Use `allow_origins=["*"]` in production
- Build SQL with string formatting

---

## Research Tools

**When to Research**: Unsure about library API, ImportError, haven't used pattern in 6+ months

**Tools**:
- **Context 7 MCP**: Read project files, check patterns, verify imports
- **Web Search**: Current docs, latest versions, implementation examples

---

## Workflow

1. Read context with tools (Context 7 MCP)
2. Research if uncertain (web search for docs)
3. Analyze performance implications
4. Plan approach
5. Write code with logging
6. Add imports last