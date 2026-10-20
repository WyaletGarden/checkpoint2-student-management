// Dependency-free checks: node tests/frontend_auth.test.mjs
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const html = await readFile(new URL('../frontend/index.html', import.meta.url), 'utf8');
const source = await readFile(new URL('../frontend/app.js', import.meta.url), 'utf8');
new vm.Script(source);

function harness(savedSession = null) {
    const elements = new Map();
    let dom;
    function element(id = '') {
        const attributes = new Map();
        const classes = new Set();
        const item = {id, value: '', hidden: false, disabled: false, textContent: '', children: [], dataset: {},
            controls: [], listeners: {}, validity: {},
            checkValidity() { return true; },
            classList: {add: value => classes.add(value), remove: value => classes.delete(value),
                contains: value => classes.has(value), toggle(value, on) { on ? classes.add(value) : classes.delete(value); }},
            setAttribute(name, value) { attributes.set(name, value); },
            getAttribute(name) { return attributes.get(name); },
            removeAttribute(name) { attributes.delete(name); },
            addEventListener(name, action) { this.listeners[name] = action; },
            focus() { if (dom) dom.activeElement = item; },
            querySelectorAll(selector) {
                if (selector.includes('.field-error')) return [...this.children, ...this.controls.flatMap(control => control.children)];
                if (selector === '[aria-invalid]') return this.controls.filter(control => control.getAttribute('aria-invalid'));
                return this.controls.filter(control => control.type !== 'hidden');
            },
            querySelector(selector) {
                if (selector === 'form') return elements.get(id.replace('-modal', '-form')) || null;
                if (selector === 'button[type="submit"]') return this.submitButton;
                if (selector === '[aria-invalid="true"]') return this.controls.find(control => control.getAttribute('aria-invalid') === 'true');
                return this.controls.find(control => control.type !== 'hidden') || null;
            },
            closest() { return item; }, remove() {
                if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this);
            },
            append(...items) {
                this.children.push(...items);
                for (const child of items) { child.parent = item; if (child.id) elements.set(child.id, child); }
            },
            prepend(child) { child.parent = item; this.children.unshift(child); },
            replaceChildren(...items) { this.children = items; },
            reset() {
                if (id === 'auth-form') {
                    for (const name of ['auth-username', 'auth-password', 'auth-confirm']) elements.get(name).value = '';
                }
            }};
        return item;
    }
    for (const match of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)) {
        const item = element(match[1]);
        item.hidden = /\bhidden(?:\s|>)/.test(match[0]);
        item.type = match[0].match(/type="([^"]+)"/)?.[1];
        item.required = /\brequired\b/.test(match[0]);
        for (const name of (match[0].match(/class="([^"]+)"/)?.[1] || '').split(' ')) item.classList.add(name);
        elements.set(item.id, item);
    }
    for (const match of html.matchAll(/<form id="([^"]+)"[^>]*>([\s\S]*?)<\/form>/g)) {
        const form = elements.get(match[1]);
        form.controls = [...match[2].matchAll(/<(?:input|select)[^>]*id="([^"]+)"/g)].map(match => elements.get(match[1]));
        form.submitButton = form.id === 'auth-form' ? elements.get('auth-submit') : element();
    }
    const storage = new Map(savedSession ? [['student-admin-session', JSON.stringify(savedSession)]] : []);
    const requests = [];
    let respond = () => ({status: 200, data: []});
    dom = {getElementById: id => elements.get(id), createElement: () => element(),
            createElementNS: () => element(), createDocumentFragment: () => element(),
            addEventListener() {}, body: element()};
    const context = vm.createContext({
        document: dom,
        sessionStorage: {getItem: key => storage.get(key) ?? null,
            setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key)},
        Headers, AbortController, TextEncoder, URLSearchParams,
        atob: value => Buffer.from(value, 'base64').toString('binary'),
        setTimeout: () => 1, clearTimeout() {},
        alert: message => { throw new Error(`Unexpected alert: ${message}`); },
        fetch: async (url, options) => {
            requests.push({url, ...options});
            const result = await respond(url, options);
            return {status: result.status, ok: result.status >= 200 && result.status < 300,
                headers: new Headers({'X-Total-Count': '0'}), json: async () => result.data};
        },
    });
    // Start restoration explicitly; isolate auth from table rendering in these checks.
    vm.runInContext(source.replace(/        restoreSession\(\);/, '') + '\nloadStudents = async () => {}; loadFilterClassDropdown = async () => {};', context);
    return {elements, storage, requests, dom, run: code => vm.runInContext(code, context),
        respond: callback => { respond = callback; }};
}

const token = `header.${Buffer.from(JSON.stringify({exp: Math.floor(Date.now() / 1000) + 1800})).toString('base64url')}.signature`;
function fill(h, password = 'StrongPassword123!') {
    h.elements.get('auth-username').value = 'student01';
    h.elements.get('auth-password').value = password;
}
const submit = h => h.run('submitAuth({preventDefault() {}})');

const h = harness();
await h.run('restoreSession()');
assert.equal(h.requests.length, 0);
assert.equal(h.elements.get('management-app').hidden, true);

h.run("setAuthMode('register')");
fill(h);
h.elements.get('auth-confirm').value = 'Mismatch';
await submit(h);
assert.match(h.elements.get('auth-message').textContent, /không khớp/);
assert.equal(h.requests.length, 0);

fill(h, 'é'.repeat(37));
await submit(h);
assert.match(h.elements.get('auth-message').textContent, /72 byte/);
assert.equal(h.requests.length, 0);

fill(h);
h.elements.get('auth-confirm').value = 'StrongPassword123!';
h.respond(() => ({status: 409, data: {detail: 'Username already registered'}}));
await submit(h);
assert.match(h.elements.get('auth-message').textContent, /đã được sử dụng/);

h.respond(() => ({status: 201, data: {id: 1, username: 'student01'}}));
await submit(h);
assert.equal(h.requests.at(-1).url, '/register');
assert.equal(h.requests.at(-1).headers.has('Authorization'), false);
assert.equal(h.elements.get('auth-password').value, '');
assert.equal(h.elements.get('auth-confirm').disabled, true);
assert.match(h.elements.get('auth-message').textContent, /Đăng ký thành công/);

fill(h);
h.respond(() => ({status: 401, data: {detail: 'Incorrect username or password'}}));
await submit(h);
assert.match(h.elements.get('auth-message').textContent, /không đúng/);
assert.equal(h.elements.get('management-app').hidden, true);

h.respond(() => ({status: 200, data: {access_token: token, token_type: 'bearer'}}));
await submit(h);
assert.equal(h.requests.at(-1).url, '/login');
assert.equal(h.elements.get('management-app').hidden, false);
assert.equal(h.elements.get('auth-screen').hidden, true);
assert.equal(h.elements.get('current-user').textContent, 'Xin chào, student01');
assert.equal(h.elements.get('auth-password').value, '');
assert.equal(JSON.parse(h.storage.get('student-admin-session')).token, token);

h.respond(() => ({status: 200, data: []}));
await h.run("apiRequest('/api/v1/students/')");
assert.equal(h.requests.at(-1).headers.get('Authorization'), `Bearer ${token}`);

h.respond(() => ({status: 403, data: {detail: 'Admin role required'}}));
await assert.rejects(h.run("apiRequest('/api/v1/students/1', {method: 'DELETE'})"),
    error => error.message === 'Admin role required');
assert.equal(h.elements.get('management-app').hidden, false);
assert.equal(JSON.parse(h.storage.get('student-admin-session')).token, token);

h.elements.get('student-table-body').children.push('private-data');
h.respond(() => ({status: 401, data: {detail: 'Invalid token'}}));
await assert.rejects(h.run("apiRequest('/api/v1/students/')"), error => error.silent);
assert.equal(h.elements.get('management-app').hidden, true);
assert.equal(h.elements.get('auth-screen').hidden, false);
assert.equal(h.storage.size, 0);
assert.equal(h.elements.get('student-table-body').children.length, 0);
assert.match(h.elements.get('auth-message').textContent, /hết hạn/);
const requestCount = h.requests.length;
await assert.rejects(h.run("apiRequest('/api/v1/classes/')"), error => error.silent);
assert.equal(h.requests.length, requestCount);

const restored = harness({token, username: 'student01'});
await restored.run('restoreSession()');
assert.equal(restored.requests[0].headers.get('Authorization'), `Bearer ${token}`);
assert.equal(restored.elements.get('management-app').hidden, false);
restored.run("endSession('Bạn đã đăng xuất.')");
assert.equal(restored.elements.get('management-app').hidden, true);
assert.equal(restored.storage.size, 0);

const invalid = harness({token, username: 'student01'});
invalid.respond(() => ({status: 401, data: {detail: 'Expired'}}));
await invalid.run('restoreSession()');
assert.equal(invalid.elements.get('management-app').hidden, true);
assert.equal(invalid.storage.size, 0);

// A late response from the previous session must not reopen or refill the UI.
const race = harness({token, username: 'student01'});
await race.run('restoreSession()');
let release;
race.respond(() => new Promise(resolve => { release = resolve; }));
const pending = race.run("apiRequest('/api/v1/students/')");
race.run('endSession()');
release({status: 200, data: []});
await assert.rejects(pending, error => error.silent);
assert.equal(race.elements.get('management-app').hidden, true);

// Exercise management requests, feedback, validation and dialog decisions.
const management = harness({token, username: 'student01'});
await management.run('restoreSession()');
management.elements.get('search-classes').value = 'CNTT';
management.respond(() => ({status: 200, data: []}));
await management.run("loadPage('classes')");
assert.match(management.requests.at(-1).url, /q=CNTT/);
assert.equal(management.elements.get('count-classes').textContent, 0);

await management.run('openTeacherModal()');
assert.equal(management.elements.get('teacher-modal').classList.contains('hidden'), false);
assert.equal(management.elements.get('management-app').inert, true);
const beforeInvalidSave = management.requests.length;
await management.run('saveTeacher({preventDefault() {}})');
assert.equal(management.requests.length, beforeInvalidSave);
assert.equal(management.elements.get('t_lastname').getAttribute('aria-invalid'), 'true');
management.elements.get('t_lastname').value = 'Le';
management.elements.get('t_firstname').value = 'An';
management.elements.get('t_email').value = 'an@example.com';
management.respond((url, options) => ({status: options.method === 'POST' ? 201 : 200, data: options.method === 'POST' ? {} : []}));
await management.run('saveTeacher({preventDefault() {}})');
const create = management.requests.find(request => request.method === 'POST');
assert.equal(create.url, '/api/v1/teachers/');
assert.equal(create.headers.get('Authorization'), `Bearer ${token}`);
assert.equal(JSON.parse(create.body).first_name, 'An');
assert.equal(management.elements.get('teacher-modal').classList.contains('hidden'), true);
assert.equal(management.elements.get('management-app').inert, false);

const beforeCancel = management.requests.length;
const cancelledDelete = management.run("deleteItem('teachers', 5)");
management.elements.get('delete-cancel').listeners.click();
await cancelledDelete;
assert.equal(management.requests.length, beforeCancel);
const confirmedDelete = management.run("deleteItem('teachers', 5)");
management.elements.get('delete-confirm').listeners.click();
await confirmedDelete;
assert.equal(management.requests.find(request => request.method === 'DELETE').url, '/api/v1/teachers/5');

management.run("endSession()");
management.elements.get('toggle-password').listeners.click();
assert.equal(management.elements.get('auth-password').type, 'text');
management.elements.get('toggle-password').listeners.click();
assert.equal(management.elements.get('auth-password').type, 'password');
management.elements.get('menu-button').listeners.click();
assert.equal(management.elements.get('sidebar').classList.contains('is-open'), true);
management.elements.get('sidebar-backdrop').listeners.click();
assert.equal(management.elements.get('sidebar').classList.contains('is-open'), false);

// All hard-coded element references and form labels must resolve after redesign.
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
assert.equal(new Set(ids).size, ids.length, 'Duplicate HTML IDs');
for (const match of source.matchAll(/getElementById\('([^']+)'\)/g)) assert.ok(ids.includes(match[1]), `Missing element ${match[1]}`);
for (const match of html.matchAll(/\bfor="([^"]+)"/g)) assert.ok(ids.includes(match[1]), `Missing label target ${match[1]}`);
assert.ok(!/\b(?:alert|confirm)\(/.test(source), 'Native popups should be replaced by in-page feedback');
console.log('Frontend checks passed: auth, search requests, form validation, CRUD, delete decisions, feedback, mobile navigation and HTML references.');
