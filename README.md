# LinkedIn Job Research Agent

## 📢 Version 2.0 - Production Architecture & Market Intelligence

Version 2.0 introduces a robust, production-grade architecture and integrates deep job market intelligence via the Adzuna API, while moving towards a more modular and maintainable codebase.

### Key Enhancements

#### **1. Adzuna Market Intelligence (6 New Tools)**
We have integrated the Adzuna API to provide the agent with real-time job market data, expanding its capabilities beyond LinkedIn profile research.
- **`search_adzuna_jobs`**: Real-time job search with full descriptions.
- **`analyze_salary_trends`**: Salary distribution histograms.
- **`get_top_hiring_companies`**: Market-leading employers by vacancy count.
- **`list_job_categories`**: Dynamic category discovery.
- **`get_regional_job_stats`**: Geographical job density analysis.
- **`get_historical_salary_trends`**: 12-24 month salary trend research.

#### **2. Production Dependency Injection (`modern-di`)**
Implemented a scalable DI container using `modern-di` to manage service lifecycles.
- **Singleton Pattern**: Services like `AdzunaService` are managed as global singletons (`Scope.APP`).
- **Resource Management**: Uses generators (`yield`) for safe initialization and cleanup of connections.
- **Type Safety**: Full integration with static analysis (Pyright/Mypy) for better developer experience.

#### **3. Structured Logging (`loguru`)**
Moved away from simple print statements to structured, performance-optimized logging.
- **Contextual Data**: Uses `logger.bind()` to attach metadata (query, location, etc.) to log entries.
- **Lazy Interpolation**: Uses `{}` placeholders to prevent unnecessary string formatting.
- **Error Tracking**: Automatic stack trace capturing with `logger.exception()`.

#### **4. Developer Experience & Debugging**
- **Conflict Resolution**: Renamed internal tools (e.g., `search_adzuna_jobs`) to avoid naming collisions with external MCP servers (like `linkedin-mcp-server`).
- **Integrated Debugging**: Added `.vscode/launch.json` for Cursor/VS Code, allowing step-by-step debugging of agent tools and sub-processes.

---

## 📢 Version 1.0 - Known Issues

The initial implementation of the **LinkedIn Job Research Agent (v1.0)** relies on a browser automation tool (`linkedin-mcp-server`) that requires a graphical user interface (GUI) to function.

### Why It Fails

#### **1. Local Development (WSL2)**
- **Problem:** WSL2 does not have a native graphical display server.
- **Impact:** ChromeDriver fails to initialize in WSL2, making local testing difficult without complex X11 forwarding.

#### **2. Production Deployment (Cloud Run / Serverless)**
- **Problem:** Serverless environments are lightweight and lack browser binaries or graphical interfaces.
- **Impact:**
  - **Bloated Container:** Including Chrome increases image size by >500MB.
  - **Resource Constraints:** Limited CPU/Memory are unsuitable for browser automation.
  - **Conclusion:** Browser-based automation is not recommended for serverless production. Version 2.0 begins the transition to API-first research tools.
