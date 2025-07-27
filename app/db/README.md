# Penny Financial Data Models Documentation

This document provides comprehensive documentation for the financial data models designed for the Penny home renovation expense tracking application.

## Overview

The financial data models are designed to support:
- Invoice/Receipt parsing from OCR documents
- Rich metadata for natural language queries
- Project-based expense tracking
- Vendor management and analytics
- Automated expense categorization
- Budget tracking and alerts
- Comprehensive reporting and analytics

## Database Schema Design

### Core Principles

1. **Normalization**: The schema follows third normal form (3NF) to minimize data redundancy
2. **Referential Integrity**: Foreign key constraints ensure data consistency
3. **Performance**: Strategic indexing for common query patterns
4. **Flexibility**: Support for both structured queries and LLM-powered natural language queries
5. **Audit Trail**: Timestamp tracking and processing metadata

### Entity Relationships

```
Documents (Base) ─────┐
                      │
                      ▼
Financial Documents ──┼── Line Items
      │               │
      ├── Vendors     │
      ├── Projects    │
      └── Payment Info│
                      │
                      ▼
            Categorization Rules
            Analytics Tables
```

## Model Descriptions

### Core Entities

#### Vendors
- **Purpose**: Store vendor/supplier information
- **Key Features**: Auto-creation from document parsing, deduplication logic
- **Indexes**: Name, tax_id for fast lookups
- **Integration**: Links to financial documents, supports vendor analytics

#### Projects
- **Purpose**: Group expenses by renovation project
- **Key Features**: Budget tracking, status management, timeline tracking
- **Indexes**: Name, type, status, date ranges
- **Integration**: Links to documents and line items, supports project analytics

#### ExpenseCategoryMapping
- **Purpose**: Hierarchical categorization system
- **Key Features**: Predefined categories for home renovation, keyword matching
- **Indexes**: Category, active status
- **Integration**: Used by auto-categorization rules and analytics

### Financial Documents

#### FinancialDocument
- **Purpose**: Enhanced document metadata with financial information
- **Key Features**: 
  - Links to base document system
  - Vendor information extraction
  - Tax calculation support
  - Project association
  - Processing confidence tracking
- **Indexes**: Document ID, vendor, project, date, amount
- **Integration**: Central hub linking all financial data

#### LineItem
- **Purpose**: Individual purchase items within documents
- **Key Features**:
  - Quantity and pricing support
  - Tax information per item
  - Category assignment
  - Product identification (SKU, brand, model)
- **Validation**: Automated total calculation validation
- **Integration**: Supports detailed analytics and categorization

#### PaymentInfo
- **Purpose**: Payment tracking and status management
- **Key Features**:
  - Multiple payment methods
  - Due date tracking
  - Partial payment support
  - Late fee calculation
- **Integration**: Supports cash flow analysis and payment alerts

### Analytics and Intelligence

#### AutoCategorizationRule
- **Purpose**: AI-powered expense categorization
- **Key Features**:
  - Pattern matching on vendor names and descriptions
  - Priority-based rule application
  - Usage tracking and confidence scoring
- **Performance**: Optimized for real-time categorization

#### CategorizationSuggestion
- **Purpose**: Machine learning suggestions with user feedback
- **Key Features**:
  - Confidence scoring
  - Similar item matching
  - User acceptance tracking
  - Feedback loop for model improvement

#### BudgetAlert
- **Purpose**: Proactive budget monitoring
- **Key Features**:
  - Threshold-based alerting
  - Project and category-specific alerts
  - Severity levels
  - Acknowledgment tracking

## Query Patterns and Performance

### Common Query Patterns

1. **Project Summary Queries**
   ```sql
   -- Optimized with project_spending_summary view
   SELECT * FROM project_spending_summary WHERE id = ?
   ```

2. **Category Analysis**
   ```sql
   -- Optimized with category_spending_summary view
   SELECT * FROM category_spending_summary WHERE category = ?
   ```

3. **Natural Language Query Support**
   - Text-based searches using document content
   - Date range filtering with proper indexing
   - Amount-based filtering with numeric indexes
   - Vendor and project filtering with foreign key indexes

### Index Strategy

- **Primary Indexes**: All foreign keys, frequently filtered columns
- **Composite Indexes**: Date ranges, amount + category combinations
- **Text Indexes**: Vendor names, item descriptions for search
- **Performance Monitoring**: Query logs table tracks execution patterns

## Natural Language Query Integration

### Query Processing Flow

1. **Intent Recognition**: Classify query type (expense_search, project_summary, etc.)
2. **Entity Extraction**: Identify dates, amounts, categories, vendors, projects
3. **Filter Generation**: Convert entities to SQL WHERE clauses
4. **Result Aggregation**: Apply appropriate grouping and summarization
5. **Response Generation**: Format results for natural language response

### Supported Query Types

- **"How much did I spend on paint this summer?"**
  - Filters: category=paint_*, date range=summer months
  - Aggregation: SUM(line_total)
  - Response: Total amount + breakdown by subcategory

- **"What was the total cost for the master bath remodel?"**
  - Filters: project_name LIKE '%master bath%'
  - Aggregation: SUM(total_amount) by project
  - Response: Project total + budget comparison

- **"Show me all electrical expenses from June to August"**
  - Filters: category=electrical_*, date range=Jun-Aug
  - Response: Detailed line items + summary

## Data Validation and Integrity

### Validation Rules

1. **Financial Totals**: Line item totals must equal quantity × unit_price
2. **Budget Constraints**: Spending cannot exceed budget (with alerts)
3. **Date Consistency**: End dates must be after start dates
4. **Amount Constraints**: All monetary values must be non-negative
5. **Category Consistency**: Categories must match predefined enums

### Triggers and Constraints

- **Auto-vendor Creation**: Automatically create vendor records from document data
- **Timestamp Updates**: Maintain updated_at timestamps
- **Total Validation**: Prevent inconsistent line item calculations
- **Foreign Key Constraints**: Maintain referential integrity

## Integration with Existing Systems

### Document Service Integration

- **ChromaDB**: Financial metadata stored alongside document vectors
- **LlamaIndex**: Enhanced search with financial filters
- **OCR Processing**: Structured extraction into financial models

### API Layer

- **RESTful Endpoints**: Full CRUD operations for all entities
- **Bulk Operations**: Efficient batch processing for imports
- **Natural Language API**: Query endpoint with context understanding
- **Analytics API**: Pre-computed summaries and trends

## Performance Considerations

### Optimization Strategies

1. **View-Based Queries**: Pre-computed summaries for common analytics
2. **Strategic Indexing**: Cover most frequent query patterns
3. **Batch Processing**: Bulk operations for data imports and updates
4. **Caching Layer**: Redis/memory cache for frequently accessed data

### Scalability Features

1. **Partitioning Ready**: Date-based partitioning for large datasets
2. **Archive Strategy**: Move old documents to archive tables
3. **Read Replicas**: Separate read/write workloads
4. **Connection Pooling**: Efficient database connection management

## Usage Examples

### Creating a New Project
```python
project = Project(
    name="Master Bath Remodel",
    project_type=ProjectType.BATHROOM_REMODEL,
    budget=Decimal("15000.00"),
    start_date=date.today()
)
```

### Processing an Invoice
```python
# Document uploaded and OCR processed
financial_doc = FinancialDocument(
    document_id=document.id,
    document_type=DocumentType.INVOICE,
    vendor_name="Home Depot",
    total_amount=Decimal("524.99"),
    project_id=project.id,
    line_items=[
        LineItem(
            description="2x4 Lumber Stud 8ft",
            quantity=Decimal("20"),
            unit_price=Decimal("3.49"),
            line_total=Decimal("69.80"),
            category=ExpenseCategory.MATERIALS_LUMBER
        )
    ]
)
```

### Natural Language Query
```python
query = "How much have I spent on the kitchen remodel so far?"
response = await process_natural_language_query(query)
# Returns: ProjectAnalytics with spending breakdown
```

## Migration and Deployment

### Initial Setup
1. Run schema.sql to create all tables and indexes
2. Insert default expense categories
3. Set up triggers and views
4. Create initial admin/system records

### Data Migration
- Import existing expense data via CSV/Excel
- Map existing categories to new system
- Validate and clean imported data
- Run data quality checks

### Backup Strategy
- Daily full database backups
- Transaction log backups for point-in-time recovery
- Document file system backups
- ChromaDB vector store backups

This comprehensive design provides a robust foundation for the Penny expense tracking system, supporting both current requirements and future growth.