import os
from werkzeug.utils import secure_filename
import uuid
from app import app, db
from models import Document
from ai_utils import process_document, generate_embedding, store_embedding, generate_summary

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'json', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_document(file, user_id):
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")

    try:
        # Generate secure filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{str(uuid.uuid4())}.{file_extension}"

        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        try:
            # Process document
            text_content = process_document(file_path, file_extension)
            embedding = generate_embedding(text_content)
            summary = generate_summary(text_content)

            # Create document record
            doc = Document(
                filename=unique_filename,
                original_filename=original_filename,
                file_type=file_extension,
                user_id=user_id,
                summary=summary
            )
            db.session.add(doc)
            db.session.commit()

            # Store embedding
            store_embedding(embedding, doc.id)

            return doc
        except Exception as e:
            # If processing fails, clean up the saved file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e

    except Exception as e:
        app.logger.error(f"Error processing document: {str(e)}")
        raise ValueError(f"Failed to process document: {str(e)}")

def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(doc)
    db.session.commit()

def rename_document(doc_id, new_name):
    doc = Document.query.get_or_404(doc_id)
    doc.original_filename = secure_filename(new_name)
    db.session.commit()