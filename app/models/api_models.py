from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from .financial import (
    ExpenseCategory, ProjectType, PaymentMethod, PaymentStatus, DocumentType,
    Vendor, Project, FinancialDocument, LineItem, PaymentInfo
)
from .analytics import (
    ExpenseSummary, ProjectAnalytics, CategoryAnalytics, VendorAnalytics,
    NaturalLanguageResponse, ReportParameters, ReportData
)


# API Request Models
class VendorCreateRequest(BaseModel):
    """Request model for creating vendors"""
    name: str = Field(..., description="Business name of the vendor")
    address: Optional[str] = Field(None, description="Business address")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    tax_id: Optional[str] = Field(None, description="Tax ID or EIN")
    notes: Optional[str] = Field(None, description="Additional notes about vendor")


class VendorUpdateRequest(BaseModel):
    """Request model for updating vendors"""
    name: Optional[str] = Field(None, description="Business name of the vendor")
    address: Optional[str] = Field(None, description="Business address")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    tax_id: Optional[str] = Field(None, description="Tax ID or EIN")
    notes: Optional[str] = Field(None, description="Additional notes about vendor")


class ProjectCreateRequest(BaseModel):
    """Request model for creating projects"""
    name: str = Field(..., description="Project name")
    project_type: ProjectType = Field(..., description="Type of renovation project")
    description: Optional[str] = Field(None, description="Detailed project description")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project completion date")
    budget: Optional[Decimal] = Field(None, description="Total project budget")
    location: Optional[str] = Field(None, description="Location within home")
    notes: Optional[str] = Field(None, description="Project notes and updates")

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class ProjectUpdateRequest(BaseModel):
    """Request model for updating projects"""
    name: Optional[str] = Field(None, description="Project name")
    project_type: Optional[ProjectType] = Field(None, description="Type of renovation project")
    description: Optional[str] = Field(None, description="Detailed project description")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project completion date")
    budget: Optional[Decimal] = Field(None, description="Total project budget")
    location: Optional[str] = Field(None, description="Location within home")
    status: Optional[str] = Field(None, description="Project status")
    notes: Optional[str] = Field(None, description="Project notes and updates")

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class LineItemCreateRequest(BaseModel):
    """Request model for creating line items"""
    description: str = Field(..., description="Item description")
    quantity: Decimal = Field(..., description="Quantity ordered/purchased")
    unit_price: Decimal = Field(..., description="Price per unit")
    unit_of_measure: Optional[str] = Field(None, description="Unit (each, sqft, lbs, etc.)")
    category: Optional[ExpenseCategory] = Field(None, description="Expense category")
    subcategory: Optional[str] = Field(None, description="Custom subcategory")
    product_code: Optional[str] = Field(None, description="SKU or product code")
    brand: Optional[str] = Field(None, description="Brand name")
    model: Optional[str] = Field(None, description="Model number")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class FinancialDocumentCreateRequest(BaseModel):
    """Request model for creating financial documents"""
    document_id: str = Field(..., description="Reference to base document ID")
    document_type: DocumentType = Field(..., description="Type of financial document")
    vendor_name: str = Field(..., description="Vendor/supplier name")
    invoice_date: Optional[date] = Field(None, description="Date on the document")
    total_amount: Decimal = Field(..., description="Total amount of the document")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    
    # Optional detailed information
    vendor_address: Optional[str] = Field(None, description="Vendor address")
    vendor_phone: Optional[str] = Field(None, description="Vendor phone")
    vendor_email: Optional[str] = Field(None, description="Vendor email")
    invoice_number: Optional[str] = Field(None, description="Invoice/receipt number")
    subtotal: Optional[Decimal] = Field(None, description="Subtotal before tax")
    total_tax: Optional[Decimal] = Field(None, description="Total tax amount")
    
    line_items: List[LineItemCreateRequest] = Field(default_factory=list, description="Line items")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class PaymentInfoCreateRequest(BaseModel):
    """Request model for creating payment information"""
    payment_method: Optional[PaymentMethod] = Field(None, description="How payment was made")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Payment status")
    due_date: Optional[date] = Field(None, description="Payment due date")
    paid_date: Optional[date] = Field(None, description="Date payment was made")
    paid_amount: Optional[Decimal] = Field(None, description="Amount actually paid")
    payment_reference: Optional[str] = Field(None, description="Check number, transaction ID, etc.")
    discount_amount: Optional[Decimal] = Field(None, description="Any discount applied")
    late_fee: Optional[Decimal] = Field(None, description="Late fees applied")
    notes: Optional[str] = Field(None, description="Payment notes")

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# API Response Models
class VendorResponse(Vendor):
    """Response model for vendor data"""
    total_spent: Optional[Decimal] = Field(None, description="Total amount spent with vendor")
    transaction_count: Optional[int] = Field(None, description="Number of transactions")
    last_transaction_date: Optional[date] = Field(None, description="Date of last transaction")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class ProjectResponse(Project):
    """Response model for project data"""
    total_spent: Optional[Decimal] = Field(None, description="Total amount spent on project")
    document_count: Optional[int] = Field(None, description="Number of documents")
    budget_remaining: Optional[Decimal] = Field(None, description="Remaining budget")
    budget_utilization: Optional[float] = Field(None, description="Percentage of budget used")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class FinancialDocumentResponse(FinancialDocument):
    """Response model for financial document data"""
    vendor: Optional[VendorResponse] = Field(None, description="Vendor information")
    project: Optional[ProjectResponse] = Field(None, description="Project information")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# Query and Filter Models
class ExpenseQueryFilters(BaseModel):
    """Filters for expense queries"""
    start_date: Optional[date] = Field(None, description="Start date filter")
    end_date: Optional[date] = Field(None, description="End date filter")
    project_ids: List[str] = Field(default_factory=list, description="Project IDs to include")
    vendor_ids: List[str] = Field(default_factory=list, description="Vendor IDs to include")
    categories: List[ExpenseCategory] = Field(default_factory=list, description="Categories to include")
    min_amount: Optional[Decimal] = Field(None, description="Minimum amount filter")
    max_amount: Optional[Decimal] = Field(None, description="Maximum amount filter")
    payment_status: Optional[PaymentStatus] = Field(None, description="Payment status filter")
    document_types: List[DocumentType] = Field(default_factory=list, description="Document types to include")
    tags: List[str] = Field(default_factory=list, description="Tags to filter by")

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class NaturalLanguageQueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    include_suggestions: bool = Field(default=True, description="Include follow-up suggestions")
    max_results: int = Field(default=10, description="Maximum number of results")


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations"""
    operation: str = Field(..., description="Operation type (categorize, assign_project, update_payment_status)")
    filters: ExpenseQueryFilters = Field(..., description="Filters to select items")
    updates: Dict[str, Any] = Field(..., description="Updates to apply")


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations"""
    operation: str = Field(..., description="Operation type")
    items_processed: int = Field(..., description="Number of items processed")
    items_updated: int = Field(..., description="Number of items successfully updated")
    items_failed: int = Field(..., description="Number of items that failed")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    execution_time: float = Field(..., description="Operation execution time in seconds")


# Dashboard and Analytics Models
class DashboardSummary(BaseModel):
    """Dashboard summary data"""
    total_projects: int = Field(..., description="Total number of projects")
    active_projects: int = Field(..., description="Number of active projects")
    total_spent_all_time: Decimal = Field(..., description="Total amount spent across all projects")
    total_spent_this_month: Decimal = Field(..., description="Total spent this month")
    total_spent_this_year: Decimal = Field(..., description="Total spent this year")
    
    # Recent activity
    recent_documents: int = Field(..., description="Documents uploaded in last 30 days")
    pending_payments: int = Field(..., description="Number of pending payments")
    overdue_payments: int = Field(..., description="Number of overdue payments")
    
    # Budget information
    total_budgets: Decimal = Field(..., description="Sum of all project budgets")
    budget_utilization: float = Field(..., description="Overall budget utilization percentage")
    projects_over_budget: int = Field(..., description="Number of projects over budget")
    
    # Top categories this month
    top_categories: List[Dict[str, Any]] = Field(default_factory=list, description="Top spending categories")
    top_vendors: List[Dict[str, Any]] = Field(default_factory=list, description="Top vendors by spending")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class CategorySpendingTrend(BaseModel):
    """Category spending trend data"""
    category: ExpenseCategory = Field(..., description="Expense category")
    monthly_data: List[Dict[str, Any]] = Field(..., description="Monthly spending data")
    trend: str = Field(..., description="Trend direction (increasing, decreasing, stable)")
    total_amount: Decimal = Field(..., description="Total amount for the period")
    percentage_change: float = Field(..., description="Percentage change from previous period")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class ProjectProgressUpdate(BaseModel):
    """Project progress update model"""
    project_id: str = Field(..., description="Project ID")
    status_update: Optional[str] = Field(None, description="Status update")
    budget_adjustment: Optional[Decimal] = Field(None, description="Budget adjustment amount")
    completion_percentage: Optional[int] = Field(None, description="Completion percentage (0-100)")
    notes: Optional[str] = Field(None, description="Progress notes")
    milestone_reached: Optional[str] = Field(None, description="Milestone description")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


# Import/Export Models
class ImportRequest(BaseModel):
    """Request model for importing data"""
    import_type: str = Field(..., description="Type of import (csv, excel, json)")
    file_path: str = Field(..., description="Path to import file")
    mapping: Dict[str, str] = Field(..., description="Field mapping configuration")
    options: Dict[str, Any] = Field(default_factory=dict, description="Import options")


class ImportResponse(BaseModel):
    """Response model for import operations"""
    import_id: str = Field(..., description="Import operation ID")
    records_processed: int = Field(..., description="Number of records processed")
    records_imported: int = Field(..., description="Number of records successfully imported")
    records_failed: int = Field(..., description="Number of records that failed")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Import errors")
    warnings: List[str] = Field(default_factory=list, description="Import warnings")
    execution_time: float = Field(..., description="Import execution time in seconds")


class ExportRequest(BaseModel):
    """Request model for exporting data"""
    export_type: str = Field(..., description="Type of export (csv, excel, json, pdf)")
    data_type: str = Field(..., description="Type of data to export (expenses, projects, vendors)")
    filters: ExpenseQueryFilters = Field(..., description="Filters for export")
    include_details: bool = Field(default=True, description="Include detailed data")
    format_options: Dict[str, Any] = Field(default_factory=dict, description="Format-specific options")


class ExportResponse(BaseModel):
    """Response model for export operations"""
    export_id: str = Field(..., description="Export operation ID")
    file_path: str = Field(..., description="Path to exported file")
    file_size: int = Field(..., description="Size of exported file in bytes")
    records_exported: int = Field(..., description="Number of records exported")
    execution_time: float = Field(..., description="Export execution time in seconds")


# WebSocket Chat Models
class ChatMessage(BaseModel):
    """WebSocket chat message model"""
    type: str = Field(..., description="Message type (user_message, ai_response, error, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatRequest(BaseModel):
    """WebSocket chat request model"""
    message: str = Field(..., description="User's chat message/question")
    session_id: Optional[str] = Field(None, description="Chat session ID for context")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    llm_provider: Optional[str] = Field(None, description="LLM provider to use (openai or claude)")
    
    
class ChatResponse(BaseModel):
    """WebSocket chat response model"""
    type: str = Field(default="ai_response", description="Response type")
    answer: str = Field(..., description="AI response to the user's question")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents")
    financial_summary: Optional[Dict[str, Any]] = Field(None, description="Financial data summary")
    llm_provider: Optional[str] = Field(None, description="LLM provider used")
    model_used: Optional[str] = Field(None, description="Model used for generation")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")
    session_id: Optional[str] = Field(None, description="Chat session ID")


class ChatError(BaseModel):
    """WebSocket chat error model"""
    type: str = Field(default="error", description="Message type")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")
    session_id: Optional[str] = Field(None, description="Chat session ID")