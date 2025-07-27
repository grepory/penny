from llama_parse import LlamaParse
from llama_index.core import Document
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.models.financial import (
    FinancialDocument, LineItem, Vendor, Project,
    ExpenseCategory, DocumentType, PaymentMethod
)
from app.models.document import DocumentResponse


class FinancialDocumentParser:
    """Parser for extracting structured financial data from invoices and receipts using LlamaParse"""
    
    def __init__(self):
        if not settings.LLAMA_CLOUD_API_KEY:
            raise ValueError("LLAMA_CLOUD_API_KEY is required for LlamaParse")
        
        self.parser = LlamaParse(
            api_key=settings.LLAMA_CLOUD_API_KEY,
            result_type="markdown",  # Can be "markdown" or "text"
            verbose=True,
            language="en",
        )
        
        # Enhanced parsing instructions for financial documents
        self.parser.parsing_instruction = """
        This is a financial document (invoice, receipt, or bill). Extract the following information in a structured format:

        1. DOCUMENT METADATA:
        - Document type (invoice, receipt, estimate, bill)
        - Invoice/receipt number
        - Issue date and due date
        - Currency

        2. VENDOR INFORMATION:
        - Company/business name
        - Address
        - Phone number
        - Email
        - Tax ID or business registration number

        3. BILLING INFORMATION:
        - Bill to name and address
        - Customer information

        4. LINE ITEMS (for each product/service):
        - Description
        - Quantity
        - Unit price
        - Total price
        - Category (materials, labor, equipment, etc.)
        - Product codes or SKUs

        5. FINANCIAL TOTALS:
        - Subtotal
        - Tax amounts (by type if multiple)
        - Discounts
        - Total amount

        6. PAYMENT INFORMATION:
        - Payment method
        - Payment terms
        - Payment status

        7. PROJECT CONTEXT:
        - Any project names or descriptions mentioned
        - Work order numbers
        - Location/property address if different from billing

        Extract all monetary amounts with their associated descriptions. Preserve the exact structure and formatting of tables when present.
        """

    async def parse_document(self, document: DocumentResponse) -> Dict[str, Any]:
        """Parse a document and extract structured financial data"""
        try:
            file_path = Path(document.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Document file not found: {file_path}")

            # Parse document with LlamaParse
            documents = await self.parser.aload_data([str(file_path)])
            
            if not documents:
                raise ValueError("No content extracted from document")

            # Extract structured data from parsed content
            parsed_content = documents[0].text
            metadata = await self._extract_financial_metadata(parsed_content, document)
            
            return {
                "document_id": document.id,
                "parsed_content": parsed_content,
                "metadata": metadata,
                "extracted_data": await self._structure_financial_data(metadata, document)
            }

        except Exception as e:
            print(f"Error parsing document {document.id}: {e}")
            raise

    async def _extract_financial_metadata(self, content: str, document: DocumentResponse) -> Dict[str, Any]:
        """Extract structured metadata from parsed content using LLM"""
        try:
            # Use OpenAI to structure the extracted content
            from llama_index.llms.openai import OpenAI
            
            if not settings.OPENAI_API_KEY:
                # Fallback to pattern matching if no LLM available
                return await self._extract_with_patterns(content)
            
            llm = OpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-3.5-turbo")
            
            prompt = f"""
            Extract structured financial information from this document content and return it as JSON:

            Document Content:
            {content}

            Extract and return a JSON object with this exact structure:
            {{
                "document_type": "invoice|receipt|estimate|bill",
                "document_number": "string or null",
                "issue_date": "YYYY-MM-DD or null",
                "due_date": "YYYY-MM-DD or null",
                "vendor": {{
                    "name": "string",
                    "address": "string or null",
                    "phone": "string or null",
                    "email": "string or null"
                }},
                "line_items": [
                    {{
                        "description": "string",
                        "quantity": number,
                        "unit_price": number,
                        "total_price": number,
                        "category": "materials|labor|equipment|supplies|other"
                    }}
                ],
                "financial_summary": {{
                    "subtotal": number,
                    "tax_amount": number,
                    "total_amount": number,
                    "currency": "USD"
                }},
                "project_info": {{
                    "project_name": "string or null",
                    "work_order": "string or null",
                    "location": "string or null"
                }}
            }}

            Only return valid JSON. If information is not available, use null values.
            """

            response = await llm.acomplete(prompt)
            extracted_json = response.text.strip()
            
            # Clean up the response to extract JSON
            if "```json" in extracted_json:
                extracted_json = extracted_json.split("```json")[1].split("```")[0]
            elif "```" in extracted_json:
                extracted_json = extracted_json.split("```")[1].split("```")[0]
            
            return json.loads(extracted_json)

        except Exception as e:
            print(f"Error extracting financial metadata: {e}")
            # Fallback to pattern matching
            return await self._extract_with_patterns(content)

    async def _extract_with_patterns(self, content: str) -> Dict[str, Any]:
        """Fallback extraction using regex patterns"""
        patterns = {
            'total_amount': r'(?:total|amount due|grand total)[\s:$]*(\d+[.,]\d{2})',
            'invoice_number': r'(?:invoice|receipt)[\s#:]*(\w+\d+)',
            'date': r'(?:date|issued)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'vendor_name': r'^([A-Z][A-Za-z\s&]+(?:LLC|Inc|Corp)?)',
        }
        
        extracted = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            extracted[key] = match.group(1) if match else None
        
        return {
            "document_type": "invoice",
            "document_number": extracted.get('invoice_number'),
            "issue_date": extracted.get('date'),
            "vendor": {"name": extracted.get('vendor_name')},
            "financial_summary": {"total_amount": float(extracted.get('total_amount', 0)) if extracted.get('total_amount') else 0},
            "line_items": [],
            "project_info": {}
        }

    async def _structure_financial_data(self, metadata: Dict[str, Any], document: DocumentResponse) -> Dict[str, Any]:
        """Convert extracted metadata to a simple dictionary for now"""
        try:
            # Extract vendor information
            vendor_data = metadata.get('vendor', {})
            vendor_name = vendor_data.get('name', 'Unknown Vendor')
            
            # Parse dates
            issue_date = None
            if metadata.get('issue_date'):
                try:
                    issue_date = datetime.strptime(metadata['issue_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            # Get financial summary
            financial_summary = metadata.get('financial_summary', {})
            total_amount = financial_summary.get('total_amount', 0.0)
            
            # Return simplified structure
            return {
                'document_id': document.id,
                'document_type': metadata.get('document_type', 'invoice'),
                'vendor_name': vendor_name,
                'issue_date': issue_date,
                'total_amount': total_amount,
                'line_items': metadata.get('line_items', []),
                'project_info': metadata.get('project_info', {})
            }

        except Exception as e:
            print(f"Error structuring financial data: {e}")
            raise

    async def categorize_expenses(self, line_items: List[LineItem]) -> List[LineItem]:
        """Auto-categorize line items using LLM"""
        try:
            if not settings.OPENAI_API_KEY:
                return line_items
            
            from llama_index.llms.openai import OpenAI
            llm = OpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-3.5-turbo")
            
            for item in line_items:
                if item.category == ExpenseCategory.OTHER:
                    prompt = f"""
                    Categorize this home renovation expense item into one of these categories:
                    - MATERIALS_LUMBER, MATERIALS_HARDWARE, MATERIALS_PAINT, MATERIALS_ELECTRICAL, MATERIALS_PLUMBING
                    - LABOR_GENERAL, LABOR_ELECTRICAL, LABOR_PLUMBING, LABOR_HVAC
                    - EQUIPMENT_RENTAL, EQUIPMENT_PURCHASE
                    - SUPPLIES_GENERAL, PERMITS_FEES, OTHER

                    Item description: {item.description}
                    
                    Return only the category name.
                    """
                    
                    response = await llm.acomplete(prompt)
                    category_name = response.text.strip()
                    
                    try:
                        item.category = ExpenseCategory(category_name)
                    except ValueError:
                        item.category = ExpenseCategory.OTHER
            
            return line_items

        except Exception as e:
            print(f"Error categorizing expenses: {e}")
            return line_items