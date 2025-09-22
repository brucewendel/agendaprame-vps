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
    let currentWeekStart = getStartOfWeek(new Date());
    let selectedBookingId = null;

    // --- Elementos do DOM ---
    const roomList = document.getElementById('room-list');
    const calendarTitle = document.getElementById('calendar-title');
    const prevWeekBtn = document.getElementById('prev-week-btn');
    const nextWeekBtn = document.getElementById('next-week-btn');
    const loadingMessage = document.getElementById('loading-message');
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
    const userNameSpan = document.getElementById('user-name');

    // --- Modal de Alerta Genérico ---
    const alertModal = document.getElementById('alert-modal');
    const alertModalCloseBtn = document.getElementById('alert-modal-close-btn');
    const alertModalOkBtn = document.getElementById('alert-modal-ok-btn');
    const alertModalMessage = document.getElementById('alert-modal-message');

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
            const response = await fetch('http://127.0.0.1:5000/rooms', { headers: { 'Authorization': `Bearer ${token}` } });
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

    async function fetchBookings(startDate) {
        const toApiFormat = (date) => new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().split('T')[0] + 'T00:00:00';
        const startIso = toApiFormat(startDate);
        const endDate = new Date(startDate);
        endDate.setDate(startDate.getDate() + 6);
        const endIso = toApiFormat(endDate);

        try {
            const response = await fetch(`http://127.0.0.1:5000/agendamentos?start=${startIso}&end=${endIso}`, { headers: { 'Authorization': `Bearer ${token}` } });
            return response.ok ? await response.json() : (showAlert('Erro ao carregar agendamentos.'), []);
        } catch (error) {
            showAlert('Erro de conexão ao buscar agendamentos.');
            return [];
        }
    }

    async function createBooking() {
        const payload = buildBookingPayload();
        try {
            const response = await fetch('http://127.0.0.1:5000/agendamentos', {
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
            const response = await fetch(`http://127.0.0.1:5000/agendamentos/${bookingId}`, {
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
            const response = await fetch(`http://127.0.0.1:5000/agendamentos/${bookingId}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } });
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
            const response = await fetch('http://127.0.0.1:5000/rooms', {
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
            const response = await fetch(`http://127.0.0.1:5000/rooms/${roomId}`, {
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
            const response = await fetch(`http://127.0.0.1:5000/rooms/${roomId}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } });
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
            const response = await fetch(`http://127.0.0.1:5000/rooms/${roomId}`, {
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
    }

    function renderHours() {
        calendarHours.innerHTML = Array.from({length: 14}, (_, i) => `<div>${(i + 7).toString().padStart(2, '0')}:00</div>`).join('');
    }

    async function renderCalendar() {
        renderHours(); // Garante que as horas sejam renderizadas
        if (currentRoomId === null) {
            calendarGridBody.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 20px;">Nenhuma sala ativa encontrada.</div>';
            calendarGridHeaders.innerHTML = '';
            calendarTitle.textContent = 'Nenhuma Sala Selecionada';
            loadingMessage.style.display = 'none';
            return;
        }

        loadingMessage.style.display = 'block';
        const weekDates = Array.from({length: 6}, (_, i) => {
            const date = new Date(currentWeekStart);
            date.setDate(currentWeekStart.getDate() + i);
            return date;
        });

        calendarTitle.textContent = `${weekDates[0].toLocaleDateString('pt-BR', {day: '2-digit', month: 'short'})} - ${weekDates[5].toLocaleDateString('pt-BR', {day: '2-digit', month: 'short'})}`;
        calendarGridHeaders.innerHTML = '<div class="calendar-hours-header">Horários</div>' + weekDates.map(date => 
            `<div class="calendar-day-header">${date.toLocaleDateString('pt-BR', {weekday: 'short'})}<br>${date.toLocaleDateString('pt-BR', {day: '2-digit'})}</div>`
        ).join('');

        const bookings = await fetchBookings(currentWeekStart);
        loadingMessage.style.display = 'none';

        calendarGridBody.innerHTML = weekDates.map(date => `
            <div class="calendar-day-cell">
                <div class="day-cell-content">
                    ${Array.from({length: 14}, (_, hour) => `<div class="time-slot" data-date="${date.toISOString().split('T')[0]}" data-hour="${hour + 7}"></div>`).join('')}
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
            const startDay = start.getDay();
            if (startDay === 0) return; // Ignora domingo

            const dayOffset = startDay - 1;
            const bookingStartDay = new Date(start.getFullYear(), start.getMonth(), start.getDate());
            if (bookingStartDay < weekDates[0] || bookingStartDay > weekDates[5]) return;

            const dayCellContent = calendarGridBody.children[dayOffset]?.querySelector('.day-cell-content');
            if (dayCellContent) {
                const bookingBlock = document.createElement('div');
                bookingBlock.className = 'booking-block';
                bookingBlock.textContent = booking.TITULO;
                bookingBlock.dataset.bookingId = booking.ID_AGENDAMENTO;
                const slotHeight = 40;
                const top = ((start.getHours() - 7) * slotHeight) + (start.getMinutes() * slotHeight / 60);
                const height = (end.getTime() - start.getTime()) / (1000 * 60) / 60 * slotHeight;
                Object.assign(bookingBlock.style, { position: 'absolute', top: `${top}px`, height: `${height}px` });
                bookingBlock.addEventListener('click', (e) => { e.stopPropagation(); openBookingModalForEdit(booking.ID_AGENDAMENTO); });
                dayCellContent.appendChild(bookingBlock);
            }
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
        document.getElementById('modal-sala').value = rooms.find(r => r.id === currentRoomId).name;
        document.getElementById('modal-inicio').value = `${date}T${hour.padStart(2, '0')}:00`;
        document.getElementById('modal-fim').value = `${date}T${(parseInt(hour) + 1).toString().padStart(2, '0')}:00`;
        deleteBookingBtn.style.display = 'none';
        bookingForm.querySelector('button[type="submit"]').textContent = 'Agendar';
        bookingModal.style.display = 'flex';
    }

    async function openBookingModalForEdit(bookingId) {
        try {
            const response = await fetch(`http://127.0.0.1:5000/agendamentos/${bookingId}`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('Falha ao carregar dados do agendamento.');
            const booking = await response.json();
            
            const isOwner = booking.ID_USUARIO === userId;
            const isAdmin = localStorage.getItem('userProfile') === 'Administrador';

            bookingForm.setAttribute('data-booking-id', bookingId);
            document.getElementById('modal-titulo').value = booking.TITULO;
            document.getElementById('modal-sala').value = rooms.find(r => r.id === booking.ID_SALA).name;
            document.getElementById('modal-inicio').value = booking.DATA_INICIO.replace(' ', 'T');
            document.getElementById('modal-fim').value = booking.DATA_FIM.replace(' ', 'T');
            
            const desc = booking.DESCRICAO || '';
            const equipmentRegex = /Equipamentos necessários:[\s\S]*/;
            document.getElementById('modal-descricao').value = desc.replace(equipmentRegex, '').trim();
            const equipmentMatch = desc.match(equipmentRegex);
            document.getElementById('modal-projetor').checked = equipmentMatch ? equipmentMatch[0].includes('Projetor') : false;
            document.getElementById('modal-regua-energia').checked = equipmentMatch ? equipmentMatch[0].includes('Régua de Energia') : false;
            document.getElementById('modal-suporte-ti').checked = equipmentMatch ? equipmentMatch[0].includes('Suporte de TI') : false;

            const canEdit = isAdmin || isOwner;
            deleteBookingBtn.style.display = canEdit ? 'inline-block' : 'none';
            bookingForm.querySelector('button[type="submit"]').style.display = canEdit ? 'inline-block' : 'none';
            Array.from(bookingForm.elements).forEach(el => el.disabled = !canEdit);
            document.getElementById('modal-sala').disabled = true; // Sala não pode ser alterada

            bookingModal.style.display = 'flex';
        } catch (error) {
            showAlert(error.message);
        }
    }

    function openRoomManagementModal() {
        roomManagementList.innerHTML = rooms.map(room => `
            <div class="room-management-item">
                <span>${room.name}</span>
                <div>
                    <button class="edit-room-btn" data-room-id="${room.id}">Editar</button>
                    <button class="delete-room-btn" data-room-id="${room.id}">Excluir</button>
                    <button class="toggle-room-status-btn" data-room-id="${room.id}">${room.active ? 'Desativar' : 'Ativar'}</button>
                </div>
            </div>`).join('');
        roomManagementModal.style.display = 'flex';
    }

    function openEditRoomModal(room) {
        editRoomId.value = room.id;
        editRoomName.value = room.name;
        editRoomModal.style.display = 'flex';
    }

    // --- Helpers ---
    function getStartOfWeek(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1);
        return new Date(new Date(d.setDate(diff)).setHours(0, 0, 0, 0));
    }

    function buildBookingPayload() {
        const equipmentObs = [
            document.getElementById('modal-projetor').checked && '- Projetor',
            document.getElementById('modal-regua-energia').checked && '- Régua de Energia',
            document.getElementById('modal-suporte-ti').checked && '- Suporte de TI'
        ].filter(Boolean);

        const userDescription = document.getElementById('modal-descricao').value;
        const finalDescription = [userDescription, equipmentObs.length > 0 ? `Equipamentos necessários:\n${equipmentObs.join('\n')}` : ''].filter(Boolean).join('\n\n');

        return {
            sala_id: currentRoomId,
            inicio: document.getElementById('modal-inicio').value,
            fim: document.getElementById('modal-fim').value,
            titulo: document.getElementById('modal-titulo').value,
            descricao: finalDescription,
            sala_nome: rooms.find(r => r.id === currentRoomId).name
        };
    }

    function logout() {
        localStorage.clear();
        window.location.href = 'index.html';
    }

    // --- Event Listeners ---
    logoutBtn.addEventListener('click', logout);
    prevWeekBtn.addEventListener('click', async () => { currentWeekStart.setDate(currentWeekStart.getDate() - 7); await renderCalendar(); });
    nextWeekBtn.addEventListener('click', async () => { currentWeekStart.setDate(currentWeekStart.getDate() + 7); await renderCalendar(); });
    closeModalBtn.addEventListener('click', () => bookingModal.style.display = 'none');
    window.addEventListener('click', (event) => { if (event.target == bookingModal) bookingModal.style.display = 'none'; });
    bookingForm.addEventListener('submit', async (e) => { e.preventDefault(); await (bookingForm.dataset.bookingId ? updateBooking(bookingForm.dataset.bookingId) : createBooking()); });
    deleteBookingBtn.addEventListener('click', () => { if (bookingForm.dataset.bookingId) deleteBooking(bookingForm.dataset.bookingId); });
    
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
                renderRoomTabs(rooms); // Re-render to update active tab
                await renderCalendar();
            }
        }
    });

    // --- Carga Inicial ---
    await fetchRooms();
    if (currentRoomId) {
        await renderCalendar();
    }
});