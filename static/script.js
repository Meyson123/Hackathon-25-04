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
        var roleStep = $('#roleStep');
        var loginStep = $('#loginStep');
        if (!roleStep || !loginStep) return;

        var goToLogin = $('#goToLogin');
        var goToRole = $('#goToRole');

        // Если пришли по ссылке /auth#login — сразу показать логин
        if (window.location.hash === '#login') {
            roleStep.style.display = 'none';
            loginStep.style.display = '';
        }

        // Переключение: «Войти»
        if (goToLogin) {
            goToLogin.addEventListener('click', function (e) {
                e.preventDefault();
                roleStep.style.display = 'none';
                loginStep.style.display = '';
            });
        }

        // Переключение: «Зарегистрироваться» (из логина → выбор роли)
        if (goToRole) {
            goToRole.addEventListener('click', function (e) {
                e.preventDefault();
                loginStep.style.display = 'none';
                roleStep.style.display = '';
            });
        }

        // Клик по карточке роли → переход на reg.html?role=...
        $$('.role-card').forEach(function (card) {
            card.addEventListener('click', function () {
                $$('.role-card').forEach(function (c) { c.classList.remove('selected'); });
                card.classList.add('selected');
                var role = card.getAttribute('data-role');
                setTimeout(function () {
                    window.location.href = '/reg?role=' + encodeURIComponent(role);
                }, 300);
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

                var demoUsers = {                    'admin': { name: 'Администратор', role: 'admin', status: 'active' },
                    'smm':   { name: 'СММ-менеджер',  role: 'smm',   status: 'active' },
                    'vol':   { name: 'Волонтёр',      role: 'volunteer', status: 'active' }
                };

                var found = demoUsers[username];
                if (found && password === '123') {
                    setUser({ username: username, name: found.name, role: found.role, status: found.status });
                    showToast('Добро пожаловать, ' + found.name + '!', 'success');
                    setTimeout(function () { window.location.href = '/lc'; }, 800);
                } else {
                    showToast('Неверное имя пользователя или пароль', 'error');
                }
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
       REG PAGE  (reg.html)
       ==================================================== */
    function initReg() {
        var regForm = $('#regForm');
        if (!regForm) return;

        var roleLabels = { smm: 'СММ', volunteer: 'Волонтёр' };
        var role = getParam('role') || '';
        var roleInput = $('#regRole');
        var roleLabel = $('#regRoleLabel');

        if (roleInput) roleInput.value = role;
        if (roleLabel) roleLabel.textContent = roleLabels[role] || 'Не выбрана';

        // Регистрация
        regForm.addEventListener('submit', function (e) {            e.preventDefault();
            var ok = true;

            var name = $('#regName').value.trim();
            var email = $('#regEmail').value.trim();
            var pass = $('#regPassword').value;
            var pass2 = $('#regPassword2').value;

            // Очистка ошибок
            ['regName', 'regEmail', 'regPassword', 'regPassword2'].forEach(clearAuthError);

            if (!name) { setAuthError('regName', 'Введите имя пользователя'); ok = false; }
            if (!email) { setAuthError('regEmail', 'Введите email'); ok = false; }
            else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setAuthError('regEmail', 'Некорректный email'); ok = false; }
            if (!pass) { setAuthError('regPassword', 'Введите пароль'); ok = false; }
            else if (pass.length < 6) { setAuthError('regPassword', 'Минимум 6 символов'); ok = false; }
            if (pass !== pass2) { setAuthError('regPassword2', 'Пароли не совпадают'); ok = false; }

            if (!ok) return;

            // Имитация регистрации (фронт-заглушка)
            showToast('Заявка отправлена! Ожидайте подтверждения администратором.', 'success');
            regForm.reset();
            setTimeout(function () { window.location.href = '/auth#login'; }, 2000);
        });
    }

    /* ====================================================
       LC PAGE  (lc.html)  — Личный кабинет
       ==================================================== */
    function initLC() {
        var lcNav = $('#lcNav');
        if (!lcNav) return;

        var user = getUser();

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
    } else if (path.indexOf('/reg') !== -1) {
        initReg();
    } else if (path.indexOf('/lc') !== -1) {
        initLC();
    } else {
        // home или корень
        initHome();
    }

})();