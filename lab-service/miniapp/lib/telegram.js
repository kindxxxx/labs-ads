import { requireEnv, optionalEnv } from "./env.js";

const API = "https://api.telegram.org";

async function call(token, method, payload) {
  const response = await fetch(`${API}/bot${token}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const json = await response.json();
  if (!json.ok) throw new Error(json.description || `Telegram ${method} failed`);
  return json.result;
}

export function checkBotToken() {
  return requireEnv("ADMIN_BOT_TOKEN");
}

export function userBotToken() {
  return requireEnv("USER_BOT_TOKEN");
}

export function adminId() {
  return Number(requireEnv("ADMIN_ID"));
}

export async function sendMessage(token, chatId, text, extra = {}) {
  return call(token, "sendMessage", { chat_id: chatId, text, parse_mode: "HTML", ...extra });
}

export async function copyMessage(token, chatId, fromChatId, messageId, extra = {}) {
  return call(token, "copyMessage", {
    chat_id: chatId,
    from_chat_id: fromChatId,
    message_id: messageId,
    ...extra,
  });
}

export async function editMessageCaption(token, chatId, messageId, caption, extra = {}) {
  return call(token, "editMessageCaption", {
    chat_id: chatId,
    message_id: messageId,
    caption,
    parse_mode: "HTML",
    ...extra,
  });
}

export async function editMessageText(token, chatId, messageId, text, extra = {}) {
  return call(token, "editMessageText", {
    chat_id: chatId,
    message_id: messageId,
    text,
    parse_mode: "HTML",
    ...extra,
  });
}

export async function answerCallbackQuery(token, callbackQueryId, text, showAlert = false) {
  return call(token, "answerCallbackQuery", {
    callback_query_id: callbackQueryId,
    text,
    show_alert: showAlert,
  });
}

export function verifyWebhookSecret(req) {
  const expected = optionalEnv("TELEGRAM_WEBHOOK_SECRET");
  if (!expected) return true;
  return req.headers["x-telegram-bot-api-secret-token"] === expected;
}

export async function setCheckWebhook(baseUrl) {
  const token = checkBotToken();
  const secret = optionalEnv("TELEGRAM_WEBHOOK_SECRET");
  const url = `${baseUrl.replace(/\/$/, "")}/api/telegram/check-webhook`;
  return call(token, "setWebhook", {
    url,
    allowed_updates: ["message", "callback_query"],
    drop_pending_updates: true,
    ...(secret ? { secret_token: secret } : {}),
  });
}
