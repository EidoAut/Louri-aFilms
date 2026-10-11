.pragma library

function visual(entry) { return entry.catalog || entry; }
function title(entry) { return entry.local_title ? entry.title : visual(entry).title || entry.title || ""; }
function metadata(entry) {
    var item = visual(entry);
    var kind = item.kind === "tv" ? "Serie" : item.kind === "movie" ? "Película" : "Vídeo";
    var duration = entry.kind === "video" ? (entry.duration_seconds ? Math.round(entry.duration_seconds / 60) : 0) : item.runtime;
    return [kind, item.year || "", duration ? duration + " min" : "", item.rating ? "TMDB " + Number(item.rating).toFixed(1) : ""].filter(Boolean).join(" · ");
}
function progress(entry, history) {
    return history.find(function(item) { return item.key === entry.key; }) || entry;
}
function resumable(entry) { return (entry.position_ms || 0) > 0 && !entry.finished; }
