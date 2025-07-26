from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
import chromadb
from pathlib import Path
from typing import List

from app.core.config import settings as app_settings
from app.models.document import DocumentResponse, SearchResult

class DocumentService:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.index = None
        self.query_engine = None
        self._initialize_llm()
        self._initialize_chroma()
    
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
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=app_settings.COLLECTION_NAME
            )
            
            # Initialize vector store
            vector_store = ChromaVectorStore(chroma_collection=self.collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            embed_model = OpenAIEmbedding(api_key=app_settings.OPENAI_API_KEY)
            
            # Create or load index
            try:
                # Try to load existing index
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context
                )
            except:
                # Create new index if none exists
                self.index = VectorStoreIndex([], storage_context=storage_context, embed_model=embed_model)
            
            # Initialize query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=10,
                response_mode="compact"
            )
            
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise
    
    async def index_document(self, document: DocumentResponse):
        """Index a single document"""
        try:
            file_path = Path(document.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Document file not found: {file_path}")
            
            # Load document
            reader = SimpleDirectoryReader(
                input_files=[str(file_path)]
            )
            documents = reader.load_data()
            
            # Add metadata
            for doc in documents:
                doc.metadata.update({
                    "document_id": document.id,
                    "filename": document.filename,
                    "content_type": document.content_type,
                    "file_size": document.file_size,
                    "uploaded_at": document.uploaded_at.isoformat()
                })
            
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
                    if hasattr(node, 'metadata') and hasattr(node, 'text'):
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