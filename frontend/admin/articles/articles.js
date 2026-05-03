/**
 * Articles management Alpine component.
 */
function articlesApp() {
    return {
        articles: [],
        pagination: {
            page: 1,
            total_pages: 0,
            total_items: 0,
        },
        filters: {
            search: '',
            enabled: '',
            sort: '-created',
            per_page: 20,
            page: 1,
        },
        loading: false,
        error: null,

        async init() {
            console.log('📰 [articlesApp] init');
            this.loadArticles();
        },

        async loadArticles() {
            this.loading = true;
            this.error = null;

            try {
                const token = localStorage.getItem('anita_token');
                const params = new URLSearchParams({
                    page: this.filters.page,
                    per_page: this.filters.per_page,
                    sort: this.filters.sort,
                });
                if (this.filters.search) params.append('search', this.filters.search);
                if (this.filters.enabled !== '') params.append('enabled', this.filters.enabled);

                const response = await fetch(`/articles?${params.toString()}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
                }

                const data = await response.json();
                this.articles = data.items ?? [];
                this.pagination = {
                    page: data.page,
                    per_page: data.per_page,
                    total_items: data.total_items,
                    total_pages: data.total_pages,
                };
                console.log(`✅ [articlesApp] loaded ${this.articles.length} articles (page ${this.pagination.page}/${this.pagination.total_pages})`);
            } catch (err) {
                this.error = err.message;
                console.error('❌ [articlesApp] load failed:', err);
            } finally {
                this.loading = false;
            }
        },

        goToPage(page) {
            if (page < 1 || page > this.pagination.total_pages) return;
            this.filters.page = page;
            this.loadArticles();
        },

        editArticle(id) {
            // Redirect to an edit page or open a modal (we'll implement later)
            window.location.href = `/admin/articles/edit/${id}`;
        },

        async createArticle() {
            // Simple redirect to a create page (placeholder)
            window.location.href = '/admin/articles/new';
        },

        async togglePublish(article) {
            const token = localStorage.getItem('anita_token');
            const endpoint = article.enabled
                ? `/articles/${article.id}/unpublish`
                : `/articles/${article.id}/publish`;

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error(`Publish toggle failed: ${await response.text()}`);
                }

                // Reload the list to reflect changes
                this.loadArticles();
            } catch (err) {
                console.error('❌ [articlesApp] togglePublish error:', err);
                alert('Failed to toggle publish status.');
            }
        },

        async deleteArticle(id) {
            if (!confirm('Are you sure you want to delete this article?')) return;

            const token = localStorage.getItem('anita_token');
            try {
                const response = await fetch(`/articles/${id}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`Delete failed: ${await response.text()}`);
                }

                // Reload the list
                this.loadArticles();
            } catch (err) {
                console.error('❌ [articlesApp] delete error:', err);
                alert('Failed to delete article.');
            }
        },
    };
}
