from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal
from .financial import ExpenseCategory, ProjectType, PaymentStatus


# API Models for Financial Endpoints
class NaturalLanguageQuery(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(..., description="Natural language query")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional filters")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold")
    max_results: int = Field(default=10, description="Maximum number of results to return")


class QueryResponse(BaseModel):
    """Response model for natural language queries"""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Natural language answer")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents")
    financial_summary: Dict[str, Any] = Field(default_factory=dict, description="Financial summary data")
    confidence_score: Optional[float] = Field(None, description="Confidence in the response")
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FinancialSummaryResponse(BaseModel):
    """Response model for financial summaries"""
    total_amount: float = Field(..., description="Total amount")
    document_count: int = Field(..., description="Number of documents")
    vendor_count: int = Field(..., description="Number of unique vendors")
    vendors: List[str] = Field(default_factory=list, description="List of vendors")
    categories: List[str] = Field(default_factory=list, description="List of categories")
    date_range: Dict[str, Optional[str]] = Field(default_factory=dict, description="Date range filters applied")
    filters: Dict[str, Optional[str]] = Field(default_factory=dict, description="Other filters applied")


class ExpenseQueryFilters(BaseModel):
    """Structured filters for expense queries"""
    categories: Optional[List[ExpenseCategory]] = Field(None, description="Expense categories to filter by")
    vendors: Optional[List[str]] = Field(None, description="Vendor names to filter by")
    projects: Optional[List[str]] = Field(None, description="Project names/IDs to filter by")
    start_date: Optional[date] = Field(None, description="Start date filter")
    end_date: Optional[date] = Field(None, description="End date filter")
    min_amount: Optional[float] = Field(None, description="Minimum amount filter")
    max_amount: Optional[float] = Field(None, description="Maximum amount filter")
    limit: int = Field(default=50, description="Maximum number of results")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


# Natural Language Query Models
class QueryContext(BaseModel):
    """Context for natural language queries"""
    query_text: str = Field(..., description="Original query text")
    intent: Literal["expense_search", "project_summary", "category_analysis", "time_analysis", "vendor_analysis"] = Field(..., description="Detected query intent")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities (dates, amounts, categories, etc.)")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Parsed filters for database query")
    confidence: float = Field(..., description="Confidence in query understanding (0-1)")


class ExpenseSummary(BaseModel):
    """Summary of expenses for a given query"""
    total_amount: Decimal = Field(..., description="Total amount for the query")
    item_count: int = Field(..., description="Number of items/transactions")
    date_range: Optional[Dict[str, date]] = Field(None, description="Date range of results")
    categories: Dict[str, Decimal] = Field(default_factory=dict, description="Amount by category")
    projects: Dict[str, Decimal] = Field(default_factory=dict, description="Amount by project")
    vendors: Dict[str, Decimal] = Field(default_factory=dict, description="Amount by vendor")
    payment_methods: Dict[str, Decimal] = Field(default_factory=dict, description="Amount by payment method")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat()
        }


class ProjectAnalytics(BaseModel):
    """Detailed analytics for a project"""
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    project_type: ProjectType = Field(..., description="Project type")
    
    # Financial metrics
    total_spent: Decimal = Field(..., description="Total amount spent")
    budget: Optional[Decimal] = Field(None, description="Project budget")
    budget_remaining: Optional[Decimal] = Field(None, description="Remaining budget")
    budget_utilization: Optional[float] = Field(None, description="Percentage of budget used")
    
    # Time metrics
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")
    duration_days: Optional[int] = Field(None, description="Project duration in days")
    
    # Expense breakdown
    category_breakdown: Dict[str, Decimal] = Field(default_factory=dict, description="Spending by category")
    vendor_breakdown: Dict[str, Decimal] = Field(default_factory=dict, description="Spending by vendor")
    monthly_spending: Dict[str, Decimal] = Field(default_factory=dict, description="Spending by month")
    
    # Document metrics
    total_documents: int = Field(default=0, description="Number of documents")
    total_line_items: int = Field(default=0, description="Number of line items")
    
    # Status
    completion_status: Literal["planning", "in_progress", "completed", "on_hold"] = Field(..., description="Project status")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat()
        }


class CategoryAnalytics(BaseModel):
    """Analytics for expense categories"""
    category: ExpenseCategory = Field(..., description="Expense category")
    total_spent: Decimal = Field(..., description="Total spent in category")
    transaction_count: int = Field(..., description="Number of transactions")
    average_transaction: Decimal = Field(..., description="Average transaction amount")
    
    # Time analysis
    spending_by_month: Dict[str, Decimal] = Field(default_factory=dict, description="Monthly spending")
    spending_trend: Literal["increasing", "decreasing", "stable"] = Field(..., description="Spending trend")
    
    # Project distribution
    project_distribution: Dict[str, Decimal] = Field(default_factory=dict, description="Spending by project")
    
    # Vendor analysis
    top_vendors: List[Dict[str, Any]] = Field(default_factory=list, description="Top vendors for this category")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class VendorAnalytics(BaseModel):
    """Analytics for vendors"""
    vendor_id: str = Field(..., description="Vendor ID")
    vendor_name: str = Field(..., description="Vendor name")
    
    # Financial metrics
    total_spent: Decimal = Field(..., description="Total spent with vendor")
    transaction_count: int = Field(..., description="Number of transactions")
    average_transaction: Decimal = Field(..., description="Average transaction amount")
    
    # Time analysis
    first_transaction: Optional[date] = Field(None, description="Date of first transaction")
    last_transaction: Optional[date] = Field(None, description="Date of last transaction")
    spending_by_month: Dict[str, Decimal] = Field(default_factory=dict, description="Monthly spending")
    
    # Category analysis
    category_breakdown: Dict[str, Decimal] = Field(default_factory=dict, description="Spending by category")
    
    # Project analysis
    project_breakdown: Dict[str, Decimal] = Field(default_factory=dict, description="Spending by project")
    
    # Payment analysis
    payment_methods: Dict[str, int] = Field(default_factory=dict, description="Payment method usage")
    payment_status_summary: Dict[str, int] = Field(default_factory=dict, description="Payment status summary")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat()
        }


class TimeAnalytics(BaseModel):
    """Time-based spending analytics"""
    period: Literal["daily", "weekly", "monthly", "quarterly", "yearly"] = Field(..., description="Time period")
    start_date: date = Field(..., description="Start date of analysis")
    end_date: date = Field(..., description="End date of analysis")
    
    # Spending data
    spending_by_period: Dict[str, Decimal] = Field(default_factory=dict, description="Spending per time period")
    total_spending: Decimal = Field(..., description="Total spending in time range")
    average_per_period: Decimal = Field(..., description="Average spending per period")
    
    # Trends
    trend: Literal["increasing", "decreasing", "stable"] = Field(..., description="Overall trend")
    peak_period: Optional[str] = Field(None, description="Period with highest spending")
    peak_amount: Optional[Decimal] = Field(None, description="Highest spending amount")
    
    # Category breakdown
    category_trends: Dict[str, Dict[str, Decimal]] = Field(default_factory=dict, description="Category spending by period")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat()
        }


class NaturalLanguageResponse(BaseModel):
    """Response model for natural language queries"""
    query: str = Field(..., description="Original query")
    query_context: QueryContext = Field(..., description="Parsed query context")
    
    # Response data
    summary: ExpenseSummary = Field(..., description="Summary of results")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed results")
    
    # Analytics (optional, based on query type)
    project_analytics: Optional[List[ProjectAnalytics]] = Field(None, description="Project analytics if requested")
    category_analytics: Optional[List[CategoryAnalytics]] = Field(None, description="Category analytics if requested")
    vendor_analytics: Optional[List[VendorAnalytics]] = Field(None, description="Vendor analytics if requested")
    time_analytics: Optional[TimeAnalytics] = Field(None, description="Time analytics if requested")
    
    # Natural language response
    natural_response: str = Field(..., description="Human-readable response")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up query suggestions")
    
    # Metadata
    confidence: float = Field(..., description="Confidence in response (0-1)")
    execution_time: float = Field(..., description="Query execution time in seconds")
    data_points: int = Field(..., description="Number of data points analyzed")
    
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Expense Tracking and Categorization Models
class AutoCategorizationRule(BaseModel):
    """Rules for automatically categorizing expenses"""
    id: str = Field(..., description="Rule ID")
    name: str = Field(..., description="Rule name")
    
    # Matching criteria
    vendor_patterns: List[str] = Field(default_factory=list, description="Vendor name patterns")
    description_patterns: List[str] = Field(default_factory=list, description="Description patterns")
    amount_range: Optional[Dict[str, Decimal]] = Field(None, description="Amount range (min/max)")
    
    # Assignment
    category: ExpenseCategory = Field(..., description="Category to assign")
    subcategory: Optional[str] = Field(None, description="Subcategory to assign")
    project_id: Optional[str] = Field(None, description="Project to assign")
    
    # Rule metadata
    priority: int = Field(default=0, description="Rule priority (higher = more important)")
    is_active: bool = Field(default=True, description="Whether rule is active")
    confidence_threshold: float = Field(default=0.8, description="Minimum confidence to apply rule")
    
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = Field(None, description="When rule was last applied")
    usage_count: int = Field(default=0, description="How many times rule has been applied")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class CategorizationSuggestion(BaseModel):
    """AI-generated categorization suggestion"""
    line_item_id: str = Field(..., description="Line item ID")
    suggested_category: ExpenseCategory = Field(..., description="Suggested category")
    suggested_subcategory: Optional[str] = Field(None, description="Suggested subcategory")
    suggested_project_id: Optional[str] = Field(None, description="Suggested project")
    
    confidence: float = Field(..., description="Confidence in suggestion (0-1)")
    reasoning: str = Field(..., description="Explanation for suggestion")
    similar_items: List[str] = Field(default_factory=list, description="IDs of similar previously categorized items")
    
    # User feedback
    accepted: Optional[bool] = Field(None, description="Whether user accepted suggestion")
    user_category: Optional[ExpenseCategory] = Field(None, description="User's chosen category if different")
    feedback_notes: Optional[str] = Field(None, description="User feedback on suggestion")
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BudgetAlert(BaseModel):
    """Budget tracking and alerts"""
    id: str = Field(..., description="Alert ID")
    project_id: Optional[str] = Field(None, description="Project ID (if project-specific)")
    category: Optional[ExpenseCategory] = Field(None, description="Category (if category-specific)")
    
    # Alert configuration
    alert_type: Literal["budget_exceeded", "budget_warning", "unusual_spending", "payment_due"] = Field(..., description="Type of alert")
    threshold_percentage: Optional[float] = Field(None, description="Threshold percentage for budget alerts")
    threshold_amount: Optional[Decimal] = Field(None, description="Threshold amount for spending alerts")
    
    # Alert data
    current_amount: Decimal = Field(..., description="Current spending amount")
    budget_amount: Optional[Decimal] = Field(None, description="Budget amount")
    percentage_used: Optional[float] = Field(None, description="Percentage of budget used")
    
    # Alert status
    is_active: bool = Field(default=True, description="Whether alert is active")
    is_acknowledged: bool = Field(default=False, description="Whether user has acknowledged")
    
    # Metadata
    message: str = Field(..., description="Alert message")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Alert severity")
    
    created_at: datetime = Field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# Reporting Models
class ReportParameters(BaseModel):
    """Parameters for generating reports"""
    report_type: Literal["project_summary", "category_breakdown", "vendor_analysis", "time_series", "budget_status"] = Field(..., description="Type of report")
    
    # Date filters
    start_date: Optional[date] = Field(None, description="Start date filter")
    end_date: Optional[date] = Field(None, description="End date filter")
    
    # Entity filters
    project_ids: List[str] = Field(default_factory=list, description="Project IDs to include")
    categories: List[ExpenseCategory] = Field(default_factory=list, description="Categories to include")
    vendor_ids: List[str] = Field(default_factory=list, description="Vendor IDs to include")
    
    # Report options
    include_details: bool = Field(default=False, description="Include detailed line items")
    group_by: Optional[Literal["project", "category", "vendor", "month", "quarter"]] = Field(None, description="Grouping option")
    sort_by: Optional[Literal["amount", "date", "category", "vendor"]] = Field("amount", description="Sort option")
    sort_descending: bool = Field(default=True, description="Sort order")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class ReportData(BaseModel):
    """Generated report data"""
    report_id: str = Field(..., description="Report ID")
    parameters: ReportParameters = Field(..., description="Report parameters")
    
    # Summary data
    total_amount: Decimal = Field(..., description="Total amount in report")
    item_count: int = Field(..., description="Number of items")
    date_range: Dict[str, date] = Field(..., description="Actual date range of data")
    
    # Report sections
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary section")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="Detail records")
    charts: List[Dict[str, Any]] = Field(default_factory=list, description="Chart data")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    generated_by: Optional[str] = Field(None, description="User who generated report")
    execution_time: float = Field(..., description="Report generation time in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }