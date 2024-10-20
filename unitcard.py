import csv
import os
import re

from unidecode import unidecode
from PIL import Image, ImageDraw, ImageFont


# def showExceptionAndExit(exc_type, exc_value, tb):
# 	import traceback
# 	print()
# 	traceback.print_exception(exc_type, exc_value, tb)
# 	input("\nPress key to exit.")
# 	exit(-1)

def searchFilter(val):
	if type(val) == str:
		return val.replace("'", "").replace("-", "").replace(".", "").replace(" ", "")
	else:
		raise TypeError


def removeTags(s):
	return " ".join([x for x in s.split(" ") if x != '' and x[0] != '#'])


def initializeTable(**kwargs):
	ut, wt, cm = {}, {}, {}
	with open(os.path.join(os.getcwd(), kwargs["mod"], cpath)) as f:
		table = csv.DictReader(f, delimiter=',', quotechar='|')
		for row in table:
			if row["country"] in kwargs:
				cm.update({row["country"]: kwargs[row["country"]]})
			elif row["country"] == row["coalition"]:
				cm.update({row["country"]: row["country"]})
	firstline = True
	with open(os.path.join(os.getcwd(), kwargs["mod"], upath), "r", newline='', encoding='utf8') as f:
		table = csv.DictReader(f, delimiter=',', quotechar='|')
		for row in table:
			row.update({"": "", "\n": ""})
			if firstline:
				firstline = False
			else:
				row.update({"country": cm[row["country"]] if row["country"] in cm else row["country"]})
				row.update({"name": row["name"].replace("'", "")})
				ut.update({row["inst_num"]: row})
	firstline = True
	with open(os.path.join(os.getcwd(), kwargs["mod"], wpath), "r", newline='', encoding='utf8') as f:
		table = csv.DictReader(f, delimiter=',', quotechar='|')
		for row in table:
			if firstline:
				firstline = False
			else:
				wt.update({row["inst_num"]: row})
	return {"modname": kwargs["mod"], "ut": {u: ut[u] for u in sorted(list(ut.keys()))},
			"wt": {w: wt[w] for w in sorted(list(wt.keys()))}}


def createCard(unit, ut, wt, mod):
	uk, uv1, uv2 = [], [], []
	wk_len = 0
	uk_pos = round(fs * 0.8)  # base position for unit data keys (leftmost column)
	uv1_pos = uk_pos * 15  # position of the secondary/"middle" column of unit data valus (just for optics for now)
	uv2_pos = uk_pos * 22  # position of the main column of unit data values
	wk_pos = uv2_pos + (3 * uk_pos)  # position of the column of weapon data keys
	wv_offset = uk_pos * 11  # offset to apply to each successive column of weapon data values
	wv_base = wk_pos + round(1.75 * wv_offset)  # position of the first column of weapon data values
	ln_interval = round(uk_pos * 1.8)  # interval between each line in the data table
	vrt_offset = ln_interval * 6.5  # offset for the whole data table (excluding images and header)

	u = {x: unit[x] for x in unit}  # deep copy so that formatting and other args may be applied later

	specs = sorted(u["specs"].split("|"))
	avail = u["avail"].split("|")

	uk.extend(["availability", "", "maxCards", "isPrototype", "tab", "year", "specs"])
	uv2.extend([u["avail"], "", u["maxCards"], u["isPrototype"], u["tab"], u["year"]])

	if len(specs) < 4:
		uv2.append(", ".join(specs))
	elif len(specs) == 4:
		uv2.append(", ".join(specs[:2]))
	else:
		uv2.append(", ".join(specs[:3]))

	uk.extend(["armor", "", "HP", "damageToStun", "sizeModifier", "ecmModifier", "stealth", "OPTICS", "- ground",
			   "- heli", "- plane", "- ship", "MOVEMENT", "maxSpeed"])
	uv1.extend([""] * 14)
	uv1.extend(["range", u["opticRange_vsGround"] + "m", u["opticRange_vsHeli"] + "m",
				u["opticRange_vsPlane"] + "m", u["opticRange_vsShip"] + "m"])
	uv2.extend([u["armors"], "", u["HP"], u["damageToStun"],
				u["sizeModifier"], u["ecmModifier"], u["stealth"], "strength", u["opticStrength_vsGround"],
				u["opticStrength_vsAir"], "", u["opticStrength_vsShip"], u["movementType"], u["maxSpeed"]])

	if u["movementType"] != "plane":
		uk.append("isCV")
		uv2.append(u["isCV"])
	if u["movementType"] not in ("foot", "plane"):
		uk.append("isTransport")
		uv2.append(u["isTransport"])

	if u["transports"]:
		uk.append("transports")
		# uv2.append("")
		for t in u["transports"].split("|"):
			avail_reduced = False
			trsp_avail = ut[t]["avail"].split("|")
			for idx, i in enumerate(trsp_avail):
				if int(avail[idx]) > int(i):
					avail_reduced = True
					break
			uv2.append(f"{removeTags(ut[t]['name'])}{'*' if avail_reduced else ''}")
	# uk.append("")

	if u["transporterOf"]:
		units_transported = [f"{ut[t]['name']}" for t in u["transporterOf"].split("|")]
		uk.append("trspFor")
		for t in sorted(units_transported):
			uv2.append(removeTags(t))

	if u["movementType"] == "foot":
		uk.insert(21, "training")
		uv1.insert(21, "")
		uv2.insert(21, u["training"])
		uv2[20] += " km/h"
	elif u["movementType"] == "sailing":
		uv2[20] += " km/h"
		uk.insert(20, "sailingType")
		uv1.insert(20, "")
		uv2.insert(20, u["sailingSubType"])
		if u["autonomy"] == "supply":
			uk.insert(22, "supplyCapacity")
			uv1.insert(22, "")
			uv2.insert(22, f"{u['fuelCapacity']}L")
	else:
		uv2[20] += " km/h"
		if u["autonomy"] != "supply":
			uk.insert(21, "autonomy")
			uv2.insert(21, f"{u['autonomy']}s")
			uk.insert(21, "fuelCapacity")
		else:
			uk.insert(21, "supplyCapacity")
		uv1.insert(21, "")
		uv2.insert(21, u["fuelCapacity"] + "L")
		if u["movementType"] == "plane":
			uk[22] = "TOT"
			uk.insert(21, "turnRadius")
			uv1.insert(21, "")
			# uv2.insert(21, u["turnData"] + "m")
			uv2.insert(21, u["turnRadius"] + "m")
			uk.insert(21, "altitude")
			uv1.insert(21, "")
			uv2.insert(21, u["altitude"] + "m")
		elif u["movementType"] == "heli":
			uv1[15] = u["opticRangeAirborne_vsGround"] + "m"
			uk.insert(21, "verticalSpeed")
			uv1.insert(21, "")
			uv2.insert(21, u["verticalSpeed"] + " km/h")
			uk.insert(16, "  - whileLanded")
			uv1.insert(16, u["opticRange_vsGround"] + "m")
			uv2.insert(16, "")
		elif u["movementType"] in ("tracked", "wheeled"):
			uk.insert(21, "isAmphibious")
			uv1.insert(21, "")
			uv2.insert(21, u["isAmphibious"])
			# uk.insert(21, "turnRate")
			# uv1.insert(21, "")
			# uv2.insert(21, u["turnData"] + "  °/s")
			uk.insert(21, "roadSpeed")
			uv1.insert(21, "")
			uv2.insert(21, u["roadSpeed"] + " km/h")
		if u["opticStrengthSEAD_vsGround"]:
			x = 17 if uk[16] == "  - whileLanded" else 16
			uk.insert(x, "  - SEAD")
			uv1.insert(x, "")
			uv2.insert(x, u["opticStrengthSEAD_vsGround"])

	if len(specs) >= 4:
		uv2.insert(7, ", ".join(specs[(2 if len(specs) == 4 else 3):]))
		uk.insert(7, "")
		uv1.insert(7, "")

	uk.extend([""] * (len(uv2) - len(uk)))
	uv1.extend([""] * (len(uv2) - len(uv1)))

	W = uv2_pos + uk_pos

	wDatas = []
	if u["numWeapons"] != "0":  # replace with a variable for number of weapons
		for i in range(1, int(u["numWeapons"]) + 1):
			wData = {x: u[f"weapon{i}_{x}"] for x in
					 ["turret", "turretType", "turretSpeed", "turretFacing", "ammoPool", "totalAmmo"]}

			w = wt[u[f"weapon{i}_TAmmunition_ID"]]
			if wData["turretFacing"]:
				wData.update({"turretFacing": wData["turretFacing"] + "°"})
			if wData["turretSpeed"]:
				wData.update({"turretSpeed": wData["turretSpeed"] + " °/s"})
			wData.update({x: w[x] for x in ["supplyPerShot", "salvoLength", "simultShots"]})
			if wData["simultShots"] == "1":
				wData.update({"simultShots": ""})

			wData.update({x: f"{w[x]}s" if w[x] else "" for x in ["salvoReload", "shotReload", "aimTime"]})

			wData.update({"noiseMalus": w["noiseMalus"] if w["noiseMalus"] else "0",
						  "muzzleVelocity": f"{round(float(w['muzzleVelocity']))} m/s"})

			for x in ["rangeGround", "rangeHeli", "rangePlane", "rangeShip", "rangeDef"]:
				if w[f"max{x}"]:
					maxR = w[f"max{x}"] + "m"
					minR = (w[f"min{x}"] + " - ") if w[f"min{x}"] else ""
				else:
					maxR, minR = "", ""
				wData.update({x: minR + maxR})
			wData.update({"accuracy": f"{round(float(w['accuracy']) * 100)}%" if w["accuracy"] else ""})
			wData.update({"stabilizer": f"{round(float(w['stabilizer']) * 100)}%" if (
						u[f"weapon{i}_hasStab"] and "stabilizer" in u and u["stabilizer"]) else ""})
			wData.update({"dispersionAngle": w["dispersionAngle"] + "°"})
			if w["dispersionMax"]:
				maxD = w["dispersionMax"]
				minD = (w["dispersionMin"] + " - ") if w["dispersionMin"] not in (maxD, "") else ""
			else:
				maxD, minD = "", ""
			wData.update({"dispersionRadius": minD + maxD})

			if mod != "vanilla":
				wData.update({"corrShotMultiplier": w["corrShotMultiplier"]})

			wData.update({x: w[x] for x in ["isKEorHEAT", "AP", "HE", "suppress"]})

			wData.update({x: f"{w[x]}m" if w[x] else "" for x in
						  ["radiusDamage", "radiusSuppress", "radiusNapalm", "radiusSmoke"]})

			wData.update({x: w[x] for x in ["isRadar", "isMissile", "isSEAD", "isFireAndForget"]})

			wData.update({"missileAcceleration": f"{round(float(w['missileAcceleration']))} m/s²" if w[
				"missileAcceleration"] else ""})
			wData.update(
				{"missileSpeedMax": f"{round(float(w['missileSpeedMax']))} m/s" if w["missileSpeedMax"] else ""})
			wData.update(
				{"missileCorrInterval": f"{w['missileCorrInterval']}s" if w["missileCorrInterval"] else ""})

			wData.update({"name": w["name"], "typeArme": w["typeArme"]})
			if wData["typeArme"] == "Main Gun":
				if int(wData["salvoLength"]) > 1:
					if wData["salvoLength"] == wData["totalAmmo"]:
						wData["typeArme"] += " [AUTO]"
					else:
						wData["typeArme"] += " [BRST]"
				else:
					wData["typeArme"] += " [MAN]"
			wDatas.append(wData)
		wk_len = len(wDatas[0])
		W = wv_base + (wv_offset * (len(wDatas) - 1)) + uk_pos

	H = int(vrt_offset + (ln_interval * (max(wk_len, len(uv2)) - 2)))

	# flags made custom
	hfs = 3 * fs
	hf = round(1.25 * hfs)
	wf = round(5 / 3 * hf)
	header_font = ImageFont.truetype(fontb, hfs)
	# header_font.set_variation_by_name(header_font.get_variation_names()[-1])

	imeasure = Image.new('RGB', (W, H), '#ABCDEF')
	drawmeasure = ImageDraw.Draw(imeasure)
	header_width = round(header_font.getlength(removeTags(u["name"])))

	drawmeasure.text((W - uk_pos, hf / 2), u["cost"], font=header_font, fill="#FFB200", anchor="rm")
	wc = round(header_font.getlength(u["cost"]))

	# adjust_size = False
	while header_width > (W - wf - wc - (6 * uk_pos)) and hfs > 2 * fs:
		hfs *= 0.9
		header_font = ImageFont.truetype(fontb, hfs)
		# header_font.set_variation_by_name(header_font.get_variation_names()[-1])
		header_width = round(header_font.getlength(removeTags(u["name"])))
	if header_width > (W - wf - wc - (6 * uk_pos)):
		W = header_width + wf + wc + (6 * uk_pos)

	image = Image.new('RGB', (W, H), '#111111')  # 36393E - discord gray
	draw = ImageDraw.Draw(image)
	flag = None
	if mod and os.path.isfile(os.path.join(os.getcwd(), "flags", mod, f"{u['country']}.png")):
		flag = Image.open(os.path.join(os.getcwd(), "flags", mod, f"{u['country']}.png"))
	elif os.path.isfile(os.path.join(os.getcwd(), "flags", f"{u['country']}.png")):
		flag = Image.open(os.path.join(os.getcwd(), "flags", f"{u['country']}.png"))
	if flag:
		Image.Image.paste(image, flag.resize((wf, round(0.6 * wf))), (0, 0))

	draw.text((((W + wf - wc) / 2), hf / 2), removeTags(u["name"]), font=header_font, fill="#FFFFFF", anchor="mm")

	header_font = ImageFont.truetype(fontb, 3 * fs)
	# header_font.set_variation_by_name(header_font.get_variation_names()[-1])
	draw.text((W - uk_pos, hf / 2), u["cost"], font=header_font, fill="#FFB200", anchor="rm")

	for idx, i in enumerate(uk):
		fillColor = "#FFFFFF" if i == "OPTICS" else "#DDDDDD"
		vpos = vrt_offset + (ln_interval * (idx - 2))
		try:
			draw.text((uv1_pos, vpos), uv1[idx], font=dataFont, fill=fillColor, anchor="rm")
		except IndexError:
			pass  # dont care didnt ask
		if i in ("availability", "armor"):
			hpos = uv2_pos - round(fs / 1.25)
			if i == "armor":
				labels = ("T", "R", "S", "F")
				vals = u["armors"].split("|")
			else:
				labels = ("EL", "VT", "HD", "TR", "RK")
				vals = avail
			for jdx, j in enumerate(reversed(vals)):
				draw.text((hpos, vpos), labels[jdx], font=dataFont, fill="#FFFFFF", anchor="mm")
				draw.text((hpos, vpos + ln_interval), j, font=dataFont, fill="#DDDDDD", anchor="mm")
				hpos -= (3 if i == "armor" else 2.5) * uk_pos
			vpos += ln_interval / 2
		elif i == "- heli":
			draw.text((uv2_pos, vpos + (ln_interval / 2)), uv2[idx], font=dataFont, fill=fillColor, anchor="rm")
		else:
			draw.text((uv2_pos, vpos), uv2[idx], font=dataFont, fill=fillColor, anchor="rm")
		draw.text((uk_pos, vpos), i, font=dataFont, fill="#FFFFFF", anchor="lm")
	for idx, i in enumerate(wDatas):
		for jdx, j in enumerate(i):
			hpos = wv_base + (wv_offset * idx)
			fillColor = "#DDDDDD"
			anchor = "rm"
			font_to_use = dataFont
			vpos = vrt_offset + (ln_interval * jdx)
			if j in ("name", "typeArme"):  # weapon name/type
				anchor = "mm"
				vpos = vrt_offset - (1.25 * ln_interval)
				hpos -= (wv_offset / 2.25)
				curr_fs = 1.3 * fs
				if j == "name":  # weapon name specifically
					curr_fs = 1.5 * fs
					font_to_use = ImageFont.truetype(fontb, curr_fs)
					# font_to_use.set_variation_by_name(font_to_use.get_variation_names()[-1])
					fillColor = "#FFFFFF"
					vpos -= 1.15 * ln_interval
				width = font_to_use.getlength(i[j])
				while width > (wv_offset * 0.9):
					curr_fs *= 0.9
					font_to_use = ImageFont.truetype(font, curr_fs)
					if j == "name":
						font_to_use = ImageFont.truetype(fontb, curr_fs)
					# font_to_use.set_variation_by_name(font_to_use.get_variation_names()[-1])
					width = font_to_use.getlength(i[j])
			elif idx == 0:
				draw.text((wk_pos, vpos), j, font=font_to_use, fill="#FFFFFF", anchor="lm")
			draw.text((hpos, vpos), i[j], font=font_to_use, fill=fillColor, anchor=anchor)
	return image


def getUnitcard(search_arg, **kwargs):
	ut = kwargs["mod"]["ut"]
	search_arg = unidecode(searchFilter(search_arg)).upper().replace("9K111", "FAGOT").replace("FUGOT", "FAGOT")
	search_list = list(search_arg)
	matches = {}
	res = []
	# get all possible matches
	search_regex = ".*".join(search_list)
	for u in ut:
		to_match = unidecode(" ".join([searchFilter(ut[u]["name"]), ut[u]["country"], ut[u]["tab"]])).upper()
		if u not in matches and re.search(search_regex, to_match):
			matches.update({to_match: u})
	c = len(search_list)
	# then grab results in the desired order from within the initial match set
	while len(matches) > len(res) < 6 and c:
		search_regex = "".join(["^"] + search_list)  # prioritize match at start of word over elsewhere
		for m in sorted(list(matches.keys())):
			if matches[m] not in res and re.search(search_regex, m):
				res.append(matches[m])
		search_regex = "".join(search_list)
		for m in sorted(list(matches.keys())):
			if matches[m] not in res and re.search(search_regex, m):
				res.append(matches[m])
		search_list.insert(c, ".*")
		c -= 1
	if res:
		if ut[res[0]]["training"] and len(res) > 1:
			for yr in ("85", "90", "95"):  # attempt to force infantry 75 variant as
				if yr in ut[res[0]]["name"]:
					if yr not in search_arg and ut[res[0]]["name"].strip(f" {yr}") == ut[res[1]]["name"]:
						temp = res[0]
						res[0] = res[1]
						res[1] = temp
					break
		unit = ut[res[0]]
		if len(res) > 6:  # 5 entries max, replace the 6th entry with ... to indicate more than 5 search results
			res = res[:6]
		for rdx, r in enumerate(res):
			if rdx == 5:
				r2 = "..."
			else:
				r2 = [ut[r]["name"], f"({ut[r]['country']},", f"{ut[r]['tab']})"]
				if rdx == 0:
					r2[0] = f"**{r2[0]}**"
				r2 = " ".join(r2).replace("FAGOT", "9K111")
			res[rdx] = r2
		img = createCard(unit, ut, kwargs["mod"]["wt"], kwargs["mod"]["modname"])
		return res, img
	else:
		return None, None


fs = 25  # font size - changing this will scale the entire image accordingly
font = os.path.join(os.getcwd(), "fonts", "Roboto-Medium.ttf")
fontb = os.path.join(os.getcwd(), "fonts", "Roboto-Bold.ttf")
# fonti = os.path.join(os.getcwd(), "fonts", "Roboto-Bold.ttf")

dataFont = ImageFont.truetype(font, fs)
# dataFont.set_variation_by_name(dataFont.get_variation_names()[-2])

upath = "unitData_formatted.csv"
wpath = "weaponData_formatted.csv"
cpath = "countryData_formatted.csv"
