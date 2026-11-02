# CLAUDE_LOG.md

# Inventory Management System – Claude Learning Log

**Project Name:** Inventory Management System  
**Developer:** Abhay  
**Purpose:** Learning, planning, and developing an Inventory Management System using Oracle Database, PL/SQL, Python FastAPI, and React.js.

---

## Day 1 – Monday: Planning and Understanding

### 1. Project Understanding
**Prompt asked:**
> Explain the Inventory Management System assignment step by step. Help me understand the backend, database, PL/SQL procedures, triggers, Python API, and React dashboard.

**What worked:**
- Understood the complete project requirements.
- Learned the difference between stock receipts and stock issues.
- Understood the purpose of reorder-level alerts.
- Identified the technologies required.

**What I learned:**
- Inventory management tracks incoming and outgoing products.
- PL/SQL procedures handle database operations.
- Triggers automatically record database changes.
- Python APIs connect the database with the frontend.
- React displays inventory information through a dashboard.

### 2. Database Design

**Prompt asked:**
> Help me design an Oracle database schema for an Inventory Management System with items, stock, receipts, issues, suppliers, and audit logs.

**What worked:**
- Identified the main database tables.
- Understood primary keys and foreign keys.
- Learned how tables are connected through relationships.

**What I learned:**
- ITEMS stores product details.
- STOCK maintains current stock quantities.
- RECEIPTS stores incoming stock transactions.
- ISSUES stores outgoing stock transactions.
- SUPPLIERS stores supplier details.
- AUDIT_LOG stores database activity.

---

## Day 2 – Tuesday: Database Development

### 3. Table Creation

**Prompt asked:**
> Teach me how to create Inventory Management System tables in Oracle SQL using primary keys, foreign keys, NOT NULL, UNIQUE, and CHECK constraints.

**What worked:**
- Learned Oracle CREATE TABLE syntax.
- Understood database constraints.
- Practised creating related tables.

**What I learned:**
- Primary keys uniquely identify records.
- Foreign keys maintain relationships between tables.
- CHECK constraints validate data.
- NOT NULL prevents empty required values.

### 4. Dummy Data

**Prompt asked:**
> Generate sample dummy data for items, suppliers, stock receipts, and stock issues to test my inventory database.

**What worked:**
- Understood INSERT statements.
- Practised inserting multiple records.
- Learned how to verify inserted records using SELECT queries.

**What I learned:**
- How to insert and retrieve inventory data.
- Why dummy data is useful for testing.

---

## Day 3 – Wednesday: PL/SQL and Python Backend

### 5. Stock In and Stock Out Procedures

**Prompt asked:**
> Explain how to create PL/SQL procedures for stock-in and stock-out operations with quantity validation and error handling.

**What worked:**
- Understood stored procedures.
- Learned how to increase and decrease stock.
- Learned how to prevent issuing more stock than available.

**What I learned:**
- Stock-in increases available quantity.
- Stock-out decreases available quantity.
- Validation prevents incorrect transactions.
- Transactions should maintain accurate stock records.

### 6. Reorder-Level Alerts

**Prompt asked:**
> Help me write a PL/SQL procedure to identify products whose available stock is below or equal to their reorder level.

**What worked:**
- Understood reorder-level conditions.
- Learned how to identify low-stock products.
- Understood how alerts can be stored and displayed.

**What I learned:**
- Reorder levels help avoid stock shortages.
- Low-stock products need timely replenishment.

### 7. Audit Log Triggers

**Prompt asked:**
> Explain Oracle PL/SQL triggers for recording INSERT, UPDATE, and DELETE operations in an audit log table.

**What worked:**
- Understood database triggers.
- Learned how triggers execute automatically.
- Understood how to record database changes.

**What I learned:**
- Triggers execute automatically when specified database events occur.
- Audit logs help track changes.
- Audit records improve accountability.

### 8. Python FastAPI

**Prompt asked:**
> Teach me how to connect Oracle Database with Python FastAPI and create REST APIs for inventory items, stock receipts, stock issues, and low-stock alerts.

**What worked:**
- Understood FastAPI basics.
- Learned API endpoints and HTTP methods.
- Understood database connectivity.

**What I learned:**
- GET retrieves information.
- POST creates records.
- PUT updates records.
- DELETE removes records.
- APIs allow frontend and backend communication.

---

## Day 4 – Thursday: React Dashboard

### 9. React Project Setup

**Prompt asked:**
> Teach me how to create a React.js frontend for my Inventory Management System using VS Code.

**What worked:**
- Understood React project structure.
- Learned components and props.
- Practised creating reusable components.

**What I learned:**
- React helps build interactive user interfaces.
- Components make the application easier to maintain.

### 10. Dashboard Design

**Prompt asked:**
> Help me design a modern inventory dashboard with total products, available stock, low-stock alerts, stock-in, and stock-out information.

**What worked:**
- Understood dashboard layout.
- Learned how to display inventory statistics.
- Planned reusable dashboard cards.

**What I learned:**
- Dashboards provide a quick overview of business operations.
- Important inventory information should be easy to understand.

---

## Day 5 – Friday: Charts and Integration

### 11. Charts and Graphs

**Prompt asked:**
> Teach me how to integrate Recharts into React to display stock levels, stock-in, stock-out, and inventory trends.

**What worked:**
- Learned chart components.
- Understood how to display data visually.
- Practised using chart data from API responses.

**What I learned:**
- Charts make inventory information easier to analyse.
- Graphs help identify stock trends.

### 12. Frontend and Backend Integration

**Prompt asked:**
> Explain how to connect my React frontend with Python FastAPI endpoints and display real inventory data.

**What worked:**
- Understood API integration.
- Learned how to fetch backend data.
- Understood JSON responses.

**What I learned:**
- React communicates with FastAPI through HTTP requests.
- FastAPI retrieves information from Oracle Database.
- API integration connects all project modules.

### 13. Responsive Design

**Prompt asked:**
> Help me make my inventory dashboard responsive for desktop, tablet, and mobile screens using CSS.

**What worked:**
- Learned CSS media queries.
- Understood responsive layouts.
- Planned mobile-friendly dashboard components.

**What I learned:**
- Responsive design improves usability across devices.
- Dashboard layouts should adapt to different screen sizes.

---

## Advanced Feature – Slow-Moving Stock Report

### 14. Slow-Moving Stock Analysis

**Prompt asked:**
> Explain how to identify slow-moving inventory products based on the last issue date and a selected period of inactivity.

**What worked:**
- Understood how to analyse stock issue history.
- Learned how to identify products with no recent stock movement.
- Planned a report using a configurable inactivity period.

**What I learned:**
- Slow-moving stock occupies storage space.
- Reports help businesses make better purchasing decisions.
- The inactivity period should be configurable.

---

## Challenges and Corrections

| Challenge | Learning / Correction |
|---|---|
| Database relationships | Studied primary and foreign keys |
| Stock quantity updates | Added validation before stock issues |
| PL/SQL errors | Learned exception handling |
| API connection | Studied Oracle database connectivity |
| React API integration | Practised HTTP requests and JSON |
| Responsive layout | Learned CSS media queries |
| Incorrect AI suggestions | Verified generated code and tested it before using |

---

## How I Used Claude

1. Used Claude to understand concepts and technologies.
2. Asked for explanations before implementing code.
3. Reviewed generated code line by line.
4. Tested code independently.
5. Corrected errors after understanding their causes.
6. Used Claude as a learning assistant, not as a replacement for my own development.

## Final Learning Outcome

Through this project, I aim to improve my knowledge of:

- Oracle SQL and PL/SQL
- Database design and relationships
- Stored procedures and triggers
- Python and FastAPI
- REST API development
- React.js
- Dashboard development
- Data visualization using Recharts
- Git and GitHub
- Debugging and problem-solving

**Note:** This is the planned learning log. After completing each task, update it with the actual prompts used, results obtained, errors encountered, corrections made, and what you personally learned. Do not mark unfinished work as completed.