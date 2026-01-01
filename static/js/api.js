// API client for DocuCraft
class API {
    constructor() {
        this.baseURL = '/api/v1';
        this.token = localStorage.getItem('access_token');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                // Unauthorized - redirect to login
                localStorage.removeItem('access_token');
                window.location.href = '/';
                return;
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Auth
    async getCurrentUser() {
        return this.request('/auth/me');
    }

    // Projects
    async getProjects() {
        return this.request('/projects');
    }

    async getProject(projectId) {
        return this.request(`/projects/${projectId}`);
    }

    async createProject(data) {
        return this.request('/projects', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateProject(projectId, data) {
        return this.request(`/projects/${projectId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteProject(projectId) {
        return this.request(`/projects/${projectId}`, {
            method: 'DELETE',
        });
    }

    async getProjectMembers(projectId) {
        return this.request(`/projects/${projectId}/members`);
    }

    async addProjectMember(projectId, userId, role) {
        return this.request(`/projects/${projectId}/members`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, role }),
        });
    }

    async updateProjectMember(projectId, userId, role) {
        return this.request(`/projects/${projectId}/members/${userId}`, {
            method: 'PUT',
            body: JSON.stringify({ role }),
        });
    }

    async removeProjectMember(projectId, userId) {
        return this.request(`/projects/${projectId}/members/${userId}`, {
            method: 'DELETE',
        });
    }

    // Documents
    async getDocuments(projectId) {
        return this.request(`/documents/projects/${projectId}/documents`);
    }

    async getDocument(documentId) {
        return this.request(`/documents/${documentId}`);
    }

    async createDocument(projectId, data) {
        return this.request(`/documents/projects/${projectId}/documents`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateDocument(documentId, data) {
        return this.request(`/documents/${documentId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteDocument(documentId) {
        return this.request(`/documents/${documentId}`, {
            method: 'DELETE',
        });
    }

    async getDocumentVersions(documentId) {
        return this.request(`/documents/${documentId}/versions`);
    }

    async getDocumentVersion(documentId, versionNumber) {
        return this.request(`/documents/${documentId}/versions/${versionNumber}`);
    }

    // Comments
    async getDocumentComments(documentId) {
        return this.request(`/documents/${documentId}/comments`);
    }

    async createComment(documentId, text, parentId = null) {
        return this.request(`/documents/${documentId}/comments`, {
            method: 'POST',
            body: JSON.stringify({ text, parent_id: parentId }),
        });
    }

    async updateComment(commentId, text) {
        return this.request(`/comments/${commentId}`, {
            method: 'PUT',
            body: JSON.stringify({ text }),
        });
    }

    async deleteComment(commentId) {
        return this.request(`/comments/${commentId}`, {
            method: 'DELETE',
        });
    }

    // Export
    async exportDocument(documentId, format) {
        const response = await fetch(`${this.baseURL}/documents/${documentId}/export?format=${format}`, {
            headers: this.getHeaders(),
        });
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `document.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}

// Global API instance
const api = new API();

