/* Vanilla JavaScript. No analytics, tracking, remote font or Adobe dependency. */
(() => {
  'use strict';
  document.documentElement.classList.remove('no-js');
  const cfg = window.PORTFOLIO_CONFIG || {};
  // Email shown in the welcome icon and disconnected-form guidance comes from config.js.
  // Future address changes require editing this one public file, not rebuilding pages.
  const emailConfig = String(cfg.email || '').trim();
  const publicEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailConfig) ? emailConfig : 'arina.samysheva@mail.ru';
  const emailLinks = [...document.querySelectorAll('a[data-contact-email]')];
  emailLinks.forEach(link => { link.href = 'mailto:' + publicEmail; });
  // A mailto: link alone can look broken when the visitor has no default mail app.
  // Keep the native mailto href as a no-JavaScript fallback, but provide an
  // explicit choice (mail app or copy) for ordinary clicks.
  if (emailLinks.length && typeof HTMLDialogElement !== 'undefined') {
    const dialog = document.createElement('dialog');
    dialog.id = 'email-contact-dialog';
    dialog.className = 'email-contact-dialog';
    dialog.setAttribute('aria-labelledby', 'email-contact-dialog-title');
    dialog.setAttribute('aria-describedby', 'email-contact-dialog-help');
    dialog.innerHTML = `
      <button class=\"email-dialog-close\" type=\"button\" data-email-close aria-label=\"Закрыть окно\">&times;</button>
      <h2 id=\"email-contact-dialog-title\">Написать на почту</h2>
      <p id=\"email-contact-dialog-help\">Откройте почтовое приложение или скопируйте адрес, чтобы написать с любого почтового сервиса.</p>
      <input class=\"email-dialog-address\" type=\"text\" readonly aria-label=\"Адрес электронной почты\" data-email-address>
      <div class=\"email-dialog-actions\">
        <button class=\"email-dialog-copy\" type=\"button\" data-email-copy>Скопировать адрес</button>
        <a class=\"email-dialog-mailto\" data-email-mailto>Открыть почтовое приложение</a>
      </div>
      <p class=\"email-dialog-feedback\" role=\"status\" aria-live=\"polite\" aria-atomic=\"true\" data-email-feedback hidden></p>`;
    const addressField = dialog.querySelector('[data-email-address]');
    const mailtoLink = dialog.querySelector('[data-email-mailto]');
    const copyButton = dialog.querySelector('[data-email-copy]');
    const feedback = dialog.querySelector('[data-email-feedback]');
    const closeButton = dialog.querySelector('[data-email-close]');
    addressField.value = publicEmail;
    mailtoLink.href = 'mailto:' + publicEmail;
    document.body.appendChild(dialog);
    let lastTrigger = null;
    emailLinks.forEach(link => {
      link.setAttribute('aria-haspopup', 'dialog');
      link.setAttribute('aria-controls', dialog.id);
      link.title = 'Контактная почта: ' + publicEmail;
      link.addEventListener('click', event => {
        // Preserve native actions for modified clicks and non-primary buttons.
        if (event.defaultPrevented || event.button !== 0 || event.ctrlKey ||
            event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        lastTrigger = link;
        feedback.hidden = true;
        feedback.textContent = '';
        dialog.showModal();
        copyButton.focus();
      });
    });
    copyButton.addEventListener('click', async () => {
      let copied = false;
      if (navigator.clipboard && window.isSecureContext) {
        try {
          await navigator.clipboard.writeText(publicEmail);
          copied = true;
        } catch (_) { /* Fall back to selecting the visible address. */ }
      }
      if (!copied) {
        addressField.focus();
        addressField.select();
        try { copied = document.execCommand('copy'); } catch (_) { copied = false; }
      }
      feedback.textContent = copied
        ? 'Адрес скопирован. Вставьте его в вашу почту.'
        : 'Не удалось скопировать автоматически. Выделите адрес выше и скопируйте вручную.';
      feedback.hidden = false;
    });
    closeButton.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener('close', () => {
      if (lastTrigger) lastTrigger.focus({preventScroll: true});
    });
  }
  const menuButton = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.site-nav');
  const siteHeader = document.querySelector('.site-header');
  if (menu && menuButton && siteHeader) {
    const desktop = window.matchMedia('(min-width: 681px)');
    const setMenuOpen = opened => {
      opened = Boolean(opened) && !desktop.matches;
      menu.classList.toggle('is-open', opened);
      menuButton.setAttribute('aria-expanded', String(opened));
      menuButton.setAttribute('aria-label', opened ? 'Закрыть меню' : 'Открыть меню');
    };
    const closeMenu = () => setMenuOpen(false);
    closeMenu();
    menuButton.addEventListener('click', () => {
      setMenuOpen(menuButton.getAttribute('aria-expanded') !== 'true');
    });
    menu.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
        closeMenu();
        menuButton.focus({preventScroll: true});
      }
    });
    document.addEventListener('click', event => {
      if (event.target instanceof Node && !siteHeader.contains(event.target)) closeMenu();
    });
    siteHeader.addEventListener('focusout', event => {
      if (event.relatedTarget instanceof Node && !siteHeader.contains(event.relatedTarget)) closeMenu();
    });
    // Safari/VK webviews may restore the page from back-forward cache with an open menu.
    window.addEventListener('pageshow', closeMenu);
    window.addEventListener('pagehide', closeMenu);
    if (typeof desktop.addEventListener === 'function') desktop.addEventListener('change', closeMenu);
    else if (typeof desktop.addListener === 'function') desktop.addListener(closeMenu);
  }
  const top = document.querySelector('.to-top');
  if (top) {
    const update = () => top.classList.toggle('is-visible', window.scrollY > 320);
    update(); addEventListener('scroll', update, {passive:true});
  }
  // Local image viewer. Without JS, the same link opens the original file.
  const viewer = document.getElementById('image-viewer');
  if (viewer && typeof viewer.showModal === 'function') {
    const image = viewer.querySelector('img');
    const stage = viewer.querySelector('.viewer-stage');
    const caption = viewer.querySelector('.viewer-caption');
    const zoom = viewer.querySelector('[data-zoom]');
    let previousFocus = null;
    document.querySelectorAll('.slide-link').forEach(link => link.addEventListener('click', e => {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
      e.preventDefault(); previousFocus = link;
      image.src = link.href; image.alt = link.querySelector('img').alt;
      caption.textContent = link.dataset.caption || 'Слайд проекта';
      viewer.querySelector('[data-original]').href = link.href;
      stage.classList.remove('is-zoomed'); zoom.textContent = 'Масштаб 100%';
      viewer.showModal(); document.body.style.overflow = 'hidden'; stage.scrollTo(0,0);
    }));
    viewer.querySelector('[data-close]').addEventListener('click', () => viewer.close());
    viewer.addEventListener('close', () => { document.body.style.overflow = ''; image.removeAttribute('src'); if (previousFocus) previousFocus.focus({preventScroll:true}); });
    zoom.addEventListener('click', () => { const large = stage.classList.toggle('is-zoomed'); zoom.textContent = large ? 'По ширине' : 'Масштаб 100%'; stage.scrollTo(0,0); });
  }
  const form = document.getElementById('contact-form');
  if (!form) return;
  const status = document.getElementById('form-status');
  const submit = form.querySelector('[type=submit]');
  const fields = ['name','email','message'];
  const id = String(cfg.formspreeId || '').trim();
  const validId = /^[a-z0-9]{6,32}$/i.test(id) && !/your|replace|example|test/i.test(id);
  const endpoint = validId ? `https://formspree.io/f/${id}` : null;
  let pending = false;
  let lastSent = 0;
  const setStatus = (text, type) => {
    status.className = `form-status ${type}`; status.textContent = text; status.hidden = false;
    status.setAttribute('role', type === 'error' ? 'alert' : 'status');
  };
  const validate = () => {
    let first = null;
    const messages = {name:'Укажите, как к вам обращаться.', email:'Укажите действительный адрес электронной почты.', message:'Напишите ваше сообщение.'};
    fields.forEach(key => {
      const field = form.elements[key]; const error = document.getElementById(`${key}-error`);
      let ok = field.value.trim().length > 0 && field.validity.valid;
      if (key === 'email') ok = ok && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value.trim());
      field.setAttribute('aria-invalid', String(!ok)); error.hidden = ok;
      error.textContent = ok ? '' : messages[key]; if (!ok && !first) first = field;
    });
    if (first) first.focus(); return !first;
  };
  fields.forEach(key => form.elements[key].addEventListener('input', () => {
    form.elements[key].removeAttribute('aria-invalid'); document.getElementById(`${key}-error`).hidden = true;
  }));
  submit.disabled = false;
  if (endpoint) form.setAttribute('action', endpoint);
  form.addEventListener('submit', async e => {
    e.preventDefault(); if (pending) return;
    status.hidden = true;
    if (!validate()) return;
    if (!endpoint) {
      setStatus(`Отправка через форму ещё не подключена. Пожалуйста, напишите в Telegram или на ${publicEmail}.`, 'error');
      return;
    }
    if (Date.now() - lastSent < 30000) { setStatus('Сообщение уже отправлено. Подождите немного перед повторной отправкой.', 'error'); return; }
    pending = true; submit.disabled = true; submit.textContent = 'Отправка…'; form.setAttribute('aria-busy','true');
    const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 20000);
    try {
      const data = new FormData(form);
      fields.forEach(key => data.set(key, form.elements[key].value.trim()));
      data.set('_subject', 'Сообщение с портфолио Арины Самышевой');
      const response = await fetch(endpoint, { method:'POST', body:data, headers:{Accept:'application/json'}, signal:controller.signal });
      const result = await response.json().catch(() => null);
      if (response.status === 429) throw new Error('Сервис временно ограничил отправку. Попробуйте позже или напишите в Telegram.');
      if (!response.ok || !result || result.ok !== true) throw new Error('Не удалось подтвердить отправку. Ваш текст сохранён. Попробуйте ещё раз или напишите в Telegram.');
      lastSent = Date.now(); form.reset();
      setStatus('Спасибо за сообщение! Ваше сообщение успешно отправлено. Я отвечу вам на указанную электронную почту.', 'success');
    } catch (error) {
      const text = error.name === 'AbortError'
        ? 'Сервис не ответил вовремя. Отправка не подтверждена; ваш текст сохранён. Попробуйте позже или напишите в Telegram.'
        : (error instanceof TypeError ? 'Нет связи с сервисом отправки. Проверьте интернет или напишите в Telegram. Ваш текст сохранён.' : error.message);
      setStatus(text, 'error');
    } finally {
      clearTimeout(timer); pending = false; submit.disabled = false; submit.textContent = 'Отправить'; form.removeAttribute('aria-busy');
    }
  });
})();
