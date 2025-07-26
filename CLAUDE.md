# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Penny is an intelligent expense tracking application that uses OCR and AI to automatically categorize and analyze receipts and invoices. The application is built with Python and designed for homeowners tracking renovation costs, contractors managing project expenses, or anyone wanting organized financial insights.

## Project Structure

The project is organized using a structured FastAPI application layout:

```
app/
├── main.py          # FastAPI application entry point
├── api/             # API route handlers and endpoints
├── core/            # Core configuration and settings
├── db/              # Database models, connections, and migrations
├── models/          # Pydantic models and data schemas
├── services/        # Business logic and external service integrations
├── utils/           # Utility functions and helpers
├── static/          # Static files (CSS, JS, images)
├── templates/       # Jinja2 templates for web interface
└── test_main.http   # HTTP test file for manual endpoint testing
```

## Architecture

Currently a skeleton project with:
- **Backend**: FastAPI application (app/main.py) with basic Hello World endpoints
- **Structure**: Organized directories for scalable development
- **Documentation**: README.md describes the planned tech stack including AWS Textract, ChromaDB, SQLite, and LLM integration

The planned architecture includes:
- Python backend with SQLite for structured data storage (app/db/)
- ChromaDB for semantic search capabilities  
- AWS Textract for OCR document processing (app/services/)
- APScheduler for async job management
- LLM integration for expense categorization and natural language queries (app/services/)
- API endpoints for expense management (app/api/)
- Data models for expenses, receipts, and categories (app/models/)

## Development Commands

Currently this is a minimal FastAPI skeleton. To run the application:

```bash
# Install FastAPI and uvicorn (no requirements.txt exists yet)
pip install fastapi uvicorn

# Run the development server (from project root)
uvicorn app.main:app --reload

# Test endpoints using the provided HTTP file
# Use test_main.http with an HTTP client or curl commands
```

## Current State

The project is in its initial skeleton phase with only basic FastAPI endpoints implemented. The main application logic for OCR processing, expense categorization, and database integration has not yet been developed.