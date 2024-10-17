from bitstring import BitArray
import base64


def convertDeckCode(parg, server):
	if server == "WG1991":
		countries_nato, countries_pact, nato_specials, pact_specials = countries_nato_1991, countries_pact_1991, nato_specials_1991, pact_specials_1991
	elif server in ("Blitzwar Community", "Testing server"):
		countries_nato, countries_pact, nato_specials, pact_specials = countries_nato_bwc, countries_pact_bwc, nato_specials_bwc, pact_specials_bwc
	else:
		return False, "Convert command has not been initialized for this server."
	t = str(parg).split(" ")[0]
	if not t.startswith("@") or t == "@":
		return False, "Invalid or no deckcode provided"
	iCode = BitArray(bytes=base64.b64decode(t.strip("@").encode("ascii"))).bin  # strip leading @, convert to bits
	# begin parsing the data
	redfor = int(iCode[0:2], 2)  # if nation is redfor or not
	nation = int(iCode[2:7], 2)  # nation val stored as integer
	# coalition = iCode[7:12]  # coalition cant change sides, is always same val for nat deck
	# finish validation here and initialize output string
	if nation >= max(len(countries_nato), len(countries_pact)):
		# if the nation code matches the non-national deck value
		return False, "Can only convert national decks from valid nations"
	elif redfor and countries_pact[nation] in countries_nato:
		# initialize deckstring as blufor, the country's blufor code, and non-coalition
		iCodeReadable = ["00", bin(nation).removeprefix("0b").zfill(5)]  # testing output
		oCodeHeader = "00" + bin(countries_nato.index(countries_pact[nation])).removeprefix("0b").zfill(5)
		oCodeReadable = ["00",
						 bin(countries_nato.index(countries_pact[nation])).removeprefix("0b").zfill(5)]
		nation = countries_pact[nation]
		ifac = "REDFOR :red_square:"
		ofac = "BLUFOR :blue_square:"
	elif not redfor and countries_nato[nation] in countries_pact:
		# initialize deckstring as redfor, the country's redfor code, and non-coalition
		iCodeReadable = ["01", bin(nation).removeprefix("0b").zfill(5)]
		oCodeHeader = "01" + bin(countries_pact.index(countries_nato[nation])).removeprefix("0b").zfill(5)
		oCodeReadable = ["00",
						 bin(countries_pact.index(countries_nato[nation])).removeprefix("0b").zfill(5)]
		nation = countries_nato[nation]
		ifac = "BLUFOR :blue_square:"
		ofac = "REDFOR :red_square:"
	else:
		if redfor:
			return False, "Cannot convert " + countries_pact[nation].split(' ')[0] + " to BLUFOR!"
		else:
			return False, "Cannot convert " + countries_nato[nation].split(' ')[0] + " to REDFOR!"
	oCodeHeader += iCode[7:17]  # spec, era remain unchanged
	# number of double transport cards
	num2Tcards = int(iCode[17:21], 2)  # can convert to int straight away since this num doesn't change
	num2Tcards_o = num2Tcards
	end2Tcards = 26 + (36 * num2Tcards)
	code2Tcards = iCode[26:end2Tcards]
	# number of single transport cards
	num1Tcards = int(iCode[21:26], 2)
	num1Tcards_o = num1Tcards
	end1Tcards = end2Tcards + (25 * num1Tcards)
	code1Tcards = iCode[end2Tcards:end1Tcards]
	# rest of the cards
	codeOtherCards = iCode[end1Tcards:]
	numOtherCards = int(len(codeOtherCards) / 14)
	numOtherCards_o = numOtherCards
	# not appending the card number counts to the output for now: must re-evaluate after its checked
	oCode = ""  # initialize separate var for the card section itself - will be merged at the end
	iCodeReadable.extend([iCode[7:12], iCode[12:15], iCode[15:17], iCode[17:21], iCode[21:26], "|"])
	oCodeReadable.extend([iCode[7:12], iCode[12:15], iCode[15:17], iCode[17:21], iCode[21:26], "|"])

	for i in range(num2Tcards):  # iterate over the double transport cards
		skip = False  # used to skip the card if it is invalid
		# isolate the block of bits to evaluate for each card in this category (36)
		card = code2Tcards[36 * i:36 * (i + 1)]
		# save the veterancy for rebuilding the new deckstring
		translated_card = card[0:3]
		# isolate the ID for the unit and the two transports
		# convert the ID to an integer
		card = [int(card[3:14], 2), int(card[14:25], 2), int(card[25:36], 2)]
		iCodeReadable.extend([card[0:3], card[3:14], card[14:25], card[25:36]])
		oCodeReadable.append(card[0:3])
		for unit in card:  # evaluate each unit
			if redfor:
				if unit in pact_specials:  # if special case, lookup corresponding value
					translated_card += bin(nato_specials[pact_specials.index(unit)]).removeprefix(
						"0b").zfill(11)
					oCodeReadable.append(
						bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11))
				elif 795 < unit < 978:  # otherwise, if in normal range, calc by add/subtract
					translated_card += bin(unit + 322).removeprefix("0b").zfill(11)
					oCodeReadable.append(bin(unit + 322).removeprefix("0b").zfill(11))
				elif 771 < unit < 776:  # finnish T-55s are separate for some reason
					translated_card += bin(unit + 342).removeprefix("0b").zfill(11)
					oCodeReadable.append(bin(unit + 342).removeprefix("0b").zfill(11))
				else:  # if unit is not found: either an unhandled special case, or a blufor boat
					skip = True
					num2Tcards_o -= 1
					break
			else:
				if unit in nato_specials:
					translated_card += bin(pact_specials[nato_specials.index(unit)]).removeprefix(
						"0b").zfill(11)
					oCodeReadable.append(
						bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11))
				elif 1117 < unit < 1300:
					translated_card += bin(unit - 322).removeprefix("0b").zfill(11)
					oCodeReadable.append(bin(unit - 322).removeprefix("0b").zfill(11))
				elif 1113 < unit < 1118:
					translated_card += bin(unit - 342).removeprefix("0b").zfill(11)
					oCodeReadable.append(bin(unit - 342).removeprefix("0b").zfill(11))
				else:
					skip = True
					num2Tcards_o -= 1
					break
		if not skip:
			oCode += translated_card

	iCodeReadable.append("|")
	oCodeReadable.append("|")

	for i in range(num1Tcards):  # Iterate over the single transport cards
		# isolate the block of bits to evaluate for each card in this category (25)
		# this code is more or less identical to the above for-loop
		skip = False
		card = code1Tcards[25 * i:25 * (i + 1)]
		translated_card = card[0:3]
		card = [int(card[3:14], 2), int(card[14:25], 2)]
		iCodeReadable.extend([card[0:3], card[3:14], card[14:25]])
		oCodeReadable.append(card[0:3])
		for unit in card:
			if redfor:
				if unit in pact_specials:
					translated_card += bin(nato_specials[pact_specials.index(unit)]).removeprefix(
						"0b").zfill(11)
					oCodeReadable.append(
						bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11))
				elif 795 < unit < 978:
					translated_card += bin(unit + 322).removeprefix("0b").zfill(11)
					oCodeReadable.append(bin(unit + 322).removeprefix("0b").zfill(11))
				elif 771 < unit < 776:
					translated_card += bin(unit + 341).removeprefix("0b").zfill(11)
					oCodeReadable.append(bin(unit + 341).removeprefix("0b").zfill(11))
				else:
					skip = True
					num1Tcards_o -= 1
					break
			else:
				if unit in nato_specials:
					translated_card += bin(pact_specials[nato_specials.index(unit)]).removeprefix(
						"0b").zfill(11)
					oCodeReadable.append(
						bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11))
				elif 1113 < unit < 1118:
					translated_card += bin(unit - 341).removeprefix("0b").zfill(11)
					oCodeReadable.append(bin(unit - 341).removeprefix("0b").zfill(11))
				elif 1117 < unit < 1300:
					translated_card += bin(unit - 322).removeprefix("0b").zfill(11)
					oCodeReadable.append(bin(unit - 322).removeprefix("0b").zfill(11))
				else:
					skip = True
					num1Tcards_o -= 1
					break
		if not skip:
			oCode += translated_card

	iCodeReadable.append("|")
	oCodeReadable.append("|")

	# iterate over the rest of the cards
	for i in range(numOtherCards):
		skip = False
		# isolate the block of bits to evaluate for each card in this category (14)
		# this code is more or less identical to the above for-loop, except only one unit, so no inner loop
		card = codeOtherCards[14 * i:14 * (i + 1)]
		translated_card = card[0:3]
		unit = int(card[3:14], 2)
		iCodeReadable.extend([card[0:3], card[3:14]])
		oCodeReadable.append(card[0:3])
		if redfor:
			if unit in pact_specials:  # if special case, lookup corresponding value
				translated_card += bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(
					11)
				oCodeReadable.append(
					bin(nato_specials[pact_specials.index(unit)]).removeprefix("0b").zfill(11))
			elif 795 < unit < 978:  # otherwise, if in normal range, calc by add/subtract
				translated_card += bin(unit + 322).removeprefix("0b").zfill(11)
				oCodeReadable.append(bin(unit + 322).removeprefix("0b").zfill(11))
			elif 771 < unit < 776:  # finnish T-55s are separate for some reason
				translated_card += bin(unit + 341).removeprefix("0b").zfill(11)
				oCodeReadable.append(bin(unit + 341).removeprefix("0b").zfill(11))
			else:
				numOtherCards_o -= 1
				skip = True
		else:
			if unit in nato_specials:
				translated_card += bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(
					11)
				oCodeReadable.append(
					bin(pact_specials[nato_specials.index(unit)]).removeprefix("0b").zfill(11))
			elif 1113 < unit < 1118:
				translated_card += bin(unit - 341).removeprefix("0b").zfill(11)
				oCodeReadable.append(bin(unit - 341).removeprefix("0b").zfill(11))
			elif 1117 < unit < 1300:
				translated_card += bin(unit - 322).removeprefix("0b").zfill(11)
				oCodeReadable.append(bin(unit - 322).removeprefix("0b").zfill(11))
			else:
				numOtherCards_o -= 1
				skip = True
		if not skip:
			oCode += translated_card
	# now that new number of cards in 2T and 1T is known, append
	oCodeHeader += bin(num2Tcards_o).removeprefix("0b").zfill(4) + bin(num1Tcards_o).removeprefix("0b").zfill(5)
	oCode = oCodeHeader + oCode
	# log if any cards were removed in the process
	diff = num2Tcards + num1Tcards + numOtherCards - num2Tcards_o - num1Tcards_o - numOtherCards_o
	if diff:
		diff = f"\n{diff} invalid card{' was' if diff == 1 else 's were'} removed"
	else:
		diff = ""
	# lastly, need to re-encode the deck binary into base 64
	o_deckstring = base64.b64encode(BitArray(bin=oCode).tobytes())  # re-encode into base64
	o_deckstring = "@" + str(o_deckstring).strip("b\'")  # clean up formatting
	return True, f"Converted {ifac.split(' ')[0]} {nation.split(' ')[0]} to {ofac.split(' ')[0]} ({nation.split(' ')[1]}{ifac.split(' ')[1]}:right_arrow:{ofac.split(' ')[1]}) {diff}\n{o_deckstring}"


# list of countries on each side; None corresponds to cancelled neutral nations, which have codepoints assigned to them
# on that faction but are not playable on that faction (e.g. vanilla: redfor sweden, blufor finland)
# list is in order of display in TShowRoomDeckSerializer - binary value of index corresponds to that stored in deckcode

# vanilla
countries_nato_vanilla = ["USA :flag_us:", "United Kingdom :flag_gb:", "France :flag_fr:", "West Germany :flag_de:",
						  "Canada :flag_ca:", "Denmark :flag_dk:", "Sweden :flag_se:", "Norway :flag_no:",
						  "ANZAC :flag_au::flag_nz:", "Japan :flag_jp:", "South Korea :flag_kr:",
						  "Netherlands :flag_nl:", "Israel :flag_il:", None, None,
						  "South Africa <:flag_xz:1296533707255058473>"]
countries_pact_vanilla = ["East Germany <:flag_ddr:1296533693640478741>", "USSR <:flag_su:1296533718856634489>",
						  "Poland :flag_pl:", "Czechoslovakia :flag_cz:", "China :flag_cn:", "North Korea :flag_kp:",
						  "Finland :flag_fi:", "Yugoslavia <:flag_yu:1296533731095351326>", None]

# 1991
countries_nato_1991 = ["USA :flag_us:", "United Kingdom :flag_gb:", "France :flag_fr:", "West Germany :flag_de:",
					   "Denmark :flag_dk:", "Sweden :flag_se:", "Norway :flag_no:",
					   "ANZMYS :flag_au::flag_nz::flag_sg::flag_my:", "Japan :flag_jp:", "South Korea :flag_kr:",
					   "Benelux :flag_be::flag_nl::flag_lu:", "Israel :flag_il:", "Finland :flag_fi:",
					   "Yugoslavia <:flag_yu:1296533731095351326>"]
countries_pact_1991 = ["East Germany <:flag_ddr:1296533693640478741>", "USSR <:flag_su:1296533718856634489>",
					   "Poland :flag_pl:", "Czechoslovakia :flag_cz:", "China :flag_cn:", "North Korea :flag_kp:",
					   "Finland :flag_fi:", "Yugoslavia <:flag_yu:1296533731095351326>", None,
					   "South-pact :flag_hu::flag_ro::flag_bg:"]
# BWC-mod
countries_nato_bwc = ["United States :flag_us:", "United Kingdom :flag_gb:", "France :flag_fr:", "Germany :flag_de:",
					  "TBD [Canada]", "TBD [Sweden]", "TBD [Norway]", "TBD [ANZAC]", "Japan :flag_jp:",
					  "South Korea :flag_kr:", ":flag_ca::flag_nl:", "Israel :flag_il:", "SILF :flag_it::flag_es:",
					  "India :flag_in:", "Poland :flag_pl:"]
countries_pact_bwc = ["Iran :flag_ir:", "India :flag_in:", "Serbia :flag_rs:", "Pakistan :flag_pk:", "Russia :flag_ru:",
					  "Poland :flag_pl:", "Algeria :flag_dz:", "China :flag_cn:", "North Korea :flag_kp:"]

# corresponding IDs for units on both sides which do not follow regular order
# names are of the original instance and do not necessarily match in-game names

# 1991
# in order: RIMa, BTR-50PK, BVP-2 Vz.86, MAZ-543 Newa-SC, OT-810D
nato_specials_1991 = [433, 1301, 1302, 1303, 1304]
pact_specials_1991 = [987, 92, 658, 669, 674]
# BWC-mod
# first 4 are finnish t55 acting up for some reason
# in order: sturmpioniere 18658, ka27plp 19366, mi2 lsk 19403, mi24 lsk 19411, mi25 nk 19415, f5b nk 19621, il102 19638,
# mig21pfm 19675, mig23m 19696, mig25p 19699, md500 scout 19385, lcm8 19251
nato_specials_bwc = [1114, 1115, 1116, 1117, 1396, 1397, 1398, 1399, 1400, 1401, 1402, 1403, 1404, 1405, 640, 573]
pact_specials_bwc = [772, 773, 774, 775, 228, 463, 484, 490, 494, 536, 539, 553, 571, 574, 988, 991]
