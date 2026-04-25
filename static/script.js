/* ===================================================
   Медиахаб — script.js
   Интерактивность: auth, reg, lc, home (навбар)
   =================================================== */

(function () {
    'use strict';

    /* ---------- HELPERS ---------- */

    function $(sel, ctx) { return (ctx || document).querySelector(sel); }
    function $$(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

    /** Показать toast-уведомление */
    function showToast(msg, type) {
        var t = $('#toast');
        if (!t) return;
        t.textContent = msg;
        t.className = 'toast show ' + (type || '');
        setTimeout(function () { t.className = 'toast'; }, 3000);
    }

    /** Получить параметр из URL */
    function getParam(name) {
        var url = new URL(window.location.href);
        return url.searchParams.get(name);
    }

    /** Простая «БД» пользователя в localStorage */
    function getUser() {
        try { return JSON.parse(localStorage.getItem('mh_user')); } catch (e) { return null; }
    }
    function setUser(u) {
        localStorage.setItem('mh_user', JSON.stringify(u));
    }
    function clearUser() {
        localStorage.removeItem('mh_user');
    }

    /* ====================================================
       AUTH PAGE  (auth.html)
       ==================================================== */
    function initAuth() {
        var loginStep = $('#loginStep');
        var regStep = $('#regStep');
        if (!loginStep || !regStep) return;

        var goToReg = $('#goToReg');
        var goToLogin = $('#goToLogin');

        // Переключение: «Зарегистрироваться» (из логина → регистрация)
        if (goToReg) {
            goToReg.addEventListener('click', function (e) {
                e.preventDefault();
                loginStep.style.display = 'none';
                regStep.style.display = '';
            });
        }

        // Переключение: «Войти» (из регистрации → логин)
        if (goToLogin) {
            goToLogin.addEventListener('click', function (e) {
                e.preventDefault();
                regStep.style.display = 'none';
                loginStep.style.display = '';
            });
        }

        // Клик по кнопке роли → выбор роли
        $$('.role-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                $$('.role-btn').forEach(function (b) { b.classList.remove('selected'); });
                btn.classList.add('selected');
                var role = btn.getAttribute('data-role');

                // Заполнить роль в форме регистрации
                var roleInput = $('#regRole');
                var roleLabel = $('#regRoleLabel');
                var roleLabels = { smm: 'СММ', volunteer: 'Волонтёр' };

                if (roleInput) roleInput.value = role;
                if (roleLabel) roleLabel.textContent = roleLabels[role] || 'Не выбрана';
            });
        });

        // Логин-форма
        var loginForm = $('#loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var ok = true;

                var username = $('#loginUsername').value.trim();
                var password = $('#loginPassword').value.trim();

                // Валидация
                clearAuthError('loginUsername');
                clearAuthError('loginPassword');

                if (!username) {
                    setAuthError('loginUsername', 'Введите имя пользователя');
                    ok = false;
                }
                if (!password) {
                    setAuthError('loginPassword', 'Введите пароль');
                    ok = false;
                }

                if (!ok) return;

                // Отправка данных на сервер
                var formData = new FormData();
                formData.append('username', username);
                formData.append('password', password);

                fetch('/auth', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;
                        return;
                    }
                    return response.text().then(text => {
                        // Проверяем наличие реального сообщения об ошибке, а не просто подстроки 'error'
                        if (text.includes('class="auth-error visible"') || text.includes('Ошибка')) {
                            showToast('Неверное имя пользователя или пароль', 'error');
                        } else {
                            window.location.href = '/lc';
                        }
                    });
                })
                .catch(err => {
                    console.error('Auth error:', err);
                    showToast('Ошибка при авторизации', 'error');
                });
            });
        }

        // Регистрационная форма
        var regForm = $('#regForm');
        if (regForm) {
            regForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var ok = true;

                var role = $('#regRole').value;
                var name = $('#regName').value.trim();
                var email = $('#regEmail').value.trim();
                var pass = $('#regPassword').value;
                var pass2 = $('#regPassword2').value;

                // Очистка ошибок
                ['regName', 'regEmail', 'regPassword', 'regPassword2'].forEach(clearAuthError);

                if (!role) {
                    showToast('Выберите роль для регистрации', 'error');
                    ok = false;
                }
                if (!name) { setAuthError('regName', 'Введите имя пользователя'); ok = false; }
                if (!email) { setAuthError('regEmail', 'Введите email'); ok = false; }
                else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setAuthError('regEmail', 'Некорректный email'); ok = false; }
                if (!pass) { setAuthError('regPassword', 'Введите пароль'); ok = false; }
                else if (pass.length < 6) { setAuthError('regPassword', 'Минимум 6 символов'); ok = false; }
                if (pass !== pass2) { setAuthError('regPassword2', 'Пароли не совпадают'); ok = false; }

                if (!ok) return;

                // Отправка данных на сервер
                var formData = new FormData();
                formData.append('username', name);
                formData.append('email', email);
                formData.append('password', pass);
                formData.append('password2', pass2);
                formData.append('role', role);

                fetch('/reg', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.redirected) {
                        showToast('Регистрация успешна! Ожидайте подтверждения.', 'success');
                        setTimeout(function () {
                            window.location.href = response.url;
                        }, 2000);
                    } else {
                        return response.text().then(text => {
                            showToast('Ошибка при регистрации', 'error');
                        });
                    }
                })
                .catch(err => {
                    console.error('Reg error:', err);
                    showToast('Ошибка при регистрации', 'error');
                });
            });
        }
    }
    function setAuthError(fieldId, msg) {
        var group = $('#' + fieldId + 'Group');
        var err = $('#' + fieldId + 'Error');
        if (group) group.classList.add('error');
        if (err) { err.textContent = msg; err.classList.add('visible'); }
    }

    function clearAuthError(fieldId) {
        var group = $('#' + fieldId + 'Group');
        var err = $('#' + fieldId + 'Error');
        if (group) group.classList.remove('error');
        if (err) { err.textContent = ''; err.classList.remove('visible'); }
    }

    /* ====================================================
       LC PAGE  (lc.html)  — Личный кабинет
       ==================================================== */    function initLC() {
        var lcNav = $('#lcNav');
        if (!lcNav) return;

        // Пытаемся получить данные из сессии (через скрытые элементы или глобальную переменную)
        // Если их нет, используем localStorage как запасной вариант
        var user = getUser();

        // Если в localStorage пусто, попробуем инициализировать из данных, которые мог передать бэкенд
        if (!user && window.userData) {
            user = window.userData;
            setUser(user);
        }

        if (!user) {
            // Если пользователя нет нигде, редирект на вход
            window.location.href = '/auth';
            return;
        }

        // Заполнить сайдбар        var avatar = $('#lcAvatar');
        var nameEl = $('#lcName');
        var roleEl = $('#lcRole');
        var profileName = $('#profileName');
        var profileRole = $('#profileRole');
        var profileStatus = $('#profileStatus');

        var roleLabels = { admin: 'Администратор', smm: 'СММ', volunteer: 'Волонтёр' };

        if (avatar) avatar.textContent = (user.name || 'U').charAt(0).toUpperCase();
        if (nameEl) nameEl.textContent = user.name || user.username;
        if (roleEl) roleEl.textContent = roleLabels[user.role] || user.role;
        if (profileName) profileName.textContent = user.name || user.username;
        if (profileRole) profileRole.textContent = roleLabels[user.role] || user.role;
        if (profileStatus) {
            var statusLabels = { active: 'Активен', pending: 'Ожидает подтверждения' };
            profileStatus.textContent = statusLabels[user.status] || user.status;
        }

        // Показать элементы навигации по роли
        var roleClass = 'role-' + user.role;
        $$('.' + roleClass).forEach(function (el) {
            el.style.display = '';
        });

        // Навбар — имя пользователя
        var navName = $('#navUserName');
        if (navName) navName.textContent = user.name || user.username;

        // Переключение панелей
        $$('.lc-nav-item[data-panel]').forEach(function (item) {
            item.addEventListener('click', function () {
                var panelId = item.getAttribute('data-panel');
                // Активный пункт меню
                $$('.lc-nav-item').forEach(function (n) { n.classList.remove('active'); });
                item.classList.add('active');
                // Показать панель
                $$('.lc-panel').forEach(function (p) { p.classList.remove('active'); });
                var panel = $('#panel-' + panelId);
                if (panel) panel.classList.add('active');
            });
        });

        // Выход
        var logoutBtn = $('#lcLogout');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function () {
                clearUser();
                showToast('Вы вышли из системы', 'success');
                setTimeout(function () { window.location.href = '/home'; }, 600);
            });
        }
    }

    /* ====================================================
       HOME PAGE  (home.html)  — навбар + календарь + фид
       ==================================================== */
    function initHome() {
        // Навбар: кнопка пользователя
        var navBtn = $('#navUserBtn');
        var navName = $('#navUserName');
        if (!navBtn) return;

        var user = getUser();
        if (user) {
            if (navName) navName.textContent = user.name || user.username;
            navBtn.href = '/lc';
        } else {
            if (navName) navName.textContent = 'Войти';
            navBtn.href = '/auth';
        }

        navBtn.addEventListener('click', function (e) {
            if (navBtn.getAttribute('href')) {
                e.preventDefault();
                window.location.href = navBtn.getAttribute('href');
            }
        });

        // Календарь
        initCalendar();

        // Фид (демо-данные)
        initFeed();

        // Модальное окно комментариев
        initCommentModal();
    }

    /* ---------- CALENDAR ---------- */
    function initCalendar() {
        var grid = $('#calendarGrid');
        var title = $('#calendarTitle');
        var prevBtn = $('#calPrev');
        var nextBtn = $('#calNext');
        var eventsTitle = $('#eventsDateTitle');
        var eventsList = $('#eventsList');
        if (!grid || !title) return;

        var now = new Date();
        var currentMonth = now.getMonth();
        var currentYear = now.getFullYear();

        // Демо-события
        var events = {
            '2025-05-15': [{ title: 'Хакатон «Код будущего»', time: '10:00' }],
            '2025-06-27': [{ title: 'День молодёжи', time: '12:00' }],
            '2025-05-10': [{ title: 'Открытие сезона', time: '18:00' }]
        };

        function render() {
            var months = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
            title.textContent = months[currentMonth] + ' ' + currentYear;

            grid.innerHTML = '';
            var days = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
            days.forEach(function (d) {
                var h = document.createElement('div');
                h.className = 'calendar-day-header';
                h.textContent = d;
                grid.appendChild(h);
            });

            var first = new Date(currentYear, currentMonth, 1);
            var startDay = (first.getDay() + 6) % 7; // Пн=0
            var daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

            for (var i = 0; i < startDay; i++) {
                var empty = document.createElement('div');
                empty.className = 'calendar-day empty';
                grid.appendChild(empty);
            }

            for (var d = 1; d <= daysInMonth; d++) {
                var cell = document.createElement('div');
                cell.className = 'calendar-day';
                cell.textContent = d;

                var dateStr = currentYear + '-' + String(currentMonth + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0');

                if (d === now.getDate() && currentMonth === now.getMonth() && currentYear === now.getFullYear()) {
                    cell.classList.add('today');
                }
                if (events[dateStr]) {
                    cell.classList.add('has-event');
                }

                cell.setAttribute('data-date', dateStr);
                cell.addEventListener('click', function () {
                    $$('.calendar-day').forEach(function (c) { c.classList.remove('selected'); });
                    this.classList.add('selected');
                    var ds = this.getAttribute('data-date');
                    showEvents(ds);
                });

                grid.appendChild(cell);
            }
        }

        function showEvents(dateStr) {
            if (!eventsTitle || !eventsList) return;
            var parts = dateStr.split('-');
            eventsTitle.textContent = parseInt(parts[2]) + '.' + parts[1] + '.' + parts[0];
            var evts = events[dateStr];
            if (evts && evts.length) {
                eventsList.innerHTML = evts.map(function (ev) {
                    return '<div class="event-item"><span class="event-time">' + ev.time + '</span> ' + ev.title + '</div>';
                }).join('');
            } else {
                eventsList.innerHTML = '<div class="no-events">Нет мероприятий на эту дату</div>';
            }
        }

        if (prevBtn) prevBtn.addEventListener('click', function () {
            currentMonth--;
            if (currentMonth < 0) { currentMonth = 11; currentYear--; }
            render();
        });
        if (nextBtn) nextBtn.addEventListener('click', function () {
            currentMonth++;
            if (currentMonth > 11) { currentMonth = 0; currentYear++; }
            render();
        });

        render();
    }

    /* ---------- FEED ---------- */
    function initFeed() {
        var scroll = $('#feedScroll');
        if (!scroll) return;

        var posts = [
            { title: 'Открытие нового сезона', excerpt: 'Молодёжный центр начинает летний сезон с обновлённой программой.', date: '10 мая 2025', likes: 34, comments: 7 },
            { title: 'Итоги хакатона', excerpt: 'Команда «Медиахаб» заняла первое место на городском хакатоне.', date: '16 мая 2025', likes: 28, comments: 12 },
            { title: 'Набор волонтёров', excerpt: 'Приглашаем волонтёров для участия в летних мероприятиях.', date: '20 мая 2025', likes: 15, comments: 3 },
            { title: 'Фотоотчёт: День Победы', excerpt: 'Как прошёл праздничный концерт в молодёжном центре.', date: '9 мая 2025', likes: 52, comments: 8 },
            { title: 'Мастер-класс по дизайну', excerpt: 'Бесплатный мастер-класс от профессионального дизайнера.', date: '5 мая 2025', likes: 19, comments: 4 }
        ];

        scroll.innerHTML = posts.map(function (p) {
            return '<div class="feed-card">' +
                '<div class="feed-card-header"><span class="feed-date">' + p.date + '</span></div>' +
                '<h3 class="feed-card-title">' + p.title + '</h3>' +
                '<p class="feed-card-text">' + p.excerpt + '</p>' +
                '<div class="feed-card-actions">' +
                    '<button class="feed-action-btn like-btn"><i class="bx bx-heart"></i> ' + p.likes + '</button>' +
                    '<button class="feed-action-btn comment-btn"><i class="bx bx-comment"></i> ' + p.comments + '</button>' +
                '</div>' +
            '</div>';
        }).join('');

        // Лайки
        $$('.like-btn', scroll).forEach(function (btn) {
            btn.addEventListener('click', function () {
                btn.classList.toggle('liked');
                var icon = btn.querySelector('i');
                if (btn.classList.contains('liked')) {
                    icon.className = 'bx bxs-heart';
                } else {
                    icon.className = 'bx bx-heart';
                }
            });
        });

        // Комментарии — открыть модалку
        $$('.comment-btn', scroll).forEach(function (btn) {
            btn.addEventListener('click', function () {
                var modal = $('#commentModal');
                if (modal) modal.classList.add('active');
            });
        });
    }

    /* ---------- COMMENT MODAL ---------- */
    function initCommentModal() {
        var modal = $('#commentModal');
        if (!modal) return;

        var cancelBtn = $('#commentCancel');
        var sendBtn = $('#commentSend');
        var textarea = $('#commentText');

        if (cancelBtn) cancelBtn.addEventListener('click', function () {
            modal.classList.remove('active');
            if (textarea) textarea.value = '';
        });

        if (sendBtn) sendBtn.addEventListener('click', function () {
            if (textarea && textarea.value.trim()) {
                showToast('Комментарий отправлен!', 'success');
            } else {
                showToast('Напишите комментарий', 'error');
                return;
            }
            modal.classList.remove('active');
            if (textarea) textarea.value = '';
        });

        // Закрытие по клику на оверлей
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                modal.classList.remove('active');
                if (textarea) textarea.value = '';
            }
        });
    }

    /* ====================================================
       INIT — определяем страницу и запускаем нужный модуль
       ==================================================== */
    var path = window.location.pathname;

    if (path.indexOf('/auth') !== -1) {
        initAuth();
    } else if (path.indexOf('/lc') !== -1) {
        initLC();
    } else {
        // home или корень
        initHome();
    }
    /*=============
     Из home.html 
     ==============*/
    let currentYear = new Date().getFullYear();
    let currentMonth = new Date().getMonth();   // 0-11
    
    let currentSelectedElement = null;   // DOM выбранной ячейки
    let lastSelectedDateStr = '';         // для панели
    let lastSelectedCircleVal = '';       // последнее значение круга выбранной даты
    
    const monthYearDisplay = document.getElementById('monthYearDisplay');
    const calendarContainer = document.getElementById('calendarDatesContainer');
    const eventsListContainer = document.getElementById('eventsListContainer');
    const prevBtn = document.getElementById('prevMonthBtn');
    const nextBtn = document.getElementById('nextMonthBtn');
    
    // ------------------ вспомогательные функции ------------------
    async function fetchEventsForDate(year, month, day) {
        try {
            // Имитация запроса к БД
            // const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            // const response = await fetch(`/api/events?date=${dateStr}`);
            // return await response.json();

            // Заглушка для демонстрации
            if (day % 3 === 0) {
                return [
                    { name: "Хакатон 2025", time: "10:00" },
                    { name: "Лекция по AI", time: "14:30" }
                ];
            }
            return [];
        } catch (e) {
            console.error("Ошибка при загрузке событий:", e);
            return [];
        }
    }

    function renderEvents(events) {
        if (!eventsListContainer) return;
        
        if (events.length === 0) {
            eventsListContainer.innerHTML = '<div class="no-events">На этот день событий не запланировано</div>';
            return;
        }

        eventsListContainer.innerHTML = events.map(event => `
            <div class="event-item">
                <div class="event-name">${event.name}</div>
                <div class="event-time">${event.time}</div>
            </div>
        `).join('');
    }
    
    function getMonthName(monthIndex) {        const months = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ];
        return months[monthIndex];
    }
    
    // Генерация цифры для круга в центре (имитация количества событий / заметок)
    // Условие: в центре должна быть возможность отобразить ЛЮБУЮ цифру. 
    // Здесь возвращаем число от 1 до 3 (но бывают и 0,4 редко — для наглядности)
    // Используем детерминированную формулу, чтобы при перерисовке месяца значения не менялись хаотично.
    // Показывает "цифру", которую можно интерпретировать как активность.

    async function hasEvents(day, month, year) {
        try {
            // Форматируем дату для запроса (YYYY-MM-DD)
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            
            // Пример запроса к вашему API
            // const response = await fetch(`/api/events/count?date=${dateStr}`);
            // const data = await response.json();
            // return data.count > 0;

            // Имитация ответа сервера для демонстрации:
            return (day % 3 === 0); // Круг будет у каждого третьего числа
        } catch (e) {
            console.error("Ошибка при проверке событий:", e);
            return false;
    }
}
    
    
    // Визуальное выделение ячейки
    async function setSelectedDateElement(cellElement, year, month, day, circleVal) {
        // снимаем выделение с предыдущей
        if (currentSelectedElement) {
            currentSelectedElement.classList.remove('selected');
        }
        if (cellElement) {
            cellElement.classList.add('selected');
            currentSelectedElement = cellElement;
            
            const formattedDay = String(day).padStart(2, '0');
            const monthName = getMonthName(month);
            const dateStr = `${formattedDay} ${monthName} ${year}`;

            // Загружаем и отрисовываем события
            const events = await fetchEventsForDate(year, month, day);
            renderEvents(events);

        } else {
            if (currentSelectedElement) {
                currentSelectedElement.classList.remove('selected');
                currentSelectedElement = null;
            }
            lastSelectedDateStr = '';
            lastSelectedCircleVal = '';
        }
    }    
    function clearSelection() {
        if (currentSelectedElement) {
            currentSelectedElement.classList.remove('selected');
            currentSelectedElement = null;
        }
        lastSelectedDateStr = '';
        lastSelectedCircleVal = '';

    }
    
    // проверка, сегодняшняя ли дата
    function isTodayDate(year, month, day) {
        const today = new Date();
        return (year === today.getFullYear() && month === today.getMonth() && day === today.getDate());
    }
    
    // ---- ГЛАВНАЯ ОТРИСОВКА КАЛЕНДАРЯ (сетка, угловой номер + круг в центре) ----
    async function renderCalendar() {
    if (!calendarContainer) return;
    
    const year = currentYear;
    const month = currentMonth;
    monthYearDisplay.textContent = `${getMonthName(month)} ${year}`;
    
    const firstDayOfMonth = new Date(year, month, 1);
    let offset = (firstDayOfMonth.getDay() === 0) ? 6 : firstDayOfMonth.getDay() - 1;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    calendarContainer.innerHTML = '';

    // Пустые ячейки
    for (let i = 0; i < offset; i++) {
        const cell = document.createElement('div');
        cell.className = 'date-cell empty';
        calendarContainer.appendChild(cell);
    }

    // Ячейки с датами
    for (let d = 1; d <= daysInMonth; d++) {
        const cellDiv = document.createElement('div');
        cellDiv.className = 'date-cell has-date';
        
        // Устанавливаем атрибуты, чтобы onDateClick мог их прочитать
        cellDiv.setAttribute('data-year', year);
        cellDiv.setAttribute('data-month', month);
        cellDiv.setAttribute('data-day', d);
        cellDiv.setAttribute('data-empty', 'false');

        if (isTodayDate(year, month, d)) cellDiv.classList.add('today');

        // Проверяем наличие событий в БД
        const showCircle = await hasEvents(d, month, year);
        if (showCircle) {
            const circle = document.createElement('div');
            circle.className = 'day-circle';
            
            // Получаем количество событий для отображения в круге
            const events = await fetchEventsForDate(year, month, d);
            circle.textContent = events.length;
            
            cellDiv.appendChild(circle);
            cellDiv.setAttribute('data-circle', events.length); 
        } else {
            cellDiv.setAttribute('data-circle', '0');
        }        const cornerNumber = document.createElement('div');
        cornerNumber.className = 'day-corner-number';
        cornerNumber.textContent = d;
        
        cellDiv.appendChild(cornerNumber);
        calendarContainer.appendChild(cellDiv);
    }
}
    
    // ---------- Обработка кликов по датам (делегирование через контейнер) ----------
    function onDateClick(event) {
        let targetCell = event.target.closest('.date-cell');
        if (!targetCell) return;
        
        // пустые ячейки не реагируют
        if (targetCell.classList.contains('empty') || targetCell.getAttribute('data-empty') === 'true') {
            return;
        }
        
        const yearAttr = targetCell.getAttribute('data-year');
        const monthAttr = targetCell.getAttribute('data-month');
        const dayAttr = targetCell.getAttribute('data-day');
        const circleAttr = targetCell.getAttribute('data-circle');
        
        if (!yearAttr || !monthAttr || !dayAttr) return;
        
        const year = parseInt(yearAttr, 10);
        const month = parseInt(monthAttr, 10);
        const day = parseInt(dayAttr, 10);
        let circleVal = circleAttr ? parseInt(circleAttr, 10) : null;
        if (isNaN(circleVal)) circleVal = 0;
        
        if (isNaN(year) || isNaN(month) || isNaN(day)) return;
        
        // визуально выделяем дату и обновляем панель
        setSelectedDateElement(targetCell, year, month, day, circleVal);
        
        // Доп. фидбек: можно вывести в консоль, но главное — всё наглядно
        console.log(`✅ Выбрано: ${day}.${month+1}.${year} | Круг: ${circleVal}`);
    }
    

    
    // ---------- Навигация по месяцам ----------
    function goPrevMonth() {
        let newMonth = currentMonth - 1;
        let newYear = currentYear;
        if (newMonth < 0) {
            newMonth = 11;
            newYear--;
        }
        currentYear = newYear;
        currentMonth = newMonth;
        clearSelection();         // сброс выделения при смене месяца
        renderCalendar();
    }
    
    function goNextMonth() {
        let newMonth = currentMonth + 1;
        let newYear = currentYear;
        if (newMonth > 11) {
            newMonth = 0;
            newYear++;
        }
        currentYear = newYear;
        currentMonth = newMonth;
        clearSelection();
        renderCalendar();
    }
    
    // ---------- Инициализация и установка обработчиков ----------
    function initCalendar() {
        const now = new Date();
        currentYear = now.getFullYear();
        currentMonth = now.getMonth();
        renderCalendar();
        
        if (calendarContainer) {
            calendarContainer.addEventListener('click', onDateClick);
        }
        if (prevBtn) prevBtn.addEventListener('click', goPrevMonth);
        if (nextBtn) nextBtn.addEventListener('click', goNextMonth);
    }
    
    initCalendar();

    // ---------- Управление лентой новостей ----------
    const newsTrack = document.getElementById('newsTrack');
    const newsPrevBtn = document.getElementById('newsPrevBtn');
    const newsNextBtn = document.getElementById('newsNextBtn');
    let currentNewsIndex = 0;
    const newsCards = document.querySelectorAll('.news-card');
    const newsCount = newsCards.length;
    const newsVisible = 2;

    function updateNewsCarousel() {
    if (!newsTrack) return;
    const newsCards = newsTrack.querySelectorAll('.news-card');
    if (newsCards.length === 0) return;

    const cardWidth = newsCards[0].offsetWidth;
    const gap = 20; // Соответствует gap в CSS
        
    const offset = currentNewsIndex * (cardWidth + gap);
    newsTrack.style.transform = `translateX(-${offset}px)`;
        
    const containerWidth = newsTrack.parentElement.offsetWidth;
    const trackWidth = newsTrack.scrollWidth;

    if (newsPrevBtn) newsPrevBtn.classList.toggle('hidden', currentNewsIndex === 0);
    if (newsNextBtn) {
        const remainingWidth = trackWidth - offset;
        newsNextBtn.classList.toggle('hidden', remainingWidth <= containerWidth + 5);
    }
}

    function nextNews() {
        if (currentNewsIndex < newsCount - newsVisible) {
            currentNewsIndex += newsVisible;
            if (currentNewsIndex > newsCount - newsVisible) {
                currentNewsIndex = newsCount - newsVisible;
            }
        } else {
            currentNewsIndex = 0; // Зацикливание для автопрокрутки
        }
        updateNewsCarousel();
    }

    function prevNews() {
        if (currentNewsIndex > 0) {
            currentNewsIndex -= newsVisible;
            if (currentNewsIndex < 0) currentNewsIndex = 0;
            updateNewsCarousel();
        }
    }

    if (newsNextBtn) {
        newsNextBtn.addEventListener('click', () => {
            nextNews();
            resetAutoScroll();
        });
    }
    
    if (newsPrevBtn) {
        newsPrevBtn.addEventListener('click', () => {
            prevNews();
            resetAutoScroll();
        });
    }

    let autoScrollInterval = setInterval(nextNews, 7000);

    function resetAutoScroll() {
        clearInterval(autoScrollInterval);
        autoScrollInterval = setInterval(nextNews, 7000);
    }

    updateNewsCarousel();
})();