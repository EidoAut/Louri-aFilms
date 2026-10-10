.pragma library

// Keep the top-level view on its selected official embed. Subframes and media
// remain controlled by the provider; this does not remove in-stream adverts.
function allowsNavigation(target, selected, checkingCodecs) {
    target = String(target);
    selected = String(selected);
    if (target === "about:blank") return checkingCodecs || selected === "about:blank";
    // Qt loadHtml uses a data URL for the local, static codec probe.
    if (checkingCodecs) return target.indexOf("data:text/html") === 0;
    return target.split(/[?#]/)[0] === selected.split(/[?#]/)[0];
}
