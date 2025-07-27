from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.document_service import DocumentService
from app.models.analytics import (
    NaturalLanguageQuery, QueryResponse, FinancialSummaryResponse,
    ExpenseQueryFilters
)

router = APIRouter(prefix="/financial", tags=["financial"])

# Initialize document service
document_service = DocumentService()

@router.post("/query", response_model=QueryResponse)
async def natural_language_query(query_request: NaturalLanguageQuery):
    """
    Process natural language queries about financial data
    Examples:
    - "How much did I spend on paint this summer?"
    - "What was the total cost for the master bath remodel?"
    - "Show me all electrical expenses from June to August"
    """
    try:
        result = await document_service.query_financial_data(
            query_request.query,
            query_request.filters
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return QueryResponse(
            query=query_request.query,
            answer=result["answer"],
            sources=result["sources"],
            financial_summary=result["financial_summary"],
            confidence_score=query_request.confidence_threshold
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    project: Optional[str] = Query(None, description="Project name filter"),
    category: Optional[str] = Query(None, description="Expense category filter")
):
    """
    Get financial summary with optional filters
    """
    try:
        result = await document_service.get_financial_summary(
            start_date=start_date,
            end_date=end_date,
            project=project,
            category=category
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return FinancialSummaryResponse(
            total_amount=result["financial_summary"].get("total_amount", 0),
            document_count=result["financial_summary"].get("document_count", 0),
            vendor_count=result["financial_summary"].get("vendor_count", 0),
            vendors=result["financial_summary"].get("vendors", []),
            categories=result["financial_summary"].get("categories", []),
            date_range={"start_date": start_date, "end_date": end_date},
            filters={"project": project, "category": category}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@router.get("/document/{document_id}/extract")
async def extract_document_data(document_id: str):
    """
    Extract structured financial data from a specific document
    """
    try:
        result = await document_service.extract_financial_data(document_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found or not processable")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data extraction failed: {str(e)}")

@router.get("/analytics/spending-by-category")
async def get_spending_by_category(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    project: Optional[str] = Query(None)
):
    """
    Get spending breakdown by expense category
    """
    try:
        query = "Show me spending breakdown by category"
        if start_date or end_date:
            date_filter = " from "
            if start_date:
                date_filter += start_date
            if end_date:
                date_filter += f" to {end_date}" if start_date else end_date
            query += date_filter
        
        if project:
            query += f" for the {project} project"
        
        result = await document_service.query_financial_data(query)
        
        # Process categories from sources
        category_totals = {}
        if result.get("sources"):
            for source in result["sources"]:
                if source.get("amount"):
                    # This would need more sophisticated processing in real implementation
                    # For now, return the general result
                    pass
        
        return {
            "query": query,
            "category_breakdown": category_totals,
            "total_amount": result["financial_summary"].get("total_amount", 0),
            "details": result["answer"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@router.get("/analytics/spending-by-vendor")
async def get_spending_by_vendor(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    project: Optional[str] = Query(None)
):
    """
    Get spending breakdown by vendor
    """
    try:
        query = "Show me spending breakdown by vendor"
        if start_date or end_date:
            date_filter = " from "
            if start_date:
                date_filter += start_date
            if end_date:
                date_filter += f" to {end_date}" if start_date else end_date
            query += date_filter
        
        if project:
            query += f" for the {project} project"
        
        result = await document_service.query_financial_data(query)
        
        # Process vendors from sources
        vendor_totals = {}
        if result.get("sources"):
            for source in result["sources"]:
                vendor = source.get("vendor")
                amount_str = source.get("amount")
                if vendor and amount_str:
                    try:
                        amount = float(amount_str)
                        vendor_totals[vendor] = vendor_totals.get(vendor, 0) + amount
                    except (ValueError, TypeError):
                        pass
        
        return {
            "query": query,
            "vendor_breakdown": vendor_totals,
            "total_amount": result["financial_summary"].get("total_amount", 0),
            "vendors": result["financial_summary"].get("vendors", []),
            "details": result["answer"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@router.get("/analytics/timeline")
async def get_spending_timeline(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    category: Optional[str] = Query(None)
):
    """
    Get spending timeline/trends
    """
    try:
        query = "Show me spending over time"
        
        filters = []
        if start_date or end_date:
            date_filter = "from "
            if start_date:
                date_filter += start_date
            if end_date:
                date_filter += f" to {end_date}" if start_date else end_date
            filters.append(date_filter)
        
        if project:
            filters.append(f"for the {project} project")
        
        if category:
            filters.append(f"in the {category} category")
        
        if filters:
            query += " " + " ".join(filters)
        
        result = await document_service.query_financial_data(query)
        
        # Process timeline data from sources
        timeline_data = []
        if result.get("sources"):
            for source in result["sources"]:
                date = source.get("date")
                amount = source.get("amount")
                if date and amount:
                    timeline_data.append({
                        "date": date,
                        "amount": amount,
                        "vendor": source.get("vendor"),
                        "document": source.get("filename")
                    })
        
        # Sort by date
        timeline_data.sort(key=lambda x: x["date"] if x["date"] else "")
        
        return {
            "query": query,
            "timeline": timeline_data,
            "total_amount": result["financial_summary"].get("total_amount", 0),
            "details": result["answer"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline analytics failed: {str(e)}")

@router.post("/search/expenses")
async def search_expenses(filters: ExpenseQueryFilters):
    """
    Search expenses with structured filters
    """
    try:
        # Convert structured filters to natural language query
        query_parts = ["Find expenses"]
        
        if filters.categories:
            category_list = ", ".join([cat.value for cat in filters.categories])
            query_parts.append(f"in categories: {category_list}")
        
        if filters.vendors:
            vendor_list = ", ".join(filters.vendors)
            query_parts.append(f"from vendors: {vendor_list}")
        
        if filters.projects:
            project_list = ", ".join(filters.projects)
            query_parts.append(f"for projects: {project_list}")
        
        if filters.start_date:
            query_parts.append(f"from {filters.start_date}")
        
        if filters.end_date:
            query_parts.append(f"to {filters.end_date}")
        
        if filters.min_amount is not None:
            query_parts.append(f"with amount >= ${filters.min_amount}")
        
        if filters.max_amount is not None:
            query_parts.append(f"with amount <= ${filters.max_amount}")
        
        query = " ".join(query_parts)
        
        result = await document_service.query_financial_data(query)
        
        return {
            "filters": filters.dict(),
            "query": query,
            "results": result["sources"][:filters.limit],
            "total_matches": len(result["sources"]),
            "financial_summary": result["financial_summary"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Expense search failed: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Check if financial services are working properly
    """
    try:
        # Check document service
        doc_count = await document_service.get_document_count()
        
        # Check if financial parser is initialized
        parser_available = document_service.financial_parser is not None
        
        return {
            "status": "healthy",
            "document_count": doc_count,
            "financial_parser_available": parser_available,
            "services": {
                "document_service": "running",
                "chroma_db": "connected" if document_service.collection else "disconnected",
                "query_engine": "available" if document_service.query_engine else "unavailable"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }