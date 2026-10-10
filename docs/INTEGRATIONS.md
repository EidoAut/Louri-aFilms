# LourihnaFilms 0.3.0 integration research

Checked 2026-10-10. External pages and HTML structures can change.

## TMDB

Official application authentication accepts a v3 `api_key` query parameter or an API Read Access Token in the Authorization bearer header:
https://developer.themoviedb.org/docs/authentication-application

The official movie details endpoint supports append_to_response, used for alternative_titles, recommendations and credits:
https://developer.themoviedb.org/reference/movie-details

Image URLs follow TMDB's published base/size/file-path pattern. The documented artwork sample was successfully downloaded into the local cache for UI verification:
https://developer.themoviedb.org/docs/image-basics

The app supports movie/TV title search, popular/trending lists, genre discovery, TV season episodes and localized metadata. TMDB is a metadata catalog and supplies no OK.ru availability mapping. Catalog details and candidate discovery remain separate steps. Credentials must be supplied by the user through Settings; no real key was used during automated verification.

## Direct OK.ru search

The published REST method listings do not provide an anonymous global video search API:
https://apiok.ru/en/dev/methods/rest/video/
https://apiok.ru/en/dev/methods/rest/search/

OK's user-facing help describes video searching:
https://m.ok.ru/help/kak-polzovatsya-poiskom?st.pltf=ANDROID

A publicly indexed anonymous search page was observed with these existing parameters (not an invented endpoint):
https://ok.ru/video/search?st.cmd=anonymVideo&st.ft=search&st.gsq=connect-gas&st.m=SEARCH

A standard unauthenticated HTTP request returned public HTML containing `video_search_result_video-card` elements, numeric `/video/` links, `video-name`, `video-description`, visible thumbnail images and `video-card_duration` text. The site's robots rules permitted this page during verification. A live query for Metropolis 1927 returned 14 parsed video candidates, all with durations. These observations establish discovery only, not content identity or playable streams.

The parser uses these visible cards only. It does not read hidden player configuration, execute JavaScript, invent offset parameters, access private APIs, follow authentication redirects, solve challenges or collect session cookies intentionally. The first page is supported; the HTML has no stability guarantee. Access denial, unreadable pages or changed markup stop direct probing for that operation and switch to the configured external search source.

External fallback is the optional Brave Search API or DuckDuckGo public HTML results. Search backend namespaces separate cached results. Numeric video URL normalization deduplicates candidates. Public metadata enrichment follows the existing robots-aware reader and stops on unavailable responses.

## Official player and Continue Watching

No supported documented OK.ru position/seek event contract was established. The official embed URL is reconstructed from a validated numeric identifier. WebEngine uses an off-the-record profile, disallows downloads and denies permission requests. Codec, regional, account and embed restrictions belong to the provider.

Continue Watching is explicitly user-managed through Watch later/Mark finished. It reopens saved sessions; it does not imply automatic timestamp resume. SQLite position remains null. Recently opened records player-open attempts, not completed playback. The user always selects a candidate; TMDB titles are never automatically treated as available videos.

## Retained Internet Archive support

Explore retains official public JSON search and metadata:
https://archive.org/advancedsearch.php
https://archive.org/developers/md-read.html

Restricted/non-video Archive metadata is rejected before embedded playback. No direct media streams are extracted.
