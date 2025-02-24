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
                    // PDF viewer initialization
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
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const question = document.getElementById('question').value;
            const docId = document.getElementById('current-doc-id').value;

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
                const messageDiv = document.createElement('div');
                messageDiv.innerHTML = `
                    <p class="question">Q: ${question}</p>
                    <p class="answer">A: ${data.answer}</p>
                `;
                document.getElementById('chat-messages').appendChild(messageDiv);
                document.getElementById('question').value = '';
            });
        });
    }
});