const TRACK_ZONES = [
  [/las vegas/, "America/Los_Angeles"],
  [/miami/, "America/New_York"],
  [/austin|cota|americas/, "America/Chicago"],
  [/imola/, "Europe/Rome"],
  [/monza/, "Europe/Rome"],
  [/mugello/, "Europe/Rome"],
  [/madrid/, "Europe/Madrid"],
  [/barcelona|catalunya|montmel/, "Europe/Madrid"],
  [/valencia/, "Europe/Madrid"],
  [/shanghai|china/, "Asia/Shanghai"],
  [/suzuka|japan/, "Asia/Tokyo"],
  [/marina bay|singapore/, "Asia/Singapore"],
  [/sakhir|bahrain/, "Asia/Bahrain"],
  [/jeddah|saudi/, "Asia/Riyadh"],
  [/lusail|losail|qatar/, "Asia/Qatar"],
  [/yas marina|abu dhabi|united arab/, "Asia/Dubai"],
  [/baku|azerbaijan/, "Asia/Baku"],
  [/melbourne|albert park|australia/, "Australia/Melbourne"],
  [/montreal|villeneuve|canada/, "America/Toronto"],
  [/interlagos|sao paulo|são paulo|brazil/, "America/Sao_Paulo"],
  [/mexico/, "America/Mexico_City"],
  [/zandvoort|netherlands|dutch/, "Europe/Amsterdam"],
  [/spa|belgium/, "Europe/Brussels"],
  [/spielberg|austria|red bull/, "Europe/Vienna"],
  [/hungaroring|budapest|hungary/, "Europe/Budapest"],
  [/silverstone|britain|united kingdom|\buk\b/, "Europe/London"],
  [/monaco|monte[- ]?carlo/, "Europe/Monaco"],
  [/sepang|malaysia/, "Asia/Kuala_Lumpur"],
];

export function trackTimeZone(race) {
  if (!race) return "";
  const hay = [race.circuit, race.location, race.country, race.name]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  const match = TRACK_ZONES.find(([pattern]) => pattern.test(hay));
  return match ? match[1] : "";
}

export function formatClock(date, timeZone) {
  const options = {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  };
  if (timeZone) options.timeZone = timeZone;
  try {
    return new Intl.DateTimeFormat("en-GB", options).format(date);
  } catch {
    return new Intl.DateTimeFormat("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date);
  }
}

export function parseIsoDate(iso) {
  if (!iso) return null;
  const date = new Date(`${iso}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatWeekend(startIso, endIso) {
  const start = parseIsoDate(startIso) || parseIsoDate(endIso);
  const end = parseIsoDate(endIso) || start;
  if (!start || !end) return "";
  const startDay = String(start.getDate()).padStart(2, "0");
  const endDay = String(end.getDate()).padStart(2, "0");
  const startMon = start.toLocaleDateString("en-GB", { month: "short" }).toUpperCase();
  const endMon = end.toLocaleDateString("en-GB", { month: "short" }).toUpperCase();
  if (startMon === endMon && start.getFullYear() === end.getFullYear()) {
    if (startDay === endDay) return `${endDay} ${endMon}`;
    return `${startDay} - ${endDay} ${endMon}`;
  }
  return `${startDay} ${startMon} - ${endDay} ${endMon}`;
}

export function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

/** Index of the upcoming round: stays on race day until the main race date has passed. */
export function nextRoundIndex(races, now = new Date()) {
  const today = startOfDay(now);
  const idx = races.findIndex((race) => {
    const raceDay = parseIsoDate(race.date) || parseIsoDate(race.weekend_end);
    return raceDay && raceDay >= today;
  });
  return idx === -1 ? Math.max(0, races.length - 1) : idx;
}
