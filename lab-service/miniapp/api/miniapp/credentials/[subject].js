import { withCors, json, readJson } from "../../../lib/http.js";
import { getInitData, validateInitData } from "../../../lib/telegram-auth.js";
import { upsertUser } from "../../../lib/orders.js";
import { saveCredential, deleteCredential, publicView } from "../../../lib/credentials.js";
import { SUBJECT_PLATFORMS } from "../../../lib/contest.js";

export default withCors(async (req, res) => {
  const subject = req.query.subject?.toUpperCase();
  if (!SUBJECT_PLATFORMS[subject]) {
    json(res, 404, { detail: "Неизвестный предмет" });
    return;
  }

  const tgUser = validateInitData(getInitData(req));
  const user = await upsertUser(tgUser);

  if (req.method === "PUT") {
    const body = (await readJson(req)) || {};
    const row = await saveCredential(user.id, subject, body.login, body.password);
    json(res, 200, publicView(subject, row));
    return;
  }

  if (req.method === "DELETE") {
    await deleteCredential(user.id, subject);
    json(res, 200, publicView(subject, null));
    return;
  }

  json(res, 405, { detail: "Method not allowed" });
});
