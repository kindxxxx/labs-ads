import { json } from "../lib/http.js";

export default function handler(req, res) {
  json(res, 200, { status: "ok", service: "paws" });
}
