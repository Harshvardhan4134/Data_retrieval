import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db
from models import User, Document, ChatLog
from document_processor import save_document, delete_document, rename_document
from ai_utils import answer_question, process_document

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Add debug logging
        app.logger.debug(f"Login attempt for email: {email}")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            app.logger.debug("Login successful")
            return redirect(url_for('index'))

        app.logger.debug("Login failed - invalid credentials")
        flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    documents = Document.query.all()
    return render_template('admin_dashboard.html', documents=documents)

@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    documents = Document.query.all()
    return render_template('user_dashboard.html', documents=documents)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Admin privileges required'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    try:
        document = save_document(file, current_user.id)
        return jsonify({'success': True, 'document_id': document.id})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/view/<int:doc_id>')
@login_required
def view_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
        if not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('index'))

        content = ''
        if document.file_type == 'pdf':
            # For PDFs, read binary content for PDF.js
            with open(file_path, 'rb') as file:
                binary_content = file.read()
                import base64
                content = base64.b64encode(binary_content).decode('utf-8')
        elif document.file_type == 'xlsx':
            # Excel content formatted as HTML table
            df = pd.read_excel(file_path, engine='openpyxl')
            content = df.to_html(classes='table table-striped', index=False)
        elif document.file_type == 'json':
            # Pretty print JSON
            with open(file_path, 'r') as file:
                data = json.load(file)
                content = json.dumps(data, indent=2)
        else:
            # Text files
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

        # Return both document content and summary
        return jsonify({
            'content': content,
            'summary': document.summary or 'Summary not available',
            'file_type': document.file_type
        })
    except Exception as e:
        app.logger.error(f"Error viewing document: {str(e)}")
        return jsonify({'error': 'Error processing document'}), 500

@app.route('/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete(doc_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Admin privileges required'}), 403

    try:
        delete_document(doc_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rename/<int:doc_id>', methods=['POST'])
@login_required
def rename(doc_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Admin privileges required'}), 403

    new_name = request.json.get('new_name')
    if not new_name:
        return jsonify({'success': False, 'error': 'New name not provided'}), 400

    try:
        rename_document(doc_id, new_name)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
@login_required
def ask_question():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        question = data.get('question')
        doc_id = data.get('document_id')

        if not question or not doc_id:
            return jsonify({'error': 'Missing question or document ID'}), 400

        document = Document.query.get_or_404(doc_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'Document file not found'}), 404

        doc_text = process_document(file_path, document.file_type)
        answer = answer_question(question, doc_id, doc_text)

        # Log the chat
        chat_log = ChatLog(
            user_id=current_user.id,
            document_id=doc_id,
            question=question,
            answer=answer
        )
        db.session.add(chat_log)
        db.session.commit()

        return jsonify({'answer': answer})
    except Exception as e:
        app.logger.error(f"Error processing question: {str(e)}")
        return jsonify({'error': 'Failed to process question'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
import pandas as pd
import json