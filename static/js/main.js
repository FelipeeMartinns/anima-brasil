document.addEventListener('DOMContentLoaded', function () {
    const btnMenu = document.getElementById('btn-menu-mobile');
    const menuMobile = document.getElementById('menu-mobile');
    if (btnMenu && menuMobile) {
        btnMenu.addEventListener('click', function () {
            const oculto = menuMobile.classList.toggle('hidden');
            btnMenu.setAttribute('aria-expanded', oculto ? 'false' : 'true');
        });
    }

    document.querySelectorAll('[data-curtir]').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            fetch(btn.dataset.curtir, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            }).then(function (r) {
                return r.json().then(function (data) {
                    return { ok: r.ok, data: data };
                });
            }).then(function (res) {
                if (!res.ok || res.data.erro) {
                    alert(res.data.erro || 'Não foi possível curtir.');
                    return;
                }
                const data = res.data;
                const total = btn.querySelector('.curtidas-total');
                const icone = btn.querySelector('.icone-coracao');
                if (data.curtiu) {
                    btn.classList.add('text-pink-600');
                    btn.classList.remove('text-slate-400');
                    if (icone) { icone.textContent = '\u2665'; }
                } else {
                    btn.classList.remove('text-pink-600');
                    btn.classList.add('text-slate-400');
                    if (icone) { icone.textContent = '\u2661'; }
                }
                if (total) { total.textContent = data.total; }
            }).catch(function () { window.location.reload(); });
        });
    });

    document.querySelectorAll('[data-favoritar]').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            fetch(btn.dataset.favoritar, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            }).then(function (r) {
                return r.json().then(function (data) {
                    return { ok: r.ok, data: data };
                });
            }).then(function (res) {
                if (!res.ok || res.data.erro) {
                    alert(res.data.erro || 'Não foi possível favoritar.');
                    return;
                }
                const data = res.data;
                const total = btn.querySelector('.favoritos-total');
                if (data.favoritou) {
                    btn.classList.add('text-yellow-500');
                    btn.classList.remove('text-slate-400');
                } else {
                    btn.classList.remove('text-yellow-500');
                    btn.classList.add('text-slate-400');
                }
                if (total) { total.textContent = data.total; }
            }).catch(function () { window.location.reload(); });
        });
    });
});

function getCookie(name) {
    const value = '; ' + document.cookie;
    const parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}