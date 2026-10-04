import fernet from "fernet";
import { requireEnv } from "./env.js";
import { getSupabase } from "./supabase.js";
import { SUBJECT_PLATFORMS } from "./contest.js";

function getFernet() {
  const key = requireEnv("CREDENTIALS_KEY");
  return new fernet.Secret(key);
}

export function encryptPassword(password) {
  const token = new fernet.Token({ secret: getFernet(), ttl: 0 });
  return token.encode(password);
}

export function decryptPassword(encrypted) {
  const token = new fernet.Token({ secret: getFernet(), ttl: 0 });
  return token.decode(encrypted);
}

export function publicView(subject, row) {
  const platform = SUBJECT_PLATFORMS[subject];
  return {
    subject,
    title: platform.title,
    platform: platform.platform,
    login: row?.login ?? null,
    has_password: Boolean(row),
  };
}

export async function listForUser(userId) {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from("subject_credentials")
    .select("*")
    .eq("user_id", userId);
  if (error) throw error;
  const map = {};
  for (const row of data || []) map[row.subject] = row;
  return map;
}

export async function saveCredential(userId, subject, login, password) {
  if (!SUBJECT_PLATFORMS[subject]) {
    const err = new Error(`Неизвестный предмет ${subject}`);
    err.status = 400;
    throw err;
  }
  if (!login?.trim() || !password) {
    const err = new Error("Нужны логин и пароль");
    err.status = 400;
    throw err;
  }

  const supabase = getSupabase();
  const { data: existing } = await supabase
    .from("subject_credentials")
    .select("id")
    .eq("user_id", userId)
    .eq("subject", subject)
    .maybeSingle();

  const payload = {
    user_id: userId,
    subject,
    login: login.trim(),
    password_encrypted: encryptPassword(password),
    updated_at: new Date().toISOString(),
  };

  if (existing) {
    const { data, error } = await supabase
      .from("subject_credentials")
      .update(payload)
      .eq("id", existing.id)
      .select("*")
      .single();
    if (error) throw error;
    return data;
  }

  const { data, error } = await supabase
    .from("subject_credentials")
    .insert(payload)
    .select("*")
    .single();
  if (error) throw error;
  return data;
}

export async function deleteCredential(userId, subject) {
  const supabase = getSupabase();
  await supabase.from("subject_credentials").delete().eq("user_id", userId).eq("subject", subject);
}
