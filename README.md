# Invoicing System Backend - Backend Assessment

**Time Limit: 60 minutes**

## Important Instructions

> **1. Fork this repo into your personal github account**
> 
> **2. Do not raise Pull Request in the original repo**
> 
> **3. Application must be runnable with `docker-compose up` command**
> 
> **4. Complete as many APIs as possible within the time limit**
> 
> **5. Prioritize working functionality - do not submit broken code that fails to run with `docker-compose up`**

### Tips
- Focus on core functionality first, then add features incrementally
- Test your application with `docker-compose up` before final submission
- A partially complete but working solution is better than a complete but broken one

---

A FastAPI backend project with SQLite database.

## Objective

Build a backend API for an **Invoicing System** that allows users to create and manage invoices.

## Functional Requirements

### Single User System
- No authentication required. The system is designed for a single user.

### Invoice Management
- User should be able to create invoices
- User should be able to list invoices
- User should be able to get an invoice by ID
- User should be able to delete an invoice

An invoice consists of:
- **Client**
- **Products** (items)

For **products** and **clients**, do not create APIs—use seed data. The developer needs to design the database schema and APIs for the invoicing system.



## Data Requirements (Fields)

### Product (seed data only)
- name
- price

### Client (seed data only)
- name
- address
- company registration no.

### Invoice
- Invoice no
- issue date
- due date
- client
- address
- items
- tax
- total

## Quick Start (Docker)

The easiest way to run the application:

```bash
docker-compose up --build
```

This will:
- Build the Docker image
- Run database migrations automatically (if applicable)
- Start the API server at `http://localhost:8000`

To stop the application:

```bash
docker-compose down
```

## Manual Setup (Without Docker)

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run database migrations (if applicable)

```bash
python migrate.py upgrade
```

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

Or run directly:

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

## Database Migrations

### Running Migrations

**Apply all pending migrations:**
```bash
python migrate.py upgrade
```

**Revert all migrations:**
```bash
python migrate.py downgrade
```

**List migration status:**
```bash
python migrate.py list
```
