# ==========================================================================
"""verify_okru_live.py
Opt-in live comparison; temporary data, no login and no playback claims.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


def main() -> None:
    """Run this isolated verification command only when explicitly invoked."""
    import argparse
    import asyncio
    import json
    import sys
    from datetime import datetime, timezone
    from pathlib import Path

    import httpx

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from lourihna_films.core.exceptions import ServiceError
    from lourihna_films.providers.direct_search import DirectPublicSearch
    from lourihna_films.providers.okru import OKRuProvider
    from lourihna_films.providers.public_metadata import PublicMetadata
    from lourihna_films.providers.public_search import PublicSearch
    from lourihna_films.services.playback_service import resolve_okru

    QUERIES = ["Metropolis 1927", "Night of the Living Dead 1968"]
    PUBLIC_ID = "2116476930726"

    async def run(label):
        report = {
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "queries": [],
            "playback_verified": False,
        }
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            for query in QUERIES:
                provider = OKRuProvider(
                    DirectPublicSearch(client, PublicSearch(client))
                )
                try:
                    videos = await provider.search(query)
                    report["queries"].append(
                        {
                            "query": query,
                            "count": len(videos),
                            "with_duration": sum(
                                v.duration_seconds is not None for v in videos
                            ),
                            "ids": [v.id for v in videos],
                            "notice": provider.notice,
                            "more": provider.more,
                        }
                    )
                except ServiceError as exc:
                    report["queries"].append({"query": query, "error": str(exc)})
            reader = PublicMetadata(client)
            fields = await reader.fetch(PUBLIC_ID)
            report["public_url"] = {
                "url": f"https://ok.ru/video/{PUBLIC_ID}",
                "fields": fields,
                "notice": getattr(reader, "notice", ""),
            }
            identifiers = report["queries"][0].get("ids", [])[:1]
            report["additional_urls"] = []
            for identifier in identifiers:
                fields = await reader.fetch(identifier)
                card = (await OKRuProvider(None).get_video(identifier)).card()
                resolved = resolve_okru(card)
                report["additional_urls"].append(
                    {
                        "url": card["original_url"],
                        "metadata_fields": sorted(fields),
                        "title": fields.get("title"),
                        "duration_seconds": fields.get("duration_seconds"),
                        "embed_url": resolved["embed_url"],
                        "embedding_permission": "unknown",
                    }
                )
        output = (
            Path(__file__).resolve().parents[1] / "artifacts" / f"okru-{label}.json"
        )
        output.parent.mkdir(exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=True), flush=True)

    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("--label", choices=["before", "after"], required=True)
        asyncio.run(run(parser.parse_args().label))


if __name__ == "__main__":
    main()
