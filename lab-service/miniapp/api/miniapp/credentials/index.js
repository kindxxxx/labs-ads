import { withCors, json } from "../../../lib/http.js";
import { getInitData, validateInitData } from "../../../lib/telegram-auth.js";
import { upsertUser } from "../../../lib/orders.js";
import { listForUser, publicView } from "../../../lib/credentials.js";
import { SUBJECT_PLATFORMS } from "../../../lib/contest.js";

export default withCors(async (req, res) => {
  if (req.method !== "GET") {
    json(res, 405, { detail: "Method not allowed" });
    return;
  }
  const tgUser = validateInitData(getInitData(req));
  const user = await upsertUser(tgUser);
  const saved = await listForUser(user.id);
  json(res, 200, Object.keys(SUBJECT_PLATFORMS).map((subject) => publicView(subject, saved[subject])));
});
