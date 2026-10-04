import { setCheckWebhook } from "../lib/telegram.js";

const baseUrl = process.argv[2] || process.env.VERCEL_URL && `https://${process.env.VERCEL_URL}`;
if (!baseUrl) {
  console.error("Usage: node scripts/set-webhook.js https://your-app.vercel.app");
  process.exit(1);
}

const result = await setCheckWebhook(baseUrl);
console.log("Webhook set:", result);
