import { withCors, json } from "../../lib/http.js";
import { getInitData, validateInitData } from "../../lib/telegram-auth.js";
import { upsertUser } from "../../lib/orders.js";

export default withCors(async (req, res) => {
  if (req.method !== "POST") {
    json(res, 405, { detail: "Method not allowed" });
    return;
  }
  const tgUser = validateInitData(getInitData(req));
  const user = await upsertUser(tgUser);
  json(res, 200, {
    telegram_id: user.telegram_id,
    username: user.username,
    first_name: user.first_name,
    photo_url: user.photo_url,
  });
});
