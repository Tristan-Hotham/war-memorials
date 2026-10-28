# How many names on your war memorial?

How many First World War names does each community's war memorial carry, and how heavy is that for the size of the place? Every memorial in the Imperial War Museums' War Memorials Register, counted place by place, with the Thankful Villages as the far tail.

**Interactive version:** https://tristan-hotham.github.io/war-memorials/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23727151

A data study by Dr Tristan Hotham (Independent researcher), published for Remembrance 2026. It pairs with the earlier study [Thankful Villages: luck or size?](https://tristan-hotham.github.io/thankful-villages/) (https://doi.org/10.5281/zenodo.23676168).

## Headline results

- The register (retrieved 28 October 2026) holds 111,532 memorials; 76,160 commemorate the First World War.
- Summed over every memorial, the First World War names of the dead total 2,496,396: about 3.4 for each of the roughly 744,000 dead and missing from the British Isles. The same man is named on village, church, school, workplace and regimental memorials.
- Taking one community memorial per place (17,967 places, 14,119 with a First World War count) brings the total to 727,184, 3.3 times fewer.
- For 6,108 villages and small towns of 100 to 5,000 residents with an exact count, the median memorial carries 18.3 names per 1,000 residents today (middle half 10.7 to 30.0).
- Rates fall steeply with modern size (38.4 per 1,000 in places of 100 to 199 people, 9.7 in places of 2,000 to 5,000) and are highest in Scotland (30.0) and lowest in Wales (12.0).
- For 181 places with a 1911 census figure in Wikidata, the median is 29.9 names per 1,000 residents of 1911, about twice the national rate of 16.4.
- Only 36 of the 6,108 small places have a community record with no dead; 8 of those are Thankful Villages. A further 61 small places hold only a roll of those who served: leads to check, not new Thankful Villages.
- On memorials with exact counts for both wars, the median ratio of Second to First World War names is 0.32.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page (map, charts, tables, "find your memorial" search). Place data is embedded; the memorial search list is loaded from `data/memorials_search.json`. |
| `header.png` | Social card (1200 by 630). |
| `data/places.csv` | One row per place (17,967): location, county and nation, number of memorials, the chosen community memorial for each war (register id, title, names of the dead, served, exact flag), the summed names over all memorials, the Wikidata population match and names per 1,000 residents, Thankful Village flags. |
| `data/memorials.csv` | One row per memorial (59,031), except memorials to one named person: id, title, town, county, nation, coordinates, lost flag, types, my class, First and Second World War counts. Links: https://www.iwm.org.uk/memorials/item/memorial/ followed by the id. |
| `data/thankful_villages.csv` | The 55 Thankful Villages from the earlier study and what the register holds at each. |
| `data/memorials_search.json` | Compact list of the published memorials for the page's search. |
| `data/results.json` | Every number used anywhere. |
| `data/coast_ne10m.json` | Natural Earth 1:10m land for the British Isles (public domain), for the header and figures. |
| `code/01_prepare.py` | Reads the register extract, picks each memorial's current location, extracts the war counts, classes each memorial, adds county and nation from OS Open Names. |
| `code/02_places.py` | Groups memorials into places, picks one community memorial per place and war, matches a Wikidata population, matches the Thankful Villages. |
| `code/03_analyse.py` | All statistics; writes `results.json`, the page's map data and the search file. |
| `code/04_build_site.py` | Fills `code/page_template.html` to make `index.html`. |
| `code/05_header.py` | Renders `header.png` with Playwright. |
| `code/06_figures.py` | Static figures for the paper and blog. |
| `code/07_paper.py` | Builds the paper PDF from `code/paper_template.tex` with xelatex. |
| `code/08_release.py` | Blog post, blog and Zenodo metadata, Zenodo folder. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Names of the dead.** The register's "died" count; where neither died nor served is given but there are names, the number of names. A memorial listing only men who served is a roll of service, with no dead.
- **Kinds of memorial.** Each memorial gets one class from its types and title by keyword rules: to one person (gravestone additions, serviceman figures, a single name, titles starting with a rank or initials), military (units, ships, squadrons, aircraft crashes, veterans), regional (county, national, clan), school, workplace (firms, railways, banks, Post Office, police, clubs, lodges, societies), church (churches, chapels, congregations, windows and fittings) and community (the rest). The place's own name is removed from the title first, so "St Ives War Memorial" is not read as a church. The rules are simple and will misfile some memorials.
- **Places.** Memorials with the same normalised town name within 6 km of each other (single linkage). A place sits at the median of its memorials.
- **The double-counting rule.** Memorials are never added together. For each place and war I take the community memorial with the most names of the dead; if no community memorial records any dead, the church memorial with the most; a roll of service only when nothing at the place records any dead. Memorials to one person, military, regional, school and workplace memorials are never chosen.
- **Population proxy (flagged everywhere).** A Wikidata settlement with the same name within 5 km, preferring civil parishes and Welsh communities. The figure is modern (mostly 2011 or 2021 census), not 1911. Rates use places of 100 to 5,000 residents with an exact count. Places that have grown since 1911 look as if they lost few men, places that have shrunk as if they lost many. A check uses the 181 places with a 1911 figure in Wikidata.
- **National benchmark.** 744,000 dead and missing from the British Isles over a population of 45.4 million (Wikipedia, "World War I casualties"): 16.4 per 1,000.
- **Thankful Villages.** The 55 villages and coordinates from the earlier study (Wikipedia list), matched to places by name within 6 km (allowing word order and near spellings) or by a memorial title naming the village within 1.5 km.

## Known limits

- The register is volunteer-built and incomplete; many memorials have no count, and some counts are rounded or miscoded (Nether Kellet's church board is coded with 21 dead, the same as the 21 who served).
- Town names in the register vary (a parish, village, suburb or descriptive location), so a "place" may be a parish, a village or part of a town.
- Modern populations are a weak proxy for 1911. Scottish and Welsh rates are affected by depopulation and by the size of the units that Wikidata gives populations for.
- No names of the dead are used or published. Titles of memorials to one named person are withheld; they count only in the totals.

## How to rerun

The register extract (`iwm_memorials.json.gz`, from the register's JSON:API at wmr.iwm.org.uk/jsonapi), OS Open Names (`osnames_gb.tsv`, compact) and the Wikidata settlement populations are read from paths given at the top of each script. Clone the earlier study into `work/`:

```
git clone https://github.com/Tristan-Hotham/thankful-villages work/thankful-villages
python3 code/01_prepare.py path/to/iwm_memorials.json.gz
python3 code/02_places.py
python3 code/03_analyse.py
python3 code/04_build_site.py
FONT_DIR=path/to/fonts python3 code/05_header.py
FONT_DIR=path/to/fonts python3 code/06_figures.py
python3 code/07_paper.py
python3 code/08_release.py
```

Needs Python 3 with pandas, numpy, scipy, matplotlib and playwright, and xelatex with TeX Gyre Pagella and Inter for the paper.

## Sources and licences

- Memorials: Imperial War Museums, War Memorials Register, https://www.iwm.org.uk/memorials, reused for non-commercial research with credit.
- Populations: Wikidata (CC0), via QLever.
- County and nation: OS Open Names, contains OS data © Crown copyright and database right 2026 (Open Government Licence v3.0).
- National casualty figure and the Thankful Villages list: English Wikipedia, "World War I casualties" and "Thankful Villages" (CC BY-SA 4.0); the list via https://github.com/Tristan-Hotham/thankful-villages.
- Coastline: Natural Earth (public domain). Base map tiles © Esri.

Because the register is reused on non-commercial terms, the derived data (`data/`) and the text of the page and paper are released under CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/). The code (`code/`) is released under the MIT licence (see `LICENSE`).

## Citation

Hotham, T. (2026) How Many Names on Your War Memorial? Counting the First World War Dead Place by Place in the War Memorials Register. Zenodo. https://doi.org/10.5281/zenodo.23727151

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
