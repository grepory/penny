# Penny - Personal Expense Analysis Assistant

An intelligent expense tracking application that uses OCR and AI to automatically categorize and analyze receipts and invoices. Perfect for homeowners tracking renovation costs, contractors managing project expenses, or anyone wanting to make sense of their spending.
Features

- *Smart Document Processing*: AWS Textract or Mistral OCR for receipts, invoices, and scanned documents
- *AI Categorization*: Automatic classification of expenses (improvements vs repairs, room assignments, vendor normalization)
- *Natural Language Queries*: Ask questions like "How much did I spend on paint?" and get intelligent answers
- *Tax-Ready Reports*: Proper categorization for tax purposes with uncertainty flagging
- *Visual Analytics*: Interactive charts, spending timelines, and category breakdowns

## Tech Stack

- Python backend with SQLite for structured data
- ChromaDB for semantic search capabilities
- AWS Textract for document processing
- APScheduler for async job management
- LLM integration for categorization and query processing

Turn your shoebox of receipts into organized, queryable financial insights.