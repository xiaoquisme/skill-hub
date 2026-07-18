/**
 * SkillHub API Client
 */
const API = {
    baseUrl: '',

    async request(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        if (response.status === 204) {
            return null;
        }

        return response.json();
    },

    async listSkills({ query, category, sort, limit = 50 } = {}) {
        const params = new URLSearchParams();
        if (query) params.set('q', query);
        if (category) params.set('category', category);
        if (sort) params.set('sort', sort);
        if (limit) params.set('limit', limit.toString());

        const qs = params.toString();
        return this.request(`/api/skills${qs ? '?' + qs : ''}`);
    },

    async getSkill(id) {
        return this.request(`/api/skills/${id}`);
    },

    async getSkillFile(skillId, filename) {
        const url = `${this.baseUrl}/api/skills/${skillId}/files/${encodeURIComponent(filename)}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('File not found');
        return response.text();
    },

    async healthCheck() {
        return this.request('/api/health');
    }
};
