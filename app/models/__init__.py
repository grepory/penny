# Models package

# Base document models
from .document import (
    DocumentUpload,
    DocumentResponse,
    DocumentQuery,
    SearchResult,
    FinancialSearchQuery,
    DocumentProcessingResult
)

# Financial models
from .financial import (
    # Enums
    ExpenseCategory,
    ProjectType,
    PaymentMethod,
    PaymentStatus,
    DocumentType,
    
    # Core entities
    Vendor,
    Project,
    ExpenseCategoryMapping,
    
    # Financial document models
    TaxInfo,
    LineItem,
    PaymentInfo,
    FinancialDocument,
    FinancialDocumentCreate,
    FinancialDocumentUpdate
)

# Analytics models
from .analytics import (
    # Query models
    QueryContext,
    ExpenseSummary,
    ProjectAnalytics,
    CategoryAnalytics,
    VendorAnalytics,
    TimeAnalytics,
    NaturalLanguageResponse,
    
    # Categorization models
    AutoCategorizationRule,
    CategorizationSuggestion,
    BudgetAlert,
    
    # Reporting models
    ReportParameters,
    ReportData
)

# API models
from .api_models import (
    # Request models
    VendorCreateRequest,
    VendorUpdateRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    LineItemCreateRequest,
    FinancialDocumentCreateRequest,
    PaymentInfoCreateRequest,
    
    # Response models
    VendorResponse,
    ProjectResponse,
    FinancialDocumentResponse,
    
    # Query models
    ExpenseQueryFilters,
    NaturalLanguageQueryRequest,
    BulkOperationRequest,
    BulkOperationResponse,
    
    # Dashboard models
    DashboardSummary,
    CategorySpendingTrend,
    ProjectProgressUpdate,
    
    # Import/Export models
    ImportRequest,
    ImportResponse,
    ExportRequest,
    ExportResponse
)

__all__ = [
    # Document models
    "DocumentUpload",
    "DocumentResponse", 
    "DocumentQuery",
    "SearchResult",
    "FinancialSearchQuery",
    "DocumentProcessingResult",
    
    # Financial enums
    "ExpenseCategory",
    "ProjectType", 
    "PaymentMethod",
    "PaymentStatus",
    "DocumentType",
    
    # Financial entities
    "Vendor",
    "Project",
    "ExpenseCategoryMapping",
    "TaxInfo",
    "LineItem",
    "PaymentInfo",
    "FinancialDocument",
    "FinancialDocumentCreate",
    "FinancialDocumentUpdate",
    
    # Analytics
    "QueryContext",
    "ExpenseSummary",
    "ProjectAnalytics", 
    "CategoryAnalytics",
    "VendorAnalytics",
    "TimeAnalytics",
    "NaturalLanguageResponse",
    "AutoCategorizationRule",
    "CategorizationSuggestion",
    "BudgetAlert",
    "ReportParameters",
    "ReportData",
    
    # API models
    "VendorCreateRequest",
    "VendorUpdateRequest",
    "ProjectCreateRequest", 
    "ProjectUpdateRequest",
    "LineItemCreateRequest",
    "FinancialDocumentCreateRequest",
    "PaymentInfoCreateRequest",
    "VendorResponse",
    "ProjectResponse",
    "FinancialDocumentResponse",
    "ExpenseQueryFilters",
    "NaturalLanguageQueryRequest",
    "BulkOperationRequest",
    "BulkOperationResponse",
    "DashboardSummary",
    "CategorySpendingTrend",
    "ProjectProgressUpdate",
    "ImportRequest",
    "ImportResponse",
    "ExportRequest",
    "ExportResponse"
]