const CONTEST_ID_BASE = { PP1: 100, ADS: 200, PP2: 300 };
const EJUDGE_CLIENT_URL = "http://ejudge.kz/new-client";

export const SUBJECT_PLATFORMS = {
  ADS: { title: "Algorithms & Data Structures", platform: "ejudge" },
  PP1: { title: "Programming Principles 1", platform: "ejudge" },
  PP2: { title: "Programming Principles 2", platform: "ejudge" },
};

export function contestId(subject, labNumber) {
  const base = CONTEST_ID_BASE[subject];
  if (!base) throw new Error(`Unknown subject: ${subject}`);
  return base + labNumber;
}

export function labContestUrl(subject, labNumber) {
  return `${EJUDGE_CLIENT_URL}?contest_id=${contestId(subject, labNumber)}`;
}
