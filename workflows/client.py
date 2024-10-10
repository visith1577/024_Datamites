import qdrant_client
from qdrant_client import models
from llama_index.vector_stores.qdrant import QdrantVectorStore
from dotenv import load_dotenv
from typing import List
import fitz
import openai
import os
import re

load_dotenv()


openai_client = openai.Client()

openai.api_key = os.getenv("OPENAI_API_KEY")

client = qdrant_client.QdrantClient(
    api_key=os.getenv("QDRANT_API_KEY"),
    url=os.getenv("QDRANT_HOST"),
)


def get_vector_store():
    if client.collection_exists("election_manifestos"):
        return QdrantVectorStore(client=client,  collection_name="election_manifestos")
    
    else:
        client.create_collection("election_manifestos", 
            vectors_config=models.VectorParams(
            size=1536, 
            distance=models.Distance.COSINE,
            hnsw_config=models.HnswConfigDiff(
                m=16,
                ef_construct=100,
                full_scan_threshold=10000,
                max_indexing_threads=0
            ))
        )
        return QdrantVectorStore(client=client,  collection_name="election_manifestos")


def chunk_markdown_by_headers(md_text: str):
    """
    Split a markdown document into chunks based on # and ## headers.
    Each chunk is separated by a header.
    """
    # Regular expression to match markdown headers (e.g. # or ##)
    header_regex = r"(#+ .+)"  
    chunks = []
    current_chunk = {"id": None, "text": ""}
    
    lines = md_text.split("\n")
    for i, line in enumerate(lines):
        if re.match(header_regex, line):  # Match headers
            # If we have accumulated some content in current_chunk, save it
            if current_chunk["id"] and current_chunk["text"]:
                chunks.append(current_chunk)
            # Start a new chunk with this header
            current_chunk = {"id": f"chunk_{i}", "text": line + "\n"}
        else:
            # Append non-header content to the current chunk
            current_chunk["text"] += line + "\n"
    
    # Append the final chunk
    if current_chunk["id"] and current_chunk["text"]:
        chunks.append(current_chunk)
    
    return chunks

# def get_embedding(text: str) -> List[float]:
#     """Get OpenAI embedding for the given text."""

#     response = openai_client.embeddings.create(input=text, model="text-embedding-3-small")
#     return response.data[0].embedding


def chunk_pdf_by_size(pdf_path: str, chunk_size=500):
    """
    Split a PDF into chunks by a given character size.
    """
    doc_chunks = []
    with fitz.open(pdf_path) as doc:
        text = ""
        chunk_id = 0
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            
            while len(text) > chunk_size:
                doc_chunks.append({
                    'id': f"chunk_{chunk_id}",
                    'text': text[:chunk_size]
                })
                text = text[chunk_size:]
                chunk_id += 1
        
        # Append any remaining text as the last chunk
        if text:
            doc_chunks.append({
                'id': f"chunk_{chunk_id}",
                'text': text
            })
    
    return doc_chunks


vector_store = get_vector_store()
