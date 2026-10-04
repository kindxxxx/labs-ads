import { corsOrigins } from "./env.js";

export function applyCors(req, res) {
  const origins = corsOrigins();
  const origin = req.headers.origin || "";
  const allow = origins.includes("*") ? "*" : origins.includes(origin) ? origin : origins[0];
  if (allow) {
    res.setHeader("Access-Control-Allow-Origin", allow);
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type,X-Telegram-Init-Data");
  }
}

export function json(res, status, body) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(body));
}

export function readJson(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (chunk) => {
      data += chunk;
    });
    req.on("end", () => {
      if (!data) return resolve(null);
      try {
        resolve(JSON.parse(data));
      } catch (error) {
        reject(error);
      }
    });
    req.on("error", reject);
  });
}

export function withCors(handler) {
  return async (req, res) => {
    applyCors(req, res);
    if (req.method === "OPTIONS") {
      res.statusCode = 204;
      return res.end();
    }
    try {
      await handler(req, res);
    } catch (error) {
      console.error(error);
      json(res, error.status || 500, { detail: error.message || "Internal error" });
    }
  };
}
