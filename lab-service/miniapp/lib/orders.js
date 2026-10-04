import { getSupabase } from "./supabase.js";
import { contestId, labContestUrl } from "./contest.js";
import { listForUser } from "./credentials.js";

const STATUS_LABELS = {
  awaiting_payment: "Ожидает оплату",
  awaiting_review: "Ожидает проверки",
  paid: "Оплачен",
  in_progress: "В работе",
  completed: "Готово",
  rejected: "Отклонён",
};

export async function upsertUser(tgUser) {
  const supabase = getSupabase();
  const { data: existing } = await supabase
    .from("users")
    .select("*")
    .eq("telegram_id", tgUser.id)
    .maybeSingle();

  const payload = {
    telegram_id: tgUser.id,
    username: tgUser.username,
    first_name: tgUser.first_name,
    last_name: tgUser.last_name,
    photo_url: tgUser.photo_url,
    language_code: tgUser.language_code,
    updated_at: new Date().toISOString(),
  };

  if (existing) {
    const { data, error } = await supabase.from("users").update(payload).eq("id", existing.id).select("*").single();
    if (error) throw error;
    return data;
  }

  const { data, error } = await supabase.from("users").insert(payload).select("*").single();
  if (error) throw error;
  return data;
}

export async function getUserByTelegramId(telegramId) {
  const supabase = getSupabase();
  const { data } = await supabase.from("users").select("*").eq("telegram_id", telegramId).maybeSingle();
  return data;
}

async function loadOrderItems(orderId) {
  const supabase = getSupabase();
  const { data: items, error } = await supabase
    .from("order_items")
    .select("lab_id, price, language_id, labs(subject, lab_number)")
    .eq("order_id", orderId);
  if (error) throw error;

  const langIds = [...new Set((items || []).map((i) => i.language_id).filter(Boolean))];
  const langMap = {};
  if (langIds.length) {
    const { data: langs } = await supabase.from("languages").select("id, name").in("id", langIds);
    for (const lang of langs || []) langMap[lang.id] = lang.name;
  }

  return (items || []).map((item) => ({
    lab_id: item.lab_id,
    subject: item.labs.subject,
    lab_number: item.labs.lab_number,
    contest_id: contestId(item.labs.subject, item.labs.lab_number),
    url: labContestUrl(item.labs.subject, item.labs.lab_number),
    language: item.language_id ? langMap[item.language_id] ?? null : null,
    price: item.price,
  }));
}

async function loadPayment(orderId) {
  const supabase = getSupabase();
  const { data } = await supabase.from("payments").select("*").eq("order_id", orderId).maybeSingle();
  return data;
}

export async function serializeOrder(order, withUser = false) {
  const items = await loadOrderItems(order.id);
  const payment = await loadPayment(order.id);
  const data = {
    id: order.id,
    status: order.status,
    status_label: STATUS_LABELS[order.status] || order.status,
    total_price: order.total_price,
    admin_comment: order.admin_comment,
    payment_status: payment?.status ?? null,
    user_message_id: payment?.user_message_id ?? null,
    admin_message_id: payment?.admin_message_id ?? null,
    items,
    created_at: order.created_at,
    updated_at: order.updated_at,
  };
  if (withUser) {
    const supabase = getSupabase();
    const { data: user } = await supabase.from("users").select("*").eq("id", order.user_id).single();
    data.user = {
      telegram_id: user.telegram_id,
      username: user.username,
      first_name: user.first_name,
    };
  }
  return data;
}

export async function listUserOrders(userId) {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from("orders")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });
  if (error) throw error;
  return Promise.all((data || []).map((o) => serializeOrder(o)));
}

export async function createOrder(user, items) {
  if (!items?.length) throw clientError("Не выбрано ни одной лабораторной");
  const labIds = items.map((i) => i.lab_id);
  if (new Set(labIds).size !== labIds.length) throw clientError("Лабораторная выбрана дважды");

  const supabase = getSupabase();
  const { data: labs, error: labsError } = await supabase
    .from("labs")
    .select("*")
    .in("id", labIds)
    .eq("is_active", true);
  if (labsError) throw labsError;

  const { data: labLangRows } = await supabase
    .from("lab_languages")
    .select("lab_id, language_id, languages(name)")
    .in("lab_id", labIds);

  const langsByLab = {};
  for (const row of labLangRows || []) {
    if (!langsByLab[row.lab_id]) langsByLab[row.lab_id] = [];
    langsByLab[row.lab_id].push({ id: row.language_id, name: row.languages?.name });
  }

  const labMap = Object.fromEntries((labs || []).map((l) => [l.id, l]));
  let total = 0;
  const orderItems = [];

  for (const { lab_id, language } of items) {
    const lab = labMap[lab_id];
    if (!lab) throw clientError(`Лабораторная ${lab_id} недоступна`);
    const langs = langsByLab[lab_id] || [];
    let languageId = null;
    if (langs.length) {
      const languageName = language || langs[0].name;
      const match = langs.find((l) => l.name === languageName);
      if (!match) throw clientError(`${lab.subject} Lab ${lab.lab_number}: язык ${languageName} недоступен`);
      languageId = match.id;
    }
    orderItems.push({ lab_id, language_id: languageId, price: lab.price });
    total += lab.price;
  }

  const saved = await listForUser(user.id);
  const missing = [...new Set(orderItems.map((i) => labMap[i.lab_id].subject))].filter((s) => !saved[s]);
  if (missing.length) throw clientError(`Укажи логин и пароль для: ${missing.join(", ")}`);

  const { data: order, error: orderError } = await supabase
    .from("orders")
    .insert({ user_id: user.id, status: "awaiting_payment", total_price: total })
    .select("*")
    .single();
  if (orderError) throw orderError;

  const rows = orderItems.map((i) => ({ ...i, order_id: order.id }));
  const { error: itemsError } = await supabase.from("order_items").insert(rows);
  if (itemsError) throw itemsError;

  await supabase.from("payments").insert({ order_id: order.id, amount: total, status: "pending" });
  await supabase.from("order_status_history").insert({
    order_id: order.id,
    old_status: null,
    new_status: "awaiting_payment",
    changed_by: user.telegram_id,
  });

  return serializeOrder(order);
}

export async function loadFullOrder(orderId) {
  const supabase = getSupabase();
  const { data: order } = await supabase.from("orders").select("*").eq("id", orderId).maybeSingle();
  if (!order) return null;
  return serializeOrder(order, true);
}

export async function findOrderForReceipt(telegramId, hintedOrderId) {
  const user = await getUserByTelegramId(telegramId);
  if (!user) throw clientError("Сначала оформите заказ в приложении, затем пришлите чек.");

  const supabase = getSupabase();
  const waiting = ["awaiting_payment", "awaiting_review"];
  let query = supabase.from("orders").select("*").eq("user_id", user.id).in("status", waiting);

  let order = null;
  if (hintedOrderId != null) {
    const { data } = await query.eq("id", hintedOrderId).maybeSingle();
    order = data;
  }
  if (!order) {
    const { data } = await supabase
      .from("orders")
      .select("*")
      .eq("user_id", user.id)
      .in("status", waiting)
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    order = data;
  }
  if (!order) throw clientError("Нет заказа, который ждёт чек.");
  return { user, order };
}

export async function attachReceipt(input) {
  const { order } = await findOrderForReceipt(input.telegramId, input.hintedOrderId);
  if (order.status === "awaiting_review") {
    throw clientError(`Чек по заказу #${order.id} уже получен. Ожидайте подтверждения оплаты.`);
  }

  // Чек не сохраняется: только статус. Файл остаётся в Telegram и копируется админу.
  const supabase = getSupabase();
  await supabase
    .from("payments")
    .update({
      status: "pending",
      receipt_attachment_id: null,
      user_chat_id: null,
      user_message_id: null,
      admin_chat_id: null,
      admin_message_id: null,
    })
    .eq("order_id", order.id);

  await supabase.from("orders").update({ status: "awaiting_review", updated_at: new Date().toISOString() }).eq("id", order.id);
  await supabase.from("order_status_history").insert({
    order_id: order.id,
    old_status: "awaiting_payment",
    new_status: "awaiting_review",
    changed_by: input.telegramId,
  });

  return loadFullOrder(order.id);
}

export async function rememberAdminMessage() {
  // Сообщение с чеком живёт только в Telegram, в БД его id не пишем.
}

export async function revertReceipt(orderId) {
  const supabase = getSupabase();
  await supabase.from("orders").update({ status: "awaiting_payment", updated_at: new Date().toISOString() }).eq("id", orderId);
  await supabase.from("order_status_history").insert({
    order_id: orderId,
    old_status: "awaiting_review",
    new_status: "awaiting_payment",
    changed_by: 0,
    comment: "Чек не доставлен админу",
  });
}

export async function confirmPayment(orderId, adminId) {
  const supabase = getSupabase();
  const { data: order } = await supabase.from("orders").select("*").eq("id", orderId).maybeSingle();
  if (!order) throw clientError("Заказ не найден");
  const payment = await loadPayment(orderId);
  if (payment?.status === "confirmed") return { order: await loadFullOrder(orderId), changed: false };
  if (order.status !== "awaiting_review") throw clientError("Нет чека на проверке");

  await supabase
    .from("payments")
    .update({ status: "confirmed", confirmed_by: adminId, confirmed_at: new Date().toISOString() })
    .eq("order_id", orderId);
  await supabase.from("orders").update({ status: "in_progress", updated_at: new Date().toISOString() }).eq("id", orderId);
  await supabase.from("order_status_history").insert({
    order_id: orderId,
    old_status: "awaiting_review",
    new_status: "in_progress",
    changed_by: adminId,
    comment: "Оплата подтверждена",
  });
  return { order: await loadFullOrder(orderId), changed: true };
}

export async function rejectPayment(orderId, adminId, reason = null) {
  const supabase = getSupabase();
  const { data: order } = await supabase.from("orders").select("*").eq("id", orderId).maybeSingle();
  if (!order) throw clientError("Заказ не найден");
  const payment = await loadPayment(orderId);
  if (payment?.status === "confirmed" || payment?.status === "rejected") {
    return { order: await loadFullOrder(orderId), changed: false };
  }
  if (order.status !== "awaiting_review") throw clientError("Нет чека на проверке");

  await supabase
    .from("payments")
    .update({ status: "rejected", rejection_reason: reason })
    .eq("order_id", orderId);
  await supabase
    .from("orders")
    .update({ status: "awaiting_payment", admin_comment: reason, updated_at: new Date().toISOString() })
    .eq("id", orderId);
  await supabase.from("order_status_history").insert({
    order_id: orderId,
    old_status: "awaiting_review",
    new_status: "awaiting_payment",
    changed_by: adminId,
    comment: reason,
  });
  return { order: await loadFullOrder(orderId), changed: true };
}

export async function completeOrder(orderId, adminId) {
  const supabase = getSupabase();
  const { data: order } = await supabase.from("orders").select("*").eq("id", orderId).maybeSingle();
  if (!order) throw clientError("Заказ не найден");
  if (order.status === "completed") return { order: await loadFullOrder(orderId), changed: false };
  if (order.status !== "in_progress") throw clientError("Сначала подтвердите оплату");

  await supabase.from("orders").update({ status: "completed", updated_at: new Date().toISOString() }).eq("id", orderId);
  await supabase.from("order_status_history").insert({
    order_id: orderId,
    old_status: "in_progress",
    new_status: "completed",
    changed_by: adminId,
  });
  return { order: await loadFullOrder(orderId), changed: true };
}

export async function credentialsForOrder(orderId) {
  const order = await loadFullOrder(orderId);
  if (!order) throw clientError("Заказ не найден");
  const supabase = getSupabase();
  const { data: dbOrder } = await supabase.from("orders").select("user_id").eq("id", orderId).single();
  const { data: creds } = await supabase.from("subject_credentials").select("*").eq("user_id", dbOrder.user_id);
  const credMap = Object.fromEntries((creds || []).map((c) => [c.subject, c]));
  const { decryptPassword } = await import("./credentials.js");

  return order.items.map((item) => {
    const row = credMap[item.subject];
    return {
      subject: item.subject,
      lab_number: item.lab_number,
      contest_id: item.contest_id,
      url: item.url,
      login: row?.login ?? null,
      password: row ? decryptPassword(row.password_encrypted) : null,
    };
  });
}

function clientError(message) {
  const err = new Error(message);
  err.status = 400;
  return err;
}
