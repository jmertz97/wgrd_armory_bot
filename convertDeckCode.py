from bitstring import BitArray
import base64


def convertDeckCode(code, ct, valid_units):  # valid units corresponds to 'pu'
	# for c in ct:
	# 	print(c)
	# 	print(ct[c]["faction"])
	# 	print(ct[c]["otanId"])
	# 	print(ct[c]["pactId"])
	# 	print()
	# 	print()
	countries_nato = {ct[c]["otanId"]: c for c in ct if "OTAN" in ct[c]["faction"] and "|" not in ct[c]["country/ies"]}
	countries_pact = {ct[c]["pactId"]: c for c in ct if "PACT" in ct[c]["faction"] and "|" not in ct[c]["country/ies"]}

	# assume valid mod - handle mod validation in main
	valid_countries = {ct[c]["otanId"]: ct[c]["pactId"] for c in ct if ct[c]["otanId"] and ct[c]["pactId"]}
	iCode = BitArray(bytes=base64.b64decode(code.strip("@").encode("ascii"))).bin  # strip leading @, convert to bits

	# begin parsing the data
	redfor = int(iCode[0:2], 2)  # if nation is redfor or not

	print(redfor)
	print(bool(redfor))

	country = int(iCode[2:7], 2)  # nation val stored as integer
	if redfor:
		valid_countries = {v: k for k, v in valid_countries.items()}
		valid_units = {v: k for k, v in valid_units.items()}

	# coalition = iCode[7:12]  # coalition cant change sides, is always same val for nat deck
	# finish validation here and initialize output string
	if country >= max(len(countries_nato), len(countries_pact)):
		# if the nation code matches the non-national deck value
		return "Can only convert national decks from valid nations"
	elif str(country) in valid_countries:
		iCodeReadable = ["00" if redfor else "01", bin(country).removeprefix("0b").zfill(5)]  # testing output
		oCodeHeader = ("00" if redfor else "01") + bin(int(valid_countries[str(country)])).removeprefix("0b").zfill(5)
		oCodeReadable = ["00" if redfor else "01", bin(int(valid_countries[str(country)])).removeprefix("0b").zfill(5)]
		country = countries_pact[str(country)] if redfor else countries_nato[str(country)]  # get name by index
		# ifac = "REDFOR :red_square:"
		# ofac = "BLUFOR :blue_square:"
		ifac = "Redfor" if redfor else "Blufor"
		ofac = "Blufor" if redfor else "Redfor"
	else:
		if redfor:
			return f"Cannot convert {countries_pact[str(country)]} to BLUFOR!"
		else:
			return f"Cannot convert {countries_nato[str(country)]} to REDFOR!"

	print(oCodeHeader)

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

	# all_units_found = []

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
			# print("unit:", unit)
			# all_units_found.append(str(unit))
			if str(unit) in valid_units:
				translated_card += bin(int(valid_units[str(unit)])).removeprefix("0b").zfill(11)
				oCodeReadable.append(bin(int(valid_units[str(unit)])).removeprefix("0b").zfill(11))
				# print(unit)
				# print(valid_units[str(unit)])
			else:  # if unit is not found: either an unhandled special case, or a blufor boat
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
			# print("unit:", unit)
			# all_units_found.append(str(unit))
			if str(unit) in valid_units:
				translated_card += bin(int(valid_units[str(unit)])).removeprefix("0b").zfill(11)
				oCodeReadable.append(bin(int(valid_units[str(unit)])).removeprefix("0b").zfill(11))
				# print(unit)
				# print(valid_units[str(unit)])
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
		# isolate the block of bits to evaluate for each card in this category (14)
		# this code is more or less identical to the above for-loop, except only one unit, so no inner loop
		card = codeOtherCards[14 * i:14 * (i + 1)]
		translated_card = card[0:3]
		unit = int(card[3:14], 2)

		# print("unit:", unit)
		# all_units_found.append(str(unit))

		iCodeReadable.extend([card[0:3], card[3:14]])
		oCodeReadable.append(card[0:3])
		if str(unit) in valid_units:
			translated_card += bin(int(valid_units[str(unit)])).removeprefix("0b").zfill(11)
			oCodeReadable.append(bin(int(valid_units[str(unit)])).removeprefix("0b").zfill(11))
			# print(unit)
			# print(valid_units[str(unit)])
			oCode += translated_card
		else:
			numOtherCards_o -= 1

	# print(", ".join(["units found"] + all_units_found))

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

	output = f"Converted {ifac} {country} to {ofac} {diff}\n{o_deckstring}"
	# output += f"({country.split(' ')[1]}{ifac.split(' ')[1]}:right_arrow:{ofac.split(' ')[1]}) "
	return output
