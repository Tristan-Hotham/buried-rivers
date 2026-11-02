## Title

[OC] London's buried rivers: 228 km of the city's mapped waterways run in culverts and tunnels. The Tyburn, which flows under Buckingham Palace, is 100% underground

## Body

I mapped every river, stream, canal, drain and ditch OpenStreetMap records inside Greater London (1,297 km) and split it into what flows in the open and what is tagged as a culvert or tunnel: 17.6%, about one kilometre in 6. Small streams suffered most (30% buried), while big rivers like the Thames, Lea and Wandle stayed mostly open. The famous lost rivers are almost wholly underground: the Tyburn 100%, the Westbourne (which crosses Sloane Square tube station in a pipe) 99%, the Fleet (of Fleet Street) 93%. The longest buried course is actually the Moselle Brook in Tottenham, 15.7 km. Leaving out the Thames, inner London has buried 37% of its waterways, outer London 16%. Caveat: OSM is a volunteer map, and 5 lost rivers (Hackney Brook, the Peck, Earl's Sluice, Stamford Brook, Falcon Brook) now survive only as sewers and are not mapped as waterways at all, so the real buried total is higher. Interactive map with every river's story: https://maps.tristanhotham.com/buried-rivers/

## Source comment

Source: OpenStreetMap waterways (waterway=river, stream, canal, drain, ditch), (c) OpenStreetMap contributors, ODbL, via the Overpass API. Buried = tunnel=culvert/yes/covered/pipe, covered=yes, location=underground or negative layer. Lengths are haversine lengths after clipping to Greater London (Natural Earth boroughs). River histories: English Wikipedia (CC BY-SA 4.0).

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: https://maps.tristanhotham.com/buried-rivers/
Paper: https://doi.org/10.5281/zenodo.23873535
Blog post: https://blog.tristanhotham.com/2026/10/31/buried-rivers/
