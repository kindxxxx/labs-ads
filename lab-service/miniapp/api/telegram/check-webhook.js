import { readJson, json } from "../../lib/http.js";
import {
  checkBotToken,
  userBotToken,
  adminId,
  sendMessage,
  copyMessage,
  editMessageCaption,
  editMessageText,
  answerCallbackQuery,
  verifyWebhookSecret,
} from "../../lib/telegram.js";
import {
  attachReceipt,
  revertReceipt,
  confirmPayment,
  rejectPayment,
  completeOrder,
  credentialsForOrder,
} from "../../lib/orders.js";
import { adminOrderText, adminOrderKeyboard } from "../../lib/formatting.js";

function parseReceiptStart(payload) {
  if (!payload) return null;
  const match = /^(?:r|receipt_)(\d+)$/i.exec(payload.trim());
  if (!match) return null;
  const id = Number(match[1]);
  return Number.isFinite(id) ? id : null;
}

function parseOrderIdFromText(text) {
  if (!text) return null;
  const match = /#(\d+)/.exec(text);
  if (!match) return null;
  const id = Number(match[1]);
  return Number.isFinite(id) ? id : null;
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function refreshAdminCard(token, query, order) {
  const text = adminOrderText(order);
  const keyboard = adminOrderKeyboard(order);
  const msg = query.message;
  if (!msg) return;
  const extra = { reply_markup: keyboard };
  try {
    if (msg.caption != null) {
      await editMessageCaption(token, msg.chat.id, msg.message_id, text, extra);
    } else {
      await editMessageText(token, msg.chat.id, msg.message_id, text, extra);
    }
  } catch (error) {
    if (!String(error.message).includes("message is not modified")) throw error;
  }
}

async function handleStart(message) {
  const token = checkBotToken();
  const text = message.text?.trim() || "";
  const [, payload] = text.split(/\s+/, 2);
  const orderId = parseReceiptStart(payload);
  const chatId = message.chat.id;

  if (orderId) {
    await sendMessage(
      token,
      chatId,
      `🧾 <b>Заказ #${orderId}</b>\n\nПереведите сумму на Kaspi и <b>отправьте сюда чек</b> — фото или PDF.`,
    );
    return;
  }

  if (message.from?.id === adminId()) {
    await sendMessage(
      token,
      chatId,
      "🐾 <b>PAWS CHECK</b> — бот проверки чеков.\n\nКлиенты присылают чеки сюда, тебе приходит копия с кнопками ✅ / ❌.",
    );
    return;
  }

  await sendMessage(
    token,
    chatId,
    "🧾 Бот для отправки чеков PAWS.\n\nОткройте Mini App, оформите заказ и нажмите «Отправить чек».",
  );
}

async function handleReceipt(message) {
  const token = checkBotToken();
  const userToken = userBotToken();
  const fromId = message.from?.id;
  if (!fromId) return;

  const photo = message.photo?.at(-1);
  const doc = message.document;
  const fileId = photo?.file_id || doc?.file_id;
  if (!fileId) return;

  const hintedOrderId =
    parseOrderIdFromText(message.reply_to_message?.text || message.reply_to_message?.caption) ||
    parseOrderIdFromText(message.caption);

  let order;
  try {
    order = await attachReceipt({
      telegramId: fromId,
      hintedOrderId,
    });
  } catch (error) {
    await sendMessage(token, message.chat.id, `❌ ${error.message}`);
    return;
  }

  const caption = adminOrderText(order);
  const keyboard = adminOrderKeyboard(order);

  const ownerId = adminId();
  try {
    await copyMessage(token, ownerId, message.chat.id, message.message_id, {
      caption,
      parse_mode: "HTML",
      reply_markup: keyboard,
    });
  } catch (error) {
    console.error("copyMessage failed", error);
    await revertReceipt(order.id);
    await sendMessage(
      token,
      message.chat.id,
      "⚠️ Чек получен, но не удалось передать на проверку. Пришлите чек ещё раз.",
    );
    return;
  }

  await sendMessage(
    token,
    message.chat.id,
    `✅ Чек по заказу #${order.id} принят.\nОжидайте подтверждения оплаты — уведомление придёт в @KBTUPaws_bot.`,
  );

  try {
    await sendMessage(
      userToken,
      fromId,
      `🟡 Чек по заказу #${order.id} на проверке. Ожидайте подтверждения оплаты.`,
    );
  } catch (error) {
    console.error("user notify failed", error);
  }
}

async function handleCallback(query) {
  const token = checkBotToken();
  const userToken = userBotToken();
  const data = query.data || "";
  const admin = adminId();

  if (query.from?.id !== admin) {
    await answerCallbackQuery(token, query.id, "Недостаточно прав", true);
    return;
  }

  if (data.startsWith("creds:")) {
    const orderId = Number(data.split(":")[1]);
    try {
      const creds = await credentialsForOrder(orderId);
      const blocks = creds.map((c) => {
        const head = `<b>${esc(c.subject)} Lab ${c.lab_number}</b> · #${c.contest_id}`;
        if (!c.login) return `${head}\n${esc(c.url)}\n— логин не указан`;
        return `${head}\n<a href="${esc(c.url)}">${esc(c.url)}</a>\nЛогин: <code>${esc(c.login)}</code>\nПароль: <tg-spoiler>${esc(c.password || "")}</tg-spoiler>`;
      });
      await sendMessage(token, query.message.chat.id, `🔑 Доступы по заказу #${orderId}\n\n${blocks.join("\n\n")}`);
      await answerCallbackQuery(token, query.id, "Доступы отправлены");
    } catch (error) {
      await answerCallbackQuery(token, query.id, error.message, true);
    }
    return;
  }

  const match = /^(pay_ok|pay_no|done):(\d+)$/.exec(data);
  if (!match) {
    await answerCallbackQuery(token, query.id);
    return;
  }

  const [, action, rawId] = match;
  const orderId = Number(rawId);

  try {
    let result;
    if (action === "done") result = await completeOrder(orderId, admin);
    else if (action === "pay_ok") result = await confirmPayment(orderId, admin);
    else result = await rejectPayment(orderId, admin);

    await refreshAdminCard(token, query, result.order);

    const labels = {
      pay_ok: "Оплата подтверждена",
      pay_no: "Оплата отклонена",
      done: "Заказ закрыт",
    };
    await answerCallbackQuery(token, query.id, labels[action]);

    if (!result.changed) return;

    const tgId = result.order.user?.telegram_id;
    if (!tgId) return;

    if (action === "pay_ok") {
      await sendMessage(
        userToken,
        tgId,
        `🟢 <b>ОПЛАТА ПОДТВЕРЖДЕНА</b>\n\nЗаказ #${orderId} принят в работу.`,
      );
    } else if (action === "pay_no") {
      await sendMessage(
        userToken,
        tgId,
        `🔴 Оплата не подтверждена.\n\nПроверьте перевод по заказу #${orderId} и пришлите чек ещё раз.`,
      );
    } else if (action === "done") {
      await sendMessage(userToken, tgId, `✅ <b>ЗАКАЗ ГОТОВ</b>\n\nЛабораторные по заказу #${orderId} выполнены.`);
    }
  } catch (error) {
    await answerCallbackQuery(token, query.id, error.message, true);
  }
}

async function handleMessage(message) {
  const text = message.text?.trim() || "";
  if (text.startsWith("/")) {
    await handleStart(message);
    return;
  }
  if (message.photo || message.document) {
    await handleReceipt(message);
  }
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    json(res, 405, { detail: "Method not allowed" });
    return;
  }
  if (!verifyWebhookSecret(req)) {
    json(res, 401, { ok: false });
    return;
  }

  try {
    const update = await readJson(req);
    if (update.callback_query) await handleCallback(update.callback_query);
    else if (update.message) await handleMessage(update.message);
    json(res, 200, { ok: true });
  } catch (error) {
    console.error(error);
    json(res, 500, { detail: error.message });
  }
}
