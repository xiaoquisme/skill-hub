/**
 * SkillHub Admin - User management UI
 */
const Admin = {
    init() {
        this.bindEvents();
        this.checkAuth();
    },

    checkAuth() {
        const loginSection = document.getElementById('login-section');
        const appSection = document.getElementById('app-section');
        const adminSection = document.getElementById('admin-section');
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const userStatus = document.getElementById('user-status');

        if (Auth.isLoggedIn()) {
            loginSection.classList.add('hidden');
            appSection.classList.remove('hidden');
            loginBtn.classList.add('hidden');
            logoutBtn.classList.remove('hidden');

            const user = Auth.getUser();
            if (user) {
                userStatus.textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);
                userStatus.classList.remove('hidden');
            }

            if (Auth.isAdmin()) {
                adminSection.classList.remove('hidden');
            } else {
                adminSection.classList.add('hidden');
            }
        } else {
            loginSection.classList.remove('hidden');
            appSection.classList.add('hidden');
            adminSection.classList.add('hidden');
            loginBtn.classList.remove('hidden');
            logoutBtn.classList.add('hidden');
            userStatus.classList.add('hidden');
        }
    },

    bindEvents() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('login-username').value;
                const password = document.getElementById('login-password').value;
                const errorEl = document.getElementById('login-error');

                try {
                    await Auth.login(username, password);
                    errorEl.classList.add('hidden');
                    this.checkAuth();
                    // Reload skills after login
                    if (typeof window.loadSkills === 'function') {
                        window.loadSkills();
                    }
                } catch (err) {
                    errorEl.textContent = err.message;
                    errorEl.classList.remove('hidden');
                }
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                Auth.logout();
                this.checkAuth();
                // Reload skills after logout
                if (typeof window.loadSkills === 'function') {
                    window.loadSkills();
                }
            });
        }

        // Create user form
        const createUserForm = document.getElementById('create-user-form');
        if (createUserForm) {
            createUserForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('new-username').value;
                const password = document.getElementById('new-password').value;
                const role = document.getElementById('new-role').value;

                try {
                    const response = await fetch('/api/users', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + Auth.getToken(),
                        },
                        body: JSON.stringify({ username, password, role }),
                    });

                    if (!response.ok) {
                        const error = await response.json().catch(() => ({}));
                        throw new Error(error.detail || 'Failed to create user');
                    }

                    createUserForm.reset();
                    this.loadUsers();
                } catch (err) {
                    alert(err.message);
                }
            });
        }

        // Load users button
        const loadUsersBtn = document.getElementById('load-users-btn');
        if (loadUsersBtn) {
            loadUsersBtn.addEventListener('click', () => this.loadUsers());
        }
    },

    async loadUsers() {
        const container = document.getElementById('users-list');
        if (!container) return;

        try {
            const response = await fetch('/api/users', {
                headers: { 'Authorization': 'Bearer ' + Auth.getToken() },
            });

            if (!response.ok) throw new Error('Failed to load users');

            const users = await response.json();

            if (users.length === 0) {
                container.innerHTML = '<p class="empty">No users found</p>';
                return;
            }

            container.innerHTML = users.map(user => `
                <div class="user-card">
                    <div class="user-info">
                        <strong>${this.escapeHtml(user.username)}</strong>
                        <span class="role-badge role-${user.role}">${user.role}</span>
                    </div>
                    <div class="user-actions">
                        ${user.role !== 'admin' ? `
                            <button class="btn btn-sm btn-secondary" onclick="Admin.changeRole('${user.id}', '${user.role}')">Change Role</button>
                            <button class="btn btn-sm btn-danger" onclick="Admin.deleteUser('${user.id}', '${this.escapeHtml(user.username)}')">Delete</button>
                        ` : ''}
                        <button class="btn btn-sm btn-secondary" onclick="Admin.resetPassword('${user.id}', '${this.escapeHtml(user.username)}')">Reset Password</button>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            container.innerHTML = '<p class="error">Failed to load users</p>';
            console.error(err);
        }
    },

    async changeRole(userId, currentRole) {
        const roles = ['admin', 'publisher', 'viewer'];
        const newRole = prompt(`Change role for user (current: ${currentRole})\nAvailable roles: ${roles.join(', ')}`, currentRole);

        if (!newRole || newRole === currentRole) return;
        if (!roles.includes(newRole)) {
            alert('Invalid role');
            return;
        }

        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + Auth.getToken(),
                },
                body: JSON.stringify({
                    username: 'placeholder',
                    password: 'placeholder',
                    role: newRole,
                }),
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Failed to update role');
            }

            this.loadUsers();
        } catch (err) {
            alert(err.message);
        }
    },

    async deleteUser(userId, username) {
        if (!confirm(`Are you sure you want to delete user "${username}"?`)) return;

        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + Auth.getToken() },
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Failed to delete user');
            }

            this.loadUsers();
        } catch (err) {
            alert(err.message);
        }
    },

    async resetPassword(userId, username) {
        const newPassword = prompt(`Enter new password for "${username}":`);
        if (!newPassword) return;

        try {
            const response = await fetch(`/api/users/${userId}/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + Auth.getToken(),
                },
                body: JSON.stringify({ new_password: newPassword }),
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Failed to reset password');
            }

            alert(`Password reset for ${username}`);
        } catch (err) {
            alert(err.message);
        }
    },

    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
};
