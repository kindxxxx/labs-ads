import crypto from "node:crypto";
import { requireEnv, optionalEnv } from "./env.js";

export class InitDataError extends Error {
  constructor(message) {
    super(message);
    this.status = 401;
  }
}

export function validateInitData(initData) {
  if (!initData) throw new InitDataError("initData отсутствует");

  const botToken = requireEnv("USER_BOT_TOKEN");
  const params = new URLSearchParams(initData);
  const hash = params.get("hash");
  if (!hash) throw new InitDataError("hash отсутствует");
  params.delete("hash");

  const checkString = [...params.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");

  const secret = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
  const expected = crypto.createHmac("sha256", secret).update(checkString).digest("hex");
  if (expected !== hash) throw new InitDataError("Неверная подпись initData");

  const maxAge = Number(optionalEnv("INIT_DATA_MAX_AGE_SECONDS", "86400"));
  const authDate = Number(params.get("auth_date") || "0");
  if (maxAge && Date.now() / 1000 - authDate > maxAge) {
    throw new InitDataError("initData устарел");
  }

  const userRaw = params.get("user");
  if (!userRaw) throw new InitDataError("user отсутствует в initData");
  const user = JSON.parse(userRaw);
  return {
    id: Number(user.id),
    first_name: user.first_name ?? null,
    last_name: user.last_name ?? null,
    username: user.username ?? null,
    photo_url: user.photo_url ?? null,
    language_code: user.language_code ?? null,
  };
}

export function getInitData(req) {
  return req.headers["x-telegram-init-data"] || "";
}
