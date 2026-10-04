import { withCors, json } from "../../lib/http.js";
import { getSupabase } from "../../lib/supabase.js";

export default withCors(async (_req, res) => {
  const supabase = getSupabase();
  const { data: labs, error } = await supabase
    .from("labs")
    .select("id, subject, lab_number, price, description, requirements")
    .eq("is_active", true)
    .order("subject")
    .order("lab_number");
  if (error) throw error;

  const labIds = (labs || []).map((l) => l.id);
  const { data: links } = await supabase
    .from("lab_languages")
    .select("lab_id, languages(name)")
    .in("lab_id", labIds);

  const langsByLab = {};
  for (const row of links || []) {
    if (!langsByLab[row.lab_id]) langsByLab[row.lab_id] = [];
    if (row.languages?.name) langsByLab[row.lab_id].push(row.languages.name);
  }

  json(
    res,
    200,
    (labs || []).map((lab) => ({
      ...lab,
      languages: langsByLab[lab.id] || [],
    })),
  );
});
