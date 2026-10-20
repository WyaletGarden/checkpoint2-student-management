
        const API_BASE = "/api/v1";

        const PAGE_SIZE = 20;
        const pagination = Object.fromEntries(['students', 'classes', 'teachers'].map(
            group => [group, {skip: 0, renderedSkip: 0, total: 0, request: 0, busy: false}]
        ));

        let accessToken = null;
        let authMode = 'login';
        let sessionController = new AbortController();
        let expiryTimer;
        let searchTimers = {};
        let activeModal = null;
        let lastFocusedElement = null;
        let deleteResolver = null;
        const authForm = document.getElementById('auth-form');
        const authSubmit = document.getElementById('auth-submit');

        function icon(name) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'icon');
            svg.setAttribute('aria-hidden', 'true');
            const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
            use.setAttribute('href', `#i-${name}`);
            svg.append(use);
            return svg;
        }

        function notify(message, error = false) {
            const toast = createTextElement('div', '', `toast${error ? ' error' : ''}`);
            const close = createTextElement('button', '', 'icon-button');
            close.type = 'button';
            close.setAttribute('aria-label', 'Đóng thông báo');
            close.append(icon('close'));
            close.addEventListener('click', () => toast.remove());
            toast.append(icon(error ? 'close' : 'check'), createTextElement('span', message), close);
            const container = document.getElementById('toast-container');
            container.replaceChildren(toast);
            setTimeout(() => toast.remove(), error ? 9000 : 5000);
        }

        function clearFormErrors(form) {
            form.querySelectorAll('.field-error, .form-error-summary').forEach(node => node.remove());
            form.querySelectorAll('[aria-invalid]').forEach(node => {
                node.removeAttribute('aria-invalid');
                const original = node.dataset.originalDescription;
                if (original) node.setAttribute('aria-describedby', original);
                else node.removeAttribute('aria-describedby');
            });
        }

        function fieldError(input, message) {
            input.setAttribute('aria-invalid', 'true');
            if (input.dataset.originalDescription === undefined) input.dataset.originalDescription = input.getAttribute('aria-describedby') || '';
            const error = createTextElement('small', message, 'field-error');
            error.id = `${input.id}-error`;
            error.setAttribute('role', 'alert');
            input.setAttribute('aria-describedby', `${input.dataset.originalDescription} ${error.id}`.trim());
            input.closest('.field').append(error);
        }

        function validateForm(form) {
            clearFormErrors(form);
            let firstInvalid;
            for (const input of form.querySelectorAll('input:not([type="hidden"]), select')) {
                if (input.disabled) continue;
                let message = '';
                if (input.required && !input.value.trim()) message = 'Vui lòng nhập thông tin này.';
                else if (!input.checkValidity()) {
                    if (input.validity.typeMismatch) message = 'Vui lòng nhập địa chỉ email hợp lệ.';
                    else if (input.validity.rangeOverflow || input.validity.rangeUnderflow) message = `Giá trị cần nằm trong khoảng ${input.min}–${input.max}.`;
                    else if (input.validity.tooShort) message = `Vui lòng nhập ít nhất ${input.minLength} ký tự.`;
                    else if (input.validity.patternMismatch) message = 'Tên đăng nhập chỉ gồm chữ không dấu, số và các dấu . _ -.';
                    else message = 'Thông tin chưa hợp lệ. Vui lòng kiểm tra lại.';
                }
                if (message) { fieldError(input, message); firstInvalid ??= input; }
            }
            firstInvalid?.focus();
            return !firstInvalid;
        }

        function setSidebar(open) {
            document.getElementById('sidebar').classList.toggle('is-open', open);
            document.getElementById('sidebar-backdrop').hidden = !open;
            document.getElementById('menu-button').setAttribute('aria-expanded', String(open));
        }

        function cancelledRequest() {
            const error = new Error('Phiên làm việc đã kết thúc.');
            error.silent = true;
            return error;
        }

        function authMessage(message = '', success = false) {
            const element = document.getElementById('auth-message');
            element.textContent = message;
            element.hidden = !message;
            element.className = `auth-notice${success ? ' success' : ''}`;
        }

        function setAuthMode(mode) {
            authMode = mode;
            const registering = mode === 'register';
            clearFormErrors(authForm);
            document.getElementById('auth-title').textContent = registering ? 'Tạo tài khoản' : 'Đăng nhập';
            document.getElementById('auth-description').textContent = registering ? 'Bắt đầu với tài khoản quản lý đào tạo của bạn.' : 'Tiếp tục công việc quản lý đào tạo của bạn.';
            document.getElementById('auth-switch-caption').textContent = registering ? 'Bạn đã có tài khoản?' : 'Bạn chưa có tài khoản?';
            authSubmit.textContent = registering ? 'Đăng ký' : 'Đăng nhập';
            document.getElementById('auth-password').autocomplete = registering ? 'new-password' : 'current-password';
            document.getElementById('auth-password').value = '';
            document.getElementById('auth-password').type = 'password';
            document.getElementById('toggle-password').setAttribute('aria-pressed', 'false');
            document.getElementById('toggle-password').setAttribute('aria-label', 'Hiện mật khẩu');
            document.getElementById('auth-confirm-group').hidden = !registering;
            const confirm = document.getElementById('auth-confirm');
            confirm.disabled = !registering;
            confirm.required = registering;
            confirm.value = '';
            for (const name of ['login', 'register']) {
                const button = document.getElementById(`auth-${name}-tab`);
                button.setAttribute('aria-pressed', String(mode === name));
                button.hidden = mode === name;
            }
            authMessage();
        }

        function endSession(message = '') {
            accessToken = null;
            sessionController.abort();
            sessionController = new AbortController();
            clearTimeout(expiryTimer);
            for (const timer of Object.values(searchTimers)) clearTimeout(timer);
            searchTimers = {};
            setSidebar(false);
            if (activeModal) closeModal(activeModal);
            document.getElementById('toast-container').replaceChildren();
            try { sessionStorage.removeItem('student-admin-session'); } catch { /* Memory-only session. */ }
            document.getElementById('management-app').hidden = true;
            document.getElementById('auth-screen').hidden = false;
            document.getElementById('current-user').textContent = '';
            for (const group of Object.keys(pagination)) {
                const state = pagination[group];
                Object.assign(state, {skip: 0, renderedSkip: 0, total: 0, busy: false, request: state.request + 1});
                document.getElementById(`${group === 'classes' ? 'class' : group === 'teachers' ? 'teacher' : 'student'}-table-body`).replaceChildren();
                renderPagination(group);
                document.getElementById(`search-${group}`).value = '';
            }
            for (const type of ['student', 'class', 'teacher']) {
                closeModal(`${type}-modal`);
                document.getElementById(`${type}-form`).reset();
            }
            for (const id of ['filter-class', 's_class_id', 'c_teacher_id']) {
                document.getElementById(id).replaceChildren();
            }
            document.getElementById('sort-by').value = '';
            authForm.reset();
            setAuthMode('login');
            authMessage(message);
            document.getElementById('auth-username').focus();
        }

        function startSession(token, username) {
            // Decoding exp only schedules UI expiry; the API verifies the JWT.
            const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
            const remaining = payload.exp * 1000 - Date.now();
            if (!Number.isFinite(remaining) || remaining <= 0) throw new Error('Phiên đăng nhập đã hết hạn.');
            accessToken = token;
            try { sessionStorage.setItem('student-admin-session', JSON.stringify({token, username})); } catch { /* Memory-only session. */ }
            clearTimeout(expiryTimer);
            expiryTimer = setTimeout(() => endSession('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.'), Math.min(remaining, 2147483647));
            document.getElementById('current-user').textContent = `Xin chào, ${username}`;
            document.getElementById('auth-screen').hidden = true;
            document.getElementById('management-app').hidden = false;
            authForm.reset();
            switchTab('students');
        }

        async function submitAuth(event) {
            event.preventDefault();
            if (authSubmit.disabled) return;
            authMessage();
            if (!validateForm(authForm)) return;
            const username = document.getElementById('auth-username').value;
            const password = document.getElementById('auth-password').value;
            if (new TextEncoder().encode(password).length > 72) {
                authMessage('Mật khẩu không được vượt quá 72 byte UTF-8.');
                fieldError(document.getElementById('auth-password'), 'Mật khẩu không được vượt quá 72 byte UTF-8.');
                return;
            }
            if (authMode === 'register' && password !== document.getElementById('auth-confirm').value) {
                authMessage('Mật khẩu xác nhận không khớp.');
                fieldError(document.getElementById('auth-confirm'), 'Mật khẩu xác nhận không khớp.');
                return;
            }
            const mode = authMode;
            authSubmit.disabled = true;
            for (const name of ['login', 'register']) document.getElementById(`auth-${name}-tab`).disabled = true;
            authSubmit.textContent = 'Đang xử lý…';
            try {
                const response = await apiRequest(`/${mode}`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                }, false);
                if (mode === 'register') {
                    setAuthMode('login');
                    authMessage('Đăng ký thành công. Vui lòng đăng nhập bằng tài khoản vừa tạo.', true);
                    document.getElementById('auth-password').focus();
                } else {
                    const data = await response.json();
                    startSession(data.access_token, username);
                }
            } catch (error) {
                authMessage(error.message);
                for (const field of error.fields || []) {
                    const id = {username: 'auth-username', password: 'auth-password'}[field.name];
                    if (id) fieldError(document.getElementById(id), field.message);
                }
            } finally {
                authSubmit.disabled = false;
                authSubmit.textContent = authMode === 'register' ? 'Đăng ký' : 'Đăng nhập';
                for (const name of ['login', 'register']) document.getElementById(`auth-${name}-tab`).disabled = false;
            }
        }

        async function restoreSession() {
            authSubmit.disabled = true;
            try {
                const saved = JSON.parse(sessionStorage.getItem('student-admin-session') || 'null');
                if (!saved) return;
                if (typeof saved.token !== 'string' || typeof saved.username !== 'string') throw new Error('Phiên đăng nhập không hợp lệ.');
                accessToken = saved.token;
                // Keep management hidden until the server confirms the saved token.
                await apiRequest(`${API_BASE}/classes/?limit=1`);
                startSession(saved.token, saved.username);
            } catch (error) {
                if (!error.silent) endSession(error.message || 'Vui lòng đăng nhập lại.');
            } finally {
                authSubmit.disabled = false;
            }
        }

        async function apiRequest(url, options = {}, authenticated = true) {
            const token = accessToken;
            if (authenticated && !token) throw cancelledRequest();
            const headers = new Headers(options.headers);
            if (authenticated) headers.set('Authorization', `Bearer ${token}`);
            let response;
            try {
                response = await fetch(url, {...options, headers,
                    signal: authenticated ? sessionController.signal : options.signal});
            } catch (error) {
                if (error.name === 'AbortError') throw cancelledRequest();
                throw new Error('Không thể kết nối máy chủ. Vui lòng thử lại.');
            }
            if (authenticated && token !== accessToken) throw cancelledRequest();
            if (authenticated && response.status === 401) {
                endSession('Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.');
                throw cancelledRequest();
            }
            if (!response.ok) {
                let message = `Yêu cầu thất bại (HTTP ${response.status})`;
                let validationFields = [];
                try {
                    const error = await response.json();
                    if (typeof error.detail === 'string') message = error.detail;
                    else if (Array.isArray(error.detail)) {
                        validationFields = error.detail.map(item => ({name: item.loc?.at(-1), message: item.msg}));
                        message = 'Một số thông tin chưa hợp lệ. Vui lòng kiểm tra các trường bên dưới.';
                    }
                } catch { /* Preserve fallback for non-JSON error responses. */ }
                if (!authenticated && response.status === 401) message = 'Tên đăng nhập hoặc mật khẩu không đúng.';
                if (!authenticated && response.status === 409) message = 'Tên đăng nhập đã được sử dụng.';
                const failure = new Error(message);
                if (response.status === 422) {
                    // Preserve field locations without reflecting submitted values.
                    failure.fields = validationFields;
                }
                throw failure;
            }
            return response;
        }

        function withErrors(action) {
            return async (...args) => {
                try { return await action(...args); }
                catch (error) { if (!error.silent && error.name !== 'AbortError') notify(error.message || 'Đã xảy ra lỗi. Vui lòng thử lại.', true); }
            };
        }

        function withForm(action, formId, fields) {
            return async event => {
                event.preventDefault();
                const form = document.getElementById(formId);
                const button = form.querySelector('button[type="submit"]');
                if (button.disabled || !validateForm(form)) return;
                button.disabled = true;
                const text = button.textContent;
                button.textContent = 'Đang lưu…';
                try {
                    await action(event);
                } catch (error) {
                    if (!error.silent && error.name !== 'AbortError') {
                        const summary = createTextElement('p', error.message, 'form-error-summary');
                        summary.setAttribute('role', 'alert');
                        form.prepend(summary);
                        for (const field of error.fields || []) {
                            const input = document.getElementById(fields[field.name]);
                            if (input) fieldError(input, field.message);
                        }
                        form.querySelector('[aria-invalid="true"]')?.focus();
                    }
                } finally {
                    button.disabled = false;
                    button.textContent = text;
                }
            };
        }

        async function loadAll(group) {
            const token = accessToken;
            const records = [];
            let total;
            do {
                const response = await apiRequest(`${API_BASE}/${group}/?skip=${records.length}&limit=100`);
                const page = await response.json();
                if (token !== accessToken) throw cancelledRequest();
                total = Number(response.headers.get('X-Total-Count'));
                records.push(...page);
                if (page.length === 0) break;
            } while (records.length < total);
            return records;
        }

        function renderPagination(group) {
            const state = pagination[group];
            const container = document.getElementById(`pagination-${group}`);
            const previous = createTextElement('button', '← Trước');
            const next = createTextElement('button', 'Sau →');
            previous.type = next.type = 'button';
            previous.disabled = state.busy || state.skip === 0;
            next.disabled = state.busy || state.skip + PAGE_SIZE >= state.total;
            const move = offset => {
                state.skip += offset;
                return ({students: loadStudents, classes: loadClasses, teachers: loadTeachers})[group]();
            };
            previous.addEventListener('click', () => move(-PAGE_SIZE));
            next.addEventListener('click', () => move(PAGE_SIZE));
            const start = state.total ? state.skip + 1 : 0;
            const label = createTextElement('span', state.busy ? 'Đang tải dữ liệu…' : `Hiển thị ${start}–${Math.min(state.skip + PAGE_SIZE, state.total)} trong ${state.total} bản ghi`);
            const controls = createTextElement('div', '', 'pagination-controls');
            const page = createTextElement('span', `${Math.floor(state.skip / PAGE_SIZE) + 1} / ${Math.max(1, Math.ceil(state.total / PAGE_SIZE))}`, 'page-number');
            controls.append(previous, page, next);
            container.replaceChildren(label, controls);
            document.getElementById(`count-${group}`).textContent = state.total;
        }

        function tableState(group, kind, message = '') {
            const body = document.getElementById(`${group === 'classes' ? 'class' : group === 'teachers' ? 'teacher' : 'student'}-table-body`);
            const row = document.createElement('tr');
            const cell = appendCell(row, '', 'table-state');
            cell.colSpan = {students: 8, classes: 4, teachers: 6}[group];
            if (kind === 'loading') {
                cell.append(createTextElement('span', '', 'spinner'), createTextElement('strong', 'Đang tải dữ liệu…'));
            } else {
                cell.append(icon('search'), createTextElement('strong', kind === 'error' ? 'Chưa thể tải dữ liệu' : 'Chưa có kết quả'), createTextElement('p', message));
                if (kind === 'error') {
                    const retry = createTextElement('button', 'Thử lại', 'button button-secondary');
                    retry.type = 'button';
                    retry.addEventListener('click', () => ({students: loadStudents, classes: loadClasses, teachers: loadTeachers})[group]());
                    cell.append(retry);
                }
            }
            body.replaceChildren(row);
            body.setAttribute('aria-busy', String(kind === 'loading'));
        }

        async function loadPage(group, params = new URLSearchParams()) {
            const state = pagination[group];
            const request = ++state.request;
            state.busy = true;
            renderPagination(group);
            tableState(group, 'loading');
            try {
                const search = document.getElementById(`search-${group}`).value.trim();
                if (search) params.set('q', search);
                params.set('skip', state.skip);
                params.set('limit', PAGE_SIZE);
                const response = await apiRequest(`${API_BASE}/${group}/?${params}`);
                const records = await response.json();
                if (request !== state.request) return null;
                state.total = Number(response.headers.get('X-Total-Count'));
                if (state.skip > 0 && state.skip >= state.total) {
                    state.skip = Math.max(0, Math.ceil(state.total / PAGE_SIZE) - 1) * PAGE_SIZE;
                    return await loadPage(group, params);
                }
                state.renderedSkip = state.skip;
                return records;
            } catch (error) {
                if (request !== state.request) return null;
                state.skip = state.renderedSkip;
                tableState(group, 'error', error.message);
                throw error;
            } finally {
                if (request === state.request) {
                    state.busy = false;
                    renderPagination(group);
                }
            }
        }

        function resetStudentPage() {
            pagination.students.skip = 0;
            loadStudents();
        }

        function switchTab(tab) {
            if (!accessToken) return;
            setSidebar(false);
            document.getElementById('tab-students').classList.add('hidden');
            document.getElementById('tab-classes').classList.add('hidden');
            document.getElementById('tab-teachers').classList.add('hidden');

            for (const group of Object.keys(pagination)) {
                const button = document.getElementById(`btn-${group}`);
                button.className = `nav-item${group === tab ? ' is-active' : ''}`;
                if (group === tab) button.setAttribute('aria-current', 'page');
                else button.removeAttribute('aria-current');
            }

            if(tab === 'students') {
                document.getElementById('tab-students').classList.remove('hidden');
                document.getElementById('page-title').innerText = "Quản lý Sinh viên";
                loadFilterClassDropdown();
                loadStudents();
            } else if(tab === 'classes') {
                document.getElementById('tab-classes').classList.remove('hidden');
                document.getElementById('page-title').innerText = "Quản lý Lớp học";
                loadClasses();
            } else if(tab === 'teachers') {
                document.getElementById('tab-teachers').classList.remove('hidden');
                document.getElementById('page-title').innerText = "Quản lý Giảng viên";
                loadTeachers();
            }
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.add('hidden');
            document.getElementById('management-app').inert = false;
            document.body.classList.remove('modal-open');
            if (activeModal === modalId) {
                activeModal = null;
                lastFocusedElement?.focus();
            }
            if (modalId === 'delete-modal' && deleteResolver) {
                deleteResolver(false);
                deleteResolver = null;
            }
        }

        function showModal(modalId) {
            if (!accessToken) return;
            lastFocusedElement = document.activeElement;
            activeModal = modalId;
            const modal = document.getElementById(modalId);
            const form = modal.querySelector('form');
            if (form) clearFormErrors(form);
            modal.classList.remove('hidden');
            document.getElementById('management-app').inert = true;
            document.body.classList.add('modal-open');
            (modal.querySelector('input:not([type="hidden"]), select') || modal.querySelector('button') || modal).focus();
        }

        async function openStudentModal() {
            document.getElementById('student-modal-title').innerText = "Thêm Sinh viên mới";
            document.getElementById('student-form').reset();
            document.getElementById('s_id').value = "";
            await loadClassDropdown();
            showModal('student-modal');
        }

        async function openClassModal() {
            document.getElementById('class-modal-title').innerText = "Thêm Lớp học mới";
            document.getElementById('class-form').reset();
            document.getElementById('c_id').value = "";
            await loadTeacherDropdown();
            showModal('class-modal');
        }

        async function openTeacherModal() {
            document.getElementById('teacher-modal-title').innerText = "Thêm Giảng viên mới";
            document.getElementById('teacher-form').reset();
            document.getElementById('t_id').value = "";
            showModal('teacher-modal');
        }

        async function editStudent(id, lastName, firstName, email, phone, major, score, classId) {
            document.getElementById('student-modal-title').innerText = "Cập nhật thông tin Sinh viên";
            document.getElementById('s_id').value = id;
            document.getElementById('s_lastname').value = lastName;
            document.getElementById('s_firstname').value = firstName;
            document.getElementById('s_email').value = email || "";
            document.getElementById('s_phone').value = phone || "";
            document.getElementById('s_major').value = major || "";
            document.getElementById('s_score').value = (score !== null && score !== undefined) ? score : "";
            await loadClassDropdown();
            document.getElementById('s_class_id').value = classId;
            showModal('student-modal');
        }

        async function editClass(id, className, teacherId) {
            document.getElementById('class-modal-title').innerText = "Cập nhật thông tin Lớp học";
            document.getElementById('c_id').value = id;
            document.getElementById('c_name').value = className;
            await loadTeacherDropdown();
            document.getElementById('c_teacher_id').value = teacherId || "";
            showModal('class-modal');
        }

        async function editTeacher(id, lastName, firstName, email, phone, degree) {
            document.getElementById('teacher-modal-title').innerText = "Cập nhật thông tin Giảng viên";
            document.getElementById('t_id').value = id;
            document.getElementById('t_lastname').value = lastName;
            document.getElementById('t_firstname').value = firstName;
            document.getElementById('t_email').value = email || "";
            document.getElementById('t_phone').value = phone || "";
            document.getElementById('t_degree').value = degree || "";
            showModal('teacher-modal');
        }

        // API values are text, never HTML or executable event attributes.
        function createTextElement(tag, value, className = '') {
            const element = document.createElement(tag);
            element.textContent = value ?? '';
            element.className = className;
            return element;
        }

        function appendCell(row, value, className = '') {
            const cell = createTextElement('td', value, className);
            row.append(cell);
            return cell;
        }

        function appendBadge(row, value, className = 'badge') {
            const cell = appendCell(row, '');
            cell.append(createTextElement('span', value, className));
        }

        function appendActions(row, onEdit, type, id) {
            const cell = appendCell(row, '');
            const actions = createTextElement('div', '', 'cell-actions');
            const editButton = createTextElement('button', '', 'icon-button');
            editButton.setAttribute('aria-label', `Sửa bản ghi ${id}`);
            editButton.title = 'Chỉnh sửa';
            editButton.append(icon('edit'));
            editButton.type = 'button';
            editButton.addEventListener('click', onEdit);
            const deleteButton = createTextElement('button', '', 'icon-button delete-button');
            deleteButton.setAttribute('aria-label', `Xóa bản ghi ${id}`);
            deleteButton.title = 'Xóa bản ghi';
            deleteButton.append(icon('trash'));
            deleteButton.type = 'button';
            deleteButton.addEventListener('click', () => deleteItem(type, id));
            actions.append(editButton, deleteButton);
            cell.append(actions);
        }

        function renderRows(bodyId, records, columnCount, emptyMessage, buildRow) {
            const fragment = document.createDocumentFragment();
            for (const record of records) {
                const row = document.createElement('tr');
                buildRow(row, record);
                fragment.append(row);
            }
            if (records.length === 0) {
                const row = document.createElement('tr');
                const cell = appendCell(row, '', 'table-state');
                cell.append(icon('search'), createTextElement('strong', emptyMessage), createTextElement('p', 'Thêm bản ghi mới hoặc thử thay đổi từ khóa và bộ lọc.'));
                cell.colSpan = columnCount;
                fragment.append(row);
            }
            document.getElementById(bodyId).replaceChildren(fragment);
            document.getElementById(bodyId).setAttribute('aria-busy', 'false');
        }

        function renderOptions(selectId, placeholder, records, getLabel) {
            const fragment = document.createDocumentFragment();
            const defaultOption = createTextElement('option', placeholder);
            defaultOption.value = '';
            fragment.append(defaultOption);
            for (const record of records) {
                const option = createTextElement('option', getLabel(record));
                option.value = record.id;
                fragment.append(option);
            }
            const select = document.getElementById(selectId);
            const previous = select.value;
            select.replaceChildren(fragment);
            if (Array.from(select.options).some(option => option.value === previous)) select.value = previous;
        }

        async function loadClassDropdown() {
            const classes = await loadAll('classes');
            renderOptions('s_class_id', '-- Chọn lớp quản lý --', classes,
                c => `${c.class_code} - ${c.class_name}`);
        }

        async function loadFilterClassDropdown() {
            const classes = await loadAll('classes');
            renderOptions('filter-class', '-- Tất cả các lớp --', classes,
                c => `${c.class_code} - ${c.class_name}`);
        }

        async function loadTeacherDropdown() {
            const teachers = await loadAll('teachers');
            renderOptions('c_teacher_id', '-- Chọn giảng viên cố vấn --', teachers,
                t => `${t.teacher_code} - ${t.last_name} ${t.first_name}`);
        }

        async function loadStudents() {
            const classId = document.getElementById('filter-class').value;
            const sortBy = document.getElementById('sort-by').value;
            const params = new URLSearchParams();
            if (classId) params.set('class_id', classId);
            if (sortBy) params.set('sort_by', sortBy);
            const students = await loadPage('students', params);
            if (!students) return;
            renderRows('student-table-body', students, 8, 'Không tìm thấy sinh viên nào', (row, s) => {
                appendCell(row, s.student_code);
                appendCell(row, s.last_name, 'cell-name');
                appendCell(row, s.first_name, 'cell-name');
                const className = s.class_room ? `${s.class_room.class_code} - ${s.class_room.class_name}` : 'Chưa phân lớp';
                appendBadge(row, className);
                appendCell(row, s.email);
                appendCell(row, s.major);
                if (s.score !== null && s.score !== undefined) {
                    appendBadge(row, s.score, 'badge badge-score');
                } else {
                    appendBadge(row, 'Chưa có');
                }
                appendActions(row, () => editStudent(s.id, s.last_name, s.first_name,
                    s.email, s.phone, s.major, s.score, s.class_id), 'students', s.id);
            });
        }

        async function loadClasses() {
            const classes = await loadPage('classes');
            if (!classes) return;
            renderRows('class-table-body', classes, 4, 'Chưa có dữ liệu lớp học', (row, c) => {
                appendCell(row, c.class_code);
                appendCell(row, c.class_name, 'cell-name');
                appendCell(row, c.advisor ? `${c.advisor.last_name} ${c.advisor.first_name}` : 'Chưa có');
                appendActions(row, () => editClass(c.id, c.class_name, c.teacher_id), 'classes', c.id);
            });
        }

        async function loadTeachers() {
            const teachers = await loadPage('teachers');
            if (!teachers) return;
            renderRows('teacher-table-body', teachers, 6, 'Chưa có dữ liệu giảng viên', (row, t) => {
                appendCell(row, t.teacher_code);
                appendCell(row, `${t.last_name} ${t.first_name}`, 'cell-name');
                appendBadge(row, t.degree || 'Chưa cập nhật');
                appendCell(row, t.email);
                appendCell(row, t.phone);
                appendActions(row, () => editTeacher(t.id, t.last_name, t.first_name,
                    t.email, t.phone, t.degree), 'teachers', t.id);
            });
        }

        async function saveStudent(e) {
            e.preventDefault();
            let id = document.getElementById('s_id').value;
            let scoreVal = document.getElementById('s_score').value;
            let data = {
                last_name: document.getElementById('s_lastname').value,
                first_name: document.getElementById('s_firstname').value,
                email: document.getElementById('s_email').value || null,
                phone: document.getElementById('s_phone').value || null,
                major: document.getElementById('s_major').value || null,
                score: scoreVal !== "" ? parseFloat(scoreVal) : null,
                class_id: parseInt(document.getElementById('s_class_id').value)
            };
            
            let url = id ? `${API_BASE}/students/${id}` : `${API_BASE}/students/`;
            let method = id ? 'PUT' : 'POST';

            let res = await apiRequest(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            closeModal('student-modal');
            notify(id ? 'Đã cập nhật thông tin sinh viên.' : 'Đã thêm sinh viên mới.');
            await loadStudents();
        }

        async function saveClass(e) {
            e.preventDefault();
            let id = document.getElementById('c_id').value;
            let teacherIdVal = document.getElementById('c_teacher_id').value;
            let data = {
                class_name: document.getElementById('c_name').value,
                teacher_id: teacherIdVal ? parseInt(teacherIdVal) : null
            };

            let url = id ? `${API_BASE}/classes/${id}` : `${API_BASE}/classes/`;
            let method = id ? 'PUT' : 'POST';

            let res = await apiRequest(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            closeModal('class-modal');
            notify(id ? 'Đã cập nhật lớp học.' : 'Đã thêm lớp học mới.');
            await loadClasses();
        }

        async function saveTeacher(e) {
            e.preventDefault();
            let id = document.getElementById('t_id').value;
            let data = {
                last_name: document.getElementById('t_lastname').value,
                first_name: document.getElementById('t_firstname').value,
                email: document.getElementById('t_email').value || null,
                phone: document.getElementById('t_phone').value || null,
                degree: document.getElementById('t_degree').value || null
            };

            let url = id ? `${API_BASE}/teachers/${id}` : `${API_BASE}/teachers/`;
            let method = id ? 'PUT' : 'POST';

            let res = await apiRequest(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            closeModal('teacher-modal');
            notify(id ? 'Đã cập nhật thông tin giảng viên.' : 'Đã thêm giảng viên mới.');
            await loadTeachers();
        }

        async function deleteItem(type, id) {
            showModal('delete-modal');
            const approved = await new Promise(resolve => { deleteResolver = resolve; });
            if (!approved || !accessToken) return;
            await apiRequest(`${API_BASE}/${type}/${id}`, {method: 'DELETE'});
            notify('Đã xóa bản ghi.');
            await ({students: loadStudents, classes: loadClasses, teachers: loadTeachers})[type]();
        }
        // Catch errors at UI entry points; nested dropdown loads still propagate
        // failures so an edit form never opens with incomplete options.
        loadStudents = withErrors(loadStudents);
        loadClasses = withErrors(loadClasses);
        loadTeachers = withErrors(loadTeachers);
        loadFilterClassDropdown = withErrors(loadFilterClassDropdown);
        openStudentModal = withErrors(openStudentModal);
        openClassModal = withErrors(openClassModal);
        editStudent = withErrors(editStudent);
        editClass = withErrors(editClass);
        saveStudent = withForm(saveStudent, 'student-form', {last_name: 's_lastname', first_name: 's_firstname', email: 's_email', phone: 's_phone', major: 's_major', score: 's_score', class_id: 's_class_id'});
        saveClass = withForm(saveClass, 'class-form', {class_name: 'c_name', teacher_id: 'c_teacher_id'});
        saveTeacher = withForm(saveTeacher, 'teacher-form', {last_name: 't_lastname', first_name: 't_firstname', email: 't_email', phone: 't_phone', degree: 't_degree'});
        deleteItem = withErrors(deleteItem);
        for (const group of Object.keys(pagination)) {
            renderPagination(group);
            document.getElementById(`search-${group}`).addEventListener('input', () => {
                clearTimeout(searchTimers[group]);
                pagination[group].request++;
                searchTimers[group] = setTimeout(() => {
                    if (!accessToken) return;
                    pagination[group].skip = 0;
                    ({students: loadStudents, classes: loadClasses, teachers: loadTeachers})[group]();
                }, 300);
            });
        }

        document.getElementById('toggle-password').addEventListener('click', () => {
            const input = document.getElementById('auth-password');
            const visible = input.type === 'password';
            input.type = visible ? 'text' : 'password';
            document.getElementById('toggle-password').setAttribute('aria-label', visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
            document.getElementById('toggle-password').setAttribute('aria-pressed', String(visible));
        });
        document.getElementById('menu-button').addEventListener('click', () => setSidebar(true));
        document.getElementById('sidebar-backdrop').addEventListener('click', () => setSidebar(false));
        document.getElementById('delete-cancel').addEventListener('click', () => closeModal('delete-modal'));
        document.getElementById('delete-confirm').addEventListener('click', () => {
            const resolve = deleteResolver;
            deleteResolver = null;
            closeModal('delete-modal');
            resolve?.(true);
        });
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                if (activeModal) closeModal(activeModal);
                else setSidebar(false);
            }
            if (event.key === 'Tab' && activeModal) {
                const focusable = [...document.getElementById(activeModal).querySelectorAll('button:not(:disabled), input:not([type="hidden"]):not(:disabled), select:not(:disabled)')];
                const first = focusable[0], last = focusable.at(-1);
                if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
                else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
            }
        });

        authForm.addEventListener('submit', submitAuth);
        document.getElementById('auth-login-tab').addEventListener('click', () => setAuthMode('login'));
        document.getElementById('auth-register-tab').addEventListener('click', () => setAuthMode('register'));
        document.getElementById('logout-button').addEventListener('click', () => endSession('Bạn đã đăng xuất.'));
        restoreSession();
    
