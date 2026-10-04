import { createClient } from "@supabase/supabase-js";
import { requireEnv } from "./env.js";

let client;

export function getSupabase() {
  if (!client) {
    client = createClient(requireEnv("SUPABASE_URL"), requireEnv("SUPABASE_SERVICE_ROLE_KEY"), {
      auth: { persistSession: false, autoRefreshToken: false },
    });
  }
  return client;
}
