import json
import os
import discord
from discord import app_commands

import convertDeckCode_backup
from initializeTables import initializeTables
from convertDeckCode import convertDeckCode
import unitcard


class myClient(discord.Client):
	def __init__(self):
		super().__init__(intents=discord.Intents.all())
		self.synced = False

	async def on_ready(self):
		await self.wait_until_ready()
		if not self.synced:
			await tree.sync(guild=discord.Object(id=1090841670574166276))
			self.synced = True
		print("-------------------------------------------------------------------------\nbatbot is online")

# async def on_command_error(ctx, error):
# 	if isinstance(error, .CommandNotFound):
# 		sender = ctx.message.author.name
# 		command_ = ctx.message.content.split(' ')[0]
# 		server = ctx.message.guild.id
# 		if server in server_id_to_name:
# 			server = server_id_to_name[server]
# 		print(f"User '{sender}' attempted to invoke non-existent command '{command_}' in server '{server}'")
# 	else:
# 		raise error


with open("config.json") as json_file:
	config = json.load(json_file)

server_id_to_name, available_commands_by_server = {}, {}

for server_id in config["SERVERS"]:
	if server_id.isdigit():
		server_id_to_name.update({int(server_id): config["SERVERS"][server_id][0]})
		if len(config["SERVERS"][server_id]) > 1:
			available_commands_by_server.update({config["SERVERS"][server_id][0]: config["SERVERS"][server_id][1:]})
		else:
			available_commands_by_server.update({config["SERVERS"][server_id][0]: []})

privileged_users = {int(user_id) for user_id in config["USERS"]}

command_descriptions = {
	"listservers": "Returns a list of IDs of servers/guilds the bot is present within.",
	"convert": "Converts a REDFOR deck code for a both-factions nation to a BLUFOR deck code, and vice versa, for compatible nations in the server's affiliated WG:RD mod.",
	"unit": "Returns the statcard for a unit in image form.",
	"bat": "Returns an emoji representation of a flying mammal."
}

mod_tables = {m: initializeTables(mod=m, renames=config["MODS"][m]) for m in config["MODS"]}

# for mod in mod_tables:
# 	print(mod)
# 	print(mod_tables[mod]["pu"])

# mod_tables = {
# 	"vanilla": initializeTables(mod="vanilla", DAN="DEN", RFA="GER", JAP="JPN", ROK="SK", HOL="NL", RDA="DDR",
# 										URSS="USSR", TCH="CZ"),
# 	"bwc": initializeTables(mod="bwc", DAN="IR", RFA="GER", ROK="SK", URSS="RU", TCH="ALG", FIN="IND", JAP="JPN"),
# 	"1991": ""  # unitcard.initializeTable(mod="1991", CAN="SP") <- add vanilla args
# }

# creates the client
client = myClient()
tree = app_commands.CommandTree(client)


def commandAvailableInServer(ctx):
	if ctx.message.guild.id in server_id_to_name:
		server = server_id_to_name[ctx.message.guild.id]
		if server in available_commands_by_server and str(ctx.command) in available_commands_by_server[server]:
			return True
		else:
			print(f"User '{ctx.message.author.name}' attempted to invoke command '!{ctx.command}' in server '{server}'")
	else:
		print(f"Server '{ctx.message.guild.id}' not recognized")
	return False


def privilegedUser(itc):
	return True if itc.user.id in privileged_users else False


@tree.command(name="listservers",
			  description="Allows privileged users to print this bot's joined servers to the bot console",
			  guilds=[discord.Object(id=int(x)) for x in server_id_to_name])
async def listServers(itc: discord.Interaction):
	if privilegedUser(itc):
		print(client.guilds)
		await itc.response.send_message("Printed server list to console", ephemeral=True)  # noqa
	else:
		await itc.response.send_message("You do not have access to this command", ephemeral=True)  # noqa


@tree.command(name="bat",
			  description="Returns an emoji depicting a flying mammal",
			  guilds=[discord.Object(id=int(x)) for x in server_id_to_name if
					  "unit" in available_commands_by_server[server_id_to_name[x]]])
async def batEmoji(itc: discord.Interaction):
	await itc.response.send_message(":bat:")  # noqa


@tree.command(name="help",
			  guilds=[discord.Object(id=int(x)) for x in server_id_to_name if
					  server_id_to_name[x] in available_commands_by_server])
async def showHelp(itc: discord.Interaction):
	cmds = []
	for cmd in available_commands_by_server[server_id_to_name[itc.guild_id]]:
		if cmd in command_descriptions:
			cmds.append(f"/{cmd}: {command_descriptions[cmd]}")
		else:
			cmds.append(f"/{cmd}: No description for this command yet")
	await itc.response.send_message("```" + "\n\n".join(cmds) + "```", ephemeral=True)  # noqa


@tree.command(name="convert",
			  description="Converts applicable deckcodes from REDFOR to BLUFOR",
			  guilds=[discord.Object(id=int(x)) for x in server_id_to_name if
					  "convert" in available_commands_by_server[server_id_to_name[x]]])
@app_commands.choices(mod=[app_commands.Choice(name=mod, value=mod) for mod in mod_tables if mod_tables[mod]["pu"]])
async def convert(itc: discord.Interaction, code: str, mod: app_commands.Choice[str]):
	if code == "@" or not code.startswith("@"):
		await itc.response.send_message("Invalid or no deckcode provided")  # noqa
	msg = convertDeckCode(code, mod_tables[mod.value]["ct"], mod_tables[mod.value]["pu"])
	await itc.response.send_message(msg[0], ephemeral=(msg[1]))  # noqa


@tree.command(name="unit",
			  description="Searches for a unit by name and returns an image displaying that unit's stats.",
			  guilds=[discord.Object(id=int(x)) for x in server_id_to_name if
					  "unit" in available_commands_by_server[server_id_to_name[x]]])
@app_commands.choices(mod=[app_commands.Choice(name=x, value=x) for x in mod_tables])
async def getUnit(itc: discord.Interaction, main_search: str, mod: app_commands.Choice[str] | None):
	# await itc.response.defer(ephemeral=True)  # noqa
	kwargs = {"tables": mod_tables["vanilla"]}
	if mod:
		kwargs.update({"tables": mod_tables[mod.value]})
	res, img = unitcard.getUnitcard(main_search, **kwargs)
	if res and img:
		fn = f'unit.png'
		img.save(fn, "PNG")
		img = discord.File(fn)
		# await ctx.message.add_reaction('✅')
		await itc.response.send_message(file=img, content=("   " + "\n".join(res)))  # noqa
		# os.remove(fn)
	else:
		await itc.response.send_message(f"Unable to find unit named {main_search}", ephemeral=True)  # noqa


DISCORD_TOKEN = config["TOKEN"]
client.run(DISCORD_TOKEN)
