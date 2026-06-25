// API base URL carregada por api-config.js.
const baseUrl = window.API_BASE_URL;

document.addEventListener('DOMContentLoaded', async function() {
    const token = localStorage.getItem('jwtToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }
    const decodedToken = jwt_decode(token);
    const userId = decodedToken.user_id;

    let rooms = [];
    let currentRoomId = null;
    // New elements for my bookings filters
    let roomFiltersContainer;
    let bookingDateSearchInput;

    function getStartOfWeek(date) {
        const dt = new Date(date);
        const day = dt.getDay(); // 0 (Sunday) to 6 (Saturday)
        // Adjust to make Monday the first day of the week.
        // If Sunday (0), subtract 6 days. If Saturday (6), subtract 5.
        const diff = dt.getDate() - day + (day === 0 ? -6 : 1); 
        dt.setDate(diff);
        dt.setHours(0, 0, 0, 0); // Set time to the beginning of the day
        return dt;
    }

    let currentWeekStart = getStartOfWeek(new Date());
    let currentMobileDate = new Date();
    currentMobileDate.setHours(0, 0, 0, 0);
    let selectedBookingId = null;

    function isMobile() {
        return window.innerWidth <= 768;
    }

    // --- Ícones SVG (Lucide-style) ---
    const ICONS = {
        moon:         `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`,
        sun:          `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>`,
        chevronLeft:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>`,
        chevronRight: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>`,
        logOut:       `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`,
        settings:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>`,
        calendarDays: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/></svg>`,
        calendarPlus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 13V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h8"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="17" y2="10"/><line x1="19" y1="16" x2="19" y2="22"/><line x1="22" y1="19" x2="16" y2="19"/></svg>`,
        trash:        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>`,
        pencil:       `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>`,
        power:        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.77.04"/></svg>`,
        search:       `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>`,
        userCheck:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>`,
        users:        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
        plus:         `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>`,
        check:        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>`,
        save:         `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>`,
        x:            `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`,
    };

    function injectIcons(root = document) {
        root.querySelectorAll('[data-icon]').forEach(el => {
            const name = el.dataset.icon;
            if (ICONS[name]) el.innerHTML = ICONS[name];
        });
    }

    // --- Elementos do DOM ---
    const roomList = document.getElementById('room-list');
    const calendarTitle = document.getElementById('calendar-title');
    const prevWeekBtn = document.getElementById('prev-week-btn');
    const nextWeekBtn = document.getElementById('next-week-btn');
    // Removido loadingMessage, agora usamos apenas spinnerOverlay
    const calendarGridHeaders = document.getElementById('calendar-grid-headers');
    const calendarGridBody = document.getElementById('calendar-grid-body');
    const calendarHours = document.querySelector('.calendar-hours');
    const bookingModal = document.getElementById('booking-modal');
    const closeModalBtn = document.querySelector('#booking-modal .close-btn');
    const bookingForm = document.getElementById('booking-form');
    const deleteBookingBtn = document.getElementById('delete-booking-btn');
    const manageRoomsBtn = document.getElementById('manage-rooms-btn');
    const roomManagementModal = document.getElementById('room-management-modal');
    const roomManagementList = document.getElementById('room-management-list');
    const addNewRoomBtn = document.getElementById('add-new-room-btn');
    const editRoomModal = document.getElementById('edit-room-modal');
    const editRoomForm = document.getElementById('edit-room-form');
    const editRoomId = document.getElementById('edit-room-id');
    const editRoomName = document.getElementById('edit-room-name');
    const logoutBtn = document.getElementById('logout-btn');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const userNameSpan = document.getElementById('user-name');
    const myBookingsBtn = document.getElementById('my-bookings-btn');
    const myBookingsModal = document.getElementById('my-bookings-modal');
    const myBookingsList = document.getElementById('my-bookings-list');
    const myBookingsTitle = document.getElementById('my-bookings-title');
    const spinnerOverlay = document.getElementById('spinner-overlay');

    // New elements for user search
    const changeOwnerBtn = document.getElementById('change-owner-btn');
    const modalOwnerDisplay = document.getElementById('modal-owner-display');
    const modalOwnerId = document.getElementById('modal-owner-id');
    const userSearchModal = document.getElementById('user-search-modal');
    const userSearchQuery = document.getElementById('user-search-query');
    const searchByMatriculaRadio = document.getElementById('search-by-matricula');
    const searchByNameRadio = document.getElementById('search-by-name');
    const userSearchButton = document.getElementById('user-search-button');
    const userSearchResults = document.getElementById('user-search-results');

    // --- Modal de Alerta Genérico ---
    const alertModal = document.getElementById('alert-modal');
    const alertModalCloseBtn = document.getElementById('alert-modal-close-btn');
    const alertModalOkBtn = document.getElementById('alert-modal-ok-btn');
    const alertModalMessage = document.getElementById('alert-modal-message');
    const themeToggleIcon = document.getElementById('theme-icon');
    const logoutIcon = document.querySelector('#logout-btn .logout-icon');
    const prevNavGlyph = document.querySelector('#prev-week-btn .nav-glyph');
    const nextNavGlyph = document.querySelector('#next-week-btn .nav-glyph');

    if (logoutIcon) logoutIcon.innerHTML = ICONS.logOut;
    if (prevNavGlyph) prevNavGlyph.innerHTML = ICONS.chevronLeft;
    if (nextNavGlyph) nextNavGlyph.innerHTML = ICONS.chevronRight;

    function applyTheme(themeClass) {
        document.body.classList.remove('dark-mode', 'light-mode');
        document.body.classList.add(themeClass);
        localStorage.setItem('themeMode', themeClass);

        if (themeToggleIcon) {
            themeToggleIcon.innerHTML = themeClass === 'dark-mode' ? ICONS.moon : ICONS.sun;
        }
    }

    const savedTheme = localStorage.getItem('themeMode');
    const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    applyTheme(savedTheme || (prefersLight ? 'light-mode' : 'dark-mode'));

    // --- Funções do Modal de Alerta ---
    function showAlert(message) {
        alertModalMessage.textContent = message;
        alertModal.style.display = 'flex';
    }

    function hideAlert() {
        alertModal.style.display = 'none';
    }

    alertModalCloseBtn.addEventListener('click', hideAlert);
    alertModalOkBtn.addEventListener('click', hideAlert);
    window.addEventListener('click', (event) => {
        if (event.target == alertModal) {
            hideAlert();
        }
    });

    // --- Inicialização ---
    const userName = localStorage.getItem('userName');
    userNameSpan.textContent = userName && userName !== 'undefined' ? `Olá, ${userName}` : 'Olá, Usuário';
    
    // --- Funções da API ---
    async function fetchRooms() {
        try {
            const response = await fetch(`${baseUrl}/rooms`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) {
                rooms = await response.json();
                if (rooms.length > 0 && currentRoomId === null) {
                    currentRoomId = rooms.find(r => r.active)?.id || null;
                }
                renderRoomTabs(rooms);
            } else {
                const error = await response.json();
                showAlert(`Erro ao carregar salas: ${error.message}`);
            }
        } catch (error) {
            showAlert('Erro de conexão ao buscar salas. Verifique o servidor.');
        }
    }

    async function fetchUsers() {
        try {
            const response = await fetch(`${baseUrl}/users`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) {
                return await response.json();
            } else {
                const error = await response.json();
                showAlert(`Erro ao carregar usuários: ${error.message}`);
                return [];
            }
        } catch (error) {
            showAlert('Erro de conexão ao buscar usuários. Verifique o servidor.');
            return [];
        }
    }

    async function fetchUsersSearch(query, searchBy) {
        try {
            const response = await fetch(`${baseUrl}/users/search?query=${query}&search_by=${searchBy}`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) {
                return await response.json();
            } else {
                const error = await response.json();
                showAlert(`Erro ao buscar usuários: ${error.message}`);
                return [];
            }
        } catch (error) {
            showAlert('Erro de conexão ao buscar usuários. Verifique o servidor.');
            return [];
        }
    }

    async function fetchBookings(startDate) {
        const toApiFormat = (date) => new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().split('T')[0] + 'T00:00:00';
        const startIso = toApiFormat(startDate);
        const endDate = new Date(startDate);
        endDate.setDate(startDate.getDate() + 6);
        const endIso = toApiFormat(endDate);

        try {
            const response = await fetch(`${baseUrl}/agendamentos?start=${startIso}&end=${endIso}`, { headers: { 'Authorization': `Bearer ${token}` } });
            return response.ok ? await response.json() : (showAlert('Erro ao carregar agendamentos.'), []);
        } catch (error) {
            showAlert('Erro de conexão ao buscar agendamentos.');
            return [];
        }
    }

    async function fetchUpcomingBookings() {
        const toApiFormat = (date) => new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().split('T')[0] + 'T00:00:00';
        const startIso = toApiFormat(new Date());
        const endDate = new Date();
        endDate.setFullYear(endDate.getFullYear() + 1);
        const endIso = toApiFormat(endDate);

        try {
            const response = await fetch(`${baseUrl}/agendamentos?start=${startIso}&end=${endIso}`, { headers: { 'Authorization': `Bearer ${token}` } });
            return response.ok ? await response.json() : (showAlert('Erro ao carregar seus agendamentos.'), []);
        } catch (error) {
            showAlert('Erro de conexão ao buscar seus agendamentos.');
            return [];
        }
    }

    async function createBooking() {
        const payload = buildBookingPayload();
        try {
            const response = await fetch(`${baseUrl}/agendamentos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok) {
                bookingModal.style.display = 'none';
                await renderCalendar();
            } else {
                showAlert(data.message || 'Erro desconhecido ao criar agendamento.');
            }
        } catch (error) {
            showAlert('Erro de conexão ao criar agendamento.');
        }
    }

    async function updateBooking(bookingId) {
        const payload = buildBookingPayload();
        try {
            const response = await fetch(`${baseUrl}/agendamentos/${bookingId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok) {
                bookingModal.style.display = 'none';
                await renderCalendar();
            } else {
                showAlert(data.message || 'Erro desconhecido ao atualizar agendamento.');
            }
        } catch (error) {
            showAlert('Erro de conexão ao atualizar agendamento.');
        }
    }

    async function deleteBooking(bookingId) {
        try {
            const response = await fetch(`${baseUrl}/agendamentos/${bookingId}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } });
            const data = await response.json();
            if (response.ok) {
                bookingModal.style.display = 'none';
                await renderCalendar();
            } else {
                showAlert(data.message || 'Erro ao excluir agendamento.');
            }
        } catch (error) {
            showAlert('Erro de conexão ao excluir agendamento.');
        }
    }

    // --- Funções de Gerenciamento de Salas (Admin) ---
    async function addNewRoom() {
        const name = prompt('Nome da nova sala:');
        if (!name) return;
        try {
            const response = await fetch(`${baseUrl}/rooms`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ name })
            });
            if (response.ok) {
                await fetchRooms();
                openRoomManagementModal();
            } else {
                const error = await response.json();
                showAlert(`Erro ao criar sala: ${error.message}`);
            }
        } catch (error) {
            showAlert('Erro de conexão ao criar sala.');
        }
    }

    async function updateRoom(e) {
        e.preventDefault();
        const roomId = parseInt(editRoomId.value);
        const newName = editRoomName.value;
        try {
            const response = await fetch(`${baseUrl}/rooms/${roomId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ name: newName })
            });
            if (response.ok) {
                await fetchRooms();
                editRoomModal.style.display = 'none';
                openRoomManagementModal();
            } else {
                const error = await response.json();
                showAlert(`Erro ao atualizar sala: ${error.message}`);
            }
        } catch (error) {
            showAlert('Erro de conexão ao atualizar sala.');
        }
    }

    async function deleteRoom(roomId) {
        if (!confirm('Deseja realmente excluir esta sala? Isso removerá todos os seus agendamentos.')) return;
        try {
            const response = await fetch(`${baseUrl}/rooms/${roomId}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) {
                if (currentRoomId === roomId) currentRoomId = rooms.find(r => r.active)?.id || null;
                await fetchRooms();
                openRoomManagementModal();
                await renderCalendar();
            } else {
                const error = await response.json();
                showAlert(`Erro ao excluir sala: ${error.message}`);
            }
        } catch (error) {
            showAlert('Erro de conexão ao excluir sala.');
        }
    }

    async function toggleRoomStatus(roomId) {
        const room = rooms.find(r => r.id === roomId);
        if (!room) return;
        try {
            const response = await fetch(`${baseUrl}/rooms/${roomId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ active: !room.active })
            });
            if (response.ok) {
                await fetchRooms();
                openRoomManagementModal();
                await renderCalendar();
            } else {
                const error = await response.json();
                showAlert(`Erro ao alterar status da sala: ${error.message}`);
            }
        } catch (error) {
            showAlert('Erro de conexão ao alterar status da sala.');
        }
    }

    // --- Renderização ---
    function renderRoomTabs(rooms) {
        const activeRooms = rooms.filter(room => room.active);
        roomList.innerHTML = activeRooms.map(room =>
            `<div class="room-tab ${room.id === currentRoomId ? 'active' : ''}" data-room-id="${room.id}">${room.name}</div>`
        ).join('');

        const mobileSelect = document.getElementById('room-select-mobile');
        if (mobileSelect) {
            mobileSelect.innerHTML = activeRooms.map(room =>
                `<option value="${room.id}" ${room.id === currentRoomId ? 'selected' : ''}>${room.name}</option>`
            ).join('');
        }
    }

    function renderHours() {
        calendarHours.innerHTML = Array.from({length: 15}, (_, i) => `<div>${(i + 7).toString().padStart(2, '0')}:00</div>`).join('');
    }

    async function renderCalendar() {
        renderHours();
        if (currentRoomId === null) {
            calendarGridBody.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 20px;">Nenhuma sala ativa encontrada.</div>';
            calendarGridHeaders.innerHTML = '';
            calendarTitle.textContent = 'Nenhuma Sala Selecionada';
            return;
        }

        spinnerOverlay.style.display = 'flex';

        const mobile = isMobile();
        document.body.classList.toggle('mobile-day-view', mobile);

        let weekDates;
        let fetchStart;

        if (mobile) {
            const d = new Date(currentMobileDate);
            d.setHours(0, 0, 0, 0);
            weekDates = [d];
            fetchStart = getStartOfWeek(d);
            calendarTitle.textContent = d.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: 'short' });
        } else {
            weekDates = Array.from({length: 6}, (_, i) => {
                const date = new Date(currentWeekStart);
                date.setDate(currentWeekStart.getDate() + i);
                return date;
            });
            fetchStart = currentWeekStart;
            calendarTitle.textContent = `${weekDates[0].toLocaleDateString('pt-BR', {day: '2-digit', month: 'short'})} - ${weekDates[5].toLocaleDateString('pt-BR', {day: '2-digit', month: 'short'})}`;
        }

        calendarGridHeaders.innerHTML = '<div class="calendar-hours-header">Horários</div>' + weekDates.map(date =>
            `<div class="calendar-day-header">${date.toLocaleDateString('pt-BR', {weekday: 'short'})}<br>${date.toLocaleDateString('pt-BR', {day: '2-digit'})}</div>`
        ).join('');

        const bookings = await fetchBookings(fetchStart);
        spinnerOverlay.style.display = 'none';

        calendarGridBody.innerHTML = weekDates.map(date => `
            <div class="calendar-day-cell">
                <div class="day-cell-content">
                    ${Array.from({length: 15}, (_, hour) => `<div class="time-slot" data-date="${date.toISOString().split('T')[0]}" data-hour="${hour + 7}"></div>`).join('')}
                </div>
            </div>`
        ).join('');

        renderBookingBlocks(bookings, weekDates);
        calendarGridBody.querySelectorAll('.time-slot').forEach(slot => slot.addEventListener('click', openBookingModalForCreation));
    }

    function renderBookingBlocks(bookings, weekDates) {
        if (!bookings) return;
        const bookingsForRoom = bookings.filter(b => b.ID_SALA === currentRoomId);

        bookingsForRoom.forEach(booking => {
            const start = new Date(booking.DATA_INICIO);
            const end = new Date(booking.DATA_FIM);
            if (isNaN(start.getTime()) || isNaN(end.getTime()) || end <= start) return;
            const now = new Date();

            let ownerName = booking.NOME_USUARIO;
            if (!ownerName) {
                if (booking.ID_USUARIO === userId) {
                    ownerName = userName;
                } else {
                    ownerName = 'Desconhecido';
                }
            }

            // Renderiza o mesmo agendamento em todos os dias da semana visível
            // quando houver interseção de DateTime entre [início, fim] e o dia da grade.
            weekDates.forEach((weekDate, dayOffset) => {
                const dayCellContent = calendarGridBody.children[dayOffset]?.querySelector('.day-cell-content');
                if (!dayCellContent) return;

                const dayGridStart = new Date(weekDate);
                dayGridStart.setHours(7, 0, 0, 0);
                const dayGridEnd = new Date(weekDate);
                dayGridEnd.setHours(22, 0, 0, 0); // grade vai de 07:00 até 21:59

                const segmentStartMs = Math.max(start.getTime(), dayGridStart.getTime());
                const segmentEndMs = Math.min(end.getTime(), dayGridEnd.getTime());
                if (segmentEndMs <= segmentStartMs) return;

                const segmentStart = new Date(segmentStartMs);
                const segmentEnd = new Date(segmentEndMs);
                const isPastSegment = segmentEnd < now;

                const bookingBlock = document.createElement('div');
                bookingBlock.className = 'booking-block';
                if (isPastSegment) {
                    bookingBlock.classList.add('past-booking');
                }
                bookingBlock.innerHTML = `${booking.TITULO}<br><small>${ownerName}</small>`;
                bookingBlock.dataset.bookingId = booking.ID_AGENDAMENTO;

                const slotSample = dayCellContent.querySelector('.time-slot');
                const slotHeightCss = getComputedStyle(document.documentElement).getPropertyValue('--slot-height').trim();
                const slotHeight = slotSample
                    ? slotSample.getBoundingClientRect().height
                    : (parseFloat(slotHeightCss) || 40);

                const minutesFromDayStart = ((segmentStart.getHours() - 7) * 60) + segmentStart.getMinutes();
                const durationMinutes = (segmentEnd.getTime() - segmentStart.getTime()) / (1000 * 60);
                const top = (minutesFromDayStart / 60) * slotHeight;
                const height = (durationMinutes / 60) * slotHeight;

                Object.assign(bookingBlock.style, { position: 'absolute', top: `${top}px`, height: `${height}px` });
                bookingBlock.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openBookingModalForEdit(booking.ID_AGENDAMENTO);
                });
                dayCellContent.appendChild(bookingBlock);
            });
        });
    }

    // --- Funções de Abertura de Modais ---
    function openBookingModalForCreation(event) {
        if (currentRoomId === null) {
            showAlert('Nenhuma sala selecionada para agendar.');
            return;
        }
        const { date, hour } = event.target.dataset;
        bookingForm.reset();
        bookingForm.removeAttribute('data-booking-id');

        // Habilita todos os campos do formulário, exceto o da sala
        Array.from(bookingForm.elements).forEach(el => el.disabled = false);
        document.getElementById('modal-sala').disabled = true;

        // Set owner display and ID for new booking
        modalOwnerDisplay.textContent = userName;
        modalOwnerId.value = userId;
        changeOwnerBtn.style.display = 'none'; // Hide change owner button for creation
        modalOwnerDisplay.style.display = 'inline-block'; // Show the span

        document.getElementById('modal-sala').value = rooms.find(r => r.id === currentRoomId).name;
        document.getElementById('modal-inicio').value = `${date}T${hour.padStart(2, '0')}:00`;
        document.getElementById('modal-fim').value = `${date}T${(parseInt(hour) + 1).toString().padStart(2, '0')}:00`;
        deleteBookingBtn.style.display = 'none';
        const submitBtn = bookingForm.querySelector('button[type="submit"]');
        submitBtn.innerHTML = `<span class="btn-icon">${ICONS.calendarPlus}</span><span>Agendar</span>`;
        submitBtn.style.display = 'inline-flex';
        bookingModal.style.display = 'flex';
    }

    async function openBookingModalForEdit(bookingId) {
        try {
            const response = await fetch(`${baseUrl}/agendamentos/${bookingId}`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('Falha ao carregar dados do agendamento.');
            const booking = await response.json();
            
            const isOwner = booking.ID_USUARIO === userId;
            const isAdmin = localStorage.getItem('userProfile') === 'Administrador';
            const isPastBooking = new Date(booking.DATA_FIM) < new Date(); // Check if the booking is in the past

            const canEdit = (isAdmin || isOwner) && !isPastBooking; 

            let ownerName = booking.NOME_USUARIO;
            if (!ownerName) {
                if (booking.ID_USUARIO === userId) {
                    ownerName = userName;
                } else {
                    ownerName = 'Usuário desconhecido';
                }
            }

            bookingForm.setAttribute('data-booking-id', bookingId);
            document.getElementById('modal-titulo').value = booking.TITULO;
            document.getElementById('modal-sala').value = rooms.find(r => r.id === booking.ID_SALA).name;
            
            // Handle owner field display
            modalOwnerDisplay.textContent = ownerName;
            modalOwnerId.value = booking.ID_USUARIO;
            modalOwnerDisplay.style.display = 'inline-block';

            // Show "Change Owner" button only for Admins on non-expired bookings
            if (isAdmin && !isPastBooking) {
                changeOwnerBtn.style.display = 'inline-flex';
            } else {
                changeOwnerBtn.style.display = 'none';
            }

            document.getElementById('modal-inicio').value = booking.DATA_INICIO.replace(' ', 'T');
            document.getElementById('modal-fim').value = booking.DATA_FIM.replace(' ', 'T');
            
            const desc = booking.DESCRICAO || '';
            const equipmentRegex = /Equipamentos necessários:[\s\S]*/;
            document.getElementById('modal-descricao').value = desc.replace(equipmentRegex, '').trim();
            const equipmentMatch = desc.match(equipmentRegex);
            document.getElementById('modal-projetor').checked = equipmentMatch ? equipmentMatch[0].includes('Projetor') : false;
            document.getElementById('modal-regua-energia').checked = equipmentMatch ? equipmentMatch[0].includes('Régua de Energia') : false;
            document.getElementById('modal-suporte-ti').checked = equipmentMatch ? equipmentMatch[0].includes('Suporte de TI') : false;

            deleteBookingBtn.style.display = canEdit ? 'inline-flex' : 'none';
            bookingForm.querySelector('button[type="submit"]').style.display = canEdit ? 'inline-flex' : 'none';
            Array.from(bookingForm.elements).forEach(el => el.disabled = !canEdit);
            document.getElementById('modal-sala').disabled = true; // Sala não pode ser alterada

            bookingModal.style.display = 'flex';
        } catch (error) {
            showAlert(error.message);
        }
    }

    function renderMyBookingsList(bookings) {
        if (bookings.length === 0) {
            myBookingsList.innerHTML = '<p>Nenhum agendamento futuro encontrado.</p>';
            return;
        }

        const sortedBookings = bookings.sort((a, b) => new Date(a.DATA_INICIO) - new Date(b.DATA_INICIO));

        myBookingsList.innerHTML = sortedBookings.map(booking => {
            const start = new Date(booking.DATA_INICIO);
            const end = new Date(booking.DATA_FIM);
            const room = rooms.find(r => r.id === booking.ID_SALA);

            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };

            return `
                <div class="booking-item">
                    <h4>${booking.TITULO}</h4>
                    <p><strong>Sala:</strong> ${room ? room.name : 'Desconhecida'}</p>
                    <p><strong>Início:</strong> ${start.toLocaleDateString('pt-BR', options)}</p>
                    <p><strong>Fim:</strong> ${end.toLocaleDateString('pt-BR', options)}</p>
                    ${booking.NOME_USUARIO ? `<p><strong>Usuário:</strong> ${booking.NOME_USUARIO}</p>` : ''}
                </div>
            `;
        }).join('');
    }

    let allMyBookings = []; // Store all fetched bookings
    let currentMyBookingsRoomFilter = 'all'; // 'all' or a room ID
    let currentMyBookingsDateFilter = ''; // YYYY-MM-DD format

    async function openMyBookingsModal() {
        const isAdmin = localStorage.getItem('userProfile') === 'Administrador';
        myBookingsTitle.textContent = isAdmin ? 'Todos os Agendamentos Futuros' : 'Meus Agendamentos Futuros';

        // Fetch all upcoming bookings once
        allMyBookings = await fetchUpcomingBookings();
        
        // Inject filter HTML if not already present
        const modalContent = myBookingsModal.querySelector('.modal-content');
        if (!modalContent.querySelector('#my-bookings-filters')) {
            const filterHtml = `
                <div id="my-bookings-filters">
                    <div id="room-filters"></div>
                    <div id="date-filter">
                        <label for="booking-date-search">Pesquisar por Data:</label>
                        <input type="date" id="booking-date-search">
                    </div>
                </div>
            `;
            // Insert after the title
            myBookingsTitle.insertAdjacentHTML('afterend', filterHtml);
            // Re-get references after injecting HTML
            roomFiltersContainer = document.getElementById('room-filters');
            bookingDateSearchInput = document.getElementById('booking-date-search');

            // Add event listeners
            bookingDateSearchInput.addEventListener('change', (e) => {
                currentMyBookingsDateFilter = e.target.value;
                renderFilteredMyBookings();
            });
        }

        renderRoomFiltersForMyBookings(); // Render room filter buttons
        bookingDateSearchInput.value = currentMyBookingsDateFilter; // Set date input value

        renderFilteredMyBookings(); // Apply filters and render
        myBookingsModal.style.display = 'flex';
    }

    function renderRoomFiltersForMyBookings() {
        const allRoomsOption = { id: 'all', name: 'Todas as Salas' };
        const roomsToDisplay = [allRoomsOption, ...rooms.filter(r => r.active)]; // Include active rooms

        roomFiltersContainer.innerHTML = roomsToDisplay.map(room => `
            <button class="room-filter-btn ${currentMyBookingsRoomFilter === String(room.id) ? 'active' : ''}" data-room-id="${room.id}">
                ${room.name}
            </button>
        `).join('');

        roomFiltersContainer.querySelectorAll('.room-filter-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                currentMyBookingsRoomFilter = e.target.dataset.roomId;
                renderRoomFiltersForMyBookings(); // Re-render to update active state
                renderFilteredMyBookings();
            });
        });
    }

    function renderFilteredMyBookings() {
        const isAdmin = localStorage.getItem('userProfile') === 'Administrador';
        let filtered = allMyBookings;

        // Filter by user if not admin
        if (!isAdmin) {
            filtered = filtered.filter(b => b.ID_USUARIO === userId);
        }

        // Filter by room
        if (currentMyBookingsRoomFilter !== 'all') {
            filtered = filtered.filter(b => b.ID_SALA === parseInt(currentMyBookingsRoomFilter));
        }

        // Filter by date
        if (currentMyBookingsDateFilter) {
            filtered = filtered.filter(b => {
                const bookingDate = new Date(b.DATA_INICIO).toISOString().split('T')[0];
                return bookingDate === currentMyBookingsDateFilter;
            });
        }

        renderMyBookingsList(filtered);
    }

    function openRoomManagementModal() {
        roomManagementList.innerHTML = rooms.map(room => `
            <div class="room-management-item">
                <span>${room.name}</span>
                <div>
                    <button class="edit-room-btn" data-room-id="${room.id}">${ICONS.pencil}<span>Editar</span></button>
                    <button class="delete-room-btn" data-room-id="${room.id}">${ICONS.trash}<span>Excluir</span></button>
                    <button class="toggle-room-status-btn ${room.active ? 'toggle-deactivate-btn' : 'toggle-activate-btn'}" data-room-id="${room.id}">${ICONS.power}<span>${room.active ? 'Desativar' : 'Ativar'}</span></button>
                </div>
            </div>`).join('');
        roomManagementModal.style.display = 'flex';
    }

    function openEditRoomModal(room) {
        editRoomId.value = room.id;
        editRoomName.value = room.name;
        editRoomModal.style.display = 'flex';
    }

    function openUserSearchModal() {
        userSearchQuery.value = '';
        searchByMatriculaRadio.checked = true;
        setUserSearchMessage('Digite um termo para iniciar a busca.');
        userSearchModal.style.display = 'flex';
        setTimeout(() => userSearchQuery.focus(), 0);
    }

    function setUserSearchMessage(message) {
        userSearchResults.innerHTML = `<p class="user-search-empty">${message}</p>`;
    }

    function renderUserSearchResults(users) {
        if (users.length === 0) {
            setUserSearchMessage('Nenhum usuário encontrado para os filtros informados.');
            return;
        }
        userSearchResults.innerHTML = users.map(user => `
            <div class="user-search-result-item">
                <div class="user-search-result-main">
                    <span class="user-search-result-name">${user.name}</span>
                    <span class="user-search-result-id">Matrícula ${user.id}</span>
                </div>
                <button type="button" class="primary-button select-user-btn" data-user-id="${user.id}" data-user-name="${user.name}">${ICONS.userCheck}<span>Selecionar</span></button>
            </div>
        `).join('');
    }

    function selectUserFromSearch(userId, userName) {
        modalOwnerDisplay.textContent = userName;
        modalOwnerId.value = userId;
        userSearchModal.style.display = 'none';
    }

    

    function buildBookingPayload() {
        const equipmentObs = [
            document.getElementById('modal-projetor').checked && '- Projetor',
            document.getElementById('modal-regua-energia').checked && '- Régua de Energia',
            document.getElementById('modal-suporte-ti').checked && '- Suporte de TI'
        ].filter(Boolean);

        const userDescription = document.getElementById('modal-descricao').value;
        const finalDescription = [userDescription, equipmentObs.length > 0 ? 'Equipamentos necessários:\n' + equipmentObs.join('\n') : ''].filter(Boolean).join('\n\n');

        const payload = {
            sala_id: currentRoomId,
            inicio: document.getElementById('modal-inicio').value,
            fim: document.getElementById('modal-fim').value,
            titulo: document.getElementById('modal-titulo').value,
            descricao: finalDescription,
            sala_nome: rooms.find(r => r.id === currentRoomId).name,
            id_usuario: parseInt(document.getElementById('modal-owner-id').value)
        };

        return payload;
    }

    function logout() {
        localStorage.removeItem('jwtToken');
        localStorage.removeItem('userProfile');
        localStorage.removeItem('userName');
        window.location.href = 'index.html';
    }

    // --- Event Listeners ---
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const nextTheme = document.body.classList.contains('dark-mode') ? 'light-mode' : 'dark-mode';
            applyTheme(nextTheme);
        });
    }

    logoutBtn.addEventListener('click', logout);
    prevWeekBtn.addEventListener('click', async () => {
        if (isMobile()) {
            currentMobileDate.setDate(currentMobileDate.getDate() - 1);
        } else {
            currentWeekStart.setDate(currentWeekStart.getDate() - 7);
        }
        await renderCalendar();
    });
    nextWeekBtn.addEventListener('click', async () => {
        if (isMobile()) {
            currentMobileDate.setDate(currentMobileDate.getDate() + 1);
        } else {
            currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        }
        await renderCalendar();
    });
    closeModalBtn.addEventListener('click', () => bookingModal.style.display = 'none');
    window.addEventListener('click', (event) => { if (event.target == bookingModal) bookingModal.style.display = 'none'; });
    bookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const inicioValue = document.getElementById('modal-inicio').value;
        const fimValue = document.getElementById('modal-fim').value;
        const now = new Date();
        const startDate = new Date(inicioValue);
        const endDate = new Date(fimValue);

        if (startDate < now && !bookingForm.dataset.bookingId) {
            showAlert('Não é possível criar agendamentos para datas ou horários passados.');
            return;
        }

        if (endDate <= startDate) {
            showAlert('O horário de término deve ser posterior ao horário de início.');
            return;
        }

        spinnerOverlay.style.display = 'flex'; // Mostra o loader
        try {
            await (bookingForm.dataset.bookingId ? updateBooking(bookingForm.dataset.bookingId) : createBooking());
        } finally {
            spinnerOverlay.style.display = 'none'; // Esconde o loader
        }
    });
    deleteBookingBtn.addEventListener('click', () => { if (bookingForm.dataset.bookingId) deleteBooking(bookingForm.dataset.bookingId); });
    myBookingsBtn.addEventListener('click', openMyBookingsModal);

    // New event listeners for user search modal
    changeOwnerBtn.addEventListener('click', openUserSearchModal);
    userSearchButton.addEventListener('click', async () => {
        const query = userSearchQuery.value.trim();
        const searchBy = searchByMatriculaRadio.checked ? 'matricula' : 'name';
        if (!query) {
            setUserSearchMessage('Digite algo para pesquisar.');
            userSearchQuery.focus();
            return;
        }

        userSearchButton.disabled = true;
        userSearchButton.textContent = 'Buscando...';
        try {
            const users = await fetchUsersSearch(query, searchBy);
            renderUserSearchResults(users);
        } finally {
            userSearchButton.disabled = false;
            userSearchButton.textContent = 'Buscar';
        }
    });
    userSearchQuery.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            userSearchButton.click();
        }
    });
    userSearchResults.addEventListener('click', (e) => {
        if (e.target.classList.contains('select-user-btn')) {
            const userId = parseInt(e.target.dataset.userId);
            const userName = e.target.dataset.userName;
            selectUserFromSearch(userId, userName);
        }
    });
    userSearchModal.querySelector('.close-btn').addEventListener('click', () => userSearchModal.style.display = 'none');
    window.addEventListener('click', (event) => { if (event.target == userSearchModal) userSearchModal.style.display = 'none'; });
    
    if (localStorage.getItem('userProfile') === 'Administrador') {
        manageRoomsBtn.style.display = 'block';
        manageRoomsBtn.addEventListener('click', openRoomManagementModal);
        addNewRoomBtn.addEventListener('click', addNewRoom);
        editRoomForm.addEventListener('submit', updateRoom);
        roomManagementModal.querySelector('.close-btn').addEventListener('click', () => roomManagementModal.style.display = 'none');
        editRoomModal.querySelector('.close-btn').addEventListener('click', () => editRoomModal.style.display = 'none');
        roomManagementList.addEventListener('click', (e) => {
            if (e.target.classList.contains('edit-room-btn')) openEditRoomModal(rooms.find(r => r.id === parseInt(e.target.dataset.roomId)));
            if (e.target.classList.contains('delete-room-btn')) deleteRoom(parseInt(e.target.dataset.roomId));
            if (e.target.classList.contains('toggle-room-status-btn')) toggleRoomStatus(parseInt(e.target.dataset.roomId));
        });
    } else {
        manageRoomsBtn.style.display = 'none';
    }

    roomList.addEventListener('click', async (e) => {
        if (e.target.classList.contains('room-tab')) {
            const roomId = parseInt(e.target.dataset.roomId);
            if (roomId !== currentRoomId) {
                currentRoomId = roomId;
                renderRoomTabs(rooms);
                await renderCalendar();
            }
        }
    });

    document.getElementById('room-select-mobile')?.addEventListener('change', async (e) => {
        const roomId = parseInt(e.target.value);
        if (roomId !== currentRoomId) {
            currentRoomId = roomId;
            renderRoomTabs(rooms);
            await renderCalendar();
        }
    });

    // Re-renderiza ao mudar entre mobile e desktop
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => renderCalendar(), 300);
    });

    // --- Carga Inicial ---
    injectIcons();
    await fetchRooms();
    await renderCalendar();
});

