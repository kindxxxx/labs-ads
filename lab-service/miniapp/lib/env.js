export function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing env: ${name}`);
  return value;
}

export function optionalEnv(name, fallback = "") {
  return process.env[name] || fallback;
}

export function corsOrigins() {
  const raw = optionalEnv("MINIAPP_ORIGINS", "*");
  return raw.split(",").map((o) => o.trim()).filter(Boolean);
}
