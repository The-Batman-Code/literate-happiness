# Base Repository Structure

A production-grade FastAPI boilerplate with Google ADK multi-agent architecture. This project demonstrates best practices for building scalable AI agent systems with FastAPI, including layered services, repositories, and proper resource management.

**Version:** 0.1.0
**Python:** 3.13+
**Backend Framework:** FastAPI
**Package Manager:** `uv` (Ultra-fast Python package installer)
**AI Framework:** Google ADK (Agent Development Kit)

---

## 📢 Version 1.0 - Known Issues

The current implementation of the **LinkedIn Job Research Agent (v1.0)** relies on a browser automation tool (`linkedin-mcp-server`) that requires a graphical user interface (GUI) to function. This creates significant limitations for both local development and production deployment.

### Why It Fails

#### **1. Local Development (WSL2)**

- **Problem:** WSL2 (Windows Subsystem for Linux), a common development environment, does not have a native graphical display server.
- **Impact:** ChromeDriver (used by the agent) needs a display to render the browser, so it fails to initialize in WSL2. This makes local testing and development difficult.

#### **2. Production Deployment (Cloud Run / Serverless)**

- **Problem:** Serverless environments like Google Cloud Run are lightweight and do not include a pre-installed browser (like Chrome/Chromium) or a graphical interface.
- **Impact:**
  - **Bloated Container:** Including Chrome in the deployment package would increase the container image size by over 500MB, which violates serverless principles of being lightweight and fast-scaling.
  - **Resource Constraints:** The limited CPU and memory in serverless environments are not suitable for running a full browser instance.
  - **Conclusion:** The agent, in its current form, **will not work** in a production serverless environment.

---

## 🎯 Version 2.0 - Planned Improvements

To address these limitations, **Version 2.0** will move away from browser automation and focus on a more robust, API-driven approach. The key improvements will include:

1. **Headless Operation:** The agent will be redesigned to operate without a GUI, making it compatible with any environment (including WSL2 and serverless).
2. **Official/Unofficial APIs:** Instead of browser scraping, the agent will use official or unofficial LinkedIn APIs to gather data. This is more reliable, efficient, and less prone to breaking.
3. **Focus on Scalability:** The new architecture will be designed for scalability and performance, making it suitable for production use in a serverless environment.

---