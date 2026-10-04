const CAPTION_LIMIT = 1024;

const PAYMENT_LINE = {
  pending: "⏳ Ожидает подтверждения",
  confirmed: "✓ Подтверждена",
  rejected: "✕ Не подтверждена — ждём новый чек",
};

const ORDER_LINE = {
  awaiting_payment: "⏳ Ожидает оплату",
  awaiting_review: "⏳ Чек на проверке",
  paid: "✓ Оплачен",
  in_progress: "🔵 В работе",
  completed: "✅ Готово",
  rejected: "✕ Отклонён",
};

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function fmtMoney(value) {
  return `${Number(value).toLocaleString("ru-RU")} ₸`;
}

function itemLine(item) {
  const lang = item.language ? ` (${esc(item.language)})` : "";
  const tag = item.contest_id ? ` · #${item.contest_id}` : "";
  return `• ${item.subject} Lab ${item.lab_number}${lang}${tag} — ${fmtMoney(item.price)}`;
}

export function adminOrderText(order) {
  const user = order.user || {};
  const handle = user.username ? `@${user.username}` : `id ${user.telegram_id ?? "?"}`;
  const items = (order.items || []).map(itemLine).join("\n");
  const lines = [
    `<b>ЗАКАЗ #${order.id}</b>`,
    "",
    "<b>Состав:</b>",
    items,
    "",
    `<b>Сумма:</b> ${fmtMoney(order.total_price)}`,
    `<b>Telegram:</b> ${esc(handle)}`,
  ];
  lines.push(
    "",
    `<b>Оплата:</b> ${PAYMENT_LINE[order.payment_status] || "—"}`,
    `<b>Статус:</b> ${ORDER_LINE[order.status] || order.status}`,
  );
  if (order.admin_comment && order.payment_status === "rejected") {
    lines.push(`<b>Причина:</b> ${esc(order.admin_comment)}`);
  }
  return lines.join("\n").slice(0, CAPTION_LIMIT);
}

export function paymentReviewKeyboard(orderId) {
  return {
    inline_keyboard: [
      [{ text: "✅ ПОДТВЕРДИТЬ ОПЛАТУ", callback_data: `pay_ok:${orderId}` }],
      [{ text: "❌ НЕ ПОДТВЕРДИТЬ ОПЛАТУ", callback_data: `pay_no:${orderId}` }],
    ],
  };
}

export function inProgressKeyboard(orderId) {
  return {
    inline_keyboard: [
      [{ text: "🔑 ДОСТУПЫ К ПЛАТФОРМЕ", callback_data: `creds:${orderId}` }],
      [{ text: "✅ РАБОТА ГОТОВА", callback_data: `done:${orderId}` }],
    ],
  };
}

export function adminOrderKeyboard(order) {
  if (order.status === "awaiting_review") return paymentReviewKeyboard(order.id);
  if (order.status === "in_progress") return inProgressKeyboard(order.id);
  return undefined;
}
