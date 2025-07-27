from pydantic import BaseModel, Field, validator, field_validator
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal
from enum import Enum
import uuid


# Enums for predefined categories
class ExpenseCategory(str, Enum):
    """Main expense categories for home renovation projects"""
    MATERIALS_LUMBER = "materials_lumber"
    MATERIALS_CONCRETE = "materials_concrete"
    MATERIALS_STEEL = "materials_steel"
    MATERIALS_STONE = "materials_stone"
    MATERIALS_TILE = "materials_tile"
    MATERIALS_FLOORING = "materials_flooring"
    MATERIALS_INSULATION = "materials_insulation"
    MATERIALS_ROOFING = "materials_roofing"
    MATERIALS_SIDING = "materials_siding"
    MATERIALS_WINDOWS = "materials_windows"
    MATERIALS_DOORS = "materials_doors"
    PAINT_INTERIOR = "paint_interior"
    PAINT_EXTERIOR = "paint_exterior"
    PAINT_SUPPLIES = "paint_supplies"
    ELECTRICAL_FIXTURES = "electrical_fixtures"
    ELECTRICAL_WIRING = "electrical_wiring"
    ELECTRICAL_OUTLETS = "electrical_outlets"
    PLUMBING_FIXTURES = "plumbing_fixtures"
    PLUMBING_PIPES = "plumbing_pipes"
    PLUMBING_FITTINGS = "plumbing_fittings"
    HVAC_UNITS = "hvac_units"
    HVAC_DUCTWORK = "hvac_ductwork"
    HVAC_MAINTENANCE = "hvac_maintenance"
    APPLIANCES_KITCHEN = "appliances_kitchen"
    APPLIANCES_LAUNDRY = "appliances_laundry"
    APPLIANCES_OTHER = "appliances_other"
    TOOLS_POWER = "tools_power"
    TOOLS_HAND = "tools_hand"
    TOOLS_RENTAL = "tools_rental"
    LABOR_CONTRACTOR = "labor_contractor"
    LABOR_ELECTRICIAN = "labor_electrician"
    LABOR_PLUMBER = "labor_plumber"
    LABOR_HVAC = "labor_hvac"
    LABOR_PAINTER = "labor_painter"
    LABOR_FLOORING = "labor_flooring"
    LABOR_GENERAL = "labor_general"
    PERMITS_BUILDING = "permits_building"
    PERMITS_ELECTRICAL = "permits_electrical"
    PERMITS_PLUMBING = "permits_plumbing"
    DELIVERY_MATERIALS = "delivery_materials"
    DELIVERY_APPLIANCES = "delivery_appliances"
    WASTE_DISPOSAL = "waste_disposal"
    MISCELLANEOUS = "miscellaneous"


class ProjectType(str, Enum):
    """Types of home renovation projects"""
    KITCHEN_REMODEL = "kitchen_remodel"
    BATHROOM_REMODEL = "bathroom_remodel"
    BASEMENT_RENOVATION = "basement_renovation"
    ADDITION = "addition"
    ROOF_REPLACEMENT = "roof_replacement"
    FLOORING = "flooring"
    PAINTING = "painting"
    ELECTRICAL_UPGRADE = "electrical_upgrade"
    PLUMBING_UPGRADE = "plumbing_upgrade"
    HVAC_INSTALLATION = "hvac_installation"
    SIDING_REPLACEMENT = "siding_replacement"
    WINDOW_REPLACEMENT = "window_replacement"
    DECK_CONSTRUCTION = "deck_construction"
    DRIVEWAY = "driveway"
    LANDSCAPING = "landscaping"
    GENERAL_MAINTENANCE = "general_maintenance"
    OTHER = "other"


class PaymentMethod(str, Enum):
    """Payment methods for expenses"""
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    FINANCING = "financing"
    STORE_CREDIT = "store_credit"
    OTHER = "other"


class PaymentStatus(str, Enum):
    """Payment status for invoices"""
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """Types of financial documents"""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    ESTIMATE = "estimate"
    CONTRACT = "contract"
    PURCHASE_ORDER = "purchase_order"
    WARRANTY = "warranty"
    OTHER = "other"


# Core Entity Models
class Vendor(BaseModel):
    """Vendor/Supplier information"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Business name of the vendor")
    address: Optional[str] = Field(None, description="Business address")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    tax_id: Optional[str] = Field(None, description="Tax ID or EIN")
    notes: Optional[str] = Field(None, description="Additional notes about vendor")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Project(BaseModel):
    """Home renovation project information"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Project name (e.g., 'Master Bath Remodel')")
    project_type: ProjectType = Field(..., description="Type of renovation project")
    description: Optional[str] = Field(None, description="Detailed project description")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project completion date")
    budget: Optional[Decimal] = Field(None, description="Total project budget")
    location: Optional[str] = Field(None, description="Location within home (e.g., 'master bedroom', 'kitchen')")
    status: Literal["planning", "in_progress", "completed", "on_hold"] = Field(default="planning")
    notes: Optional[str] = Field(None, description="Project notes and updates")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator('budget')
    def validate_budget(cls, v):
        if v is not None and v < 0:
            raise ValueError('Budget must be non-negative')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class ExpenseCategoryMapping(BaseModel):
    """Mapping of expense categories with hierarchy support"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: ExpenseCategory = Field(..., description="Primary expense category")
    subcategory: Optional[str] = Field(None, description="Custom subcategory")
    description: Optional[str] = Field(None, description="Category description")
    keywords: List[str] = Field(default_factory=list, description="Keywords for auto-categorization")
    is_active: bool = Field(default=True, description="Whether category is active")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Financial Document Models
class TaxInfo(BaseModel):
    """Tax information for invoices and line items"""
    tax_rate: Optional[Decimal] = Field(None, description="Tax rate as decimal (e.g., 0.0875 for 8.75%)")
    tax_amount: Optional[Decimal] = Field(None, description="Tax amount in dollars")
    tax_type: Optional[str] = Field(None, description="Type of tax (sales, VAT, etc.)")
    tax_exempt: bool = Field(default=False, description="Whether item is tax exempt")

    @field_validator('tax_rate')
    def validate_tax_rate(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Tax rate must be between 0 and 1')
        return v

    @field_validator('tax_amount')
    def validate_tax_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('Tax amount must be non-negative')
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class LineItem(BaseModel):
    """Individual line item within an invoice or receipt"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(..., description="Item description")
    quantity: Decimal = Field(..., description="Quantity ordered/purchased")
    unit_price: Decimal = Field(..., description="Price per unit")
    unit_of_measure: Optional[str] = Field(None, description="Unit (each, sqft, lbs, etc.)")
    line_total: Decimal = Field(..., description="Total for this line (quantity * unit_price)")
    category: Optional[ExpenseCategory] = Field(None, description="Expense category")
    subcategory: Optional[str] = Field(None, description="Custom subcategory")
    product_code: Optional[str] = Field(None, description="SKU or product code")
    brand: Optional[str] = Field(None, description="Brand name")
    model: Optional[str] = Field(None, description="Model number")
    tax_info: Optional[TaxInfo] = Field(None, description="Tax information for this line item")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator('quantity', 'unit_price', 'line_total')
    def validate_positive_numbers(cls, v):
        if v < 0:
            raise ValueError('Values must be non-negative')
        return v

    @field_validator('line_total')
    def validate_line_total(cls, v, info):
        if info.data and 'quantity' in info.data and 'unit_price' in info.data:
            expected_total = info.data['quantity'] * info.data['unit_price']
            # Allow small rounding differences
            if abs(v - expected_total) > Decimal('0.01'):
                raise ValueError('Line total must equal quantity * unit_price')
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PaymentInfo(BaseModel):
    """Payment information for invoices"""
    payment_method: Optional[PaymentMethod] = Field(None, description="How payment was made")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Payment status")
    due_date: Optional[date] = Field(None, description="Payment due date")
    paid_date: Optional[date] = Field(None, description="Date payment was made")
    paid_amount: Optional[Decimal] = Field(None, description="Amount actually paid")
    payment_reference: Optional[str] = Field(None, description="Check number, transaction ID, etc.")
    discount_amount: Optional[Decimal] = Field(None, description="Any discount applied")
    late_fee: Optional[Decimal] = Field(None, description="Late fees applied")
    notes: Optional[str] = Field(None, description="Payment notes")

    @field_validator('paid_amount', 'discount_amount', 'late_fee')
    def validate_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Amounts must be non-negative')
        return v

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class FinancialDocument(BaseModel):
    """Enhanced financial document model that extends the basic document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = Field(..., description="Reference to base DocumentResponse ID")
    
    # Document classification
    document_type: DocumentType = Field(..., description="Type of financial document")
    
    # Vendor information
    vendor_id: Optional[str] = Field(None, description="Reference to Vendor ID")
    vendor_name: str = Field(..., description="Vendor/supplier name from document")
    vendor_address: Optional[str] = Field(None, description="Vendor address from document")
    vendor_phone: Optional[str] = Field(None, description="Vendor phone from document")
    vendor_email: Optional[str] = Field(None, description="Vendor email from document")
    vendor_tax_id: Optional[str] = Field(None, description="Vendor tax ID from document")
    
    # Document details
    invoice_number: Optional[str] = Field(None, description="Invoice/receipt number")
    invoice_date: Optional[date] = Field(None, description="Date on the document")
    purchase_order_number: Optional[str] = Field(None, description="PO number if applicable")
    
    # Financial totals
    subtotal: Optional[Decimal] = Field(None, description="Subtotal before tax")
    total_tax: Optional[Decimal] = Field(None, description="Total tax amount")
    total_amount: Decimal = Field(..., description="Total amount of the document")
    currency: str = Field(default="USD", description="Currency code")
    
    # Line items
    line_items: List[LineItem] = Field(default_factory=list, description="Individual line items")
    
    # Project association
    project_id: Optional[str] = Field(None, description="Associated project ID")
    
    # Payment information
    payment_info: Optional[PaymentInfo] = Field(None, description="Payment details")
    
    # Additional metadata
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    
    # Processing metadata
    extracted_at: datetime = Field(default_factory=datetime.now, description="When data was extracted")
    confidence_score: Optional[float] = Field(None, description="OCR/extraction confidence (0-1)")
    manually_verified: bool = Field(default=False, description="Whether manually verified")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator('total_amount')
    def validate_total_amount(cls, v):
        if v < 0:
            raise ValueError('Total amount must be non-negative')
        return v

    @field_validator('confidence_score')
    def validate_confidence_score(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Confidence score must be between 0 and 1')
        return v

    @property
    def calculated_total(self) -> Decimal:
        """Calculate total from line items"""
        return sum(item.line_total for item in self.line_items)

    @property
    def calculated_tax(self) -> Decimal:
        """Calculate total tax from line items"""
        return sum(item.tax_info.tax_amount or Decimal('0') for item in self.line_items if item.tax_info)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# Request/Response Models for API
class FinancialDocumentCreate(BaseModel):
    """Request model for creating financial documents"""
    document_id: str
    document_type: DocumentType
    vendor_name: str
    invoice_date: Optional[date] = None
    total_amount: Decimal
    project_id: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    payment_info: Optional[PaymentInfo] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class FinancialDocumentUpdate(BaseModel):
    """Request model for updating financial documents"""
    document_type: Optional[DocumentType] = None
    vendor_name: Optional[str] = None
    invoice_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    project_id: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    payment_info: Optional[PaymentInfo] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    manually_verified: Optional[bool] = None

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }