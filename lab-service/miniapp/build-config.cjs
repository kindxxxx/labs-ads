/** Сборка config.js из переменных Vercel (или локальный config.local.js как fallback). */
const fs = require("fs");
const path = require("path");

const defaults = {
  apiBase: "",
  demoMode: false,
  botUsername: "KBTUPaws_bot",
  checkBotUsername: "PAWS_CHECK_bot",
  paymentRequisites: "+77785520300",
  paymentRecipient: "\u0421\u0430\u0432\u0435\u043b\u0438\u0439 \u041c.",
  paymentInstructions:
    "\u041f\u0435\u0440\u0435\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443 \u043d\u0430 Kaspi \u0438 \u043e\u0442\u043f\u0440\u043e\u0439\u0442\u0435 @PAWS_CHECK_bot \u0434\u043b\u044f \u0447\u0435\u043a\u0430.",
};

const env = {
  apiBase: process.env.API_BASE ?? process.env.VITE_API_BASE ?? "",
  demoMode: process.env.DEMO_MODE === "true" || process.env.DEMO_MODE === "1",
  botUsername: process.env.USER_BOT_USERNAME || process.env.BOT_USERNAME || "",
  checkBotUsername: process.env.CHECK_BOT_USERNAME || "",
  paymentRequisites: process.env.PAYMENT_REQUISITES || "",
  paymentRecipient: process.env.PAYMENT_RECIPIENT || "",
  paymentInstructions: process.env.PAYMENT_INSTRUCTIONS || "",
};

const localPath = path.join(__dirname, "config.local.js");
if (fs.existsSync(localPath)) {
  Object.assign(defaults, require(localPath));
}

const out = { ...defaults };
for (const [k, v] of Object.entries(env)) {
  if (v) out[k] = v;
}
if (process.env.DEMO_MODE != null) out.demoMode = env.demoMode;

const body = `// Generated at deploy time. Edit env vars on Vercel or config.local.js locally.\nwindow.APP_CONFIG = ${JSON.stringify(out, null, 2)};\n`;
fs.writeFileSync(path.join(__dirname, "config.js"), body, "utf8");
console.log("config.js written", {
  apiBase: out.apiBase || "(same-origin)",
  demoMode: out.demoMode,
  botUsername: out.botUsername || "(empty)",
});
