// Document viewer and AI chat functionality
document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Upload failed: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
                alert('Upload failed: Please try again');
            });
        });
    }

    // Document viewer
    const documentLinks = document.querySelectorAll('.document-link');
    documentLinks.forEach(link => {
        link.addEventListener('click', async function(e) {
            e.preventDefault();
            const docId = this.getAttribute('data-doc-id');

            // Clear previous content and show loading state
            document.getElementById('document-content').innerHTML = '<div class="text-center"><p>Loading document...</p></div>';
            document.getElementById('document-summary').textContent = 'Loading summary...';
            document.getElementById('current-doc-id').value = docId;

            try {
                const response = await fetch(`/view/${docId}`);
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                // Update summary
                document.getElementById('document-summary').textContent = data.summary;

                // Update document content based on file type
                const contentDiv = document.getElementById('document-content');
                if (data.file_type === 'pdf') {
                    contentDiv.innerHTML = '<canvas id="pdf-viewer"></canvas>';
                    // Initialize PDF viewer
                    const canvas = document.getElementById('pdf-viewer');
                    pdfjsLib.getDocument({data: atob(data.content)}).promise.then(function(pdf) {
                        pdf.getPage(1).then(function(page) {
                            const viewport = page.getViewport({scale: 1.5});
                            const context = canvas.getContext('2d');
                            canvas.height = viewport.height;
                            canvas.width = viewport.width;
                            page.render({
                                canvasContext: context,
                                viewport: viewport
                            });
                        });
                    });
                } else if (data.file_type === 'xlsx') {
                    contentDiv.innerHTML = data.content; // Already formatted as HTML table
                } else if (data.file_type === 'json') {
                    contentDiv.innerHTML = `<pre class="json-content">${data.content}</pre>`;
                } else {
                    contentDiv.innerHTML = `<pre>${data.content}</pre>`;
                }

                // Set current document ID for chat
                document.getElementById('current-doc-id').value = docId;
            } catch (error) {
                console.error('Document view error:', error);
                document.getElementById('document-content').innerHTML = `
                    <div class="alert alert-danger">
                        Failed to load document: ${error.message}
                    </div>
                `;
                document.getElementById('document-summary').textContent = 'Error loading summary';
            }
        });
    });

    // AI Chat
    const chatForm = document.getElementById('chat-form');
    const chatMessages = document.getElementById('chat-messages');

    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const question = document.getElementById('question').value;
            const docId = document.getElementById('current-doc-id').value;

            if (!docId) {
                alert('Please select a document first');
                return;
            }

            // Add loading state
            const loadingMessage = document.createElement('div');
            loadingMessage.className = 'text-muted';
            loadingMessage.textContent = 'Processing your question...';
            chatMessages.appendChild(loadingMessage);

            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    document_id: docId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove loading message
                loadingMessage.remove();

                if (data.error) {
                    throw new Error(data.error);
                }

                const messageDiv = document.createElement('div');
                messageDiv.innerHTML = `
                    <p class="question">Q: ${question}</p>
                    <p class="answer">A: ${data.answer}</p>
                `;
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                document.getElementById('question').value = '';
            })
            .catch(error => {
                // Remove loading message
                loadingMessage.remove();

                console.error('Chat error:', error);
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger';
                errorDiv.textContent = 'Failed to get answer: ' + error.message;
                chatMessages.appendChild(errorDiv);
            });
        });
    }
});
// Document viewer and AI chat functionality
document.addEventListener('DOMContentLoaded', function() {
    // Document viewer
    const documentLinks = document.querySelectorAll('.document-link');
    documentLinks.forEach(link => {
        link.addEventListener('click', async function(e) {
            e.preventDefault();
            const docId = this.getAttribute('data-doc-id');

            try {
                const response = await fetch(`/view/${docId}`);
                const data = await response.json();

                // Update document content based on file type
                const contentDiv = document.getElementById('document-content');
                if (data.file_type === 'pdf') {
                    contentDiv.innerHTML = '<canvas id="pdf-viewer"></canvas>';
                    const canvas = document.getElementById('pdf-viewer');
                    pdfjsLib.getDocument({data: atob(data.content)}).promise.then(function(pdf) {
                        pdf.getPage(1).then(function(page) {
                            const viewport = page.getViewport({scale: 1.5});
                            const context = canvas.getContext('2d');
                            canvas.height = viewport.height;
                            canvas.width = viewport.width;
                            page.render({
                                canvasContext: context,
                                viewport: viewport
                            });
                        });
                    });
                } else if (data.file_type === 'xlsx') {
                    contentDiv.innerHTML = data.content; // HTML table
                } else if (data.file_type === 'json') {
                    contentDiv.innerHTML = `<pre class="json-content">${data.content}</pre>`;
                } else {
                    contentDiv.innerHTML = `<pre>${data.content}</pre>`;
                }

                // Update summary
                document.getElementById('document-summary').textContent = data.summary;
            } catch (error) {
                console.error('Document view error:', error);
                contentDiv.innerHTML = `
                    <div class="alert alert-danger">
                        Failed to load document: ${error.message}
                    </div>
                `;
            }
        });
    });

    // AI Chat functionality
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const question = document.getElementById('question').value;
            const docId = document.getElementById('current-doc-id').value;

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: question,
                        document_id: docId
                    })
                });
                const data = await response.json();
                
                const messageDiv = document.createElement('div');
                messageDiv.innerHTML = `
                    <p class="question">Q: ${question}</p>
                    <p class="answer">A: ${data.answer}</p>
                `;
                document.getElementById('chat-messages').appendChild(messageDiv);
                document.getElementById('question').value = '';
            } catch (error) {
                console.error('Chat error:', error);
            }
        });
    }

    // Admin functionality
    if (window.location.pathname.includes('admin')) {
        // File upload handling
        const uploadForm = document.getElementById('upload-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Upload failed: ' + data.error);
                    }
                } catch (error) {
                    console.error('Upload error:', error);
                    alert('Upload failed');
                }
            });
        }
    }
});

// Document management functions
function deleteDocument(docId) {
    if (confirm('Are you sure you want to delete this document?')) {
        fetch(`/delete/${docId}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Delete failed: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Delete error:', error);
                alert('Delete failed');
            });
    }
}

function renameDocument(docId) {
    const newName = prompt('Enter new name:');
    if (newName) {
        fetch(`/rename/${docId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ new_name: newName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Rename failed: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Rename error:', error);
            alert('Rename failed');
        });
    }
}