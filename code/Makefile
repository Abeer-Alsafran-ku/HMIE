
nonoverlapLoc:
	python3 nonoverlap_locations.py /Users/abeer/Library/CloudStorage/GoogleDrive-3beeral9afran@gmail.com/My\ Drive/sample_6RR/images overlaps.json /Users/abeer/Downloads/geoTags_6RR.csv
plotLocations:
	python3 plot_locations.py non_overlapping_locations.json
simhash:
	python3 simhash_dedupe.py /Users/abeer/Library/CloudStorage/GoogleDrive-3beeral9afran@gmail.com/My\ Drive/sample_6RR/images --threshold $(t) --output overlaps.json
