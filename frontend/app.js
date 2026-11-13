const API = '/api/v1';
const BOOKS_PER_PAGE = 10;

let categories = [];
let authors = [];
let members = [];
let books = [];

let bookPage = 1;
let bookTotalPages = 1;
let bookItems = [];
let memberItems = [];
let editingBookId = null;
let editingMemberId = null;
let bookRequest = 0;
let chatMessages = [];
let messageTimer = null;

const $ = (id) => document.getElementById(id);


// Thirrja e API-se, key dergohet vetem nese eshte ruajtur
async function api(path, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    const key = localStorage.getItem('apiKey');
    if (key) headers['X-API-Key'] = key;

    const res = await fetch(API + path, { ...options, headers });
    if (res.status === 204) return null;

    const data = await res.json().catch(() => null);
    if (!res.ok) throw new Error(errorText(res.status, data));
    return data;
}


function errorText(status, data) {
    const detail = data ? data.detail : null;
    if (typeof detail === 'string') return detail;

    // 422 kthen liste, nese mungon header-i atehere nuk eshte shkru API key
    if (Array.isArray(detail)) {
        if (detail.some((d) => d.loc && d.loc[0] === 'header')) {
            return 'Shkruaj API key lart per te bere ndryshime';
        }
        return detail.map((d) => `${d.loc[d.loc.length - 1]}: ${d.msg}`).join(', ');
    }
    return `Gabim ne server (${status})`;
}


function showMessage(text, isError = false) {
    const el = $('message');
    el.textContent = text;
    el.className = isError ? 'error' : '';
    el.hidden = false;
    // Dialogu i hapur e mbulon faqen, prandaj mesazhi shfaqet brenda tij
    (document.querySelector('dialog[open]') || document.querySelector('main')).prepend(el);
    clearTimeout(messageTimer);
    messageTimer = setTimeout(() => { el.hidden = true; }, 5000);
}


async function run(action) {
    try {
        await action();
    } catch (err) {
        showMessage(err.message, true);
    }
}


// Te dhenat nga API futen ne HTML, prandaj duhet escape
function esc(value) {
    const chars = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return String(value ?? '').replace(/[&<>"']/g, (c) => chars[c]);
}


function formatDate(iso) {
    if (!iso) return '—';
    const [year, month, day] = iso.split('-');
    return `${day}.${month}.${year}`;
}


function isoDate(daysFromToday = 0) {
    const d = new Date();
    d.setDate(d.getDate() + daysFromToday);
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${month}-${day}`;
}


function emptyRow(columns, text) {
    return `<tr><td class="empty" colspan="${columns}">${text}</td></tr>`;
}


function nameOf(list, id, field) {
    const item = list.find((x) => x.id === id);
    return item ? item[field] : `#${id}`;
}


// Listat qe perdoren neper select-a dhe per me i kthy id-te ne emra
async function loadLookups() {
    [categories, authors, members, books] = await Promise.all([
        api('/categories/?page_size=200'),
        api('/authors/?page_size=200'),
        api('/members/?page_size=500'),
        api('/books/?page_size=500'),
    ]);

    const lists = {
        categories: categories.map((c) => [c.id, c.name]),
        authors: authors.map((a) => [a.id, a.full_name]),
        members: members.map((m) => [m.id, m.full_name]),
        activeMembers: members.filter((m) => m.is_active).map((m) => [m.id, m.full_name]),
        books: books.map((b) => [b.id, b.title]),
    };

    document.querySelectorAll('select[data-list]').forEach((select) => {
        const selected = select.value;
        const options = lists[select.dataset.list]
            .sort((a, b) => a[1].localeCompare(b[1]))
            .map(([id, label]) => `<option value="${id}">${esc(label)}</option>`)
            .join('');
        select.innerHTML = `<option value="">${select.dataset.empty}</option>${options}`;
        select.value = selected;
    });
}


// ── LIBRAT ──────────────────────────────────

async function loadBooks() {
    const form = $('book-filters');
    const [sortBy, orderBy] = form.sort.value.split(':');
    const params = new URLSearchParams({
        page: bookPage,
        page_size: BOOKS_PER_PAGE,
        sort_by: sortBy,
        order_by: orderBy,
    });
    if (form.q.value.trim()) params.set('q', form.q.value.trim());
    if (form.category_id.value) params.set('category_id', form.category_id.value);
    if (form.author_id.value) params.set('author_id', form.author_id.value);
    if (form.available_only.checked) params.set('available_only', 'true');

    // Gjate shkrimit nisen disa kerkesa, shfaqet vetem pergjigjja e te fundit
    const request = ++bookRequest;
    const data = await api(`/books/search?${params}`);
    if (request !== bookRequest) return;

    bookItems = data.items;
    bookTotalPages = Math.max(data.total_pages, 1);

    $('books-body').innerHTML = bookItems.map((b) => `
        <tr>
            <td>${esc(b.title)}</td>
            <td>${esc(b.authors.map((a) => a.full_name).join(', ')) || '—'}</td>
            <td>${esc(nameOf(categories, b.category_id, 'name'))}</td>
            <td>${esc(b.isbn)}</td>
            <td>${b.published_year ? b.published_year.slice(0, 4) : '—'}</td>
            <td class="num">${b.total_copies}</td>
            <td class="actions">
                <button type="button" data-action="edit" data-id="${b.id}">Ndrysho</button>
                <button type="button" class="danger" data-action="delete" data-id="${b.id}">Fshij</button>
            </td>
        </tr>`).join('') || emptyRow(7, 'Nuk u gjet asnje liber');

    $('books-page').textContent = `Faqja ${data.page} nga ${bookTotalPages} (${data.total} libra)`;
    $('books-prev').disabled = bookPage <= 1;
    $('books-next').disabled = bookPage >= bookTotalPages;
}


function openBookDialog(book) {
    const form = $('book-form');
    form.reset();
    editingBookId = book ? book.id : null;
    $('book-dialog-title').textContent = book ? 'Ndrysho librin' : 'Shto liber';

    const linked = book ? book.authors.map((a) => a.id) : [];
    $('book-authors').innerHTML = authors.map((a) => `
        <label class="check">
            <input type="checkbox" name="author" value="${a.id}" ${linked.includes(a.id) ? 'checked' : ''}>
            ${esc(a.full_name)}
        </label>`).join('') || 'Nuk ka autore';

    if (book) {
        form.elements.title.value = book.title;
        form.isbn.value = book.isbn;
        form.category_id.value = book.category_id;
        form.total_copies.value = book.total_copies;
        form.year.value = Number(book.published_year.slice(0, 4));
        form.description.value = book.description || '';
    }
    $('message').hidden = true;
    $('book-dialog').showModal();
}


async function saveBook() {
    const form = $('book-form');
    // Backend-i e ruan vitin si date, prandaj dergohet 1 janari i atij viti
    const body = {
        title: form.elements.title.value.trim(),
        isbn: form.isbn.value.trim(),
        category_id: Number(form.category_id.value),
        total_copies: Number(form.total_copies.value),
        published_year: `${form.year.value.padStart(4, '0')}-01-01`,
        description: form.description.value.trim() || null,
    };

    let saved;
    let linked = [];
    if (editingBookId) {
        linked = bookItems.find((b) => b.id === editingBookId).authors.map((a) => a.id);
        saved = await api(`/books/${editingBookId}`, { method: 'PUT', body: JSON.stringify(body) });
    } else {
        saved = await api('/books/', { method: 'POST', body: JSON.stringify(body) });
    }

    // Autoret lidhen me endpoint te vecante, dergohen vetem ndryshimet
    const checked = [...form.querySelectorAll('[name="author"]:checked')].map((box) => Number(box.value));
    for (const id of checked.filter((x) => !linked.includes(x))) {
        await api(`/books/${saved.id}/authors/${id}`, { method: 'POST' });
    }
    for (const id of linked.filter((x) => !checked.includes(x))) {
        await api(`/books/${saved.id}/authors/${id}`, { method: 'DELETE' });
    }

    $('book-dialog').close();
    showMessage('Libri u ruajt');
    await loadLookups();
    await loadBooks();
}


async function deleteBook(book) {
    if (!confirm(`Te fshihet libri "${book.title}" bashke me historine e huazimeve?`)) return;
    await api(`/books/${book.id}`, { method: 'DELETE' });
    showMessage('Libri u fshi');
    await loadLookups();
    await loadBooks();
}


// ── BIBLIOTEKARI ────────────────────────────

function renderChat() {
    $('chat').innerHTML = chatMessages.map((m) => {
        if (m.role === 'user') return `<div class="bubble user">${esc(m.text)}</div>`;

        // Librat e rekomanduar vijne si id, te dhenat merren nga lista e librave
        const recommended = m.bookIds
            .map((id) => books.find((b) => b.id === id))
            .filter((b) => b)
            .map((b) => `
                <li>
                    <strong>${esc(b.title)}</strong>
                    <span>${esc(nameOf(categories, b.category_id, 'name'))}, ${b.published_year.slice(0, 4)}</span>
                </li>`).join('');

        const state = m.pending ? ' pending' : (m.error ? ' error' : '');
        return `
            <div class="bubble${state}">
                <p>${esc(m.text)}</p>
                ${recommended ? `<ul class="chat-books">${recommended}</ul>` : ''}
            </div>`;
    }).join('');

    const last = $('chat').lastElementChild;
    if (last) last.scrollIntoView({ block: 'nearest' });
}


async function askLibrarian() {
    const input = $('chat-form').question;
    const question = input.value.trim();
    if (!question) return;

    // Pergjigjja zgjat disa sekonda, prandaj shfaqet menjehere nje mesazh pritjeje
    const reply = { role: 'assistant', text: 'Duke kerkuar ne biblioteke...', bookIds: [], pending: true };
    chatMessages.push({ role: 'user', text: question }, reply);
    input.value = '';
    input.disabled = true;
    renderChat();

    try {
        const data = await api('/ai/ask', { method: 'POST', body: JSON.stringify({ question }) });
        reply.text = data.answer;
        reply.bookIds = data.book_ids;
    } catch (err) {
        reply.text = err.message;
        reply.error = true;
    }

    reply.pending = false;
    input.disabled = false;
    renderChat();
    input.focus();
}


// ── ANETARET ────────────────────────────────

async function loadMembers() {
    const filter = $('member-filters').is_active.value;
    const params = new URLSearchParams({ page_size: 500 });
    if (filter) params.set('is_active', filter);

    memberItems = await api(`/members/?${params}`);
    memberItems.sort((a, b) => a.full_name.localeCompare(b.full_name));

    $('members-body').innerHTML = memberItems.map((m) => `
        <tr>
            <td>${esc(m.full_name)}</td>
            <td>${esc(m.email)}</td>
            <td>${formatDate(m.join_date)}</td>
            <td class="${m.is_active ? 'status-active' : 'status-inactive'}">${m.is_active ? 'Aktiv' : 'Joaktiv'}</td>
            <td class="actions">
                <button type="button" data-action="loans" data-id="${m.id}">Huazimet</button>
                <button type="button" data-action="recommend" data-id="${m.id}">Rekomandime</button>
                <button type="button" data-action="edit" data-id="${m.id}">Ndrysho</button>
                <button type="button" class="danger" data-action="delete" data-id="${m.id}">Fshij</button>
            </td>
        </tr>`).join('') || emptyRow(5, 'Nuk u gjet asnje anetar');
}


function openMemberDialog(member) {
    const form = $('member-form');
    form.reset();
    editingMemberId = member ? member.id : null;
    $('member-dialog-title').textContent = member ? 'Ndrysho anetarin' : 'Shto anetar';

    form.full_name.value = member ? member.full_name : '';
    form.email.value = member ? member.email : '';
    form.join_date.value = member ? member.join_date : isoDate();
    form.is_active.checked = member ? member.is_active : true;
    $('message').hidden = true;
    $('member-dialog').showModal();
}


async function saveMember() {
    const form = $('member-form');
    const body = {
        full_name: form.full_name.value.trim(),
        email: form.email.value.trim(),
        join_date: form.join_date.value,
        is_active: form.is_active.checked,
    };

    if (editingMemberId) {
        await api(`/members/${editingMemberId}`, { method: 'PUT', body: JSON.stringify(body) });
    } else {
        await api('/members/', { method: 'POST', body: JSON.stringify(body) });
    }

    $('member-dialog').close();
    showMessage('Anetari u ruajt');
    await loadLookups();
    await loadMembers();
}


async function deleteMember(member) {
    if (!confirm(`Te fshihet anetari "${member.full_name}" bashke me historine e huazimeve?`)) return;
    await api(`/members/${member.id}`, { method: 'DELETE' });
    showMessage('Anetari u fshi');
    await loadLookups();
    await loadMembers();
}


async function showMemberLoans(member) {
    const loans = await api(`/members/${member.id}/loans`);
    loans.sort((a, b) => b.id - a.id);

    $('member-loans-title').textContent = `Huazimet e ${member.full_name}`;
    $('member-loans-body').innerHTML = loans.map((l) => `
        <tr>
            <td>${esc(nameOf(books, l.book_id, 'title'))}</td>
            <td>${formatDate(l.loan_date)}</td>
            <td>${formatDate(l.due_date)}</td>
            <td>${formatDate(l.return_date)}</td>
        </tr>`).join('') || emptyRow(4, 'Ky anetar nuk ka huazime');
    $('member-loans-dialog').showModal();
}


async function showRecommendations(member) {
    // Dialogu hapet menjehere sepse modeli e kthen pergjigjen pas disa sekondash
    $('recommend-title').textContent = `Rekomandime per ${member.full_name}`;
    $('recommend-list').innerHTML = '<li><span>Duke kerkuar libra...</span></li>';
    $('message').hidden = true;
    $('recommend-dialog').showModal();

    try {
        const items = await api(`/members/${member.id}/recommendations?limit=3`);
        $('recommend-list').innerHTML = items.map((b) => `
            <li>
                <strong>${esc(b.title)}</strong>
                <span>${esc(b.reason)}</span>
            </li>`).join('') || '<li><span>Ky anetar i ka huazuar te gjithe librat</span></li>';
    } catch (err) {
        $('recommend-list').innerHTML = '';
        throw err;
    }
}


// ── HUAZIMET ────────────────────────────────

function loanStatus(loan) {
    if (loan.return_date) return ['returned', 'Kthyer'];
    if (loan.due_date < isoDate()) return ['overdue', 'Me vonese'];
    return ['active', 'Aktiv'];
}


async function loadLoans() {
    const form = $('loan-filters');
    const params = new URLSearchParams({ page_size: 500 });
    if (form.status.value) params.set('status', form.status.value);
    if (form.member_id.value) params.set('member_id', form.member_id.value);

    const loans = await api(`/loans/?${params}`);
    loans.sort((a, b) => b.id - a.id);

    $('loans-body').innerHTML = loans.map((l) => {
        const [status, label] = loanStatus(l);
        const returnButton = l.return_date
            ? ''
            : `<button type="button" data-action="return" data-id="${l.id}">Kthe librin</button>`;
        return `
        <tr>
            <td>${esc(nameOf(members, l.member_id, 'full_name'))}</td>
            <td>${esc(nameOf(books, l.book_id, 'title'))}</td>
            <td>${formatDate(l.loan_date)}</td>
            <td>${formatDate(l.due_date)}</td>
            <td>${formatDate(l.return_date)}</td>
            <td class="status-${status}">${label}</td>
            <td class="actions">${returnButton}</td>
        </tr>`;
    }).join('') || emptyRow(7, 'Nuk u gjet asnje huazim');
}


async function createLoan() {
    const form = $('loan-form');
    const body = {
        member_id: Number(form.member_id.value),
        book_id: Number(form.book_id.value),
        due_date: form.due_date.value,
    };
    await api('/loans/', { method: 'POST', body: JSON.stringify(body) });

    form.reset();
    resetLoanForm();
    showMessage('Huazimi u regjistrua');
    await loadLoans();
}


// Afati fillestar eshte 14 dite, dhe nuk lejohet date ne te kaluaren
function resetLoanForm() {
    const dueDate = $('loan-form').due_date;
    dueDate.min = isoDate();
    dueDate.value = isoDate(14);
}


async function returnLoan(id) {
    await api(`/loans/${id}/return`, { method: 'POST' });
    showMessage('Libri u kthye');
    await loadLoans();
}


// ── AUTORET DHE KATEGORITE ──────────────────

async function loadAuthorsAndCategories() {
    await loadLookups();

    $('authors-body').innerHTML = authors.map((a) => `
        <tr>
            <td>${esc(a.full_name)}</td>
            <td>${esc(a.country)}</td>
        </tr>`).join('') || emptyRow(2, 'Nuk ka autore');

    $('categories-body').innerHTML = categories.map((c) => `
        <tr>
            <td>${esc(c.name)}</td>
        </tr>`).join('') || emptyRow(1, 'Nuk ka kategori');
}


async function createAuthor() {
    const form = $('author-form');
    const body = {
        full_name: form.full_name.value.trim(),
        country: form.country.value.trim(),
    };
    await api('/authors/', { method: 'POST', body: JSON.stringify(body) });

    form.reset();
    showMessage('Autori u shtua');
    await loadAuthorsAndCategories();
}


async function createCategory() {
    const form = $('category-form');
    const name = form.elements.name.value.trim();

    await api('/categories/', { method: 'POST', body: JSON.stringify({ name }) });

    form.reset();
    showMessage('Kategoria u shtua');
    await loadAuthorsAndCategories();
}


// ── RAPORTET ────────────────────────────────

async function loadReports() {
    const [top, overdue] = await Promise.all([
        api('/reports/top-borrowers?limit=5'),
        api('/reports/overdue-loans'),
    ]);

    $('top-body').innerHTML = top.map((m) => `
        <tr>
            <td>${esc(m.full_name)}</td>
            <td>${esc(m.email)}</td>
            <td class="num">${m.total_loans}</td>
        </tr>`).join('') || emptyRow(3, 'Nuk ka huazime');

    overdue.sort((a, b) => b.days_overdue - a.days_overdue);
    $('overdue-body').innerHTML = overdue.map((l) => `
        <tr>
            <td>${esc(l.member_name)}</td>
            <td>${esc(l.book_title)}</td>
            <td>${formatDate(l.due_date)}</td>
            <td class="num">${l.days_overdue}</td>
        </tr>`).join('') || emptyRow(4, 'Nuk ka huazime me vonese');
}


// ── NAVIGIMI ────────────────────────────────

const views = {
    librat: loadBooks,
    bibliotekari: renderChat,
    anetaret: loadMembers,
    huazimet: loadLoans,
    autoret: loadAuthorsAndCategories,
    raportet: loadReports,
};


// Pamja zgjidhet nga hash-i ne URL, keshtu funksionon edhe refresh
function showView() {
    const hash = location.hash.slice(1);
    const name = hash in views ? hash : 'librat';
    $('message').hidden = true;

    document.querySelectorAll('main > section').forEach((section) => {
        section.hidden = section.id !== name;
    });
    document.querySelectorAll('nav a').forEach((link) => {
        if (link.getAttribute('href') === `#${name}`) {
            link.setAttribute('aria-current', 'page');
        } else {
            link.removeAttribute('aria-current');
        }
    });

    run(views[name]);
}


function onSubmit(formId, action) {
    $(formId).addEventListener('submit', (event) => {
        event.preventDefault();
        run(action);
    });
}


// Nje listener per krejt tabelen, butonat dallohen me data-action
function onRowAction(bodyId, handler) {
    $(bodyId).addEventListener('click', (event) => {
        const button = event.target.closest('button[data-action]');
        if (button) run(() => handler(button.dataset.action, Number(button.dataset.id)));
    });
}


function setup() {
    $('api-key').value = localStorage.getItem('apiKey') || '';
    $('key-form').addEventListener('submit', (event) => {
        event.preventDefault();
        const key = $('api-key').value.trim();
        if (key) {
            localStorage.setItem('apiKey', key);
            showMessage('API key u ruajt ne kete shfletues');
        } else {
            localStorage.removeItem('apiKey');
            showMessage('API key u hoq');
        }
    });

    const reloadBooks = () => {
        bookPage = 1;
        run(loadBooks);
    };
    $('book-filters').addEventListener('input', reloadBooks);
    $('book-filters').addEventListener('submit', (event) => event.preventDefault());
    $('books-prev').addEventListener('click', () => { bookPage -= 1; run(loadBooks); });
    $('books-next').addEventListener('click', () => { bookPage += 1; run(loadBooks); });
    $('add-book').addEventListener('click', () => openBookDialog(null));
    onSubmit('book-form', saveBook);
    onRowAction('books-body', (action, id) => {
        const book = bookItems.find((b) => b.id === id);
        if (action === 'edit') return openBookDialog(book);
        if (action === 'delete') return deleteBook(book);
    });

    onSubmit('chat-form', askLibrarian);

    $('member-filters').addEventListener('input', () => run(loadMembers));
    $('add-member').addEventListener('click', () => openMemberDialog(null));
    onSubmit('member-form', saveMember);
    onRowAction('members-body', (action, id) => {
        const member = memberItems.find((m) => m.id === id);
        if (action === 'loans') return showMemberLoans(member);
        if (action === 'recommend') return showRecommendations(member);
        if (action === 'edit') return openMemberDialog(member);
        if (action === 'delete') return deleteMember(member);
    });

    $('loan-filters').addEventListener('input', () => run(loadLoans));
    onSubmit('loan-form', createLoan);
    onRowAction('loans-body', (action, id) => returnLoan(id));
    resetLoanForm();

    onSubmit('author-form', createAuthor);
    onSubmit('category-form', createCategory);

    document.querySelectorAll('[data-close]').forEach((button) => {
        button.addEventListener('click', () => button.closest('dialog').close());
    });

    window.addEventListener('hashchange', showView);
}


setup();
run(async () => {
    await loadLookups();
    showView();
});
