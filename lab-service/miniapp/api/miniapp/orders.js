import { withCors, json, readJson } from "../../lib/http.js";
import { getInitData, validateInitData } from "../../lib/telegram-auth.js";
import { upsertUser, listUserOrders, createOrder } from "../../lib/orders.js";

export default withCors(async (req, res) => {
  const tgUser = validateInitData(getInitData(req));
  const user = await upsertUser(tgUser);

  if (req.method === "GET") {
    json(res, 200, await listUserOrders(user.id));
    return;
  }

  if (req.method === "POST") {
    const body = (await readJson(req)) || {};
    const items = (body.items || []).map((i) => ({ lab_id: i.lab_id, language: i.language ?? null }));
    const order = await createOrder(user, items);
    json(res, 201, order);
    return;
  }

  json(res, 405, { detail: "Method not allowed" });
});
