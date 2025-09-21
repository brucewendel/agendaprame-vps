document.addEventListener('DOMContentLoaded', async function() {
    const token = localStorage.getItem('jwtToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }
    const decodedToken = jwt_decode(token);
    const userId = decodedToken.user_id;

    let rooms = []; // Agora as salas serão carregadas da API
    let currentRoomId = null;
    let currentWeekStart = getStartOfWeek(new Date());
    let selectedBookingId = null;

    // Elementos do DOM
    const roomList = document.getElementById('room-list');
    const calendarTitle = document.getElementById('calendar-title');
    const prevWeekBtn = document.getElementById('prev-week-btn');
    const nextWeekBtn = document.getElementById('next-week-btn');
    const loadingMessage = document.getElementById('loading-message');
    const calendarGridHeaders = document.getElementById('calendar-grid-headers');
    const calendarGridBody = document.getElementById('calendar-grid-body');
    const calendarHours = document.querySelector('.calendar-hours');
    const modal = document.getElementById('booking-modal');
    const closeModalBtn = document.querySelector('.close-btn');
    const bookingForm = document.getElementById('booking-form');
    const modalRoomInput = document.getElementById('modal-sala');
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

    // Inicialização
    const userName = localStorage.getItem('userName');
    if (userName && userName !== 'undefined') {
        userNameSpan.textContent = `Olá, ${userName}`;
    } else {
        userNameSpan.textContent = 'Olá, Usuário';
    }
    
    // Função para buscar as salas da API
    async function fetchRooms() {
        try {
            const response = await fetch('http://127.0.0.1:5000/rooms', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                rooms = await response.json();
                if (rooms.length > 0 && currentRoomId === null) {
                    const activeRooms = rooms.filter(room => room.active);
                    if (activeRooms.length > 0) {
                        currentRoomId = activeRooms[0].id;
                    } else {
                        currentRoomId = null; // No active rooms found
                    }
                }
                renderRoomTabs(rooms);
            } else {
                console.error('Erro ao carregar salas:', await response.text());
            }
        } catch (error) {
            console.error('Erro ao conectar com o servidor para buscar salas:', error);
        }
    }

    await fetchRooms(); // Carrega as salas antes de renderizar o calendário
    renderHours();
    await renderCalendar();

    // Event Listeners
    roomList.addEventListener('click', async (event) => {
        const tab = event.target.closest('.room-tab');
        if (tab && !tab.classList.contains('active')) {
            currentRoomId = parseInt(tab.dataset.roomId);
            document.querySelectorAll('.room-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            await renderCalendar();
        }
    });

    prevWeekBtn.addEventListener('click', async () => {
        currentWeekStart.setDate(currentWeekStart.getDate() - 7);
        await renderCalendar();
    });

    nextWeekBtn.addEventListener('click', async () => {
        currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        await renderCalendar();
    });

    closeModalBtn.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });

    bookingForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const bookingId = bookingForm.dataset.bookingId;
        if (bookingId) {
            await updateBooking(token, bookingId);
        } else {
            await createBooking(token);
        }
    });

    deleteBookingBtn.addEventListener('click', async () => {
        if (selectedBookingId && confirm('Tem certeza que deseja excluir este agendamento?')) {
            await deleteBooking(token, selectedBookingId);
        }
    });

    

    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    if (localStorage.getItem('userProfile') === 'Administrador') {
        manageRoomsBtn.style.display = 'block';
        manageRoomsBtn.addEventListener('click', openRoomManagementModal);
        addNewRoomBtn.addEventListener('click', openAddRoomModal);
        editRoomForm.addEventListener('submit', updateRoom);
    } else {
        manageRoomsBtn.style.display = 'none';
    }

    // Utilitários
    function getStartOfWeek(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Segunda-feira
        const startOfWeek = new Date(d.setDate(diff));
        startOfWeek.setHours(0, 0, 0, 0);
        return startOfWeek;
    }

    function formatDateTimeLocal(date) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const seconds = date.getSeconds().toString().padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
    }

    // Gera observações com base nos equipamentos selecionados
    function generateEquipmentObservations() {
        const observations = [];
        if (document.getElementById('modal-projetor').checked) {
            observations.push('- Projetor');
        }
        if (document.getElementById('modal-regua-energia').checked) {
            observations.push('- Régua de Energia');
        }
        if (document.getElementById('modal-suporte-ti').checked) {
            observations.push('- Suporte de TI');
        }
        return observations.length > 0 ? `Equipamentos necessários:\n${observations.join('\n')}` : '';
    }
    // Renderização das abas de sala
    function renderRoomTabs(rooms) {
        const userProfile = localStorage.getItem('userProfile');
        const activeRooms = rooms.filter(room => room.active);
        roomList.innerHTML = activeRooms.map(room => `
            <div class="room-tab ${room.id === currentRoomId ? 'active' : ''}" data-room-id="${room.id}">
                ${room.name}
            </div>
        `).join('');
    }

    function openRoomManagementModal() {
        roomManagementList.innerHTML = rooms.map(room => `
            <div class="room-management-item">
                <span>${room.name}</span>
                <div>
                    <button class="edit-room-btn" data-room-id="${room.id}">Editar</button>
                    <button class="delete-room-btn" data-room-id="${room.id}">Excluir</button>
                    <button class="deactivate-room-btn" data-room-id="${room.id}">${room.active ? 'Desativar' : 'Ativar'}</button>
                </div>
            </div>
        `).join('');

        roomManagementModal.style.display = 'flex';

        roomManagementList.querySelectorAll('.edit-room-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const roomId = parseInt(e.target.dataset.roomId);
                const room = rooms.find(r => r.id === roomId);
                openEditRoomModal(room);
            });
        });

        roomManagementList.querySelectorAll('.delete-room-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const roomId = parseInt(e.target.dataset.roomId);
                deleteRoom(roomId);
            });
        });

        roomManagementList.querySelectorAll('.deactivate-room-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const roomId = parseInt(e.target.dataset.roomId);
                deactivateRoom(roomId);
            });
        });
    }

    // Modal de adicionar sala
    async function openAddRoomModal() {
        const name = prompt('Nome da nova sala:');
        if (name) {
            try {
                const response = await fetch('http://127.0.0.1:5000/rooms', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ name: name })
                });
                if (response.ok) {
                    await fetchRooms();
                    await renderCalendar();
                    openRoomManagementModal();
                } else {
                    console.error('Erro ao criar sala:', await response.text());
                    alert('Erro ao criar sala.');
                }
            } catch (error) {
                console.error('Erro ao conectar com o servidor para criar sala:', error);
                alert('Erro ao conectar com o servidor.');
            }
        }
    }

    // Modal de editar sala
    function openEditRoomModal(room) {
        editRoomId.value = room.id;
        editRoomName.value = room.name;
        editRoomModal.style.display = 'flex';
    }

    async function updateRoom(e) {
        e.preventDefault();
        const roomId = parseInt(editRoomId.value);
        const newName = editRoomName.value;
        
        try {
            const response = await fetch(`http://127.0.0.1:5000/rooms/${roomId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ name: newName })
            });
            if (response.ok) {
                await fetchRooms();
                await renderCalendar();
                editRoomModal.style.display = 'none';
                openRoomManagementModal();
            } else {
                console.error('Erro ao atualizar sala:', await response.text());
                alert('Erro ao atualizar sala.');
            }
        } catch (error) {
            console.error('Erro ao conectar com o servidor para atualizar sala:', error);
            alert('Erro ao conectar com o servidor.');
        }
    }

    // Excluir sala
    async function deleteRoom(roomId) {
        if (confirm('Deseja realmente excluir esta sala?')) {
            try {
                const response = await fetch(`http://127.0.0.1:5000/rooms/${roomId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    await fetchRooms();
                    if (currentRoomId === roomId) {
                        currentRoomId = rooms[0]?.id || null;
                    }
                    await renderCalendar();
                    openRoomManagementModal();
                } else {
                    console.error('Erro ao excluir sala:', await response.text());
                    alert('Erro ao excluir sala.');
                }
            } catch (error) {
                console.error('Erro ao conectar com o servidor para excluir sala:', error);
                alert('Erro ao conectar com o servidor.');
            }
        }
    }

    async function deactivateRoom(roomId) {
        const room = rooms.find(r => r.id === roomId);
        if (room) {
            try {
                const response = await fetch(`http://127.0.0.1:5000/rooms/${roomId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ active: !room.active })
                });
                if (response.ok) {
                    await fetchRooms();
                    await renderCalendar();
                    openRoomManagementModal();
                } else {
                    console.error('Erro ao desativar/ativar sala:', await response.text());
                    alert('Erro ao desativar/ativar sala.');
                }
            } catch (error) {
                console.error('Erro ao conectar com o servidor para desativar/ativar sala:', error);
                alert('Erro ao conectar com o servidor.');
            }
        }
    }

    // Renderização das horas
    function renderHours() {
        calendarHours.innerHTML = '';
        for (let i = 7; i <= 20; i++) {
            const hour = i.toString().padStart(2, '0') + ':00';
            calendarHours.innerHTML += `<div>${hour}</div>`;
        }
    }

    // Renderização do calendário (segunda a sábado, 07h às 20h)
    async function renderCalendar() {
        if (currentRoomId === null) {
            calendarGridBody.innerHTML = '<div style="text-align: center; padding: 20px;">Nenhuma sala ativa encontrada para exibir o calendário.</div>';
            calendarGridHeaders.innerHTML = '';
            calendarTitle.textContent = 'Nenhuma Sala';
            loadingMessage.style.display = 'none';
            return;
        }

        const daysOfWeekNames = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
        calendarGridHeaders.innerHTML = '<div class="calendar-hours-header">Horários</div>';
        const weekDates = [];
        for (let i = 0; i < 6; i++) {
            const date = new Date(currentWeekStart);
            date.setDate(currentWeekStart.getDate() + i);
            weekDates.push(date);
        }
        calendarTitle.textContent =
            `${weekDates[0].toLocaleString('pt-BR', { month: 'long', day: 'numeric' })} - ${weekDates[5].toLocaleString('pt-BR', { month: 'long', day: 'numeric' })}`;
        weekDates.forEach(date => {
            const dayName = daysOfWeekNames[date.getDay() === 0 ? 6 : date.getDay() - 1];
            const formattedDate = `${dayName} ${date.getDate()}/${date.getMonth() + 1}`;
            calendarGridHeaders.innerHTML += `<div class="calendar-day-header">${formattedDate}</div>`;
        });

        calendarGridBody.innerHTML = '';
        loadingMessage.style.display = 'block';

        const bookings = await fetchBookings(token, currentWeekStart);
        loadingMessage.style.display = 'none';

        for (let dayIndex = 0; dayIndex < 6; dayIndex++) {
            const dayCell = document.createElement('div');
            dayCell.className = 'calendar-day-cell';
            
            // Cria um contêiner interno para os slots e blocos
            const dayCellContent = document.createElement('div');
            dayCellContent.className = 'day-cell-content';
 
            const date = weekDates[dayIndex];
 
            for (let hour = 7; hour <= 20; hour++) {
                const timeSlot = document.createElement('div');
                timeSlot.className = 'time-slot';
                timeSlot.dataset.date = date.toISOString().split('T')[0];
                timeSlot.dataset.hour = hour;
                timeSlot.addEventListener('click', (event) => openBookingModalForCreation(event));
                dayCellContent.appendChild(timeSlot);
            }
            dayCell.appendChild(dayCellContent);
            calendarGridBody.appendChild(dayCell);
        }

        renderBookingBlocks(bookings, weekDates);
    }

    // Renderização dos blocos de agendamento
    function renderBookingBlocks(bookings, weekDates) {
        document.querySelectorAll('.booking-block').forEach(block => block.remove());
        if (!bookings) return;
        const bookingsForRoom = bookings.filter(b => b.ID_SALA === currentRoomId);

        bookingsForRoom.forEach(booking => {
            // O backend agora envia a data formatada, então podemos criar o objeto Date diretamente.
            const start = new Date(booking.DATA_INICIO);
            const end = new Date(booking.DATA_FIM);

            // Só exibe se estiver entre segunda e sábado
            const startDay = start.getDay();
            if (startDay === 0 || startDay > 6) return; // Ignora domingo

            // Calcula o índice do dia (segunda=0, ..., sábado=5)
            const dayOffset = startDay - 1;
            if (dayOffset < 0 || dayOffset > 5) return;

            const bookingStartDay = new Date(start.getFullYear(), start.getMonth(), start.getDate());
            const weekStartDay = new Date(weekDates[0].getFullYear(), weekDates[0].getMonth(), weekDates[0].getDate());
            const weekEndDay = new Date(weekDates[5].getFullYear(), weekDates[5].getMonth(), weekDates[5].getDate());
            if (bookingStartDay < weekStartDay || bookingStartDay > weekEndDay) return;

            const startHour = start.getHours();
            const startMinute = start.getMinutes();
            const endHour = end.getHours();
            const endMinute = end.getMinutes();
            const durationInMinutes = (end.getTime() - start.getTime()) / (1000 * 60);

            // O bloco de agendamento deve ser filho do .day-cell-content
            const dayCell = calendarGridBody.children[dayOffset]?.querySelector('.day-cell-content');

            if (dayCell) {
                const bookingBlock = document.createElement('div');
                bookingBlock.className = 'booking-block';
                bookingBlock.textContent = booking.TITULO;
                bookingBlock.dataset.bookingId = booking.ID_AGENDAMENTO;
                bookingBlock.dataset.roomId = booking.ID_SALA;
                // Ajuste: calcula top e height para englobar as grades corretamente
                const slotHeight = 40; // Altura de cada slot em pixels
                const top = ((startHour - 7) * slotHeight) + (startMinute * slotHeight / 60);
                const height = (durationInMinutes / 60) * slotHeight; // Correção no cálculo da altura
                bookingBlock.style.position = 'absolute';
                bookingBlock.style.top = `${top}px`;
                bookingBlock.style.height = `${height}px`;
                bookingBlock.addEventListener('click', (event) => {
                    event.stopPropagation();
                    openBookingModalForEdit(booking.ID_AGENDAMENTO, booking.ID_SALA);
                });
                dayCell.appendChild(bookingBlock);
            }
        });
    }

    // Requisição dos agendamentos
    async function fetchBookings(token, startDate) {
        // Helper para formatar a data para o formato YYYY-MM-DDTHH:MM:SS que a API espera,
        // usando os componentes da data local para evitar problemas de fuso horário.
        const toApiFormat = (date) => {
            const year = date.getFullYear();
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            const day = date.getDate().toString().padStart(2, '0');
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            const seconds = date.getSeconds().toString().padStart(2, '0');
            return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
        };

        const startIso = toApiFormat(startDate);

        // O período de busca deve cobrir a semana inteira, de segunda a sábado.
        // A query do backend é (DATA_INICIO < end_date), então pegamos o início do próximo dia (domingo).
        const endDate = new Date(startDate);
        endDate.setDate(startDate.getDate() + 6); // startDate (segunda) + 6 dias = Domingo
        const endIso = toApiFormat(endDate);

        try {
            const response = await fetch(`http://127.0.0.1:5000/agendamentos?start=${startIso}&end=${endIso}`, {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                return data;
            } else {
                console.error('Erro ao carregar agendamentos:', await response.text());
                return [];
            }
        } catch (error) {
            console.error('Erro ao conectar com o servidor:', error);
            return [];
        }
    }

    // Criação de agendamento
    async function createBooking(token) {
        const messageArea = document.getElementById('modal-message-area');
        messageArea.style.display = 'none';
        messageArea.classList.remove('message-success', 'message-error');

        const equipmentObs = generateEquipmentObservations();
        const userDescription = document.getElementById('modal-descricao').value;

        const roomName = rooms.find(r => r.id === currentRoomId).name;

        const payload = {
            sala_id: currentRoomId,
            inicio: document.getElementById('modal-inicio').value,
            fim: document.getElementById('modal-fim').value,
            titulo: document.getElementById('modal-titulo').value,
            descricao: [userDescription, equipmentObs].filter(Boolean).join('\n\n'),
            sala_nome: roomName // Adiciona o nome da sala para a notificação
        };

        console.log('Payload sent to createBooking:', payload);
        console.log('currentRoomId before sending:', currentRoomId);

        try {
            const response = await fetch('http://127.0.0.1:5000/agendamentos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                messageArea.textContent = data.message || 'Agendamento criado com sucesso!';
                messageArea.classList.add('message-success');
                messageArea.style.display = 'block';
                modal.style.display = 'none';
                await renderCalendar();
            } else {
                messageArea.textContent = data.message || 'Erro ao agendar a sala.';
                messageArea.classList.add('message-error');
                messageArea.style.display = 'block';
            }
        } catch (error) {
            messageArea.textContent = 'Erro ao conectar com o servidor.';
            messageArea.classList.add('message-error');
            messageArea.style.display = 'block';
            console.error('Erro na requisição:', error);
        }
    }

    // Atualização de agendamento
    async function updateBooking(token, bookingId) {
        const messageArea = document.getElementById('modal-message-area');
        messageArea.style.display = 'none';
        messageArea.classList.remove('message-success', 'message-error');

        const equipmentObs = generateEquipmentObservations();
        const userDescription = document.getElementById('modal-descricao').value;

        const payload = {
            sala_id: currentRoomId,
            inicio: document.getElementById('modal-inicio').value,
            fim: document.getElementById('modal-fim').value,
            titulo: document.getElementById('modal-titulo').value,
            descricao: [userDescription, equipmentObs].filter(Boolean).join('\n\n')
        };

        try {
            const response = await fetch(`http://127.0.0.1:5000/agendamentos/${bookingId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                messageArea.textContent = data.message || 'Agendamento alterado com sucesso!';
                messageArea.classList.add('message-success');
                messageArea.style.display = 'block';
                modal.style.display = 'none';
                await renderCalendar();
            } else {
                messageArea.textContent = data.message || 'Erro ao alterar o agendamento.';
                messageArea.classList.add('message-error');
                messageArea.style.display = 'block';
            }
        } catch (error) {
            messageArea.textContent = 'Erro ao conectar com o servidor.';
            messageArea.classList.add('message-error');
            messageArea.style.display = 'block';
            console.error('Erro na requisição:', error);
        }
    }

    // Exclusão de agendamento
    async function deleteBooking(token, bookingId) {
        const messageArea = document.getElementById('modal-message-area');
        messageArea.style.display = 'none';
        messageArea.classList.remove('message-success', 'message-error');

        try {
            const response = await fetch(`http://127.0.0.1:5000/agendamentos/${bookingId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (response.ok) {
                messageArea.textContent = data.message || 'Agendamento excluído com sucesso!';
                messageArea.classList.add('message-success');
                messageArea.style.display = 'block';
                modal.style.display = 'none';
                await renderCalendar();
            } else {
                messageArea.textContent = data.message || 'Erro ao excluir o agendamento.';
                messageArea.classList.add('message-error');
                messageArea.style.display = 'block';
            }
        } catch (error) {
            messageArea.textContent = 'Erro ao conectar com o servidor.';
            messageArea.classList.add('message-error');
            messageArea.style.display = 'block';
            console.error('Erro na requisição:', error);
        }
    }

    // Modal de criação de agendamento
    function openBookingModalForCreation(event) {
        if (currentRoomId === null) {
            alert('Nenhuma sala selecionada para agendar.');
            return;
        }

        const slot = event.target;
        const date = slot.dataset.date;
        const hour = slot.dataset.hour;

        bookingForm.reset();
        bookingForm.removeAttribute('data-booking-id');
        document.getElementById('modal-titulo').value = '';
        document.getElementById('modal-descricao').value = '';
        document.getElementById('modal-projetor').checked = false;
        document.getElementById('modal-regua-energia').checked = false;
        document.getElementById('modal-suporte-ti').checked = false;
        document.getElementById('modal-sala').value = rooms.find(r => r.id === currentRoomId).name;
        document.getElementById('modal-inicio').value = `${date}T${hour.padStart(2, '0')}:00`;
        document.getElementById('modal-fim').value = `${date}T${(parseInt(hour) + 1).toString().padStart(2, '0')}:00`;

        deleteBookingBtn.style.display = 'none';
        bookingForm.querySelector('button[type="submit"]').textContent = 'Agendar';
        selectedBookingId = null;
        document.getElementById('modal-message-area').style.display = 'none';
        modal.style.display = 'flex';
    }

    // Modal de edição de agendamento
    async function openBookingModalForEdit(bookingId, roomId) {
        selectedBookingId = bookingId;
        bookingForm.setAttribute('data-booking-id', bookingId);

        const messageArea = document.getElementById('modal-message-area');
        messageArea.style.display = 'none';
        messageArea.classList.remove('message-success', 'message-error');

        try {
            const response = await fetch(`http://127.0.0.1:5000/agendamentos/${bookingId}`, {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const booking = await response.json();
                const userProfile = localStorage.getItem('userProfile');
                const userId = jwt_decode(token).user_id;

                const isOwner = booking.ID_USUARIO === userId;
                const isAdmin = userProfile === 'Administrador';

                document.getElementById('modal-titulo').value = booking.TITULO;
                document.getElementById('modal-sala').value = rooms.find(r => r.id === roomId).name;
                document.getElementById('modal-inicio').value = formatDateTimeLocal(new Date(booking.DATA_INICIO));
                document.getElementById('modal-fim').value = formatDateTimeLocal(new Date(booking.DATA_FIM));
                
                // Separa a descrição do usuário das observações de equipamento
                const desc = booking.DESCRICAO || '';
                const equipmentRegex = /Equipamentos necessários:([\s\S]*)/;
                const equipmentMatch = desc.match(equipmentRegex);
                
                document.getElementById('modal-descricao').value = desc.replace(equipmentRegex, '').trim();

                if (equipmentMatch && equipmentMatch[1]) {
                    document.getElementById('modal-projetor').checked = equipmentMatch[1].includes('Projetor');
                    document.getElementById('modal-regua-energia').checked = equipmentMatch[1].includes('Régua de Energia');
                    document.getElementById('modal-suporte-ti').checked = equipmentMatch[1].includes('Suporte de TI');
                }

                if (isAdmin || isOwner) {
                    deleteBookingBtn.style.display = 'inline-block';
                    bookingForm.querySelector('button[type="submit"]').textContent = 'Salvar Alterações';
                    bookingForm.querySelector('button[type="submit"]').style.display = 'inline-block';
                    document.getElementById('modal-titulo').disabled = false;
                    document.getElementById('modal-inicio').disabled = false;
                    document.getElementById('modal-fim').disabled = false;
                    document.getElementById('modal-descricao').disabled = false;
                    document.getElementById('modal-projetor').disabled = false;
                    document.getElementById('modal-regua-energia').disabled = false;
                    document.getElementById('modal-suporte-ti').disabled = false;
                } else {
                    deleteBookingBtn.style.display = 'none';
                    bookingForm.querySelector('button[type="submit"]').style.display = 'none';
                    document.getElementById('modal-titulo').disabled = true;
                    document.getElementById('modal-inicio').disabled = true;
                    document.getElementById('modal-fim').disabled = true;
                    document.getElementById('modal-descricao').disabled = true;
                    document.getElementById('modal-projetor').disabled = true;
                    document.getElementById('modal-regua-energia').disabled = true;
                    document.getElementById('modal-suporte-ti').disabled = true;
                    messageArea.textContent = 'Você não tem permissão para editar este agendamento.';
                    messageArea.classList.add('message-error');
                    messageArea.style.display = 'block';
                }

                modal.style.display = 'flex';
            } else {
                messageArea.textContent = 'Erro ao carregar detalhes do agendamento.';
                messageArea.classList.add('message-error');
                messageArea.style.display = 'block';
                modal.style.display = 'flex';
            }
        } catch (error) {
            messageArea.textContent = 'Erro ao conectar com o servidor.';
            messageArea.classList.add('message-error');
            messageArea.style.display = 'block';
            modal.style.display = 'flex';
            console.error('Erro na requisição:', error);
        }
    }

    

    // Logout
    function logout() {
        localStorage.removeItem('jwtToken');
        localStorage.removeItem('userProfile');
        localStorage.removeItem('userName');
        window.location.href = 'index.html';
    }
});