/**
 * SkillHub Admin - User management UI (standalone page)
 */
const Admin = {
    bindEvents() {
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
                        throw new Error(error.detail || '创建用户失败');
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

            if (!response.ok) throw new Error('加载用户失败');

            const users = await response.json();

            if (users.length === 0) {
                container.innerHTML = '<p class="empty">暂无用户</p>';
                return;
            }

            container.innerHTML = users.map(user => `
                <div class="user-card">
                    <div class="user-info">
                        <strong>${this.escapeHtml(user.username)}</strong>
                        <span class="role-badge role-${user.role}">${user.role === 'admin' ? '管理员' : user.role === 'publisher' ? '发布者' : '观察者'}</span>
                    </div>
                    <div class="user-actions">
                        ${user.role !== 'admin' ? `
                            <button class="btn btn-sm btn-secondary" onclick="Admin.changeRole('${user.id}', '${user.role}')">修改角色</button>
                            <button class="btn btn-sm btn-danger" onclick="Admin.deleteUser('${user.id}', '${this.escapeHtml(user.username)}')">删除</button>
                        ` : ''}
                        <button class="btn btn-sm btn-secondary" onclick="Admin.resetPassword('${user.id}', '${this.escapeHtml(user.username)}')">重置密码</button>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            container.innerHTML = '<p class="error">加载用户失败</p>';
            console.error(err);
        }
    },

    async changeRole(userId, currentRole) {
        const roles = ['admin', 'publisher', 'viewer'];
        const roleLabels = { admin: '管理员', publisher: '发布者', viewer: '观察者' };
        const newRole = prompt(`修改用户角色（当前: ${roleLabels[currentRole] || currentRole}）\n可选角色: ${roles.map(r => roleLabels[r]).join(', ')}`, currentRole);

        if (!newRole || newRole === currentRole) return;
        if (!roles.includes(newRole)) {
            alert('无效的角色');
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
                throw new Error(error.detail || '修改角色失败');
            }

            this.loadUsers();
        } catch (err) {
            alert(err.message);
        }
    },

    async deleteUser(userId, username) {
        if (!confirm(`确定要删除用户 "${username}" 吗？`)) return;

        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + Auth.getToken() },
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || '删除用户失败');
            }

            this.loadUsers();
        } catch (err) {
            alert(err.message);
        }
    },

    async resetPassword(userId, username) {
        const newPassword = prompt(`为 "${username}" 输入新密码:`);
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
                throw new Error(error.detail || '重置密码失败');
            }

            alert(`已重置 ${username} 的密码`);
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
