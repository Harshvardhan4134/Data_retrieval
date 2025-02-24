import os
from app import openai_client, pinecone_client
import json
import PyPDF2
import pandas as pd
import io

# Initialize Pinecone index or create if doesn't exist
def init_pinecone():
    index_name = "document-embeddings"
    existing_indexes = pinecone_client.list_indexes()

    if index_name not in existing_indexes.names():
        pinecone_client.create_index(
            name=index_name,
            dimension=1536,  # OpenAI embedding dimension
            metric='cosine'
        )
    return pinecone_client.Index(index_name)

vector_db = init_pinecone()

def process_document(file_path, file_type):
    """Extract text from various document types"""
    try:
        text = ""
        if file_type == 'pdf':
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        elif file_type == 'xlsx':
            df = pd.read_excel(file_path, engine='openpyxl')
            # Clean up the DataFrame by handling NaN values and unnamed columns
            df = df.fillna('')  # Replace NaN with empty string
            df.columns = [f"Column {i+1}" if 'Unnamed' in str(col) else str(col) 
                         for i, col in enumerate(df.columns)]
            text = df.to_string(index=False)
        elif file_type in ['txt', 'json']:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

        # Basic HTML formatting for display
        text = text.replace('\n', '<br>')
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error processing {file_type} file: {str(e)}")

def generate_embedding(text):
    """Generate document embedding using OpenAI"""
    try:
        # Limit text length and clean it up
        text = ' '.join(text.split())[:8000] 
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        raise ValueError(f"Error generating embedding: {str(e)}")

def store_embedding(embedding, doc_id):
    """Store embedding in Pinecone"""
    try:
        vector_db.upsert(vectors=[{
            'id': str(doc_id),
            'values': embedding
        }])
    except Exception as e:
        raise ValueError(f"Error storing embedding: {str(e)}")

def generate_summary(text):
    """Generate document summary using OpenAI"""
    try:
        # Clean up and limit text
        text = ' '.join(text.split())[:4000]  # Clean whitespace and limit length

        response = openai_client.chat.completions.create(
            model="gpt-4o",  
            messages=[
                {"role": "system", "content": "You are a document summarization expert. "
                 "Provide a clear, concise summary of the document, highlighting key points "
                 "and main ideas. Format the summary in a reader-friendly way."},
                {"role": "user", "content": text}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"Error generating summary: {str(e)}")

def answer_question(question, doc_id, doc_text):
    """Answer questions about a specific document"""
    try:
        # Clean up and limit text
        doc_text = ' '.join(doc_text.split())[:4000]  # Clean whitespace and limit length

        response = openai_client.chat.completions.create(
            model="gpt-4o",  
            messages=[
                {"role": "system", "content": "You are a document analysis expert. "
                 "Answer questions based on the provided document content. "
                 "Include relevant quotes or references when possible. "
                 "If you're not sure about something, acknowledge the uncertainty."},
                {"role": "user", "content": f"Document content:\n{doc_text}\n\nQuestion: {question}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"Error processing question: {str(e)}")