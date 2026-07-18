/**
 * SkillHub Web UI Application
 */
(function() {
    'use strict';

    // DOM Elements
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const categoryFilter = document.getElementById('category-filter');
    const sortFilter = document.getElementById('sort-filter');
    const skillList = document.getElementById('skill-list');
    const modal = document.getElementById('skill-modal');
    const skillDetail = document.getElementById('skill-detail');
    const modalClose = document.querySelector('.modal-close');

    let allSkills = [];
    let categories = new Set();

    // Initialize
    async function init() {
        await loadSkills();
        setupEventListeners();
    }

    // Load skills from API
    async function loadSkills(query, category, sort) {
        skillList.innerHTML = '<div class="loading">Loading skills...</div>';

        try {
            allSkills = await API.listSkills({ query, category, sort });
            categories = new Set(allSkills.map(s => s.category).filter(Boolean));
            updateCategoryFilter();
            renderSkills(allSkills);
        } catch (err) {
            skillList.innerHTML = '<div class="empty">Failed to load skills. Is the server running?</div>';
            console.error('Failed to load skills:', err);
        }
    }

    // Update category filter dropdown
    function updateCategoryFilter() {
        const current = categoryFilter.value;
        categoryFilter.innerHTML = '<option value="">All Categories</option>';

        Array.from(categories).sort().forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            if (cat === current) option.selected = true;
            categoryFilter.appendChild(option);
        });
    }

    // Render skill cards
    function renderSkills(skills) {
        if (skills.length === 0) {
            skillList.innerHTML = '<div class="empty">No skills found</div>';
            return;
        }

        skillList.innerHTML = skills.map(skill => `
            <div class="skill-card" data-id="${skill.id}">
                <h3>${escapeHtml(skill.display_name || skill.name)}</h3>
                <p class="description">${escapeHtml(skill.description || 'No description')}</p>
                <div class="meta">
                    ${skill.category ? `<span class="category">${escapeHtml(skill.category)}</span>` : ''}
                    ${(skill.tags || []).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            </div>
        `).join('');

        // Add click handlers
        document.querySelectorAll('.skill-card').forEach(card => {
            card.addEventListener('click', () => showSkillDetail(card.dataset.id));
        });
    }

    // Show skill detail modal
    async function showSkillDetail(skillId) {
        try {
            const skill = await API.getSkill(skillId);
            skillDetail.innerHTML = `
                <h2>${escapeHtml(skill.display_name || skill.name)}</h2>
                <p class="description">${escapeHtml(skill.description || 'No description available')}</p>

                <dl class="metadata">
                    <dt>Name</dt>
                    <dd>${escapeHtml(skill.name)}</dd>
                    ${skill.author ? `<dt>Author</dt><dd>${escapeHtml(skill.author)}</dd>` : ''}
                    ${skill.category ? `<dt>Category</dt><dd>${escapeHtml(skill.category)}</dd>` : ''}
                    ${skill.license ? `<dt>License</dt><dd>${escapeHtml(skill.license)}</dd>` : ''}
                    ${(skill.tags || []).length > 0 ? `<dt>Tags</dt><dd>${skill.tags.map(t => escapeHtml(t)).join(', ')}</dd>` : ''}
                    <dt>Updated</dt>
                    <dd>${new Date(skill.updated_at).toLocaleDateString()}</dd>
                </dl>

                ${skill.files && skill.files.length > 0 ? `
                    <div class="file-list">
                        <h4>Files (${skill.files.length})</h4>
                        <ul>
                            ${skill.files.map(f => `<li>${escapeHtml(f.filename)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                <div class="install-command">
                    <code>skillhub install ${escapeHtml(skill.name)}</code>
                    <button class="copy-btn" onclick="copyInstallCommand('${escapeHtml(skill.name)}')">Copy</button>
                </div>
            `;

            modal.classList.remove('hidden');
        } catch (err) {
            console.error('Failed to load skill detail:', err);
        }
    }

    // Copy install command to clipboard
    window.copyInstallCommand = function(name) {
        const cmd = `skillhub install ${name}`;
        navigator.clipboard.writeText(cmd).then(() => {
            const btn = document.querySelector('.copy-btn');
            if (btn) {
                btn.textContent = 'Copied!';
                setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
            }
        });
    };

    // Setup event listeners
    function setupEventListeners() {
        // Search
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch();
        });

        // Filters
        categoryFilter.addEventListener('change', performSearch);
        sortFilter.addEventListener('change', performSearch);

        // Modal close
        modalClose.addEventListener('click', () => modal.classList.add('hidden'));
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.add('hidden');
        });

        // Escape key closes modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') modal.classList.add('hidden');
        });
    }

    // Perform search with current filters
    function performSearch() {
        const query = searchInput.value.trim();
        const category = categoryFilter.value;
        const sort = sortFilter.value;
        loadSkills(query || undefined, category || undefined, sort);
    }

    // Escape HTML to prevent XSS
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Start the app
    init();
})();
