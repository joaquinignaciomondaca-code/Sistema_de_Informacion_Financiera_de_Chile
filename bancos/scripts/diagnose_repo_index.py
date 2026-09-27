"""Diagnóstico acotado de rótulos del índice CMF; nunca descarga ZIP ni publica."""
from bancos.scripts import probe_repos_zip_cmf as probe
import urllib.parse


def main():
    html = probe.read_public(probe.INDEX, 4_000_000).decode("utf-8", errors="replace")
    parser = probe.ZipLinks()
    parser.feed(html)
    matches = []
    for link in parser.links:
        url = urllib.parse.urljoin(probe.INDEX, link.get("href", ""))
        if not probe.trusted_zip(url):
            continue
        context = probe.context_for(parser.stream, link)
        resolved = probe.period_of(link, parser.stream)
        if (resolved and resolved[0] == "2020-03") or "marzo 2020" in context.lower():
            matches.append({"ruta": urllib.parse.urlsplit(url).path,
                            "texto": probe.clean(link["texto"])[:100],
                            "atributos": probe.clean(link["atributos"])[:100],
                            "contexto": context[:180], "periodo": resolved})
    conflicts = set()
    result = probe.discover(html, strict=False, conflicts_out=conflicts)
    print(f"::notice title=CMF marzo 2020 diagnóstico::candidatos={matches} "
          f"conflictos={sorted(conflicts)} indice={result.get('2020-03')}")


if __name__ == "__main__":
    main()
