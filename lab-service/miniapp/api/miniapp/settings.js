import { withCors, json } from "../../lib/http.js";
import { optionalEnv } from "../../lib/env.js";

export default withCors(async (_req, res) => {
  json(res, 200, {
    bot_username: optionalEnv("USER_BOT_USERNAME"),
    check_bot_username: optionalEnv("CHECK_BOT_USERNAME", optionalEnv("USER_BOT_USERNAME")),
    payment_requisites: optionalEnv("PAYMENT_REQUISITES"),
    payment_recipient: optionalEnv("PAYMENT_RECIPIENT"),
    payment_instructions: optionalEnv("PAYMENT_INSTRUCTIONS"),
  });
});
