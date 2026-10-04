(() => {
  const cfg = window.APP_CONFIG || {};
  const tg = window.Telegram?.WebApp;
  const DEMO = cfg.demoMode === true;

  const SUBJECT_META = { ADS: "алгоритмы", PP1: "основы", PP2: "продвинутый" };

  const STATUS = {
    awaiting_payment: "Ожидает оплату",
    awaiting_review: "Чек на проверке",
    paid: "Оплачен",
    in_progress: "В работе",
    completed: "Готово",
    rejected: "Отклонён",
  };

  const STEP_ORDER = ["awaiting_payment", "awaiting_review", "in_progress", "completed"];

  const state = {
    user: null,
    subjects: [],
    catalog: [],
    creds: {}, // subject -> { login, has_password }
    subject: "ADS",
    cart: new Map(), // labId -> language
    orders: [],
  };

  const $ = (sel) => document.querySelector(sel);
  const fmt = (n) => `${n.toLocaleString("ru-RU")} ₸`;
  const pad = (n) => String(n).padStart(2, "0");
  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  // ---------------- API ----------------

  async function api(path, options = {}) {
    const base = cfg.apiBase.replace(/\/$/, "");
    const res = await fetch(`${base}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": tg?.initData || "",
        ...(base.includes("loca.lt") ? { "Bypass-Tunnel-Reminder": "1" } : {}),
        ...(options.headers || {}),
      },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  // Демо-хранилище: заказы и логины на этом устройстве. Пароли в демо не сохраняются.
  const store = {
    get(key, fallback) {
      try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
    },
    set(key, value) { localStorage.setItem(key, JSON.stringify(value)); },
  };

  const backend = {
    async auth() {
      if (!DEMO) return api("/miniapp/auth", { method: "POST" });
      const u = tg?.initDataUnsafe?.user;
      return u
        ? { telegram_id: u.id, first_name: u.first_name, username: u.username, photo_url: u.photo_url }
        : { telegram_id: 0, first_name: "Demo", username: "demo_student" };
    },
    async catalog() {
      return DEMO ? window.DEMO_CATALOG : api("/miniapp/catalog");
    },
    async settings() {
      const local = {
        bot_username: cfg.botUsername || "",
        check_bot_username: cfg.checkBotUsername || "PAWS_CHECK_bot",
        payment_requisites: cfg.paymentRequisites || "",
        payment_recipient: cfg.paymentRecipient || "",
        payment_instructions: cfg.paymentInstructions || "",
      };
      if (DEMO) return local;
      const remote = await api("/miniapp/settings").catch(() => ({}));
      // Пустые значения с сервера не затирают config.js.
      for (const [k, v] of Object.entries(remote)) if (v) local[k] = v;
      return local;
    },
    async credentials() {
      if (!DEMO) return api("/miniapp/credentials");
      const saved = store.get("demo_creds", {});
      return window.DEMO_SUBJECTS.map((s) => ({ ...s, login: saved[s.subject] || null, has_password: !!saved[s.subject] }));
    },
    async saveCredential(subject, login, password) {
      if (!DEMO) {
        return api(`/miniapp/credentials/${subject}`, { method: "PUT", body: JSON.stringify({ login, password }) });
      }
      const saved = store.get("demo_creds", {});
      saved[subject] = login;
      store.set("demo_creds", saved);
      const s = window.DEMO_SUBJECTS.find((x) => x.subject === subject);
      return { ...s, login, has_password: true };
    },
    async orders() {
      return DEMO ? store.get("demo_orders", []) : api("/miniapp/orders");
    },
    async createOrder(items) {
      if (!DEMO) return api("/miniapp/orders", { method: "POST", body: JSON.stringify({ items }) });
      const orders = store.get("demo_orders", []);
      const lines = items.map(({ lab_id, language }) => {
        const lab = state.catalog.find((l) => l.id === lab_id);
        return { lab_id, subject: lab.subject, lab_number: lab.lab_number, language, price: lab.price };
      });
      const order = {
        id: 1001 + orders.length,
        status: "awaiting_payment",
        total_price: lines.reduce((s, l) => s + l.price, 0),
        items: lines,
        created_at: new Date().toISOString(),
      };
      store.set("demo_orders", [order, ...orders]);
      return order;
    },
  };

  // ---------------- UI helpers ----------------

  function haptic(type = "light") {
    tg?.HapticFeedback?.impactOccurred?.(type);
  }

  let toastTimer;
  function toast(text) {
    const el = $("#toast");
    el.textContent = text;
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (el.hidden = true), 3000);
  }

  function openSheet(html) {
    $("#sheetBody").innerHTML = html;
    $("#sheet").hidden = false;
  }

  function closeSheet() {
    $("#sheet").hidden = true;
  }

  function switchView(view) {
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("is-active", t.dataset.view === view));
    $("#view-catalog").hidden = view !== "catalog";
    $("#view-orders").hidden = view !== "orders";
    renderCartbar();
  }

  const hasAccess = (subject) => !!state.creds[subject]?.has_password;

  // ---------------- render ----------------

  function renderUser() {
    const u = state.user;
    if (!u) return;
    const name = u.username ? `@${u.username}` : u.first_name || "user";
    $("#userName").textContent = name;
    const avatar = $("#userAvatar");
    if (u.photo_url) avatar.innerHTML = `<img src="${esc(u.photo_url)}" alt="" />`;
    else avatar.textContent = (u.first_name || name).replace("@", "").charAt(0).toUpperCase();
  }

  function renderSubjects() {
    $("#subjects").innerHTML = state.subjects.map((s) => {
      const count = state.catalog.filter((l) => l.subject === s.subject).length;
      return `
        <button class="subject ${s.subject === state.subject ? "is-active" : ""}" data-subject="${s.subject}">
          <span class="subject__code">${s.subject}${hasAccess(s.subject) ? '<i class="subject__key">●</i>' : ""}</span>
          <span class="subject__meta">${count} лаб · ${SUBJECT_META[s.subject] || ""}</span>
        </button>`;
    }).join("");
  }

  function renderAccess() {
    const s = state.subjects.find((x) => x.subject === state.subject);
    if (!s) return;
    const cred = state.creds[s.subject];
    const ok = hasAccess(s.subject);
    $("#access").innerHTML = `
      <div class="access ${ok ? "is-ok" : ""}">
        <div class="access__row">
          <div>
            <div class="access__label">ДОСТУП · ${esc(s.platform.toUpperCase())} · ${esc(s.subject)}</div>
            <div class="access__hint">логин и пароль от ejudge</div>
          </div>
          <button class="btn btn--ghost btn--sm" data-access="${s.subject}">${ok ? "ИЗМЕНИТЬ" : "УКАЗАТЬ"}</button>
        </div>
        <div class="access__status">
          ${ok ? `логин <b>${esc(cred.login)}</b> · пароль сохранён` : "логин и пароль не указаны — нужны для выполнения лабы"}
        </div>
      </div>`;
  }

  function renderLabs() {
    const labs = state.catalog.filter((l) => l.subject === state.subject);
    if (!labs.length) {
      $("#labs").innerHTML = `<div class="empty"><span class="empty__art">[ ]</span>Лабораторные скоро появятся</div>`;
      return;
    }
    $("#labs").innerHTML = labs.map((lab) => {
      const selected = state.cart.has(lab.id);
      const chosen = state.cart.get(lab.id) || lab.languages[0];
      return `
        <article class="lab ${selected ? "is-selected" : ""}" data-lab="${lab.id}">
          <div class="lab__head">
            <div class="lab__title">LAB<span>_</span>${pad(lab.lab_number)}</div>
            <div class="lab__price">${fmt(lab.price)}</div>
          </div>
          ${lab.description ? `<p class="lab__desc">${esc(lab.description)}</p>` : ""}
          <div class="lab__foot">
            <div class="langs">
              ${lab.languages.map((lang) => `
                <button class="lang ${lang === chosen ? "is-active" : ""}" data-lang="${esc(lang)}">${esc(lang)}</button>
              `).join("")}
            </div>
            <button class="lab__toggle" data-toggle>${selected ? "✓ ВЫБРАНО" : "+ ВЫБРАТЬ"}</button>
          </div>
        </article>`;
    }).join("");
  }

  function renderCatalog() {
    renderSubjects();
    renderAccess();
    renderLabs();
    renderCartbar();
  }

  function cartLines() {
    return [...state.cart.entries()].map(([id, language]) => ({
      lab: state.catalog.find((l) => l.id === id),
      language,
    }));
  }

  function renderCartbar() {
    const lines = cartLines();
    $("#cartbar").hidden = !lines.length || $("#view-catalog").hidden;
    $("#cartCount").textContent = `${lines.length} ЛАБ`;
    $("#cartTotal").textContent = fmt(lines.reduce((s, l) => s + l.lab.price, 0));
  }

  function renderOrders() {
    const active = state.orders.filter((o) => !["completed", "rejected"].includes(o.status)).length;
    const badge = $("#ordersBadge");
    badge.hidden = !active;
    badge.textContent = active;

    if (!state.orders.length) {
      $("#orders").innerHTML = `
        <div class="empty">
          <span class="empty__art">¯\\_(ツ)_/¯</span>
          Заказов пока нет.<br />Выбери лабы в каталоге.
        </div>`;
      return;
    }

    $("#orders").innerHTML = state.orders.map((o) => `
      <article class="order">
        <div class="order__head">
          <span class="order__id">#${o.id}</span>
          <span class="status status--${o.status}">${STATUS[o.status] || o.status}</span>
        </div>
        <div class="order__items">
          ${o.items.map((i) => `
            <div class="order__item">
              <span>${i.subject} · LAB_${pad(i.lab_number)}</span>
              <span>${esc(i.language || "—")}</span>
            </div>`).join("")}
        </div>
        <div class="order__foot">
          <span class="order__date">${new Date(o.created_at).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</span>
          <span class="order__total">${fmt(o.total_price)}</span>
        </div>
        ${o.status === "awaiting_payment"
          ? `<button class="btn btn--primary btn--block" data-pay="${o.id}">ОПЛАТИТЬ</button>`
          : `<button class="btn btn--ghost btn--block" data-track="${o.id}">СТАТУС →</button>`}
      </article>`).join("");
  }

  function checkBotName() {
    return state.settings?.check_bot_username || cfg.checkBotUsername || "PAWS_CHECK_bot";
  }

  function stepsHtml(status) {
    const bot = checkBotName();
    const steps = [
      { title: "Оплата", text: "Переведи сумму по реквизитам Kaspi" },
      { title: "Чек в боте", text: `Фото/PDF только в @${bot} — не в Mini App` },
      { title: "Проверка", text: "Админ подтвердит оплату" },
      { title: "Готово", text: "Уведомление придёт в @KBTUPaws_bot" },
    ];
    const idx = STEP_ORDER.indexOf(status);
    return `<div class="steps">${steps.map((s, i) => `
      <div class="step ${i < idx ? "is-done" : ""} ${i === idx ? "is-current" : ""}">
        <span class="step__dot">${i < idx ? "✓" : i + 1}</span>
        <div>
          <div class="step__title">${s.title}</div>
          <div class="step__text">${s.text}</div>
        </div>
      </div>`).join("")}</div>`;
  }

  // ---------------- flows ----------------

  function openAccessForm(subject, onSaved) {
    const s = state.subjects.find((x) => x.subject === subject);
    const cred = state.creds[subject];
    openSheet(`
      <h2>ДОСТУП · ${subject}</h2>
      <p class="sheet__sub">
        Логин и пароль от ${esc(s.platform)} для предмета ${esc(s.title)}.
        Ссылки на контесты подставляются автоматически — укажи только доступы.
      </p>
      <form class="form" id="accessForm" autocomplete="off">
        <label class="field">
          <span class="field__label">ЛОГИН</span>
          <input class="field__input" name="login" value="${esc(cred?.login || "")}" placeholder="ADS26_..." required />
        </label>
        <label class="field">
          <span class="field__label">ПАРОЛЬ</span>
          <div class="field__wrap">
            <input class="field__input" name="password" type="password" placeholder="${cred?.has_password ? "••••••• (сохранён, введи новый)" : "пароль"}" required />
            <button class="field__eye" type="button" data-eye>👁</button>
          </div>
        </label>
        <div class="sheet__actions">
          <button class="btn btn--primary btn--block" type="submit">СОХРАНИТЬ</button>
          <button class="btn btn--ghost btn--block" type="button" data-close>ОТМЕНА</button>
        </div>
      </form>`);

    const form = $("#accessForm");
    form.querySelector("[data-eye]").addEventListener("click", () => {
      const input = form.password;
      input.type = input.type === "password" ? "text" : "password";
    });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector("[type=submit]");
      btn.disabled = true;
      btn.textContent = "СОХРАНЯЕМ…";
      try {
        state.creds[subject] = await backend.saveCredential(subject, form.login.value.trim(), form.password.value);
        haptic("medium");
        toast(`Доступ к ${subject} сохранён`);
        renderCatalog();
        if (onSaved) onSaved();
        else closeSheet();
      } catch (err) {
        btn.disabled = false;
        btn.textContent = "СОХРАНИТЬ";
        toast(`Ошибка: ${err.message}`);
      }
    });
  }

  function openCheckout() {
    const lines = cartLines();
    const total = lines.reduce((s, l) => s + l.lab.price, 0);
    const subjects = [...new Set(lines.map((l) => l.lab.subject))];
    const missing = subjects.filter((s) => !hasAccess(s));

    openSheet(`
      <h2>ОФОРМЛЕНИЕ</h2>
      <p class="sheet__sub">Проверь состав заказа. После создания появятся реквизиты для оплаты.</p>
      <div class="summary">
        ${lines.map(({ lab, language }) => `
          <div class="summary__row">
            <span>${lab.subject} · LAB_${pad(lab.lab_number)} · ${esc(language)}</span>
            <span>${fmt(lab.price)}</span>
          </div>`).join("")}
        <div class="summary__total"><span>ИТОГО</span><span>${fmt(total)}</span></div>
      </div>
      <div class="access-list">
        ${subjects.map((s) => `
          <button class="access-chip ${hasAccess(s) ? "is-ok" : ""}" data-access="${s}">
            <span>${s} · ${hasAccess(s) ? esc(state.creds[s].login) : "нет доступа"}</span>
            <span>${hasAccess(s) ? "✓" : "УКАЗАТЬ →"}</span>
          </button>`).join("")}
      </div>
      <div class="sheet__actions">
        <button class="btn btn--primary btn--block" id="createOrderBtn" ${missing.length ? "disabled" : ""}>
          ${missing.length ? `УКАЖИ ДОСТУП: ${missing.join(", ")}` : "СОЗДАТЬ ЗАКАЗ"}
        </button>
        <button class="btn btn--ghost btn--block" data-close>НАЗАД</button>
      </div>`);

    $("#sheetBody").querySelectorAll("[data-access]").forEach((b) =>
      b.addEventListener("click", () => openAccessForm(b.dataset.access, openCheckout)),
    );

    $("#createOrderBtn").addEventListener("click", async (e) => {
      const btn = e.currentTarget;
      btn.disabled = true;
      btn.textContent = "СОЗДАЁМ…";
      try {
        const order = await backend.createOrder(lines.map(({ lab, language }) => ({ lab_id: lab.id, language })));
        haptic("medium");
        state.cart.clear();
        state.orders = [order, ...state.orders.filter((o) => o.id !== order.id)];
        renderCatalog();
        renderOrders();
        openPayment(order);
      } catch (err) {
        btn.disabled = false;
        btn.textContent = "СОЗДАТЬ ЗАКАЗ";
        toast(`Ошибка: ${err.message}`);
      }
    });
  }

  function fmtPhone(raw) {
    const d = String(raw).replace(/\D/g, "");
    if (d.length === 11 && d.startsWith("7")) {
      return `+7 ${d.slice(1, 4)} ${d.slice(4, 7)} ${d.slice(7, 9)} ${d.slice(9)}`;
    }
    return raw;
  }

  function phoneForCopy(raw) {
    const d = String(raw).replace(/\D/g, "");
    return d.startsWith("7") ? `+${d}` : raw;
  }

  function copyText(text) {
    if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    return Promise.resolve();
  }

  function openPayment(order) {
    const s = state.settings || {};
    const bot = checkBotName();
    const rejected = order.payment_status === "rejected";
    openSheet(`
      <h2>ЗАКАЗ #${order.id}</h2>
      <p class="sheet__sub">Сумма к оплате: <b>${fmt(order.total_price)}</b></p>
      ${rejected ? `<div class="pay-box pay-box--warn">🔴 Оплата не подтверждена. Переведи снова и пришли чек в @${esc(bot)}.</div>` : ""}
      ${s.payment_requisites
        ? `<div class="requisites">
            <div class="requisites__label">KASPI · НОМЕР ДЛЯ ПЕРЕВОДА</div>
            ${s.payment_recipient
              ? `<div class="requisites__recipient">
                  <span class="requisites__recipient-name">${esc(s.payment_recipient)}</span>
                  <span class="requisites__recipient-hint">имя на Kaspi — только для проверки, копировать не нужно</span>
                </div>`
              : ""}
            <div class="requisites__row">
              <span class="requisites__value">${esc(fmtPhone(s.payment_requisites))}</span>
              <button class="btn btn--ghost requisites__copy" id="copyReqBtn">КОПИРОВАТЬ</button>
            </div>
          </div>`
        : ""}
      <div class="pay-note">
        <div class="pay-note__title">Чек принимается только в Telegram-боте</div>
        <div class="pay-note__text">
          1. Переведи сумму на Kaspi<br />
          2. Нажми кнопку ниже — откроется <b>@${esc(bot)}</b><br />
          3. Отправь туда фото или PDF чека<br />
          <span class="pay-note__muted">В Mini App чек прикрепить нельзя. Заказ #${order.id} подставится автоматически.</span>
        </div>
      </div>
      <div class="sheet__actions">
        <button class="btn btn--primary btn--block" id="sendReceiptBtn">ОТКРЫТЬ @${esc(bot)} →</button>
        <button class="btn btn--ghost btn--block" data-close>ЗАКРЫТЬ</button>
      </div>`);
    $("#copyReqBtn")?.addEventListener("click", async (e) => {
      const btn = e.currentTarget;
      await copyText(phoneForCopy(s.payment_requisites));
      haptic();
      btn.textContent = "СКОПИРОВАНО";
      setTimeout(() => (btn.textContent = "КОПИРОВАТЬ"), 1500);
    });
    $("#sendReceiptBtn").addEventListener("click", () => {
      haptic("medium");
      sendReceipt(order.id);
    });
  }

  function openTracking(order) {
    openSheet(`
      <h2>ЗАКАЗ #${order.id}</h2>
      <p class="sheet__sub"><span class="status status--${order.status}">${STATUS[order.status]}</span></p>
      ${order.status === "rejected"
        ? `<div class="pay-box">Заказ отклонён${order.admin_comment ? `: ${esc(order.admin_comment)}` : ""}. Напиши боту, если это ошибка.</div>`
        : stepsHtml(order.status)}
      <div class="sheet__actions"><button class="btn btn--ghost btn--block" data-close>ЗАКРЫТЬ</button></div>`);
  }

  function sendReceipt(orderId) {
    const bot = checkBotName();
    if (!bot) {
      toast("Username бота для чеков не настроен");
      return;
    }
    closeSheet();
    const link = `https://t.me/${bot}?start=r${orderId}`;
    if (tg?.openTelegramLink) {
      tg.openTelegramLink(link);
      tg.close?.();
      return;
    }
    window.open(link, "_blank");
  }

  // ---------------- events ----------------

  function bindEvents() {
    $("#tabs").addEventListener("click", (e) => {
      const tab = e.target.closest(".tab");
      if (!tab) return;
      haptic();
      switchView(tab.dataset.view);
      if (tab.dataset.view === "orders") refreshOrders();
    });

    $("#subjects").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-subject]");
      if (!btn) return;
      haptic();
      state.subject = btn.dataset.subject;
      renderCatalog();
    });

    $("#access").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-access]");
      if (!btn) return;
      haptic();
      openAccessForm(btn.dataset.access);
    });

    $("#labs").addEventListener("click", (e) => {
      const card = e.target.closest("[data-lab]");
      if (!card) return;
      const id = Number(card.dataset.lab);
      const lab = state.catalog.find((l) => l.id === id);

      const langBtn = e.target.closest("[data-lang]");
      if (langBtn) {
        state.cart.set(id, langBtn.dataset.lang);
      } else if (e.target.closest("[data-toggle]")) {
        if (state.cart.has(id)) state.cart.delete(id);
        else state.cart.set(id, lab.languages[0]);
      } else {
        return;
      }
      haptic();
      renderLabs();
      renderCartbar();
    });

    $("#checkoutBtn").addEventListener("click", () => {
      haptic("medium");
      openCheckout();
    });

    $("#orders").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-pay], [data-track]");
      if (!btn) return;
      const order = state.orders.find((o) => o.id === Number(btn.dataset.pay || btn.dataset.track));
      if (!order) return;
      haptic();
      if (btn.dataset.pay) openPayment(order);
      else openTracking(order);
    });

    $("#sheet").addEventListener("click", (e) => {
      if (e.target.closest("[data-close]")) closeSheet();
    });
  }

  async function refreshOrders() {
    try {
      state.orders = await backend.orders();
      renderOrders();
    } catch (err) {
      toast(`Не удалось загрузить заказы: ${err.message}`);
    }
  }

  // ---------------- init ----------------

  async function init() {
    tg?.ready();
    tg?.expand();
    tg?.setHeaderColor?.("#0b0d10");
    tg?.setBackgroundColor?.("#0b0d10");

    bindEvents();

    const banner = $("#banner");
    if (DEMO) {
      banner.hidden = false;
      banner.textContent = "ДЕМО-ВЕРСИЯ: данные хранятся на этом устройстве, бот и админ имитируются.";
    } else if (!tg?.initData) {
      banner.hidden = false;
      banner.textContent = "Открой приложение через Telegram-бота — вход выполняется по аккаунту Telegram.";
    }

    try {
      const [user, catalog, creds, settings] = await Promise.all([
        backend.auth(),
        backend.catalog(),
        backend.credentials(),
        backend.settings(),
      ]);
      state.settings = settings;
      state.user = user;
      state.catalog = catalog;
      state.subjects = creds;
      state.creds = Object.fromEntries(creds.map((c) => [c.subject, c]));
      renderUser();
      renderCatalog();
      await refreshOrders();
    } catch (err) {
      toast(`Ошибка загрузки: ${err.message}`);
    }
  }

  init();
})();
