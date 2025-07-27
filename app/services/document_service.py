from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from app.core.config import settings as app_settings
from app.models.document import DocumentResponse, SearchResult
from app.services.financial_parser import FinancialDocumentParser

class DocumentService:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.index = None
        self.query_engine = None
        self.financial_parser = None
        self._initialize_llm()
        self._initialize_chroma()
        self._initialize_financial_parser()
    
    def _initialize_llm(self):
        """Initialize the LLM with OpenAI"""
        if app_settings.OPENAI_API_KEY:
            llm = OpenAI(
                api_key=app_settings.OPENAI_API_KEY,
                model="gpt-3.5-turbo",
                temperature=0.1
            )
            Settings.llm = llm
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path=app_settings.CHROMA_DB_PATH)
            
            # Handle collection with potential embedding dimension mismatch
            try:
                # Try to get existing collection
                self.collection = self.chroma_client.get_collection(
                    name=app_settings.COLLECTION_NAME
                )
                # Test if we can add embeddings (this will fail if dimensions don't match)
                if app_settings.OPENAI_API_KEY:
                    test_embed = OpenAIEmbedding(api_key=app_settings.OPENAI_API_KEY)
                    # Try a test embedding to see if dimensions match
                    test_embedding = test_embed.get_text_embedding("test")
                    if self.collection.count() > 0:
                        # Collection exists and has data, check if dimensions match
                        try:
                            self.collection.add(
                                embeddings=[test_embedding],
                                documents=["test"],
                                ids=["test_dimension_check"]
                            )
                            # If successful, remove the test document
                            self.collection.delete(ids=["test_dimension_check"])
                        except Exception as dim_error:
                            if "dimension" in str(dim_error).lower():
                                print(f"Dimension mismatch detected: {dim_error}")
                                print("Recreating collection with correct dimensions...")
                                self.chroma_client.delete_collection(name=app_settings.COLLECTION_NAME)
                                self.collection = self.chroma_client.create_collection(
                                    name=app_settings.COLLECTION_NAME
                                )
                            else:
                                raise
            except Exception:
                # Collection doesn't exist or other error, create new one
                try:
                    self.collection = self.chroma_client.create_collection(
                        name=app_settings.COLLECTION_NAME
                    )
                except:
                    # If collection already exists, get it
                    self.collection = self.chroma_client.get_collection(
                        name=app_settings.COLLECTION_NAME
                    )
            
            # Set up embedding model
            if app_settings.OPENAI_API_KEY:
                embed_model = OpenAIEmbedding(api_key=app_settings.OPENAI_API_KEY)
                Settings.embed_model = embed_model
            
            # Initialize vector store
            vector_store = ChromaVectorStore(chroma_collection=self.collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Create or load index
            try:
                # Try to load existing index
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context
                )
            except Exception as e:
                print(f"Failed to load existing index, creating new one: {e}")
                # Create new index if none exists or there's a dimension mismatch
                self.index = VectorStoreIndex([], storage_context=storage_context)
            
            # Initialize query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=10,
                response_mode="compact"
            )
            
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise
    
    def _initialize_financial_parser(self):
        """Initialize the financial document parser"""
        try:
            if app_settings.LLAMA_CLOUD_API_KEY:
                self.financial_parser = FinancialDocumentParser()
            else:
                print("Warning: LLAMA_CLOUD_API_KEY not set, financial parsing will be limited")
        except Exception as e:
            print(f"Error initializing financial parser: {e}")
            self.financial_parser = None
    
    async def index_document(self, document: DocumentResponse):
        """Index a single document with enhanced financial parsing"""
        try:
            file_path = Path(document.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Document file not found: {file_path}")
            
            # Parse financial data if possible
            financial_data = None
            if self.financial_parser and self._is_financial_document(document):
                try:
                    financial_data = await self.financial_parser.parse_document(document)
                except Exception as e:
                    print(f"Error parsing financial data: {e}")
            
            # Load document with enhanced content
            if financial_data:
                # Use LlamaParse parsed content
                enhanced_content = self._create_enhanced_content(financial_data)
                documents = [enhanced_content]
            else:
                # Fallback to SimpleDirectoryReader
                reader = SimpleDirectoryReader(input_files=[str(file_path)])
                documents = reader.load_data()
            
            # Add comprehensive metadata
            for doc in documents:
                base_metadata = {
                    "document_id": document.id,
                    "filename": document.filename,
                    "content_type": document.content_type,
                    "file_size": document.file_size,
                    "uploaded_at": document.uploaded_at.isoformat()
                }
                
                # Add basic financial metadata if available
                if financial_data:
                    financial_doc = financial_data.get('extracted_data')
                    if financial_doc:
                        # Only add simple string/number fields to avoid ChromaDB issues
                        if financial_doc.get('vendor_name'):
                            base_metadata["vendor_name"] = str(financial_doc.get('vendor_name'))
                        if financial_doc.get('total_amount'):
                            base_metadata["total_amount"] = str(financial_doc.get('total_amount'))
                        if financial_doc.get('document_type'):
                            base_metadata["document_type"] = str(financial_doc.get('document_type'))
                
                doc.metadata.update(base_metadata)
                
                # Set the document ID to our custom ID to ensure consistency
                doc.doc_id = document.id
            
            # Parse into nodes with chunking
            parser = SentenceSplitter(
                chunk_size=app_settings.CHUNK_SIZE,
                chunk_overlap=app_settings.CHUNK_OVERLAP
            )
            nodes = parser.get_nodes_from_documents(documents)
            
            # Add nodes to index
            self.index.insert_nodes(nodes)
            
            return True
            
        except Exception as e:
            print(f"Error indexing document {document.id}: {e}")
            raise
    
    async def search_documents(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search documents using vector similarity"""
        try:
            if not self.query_engine:
                return []
            
            # Perform similarity search
            response = self.query_engine.query(query)
            
            results = []
            
            # Extract source nodes from response
            if hasattr(response, 'source_nodes'):
                for i, node in enumerate(response.source_nodes[:limit]):
                    if hasattr(node, 'metadata') and hasattr(node, 'text') and node.text is not None:
                        metadata = node.metadata
                        results.append(SearchResult(
                            document_id=metadata.get("document_id", "unknown"),
                            filename=metadata.get("filename", "unknown"),
                            content=node.text[:500] + "..." if len(node.text) > 500 else node.text,
                            score=getattr(node, 'score', 0.0) if hasattr(node, 'score') else 1.0
                        ))
            
            return results
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from both disk and ChromaDB"""
        try:
            # Find the document file
            document_files = list(app_settings.DOCUMENTS_DIR.glob(f"{document_id}_*"))
            
            if not document_files:
                raise FileNotFoundError(f"Document with ID {document_id} not found")
            
            file_path = document_files[0]
            
            # Delete from ChromaDB using metadata filter
            if self.collection:
                # Get all documents with this document_id
                results = self.collection.get(
                    where={"document_id": document_id}
                )
                
                if results['ids']:
                    # Delete all chunks/nodes for this document
                    self.collection.delete(ids=results['ids'])
            
            # Delete the file from disk
            file_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            raise

    async def get_document_count(self) -> int:
        """Get total number of indexed documents"""
        try:
            if self.collection:
                return self.collection.count()
            return 0
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0
    
    def _is_financial_document(self, document: DocumentResponse) -> bool:
        """Check if document is likely a financial document"""
        financial_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
        file_extension = Path(document.filename).suffix.lower()
        
        # Check file extension and content type
        return (file_extension in financial_extensions or 
                any(keyword in document.filename.lower() 
                    for keyword in ['invoice', 'receipt', 'bill', 'estimate']))
    
    def _create_enhanced_content(self, financial_data: Dict[str, Any]) -> Any:
        """Create enhanced document content from financial data"""
        from llama_index.core import Document
        
        parsed_content = financial_data.get('parsed_content', '')
        metadata = financial_data.get('metadata', {})
        extracted_data = financial_data.get('extracted_data')
        
        # Create structured content for better searchability
        enhanced_text_parts = [parsed_content]
        
        if extracted_data:
            # Add searchable financial summary
            if extracted_data.get('vendor_name'):
                enhanced_text_parts.append(f"Vendor: {extracted_data['vendor_name']}")
            
            if extracted_data.get('total_amount'):
                enhanced_text_parts.append(f"Total Amount: ${extracted_data['total_amount']}")
            
            if extracted_data.get('issue_date'):
                enhanced_text_parts.append(f"Date: {extracted_data['issue_date']}")
            
            project_info = extracted_data.get('project_info', {})
            if project_info.get('project_name'):
                enhanced_text_parts.append(f"Project: {project_info['project_name']}")
            
            # Add line item details for better search
            line_items = extracted_data.get('line_items', [])
            if line_items:
                enhanced_text_parts.append("Items purchased:")
                for item in line_items:
                    description = item.get('description', 'Item')
                    category = item.get('category', 'general')
                    total = item.get('total_price', 0)
                    enhanced_text_parts.append(
                        f"- {description} ({category}): ${total}"
                    )
        
        enhanced_content = "\n".join(enhanced_text_parts)
        
        # Ensure metadata only contains simple types for ChromaDB
        clean_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, type(None))):
                clean_metadata[key] = value
            elif hasattr(value, 'isoformat'):  # date objects
                clean_metadata[key] = value.isoformat()
            elif isinstance(value, (list, tuple)):
                # Convert lists to comma-separated strings
                if value:
                    clean_metadata[key] = ", ".join(str(item) for item in value)
                else:
                    clean_metadata[key] = ""
            else:
                # Skip complex objects
                continue
        
        doc = Document(
            text=enhanced_content,
            metadata=clean_metadata
        )
        # Set doc_id from metadata to ensure consistency
        if clean_metadata.get('document_id'):
            doc.doc_id = clean_metadata['document_id']
        return doc
    
    async def query_financial_data(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enhanced query method for financial data with natural language support"""
        try:
            if not self.query_engine:
                return {"error": "Query engine not initialized"}
            
            # Enhanced query with financial context
            financial_context = """
            This is a financial document database containing invoices, receipts, and bills for home renovation projects.
            When answering questions about spending, costs, or expenses, please:
            1. Look for specific dollar amounts and totals
            2. Consider date ranges when asked about time periods like "this summer" or "last month"
            3. Group expenses by categories (paint, lumber, electrical, plumbing, labor, etc.)
            4. Consider project associations when asked about specific renovations
            5. Provide specific details from the documents when possible
            """
            
            enhanced_query = f"{financial_context}\n\nUser question: {query}"
            
            response = self.query_engine.query(enhanced_query)
            
            # Extract financial insights from response
            result = {
                "answer": str(response),
                "sources": [],
                "financial_summary": {}
            }
            
            # Process source nodes for financial data
            if hasattr(response, 'source_nodes'):
                total_amount = 0
                vendors = set()
                categories = set()
                
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        metadata = node.metadata
                        
                        # Collect financial metadata
                        if metadata.get('total_amount'):
                            try:
                                amount = float(metadata['total_amount'])
                                total_amount += amount
                            except (ValueError, TypeError):
                                pass
                        
                        if metadata.get('vendor_name'):
                            vendors.add(metadata['vendor_name'])
                        
                        if metadata.get('expense_categories'):
                            categories.update(metadata['expense_categories'])
                        
                        # Handle case where node.text might be None
                        content_preview = ""
                        if hasattr(node, 'text') and node.text is not None:
                            content_preview = node.text[:200] + "..." if len(node.text) > 200 else node.text
                        
                        result["sources"].append({
                            "document_id": metadata.get("document_id"),
                            "filename": metadata.get("filename"),
                            "vendor": metadata.get("vendor_name"),
                            "amount": metadata.get("total_amount"),
                            "date": metadata.get("issue_date"),
                            "content_preview": content_preview
                        })
                
                result["financial_summary"] = {
                    "total_amount": total_amount,
                    "vendor_count": len(vendors),
                    "vendors": list(vendors),
                    "categories": list(categories),
                    "document_count": len(response.source_nodes)
                }
            
            return result
            
        except Exception as e:
            print(f"Error querying financial data: {e}")
            return {"error": f"Query failed: {str(e)}"}
    
    async def get_financial_summary(self, 
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None,
                                   project: Optional[str] = None,
                                   category: Optional[str] = None) -> Dict[str, Any]:
        """Get financial summary with optional filters"""
        try:
            # Build query based on filters
            query_parts = ["Show me a summary of all expenses"]
            
            if start_date or end_date:
                date_filter = "from "
                if start_date:
                    date_filter += start_date
                if end_date:
                    date_filter += f" to {end_date}" if start_date else end_date
                query_parts.append(date_filter)
            
            if project:
                query_parts.append(f"for the {project} project")
            
            if category:
                query_parts.append(f"in the {category} category")
            
            query = " ".join(query_parts)
            
            return await self.query_financial_data(query)
            
        except Exception as e:
            print(f"Error getting financial summary: {e}")
            return {"error": f"Summary failed: {str(e)}"}

    async def extract_financial_data(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Extract structured financial data for a specific document"""
        try:
            # Find the document file
            document_files = list(app_settings.DOCUMENTS_DIR.glob(f"{document_id}_*"))
            
            if not document_files:
                return None
            
            file_path = document_files[0]
            filename = file_path.name.split("_", 1)[1]
            
            # Create DocumentResponse object
            document = DocumentResponse(
                id=document_id,
                filename=filename,
                file_path=str(file_path),
                content_type="application/pdf",  # Default, could be detected
                file_size=file_path.stat().st_size,
                uploaded_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                indexed=True
            )
            
            if self.financial_parser:
                return await self.financial_parser.parse_document(document)
            
            return None
            
        except Exception as e:
            print(f"Error extracting financial data for {document_id}: {e}")
            return None