import os
import csv


def initializeTables(mod, renames):
	ut, wt, ct, cm, pu = {}, {}, {}, {}, {}
	# ut, wt, ct - tables
	# cm - map old country tags to new ones as defined in kwargs
	# pu - purplefor units; parse now to avoid parsing later
	# print(renames)
	with open(os.path.join(os.getcwd(), mod, cpath)) as f:
		table = csv.DictReader(f, delimiter=',', quotechar='|')
		for row in table:
			if row["coalition"] in renames:
				row.update({"coalition": renames[row["coalition"]]})
			coalition_countries = row["country/ies"]
			for cc in coalition_countries.split("|"):
				if cc in renames:
					coalition_countries = coalition_countries.replace(cc, renames[cc])
			row.update({"coalition": coalition_countries})
			ct.update({row["coalition"]: row})
	firstline = True
	with open(os.path.join(os.getcwd(), mod, upath), "r", newline='', encoding='utf8') as f:
		table = csv.DictReader(f, delimiter=',', quotechar='|')
		for row in table:
			row.update({"": "", "\n": ""})
			if firstline:
				firstline = False
			else:
				if row["purple"] == "true":
					pu.update({row["otanId"]: row["pactId"]})
				row.update({"country": renames[row["country"]] if row["country"] in renames else row["country"]})
				row.update({"name": row["name"].replace("'", "")})
				ut.update({row["inst_num"]: row})
	firstline = True
	with open(os.path.join(os.getcwd(), mod, wpath), "r", newline='', encoding='utf8') as f:
		table = csv.DictReader(f, delimiter=',', quotechar='|')
		for row in table:
			if firstline:
				firstline = False
			else:
				wt.update({row["inst_num"]: row})
	ret = {
		"mod": mod,
		"ut": {u: ut[u] for u in sorted(list(ut.keys()))},
		"wt": {w: wt[w] for w in sorted(list(wt.keys()))},
		"ct": {c: ct[c] for c in sorted(list(ct.keys()))},
		"pu": pu
	}
	return ret


upath = "unitData_formatted.csv"
wpath = "weaponData_formatted.csv"
cpath = "countryData_formatted.csv"
