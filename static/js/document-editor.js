// Document editor utilities
class DocumentEditor {
    constructor(quill, api, documentId) {
        this.quill = quill;
        this.api = api;
        this.documentId = documentId;
        this.saveTimeout = null;
        this.isSaving = false;
    }

    async uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/v1/uploads/images', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.api.token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Failed to upload image');
            }

            const data = await response.json();
            return data.url;
        } catch (error) {
            console.error('Image upload error:', error);
            throw error;
        }
    }

    async save() {
        if (this.isSaving) return;
        
        const content = this.quill.root.innerHTML;
        const markdown = this.htmlToMarkdown(content);
        
        this.isSaving = true;
        this.showSaveIndicator('Сохранение...', 'saving');

        try {
            await this.api.updateDocument(this.documentId, {
                content: markdown,
                content_json: { html: content },
            });
            this.showSaveIndicator('Сохранено', 'saved');
            setTimeout(() => this.hideSaveIndicator(), 2000);
        } catch (error) {
            this.showSaveIndicator('Ошибка сохранения: ' + error.message, 'error');
            setTimeout(() => this.hideSaveIndicator(), 3000);
        } finally {
            this.isSaving = false;
        }
    }

    autoSave() {
        clearTimeout(this.saveTimeout);
        this.saveTimeout = setTimeout(() => {
            this.save();
        }, 2000);
    }

    htmlToMarkdown(html) {
        // Simple HTML to Markdown converter
        // For production, use a library like turndown
        let markdown = html;
        markdown = markdown.replace(/<h1>(.*?)<\/h1>/gi, '# $1\n\n');
        markdown = markdown.replace(/<h2>(.*?)<\/h2>/gi, '## $1\n\n');
        markdown = markdown.replace(/<h3>(.*?)<\/h3>/gi, '### $1\n\n');
        markdown = markdown.replace(/<strong>(.*?)<\/strong>/gi, '**$1**');
        markdown = markdown.replace(/<em>(.*?)<\/em>/gi, '*$1*');
        markdown = markdown.replace(/<code>(.*?)<\/code>/gi, '`$1`');
        markdown = markdown.replace(/<pre><code>(.*?)<\/code><\/pre>/gis, '```\n$1\n```');
        markdown = markdown.replace(/<p>(.*?)<\/p>/gi, '$1\n\n');
        markdown = markdown.replace(/<br\s*\/?>/gi, '\n');
        markdown = markdown.replace(/<img[^>]+src="([^"]+)"[^>]*>/gi, '![]($1)');
        markdown = markdown.replace(/<a[^>]+href="([^"]+)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)');
        markdown = markdown.replace(/<[^>]+>/g, '');
        return markdown.trim();
    }

    showSaveIndicator(text, className) {
        const indicator = document.getElementById('saveIndicator');
        if (indicator) {
            indicator.textContent = text;
            indicator.className = `save-indicator show ${className}`;
        }
    }

    hideSaveIndicator() {
        const indicator = document.getElementById('saveIndicator');
        if (indicator) {
            indicator.classList.remove('show');
        }
    }
}

