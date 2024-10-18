import json
import discord
import os

from discord.ext import commands

import unitcard
from convertDeckCode import convertDeckCode

with open("config.json") as json_file:
	config = json.load(json_file)

DISCORD_TOKEN = config["TOKEN"]

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

# sets intents for the bot
intents = discord.Intents.all()

# creates the client
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
# bot.remove_command("help")

mod_tables = {
	"vanilla": unitcard.initializeTable(mod="vanilla", DAN="DEN", RFA="GER", JAP="JPN", ROK="SK", HOL="NL", RDA="DDR",
										URSS="USSR", TCH="CZ"),
	"bwc": unitcard.initializeTable(mod="bwc", DAN="IR", RFA="GER", ROK="SK", URSS="RU", TCH="ALG", FIN="IND",
									JAP="JPN"),
	"1991": ""  # unitcard.initializeTable(mod="1991", CAN="SP") <- add vanilla args
}


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


def privilegedUser(ctx):
	return True if ctx.message.author.id in privileged_users else False


@bot.event
async def on_ready():
	print("-------------------------------------------------------------------------\nbatbot is online")


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		sender = ctx.message.author.name
		command_ = ctx.message.content.split(' ')[0]
		server = ctx.message.guild.id
		if server in server_id_to_name:
			server = server_id_to_name[server]
		print(f"User '{sender}' attempted to invoke non-existent command '{command_}' in server '{server}'")
	else:
		raise error


@bot.command(name="listservers")
async def listServers(ctx):
	if commandAvailableInServer(ctx):
		print(bot.guilds)
		await ctx.send("printed server list to console")


@bot.command(name="bat")
async def batEmoji(ctx):
	if commandAvailableInServer(ctx):
		await ctx.send(":bat:")


@bot.command(name="help")
async def showHelp(ctx, *argv):
	if server_id_to_name[ctx.message.guild.id] in available_commands_by_server:
		if argv and argv[0] in available_commands_by_server[server_id_to_name[ctx.message.guild.id]]:
			if argv[0] in command_descriptions:
				await ctx.send(command_descriptions[argv[0]])
			else:
				await ctx.send("No description for this command yet")
		else:
			cmds = []
			for cmd in available_commands_by_server[server_id_to_name[ctx.message.guild.id]]:
				if cmd in command_descriptions:
					cmds.append(f"!{cmd}: {command_descriptions[cmd]}")
				else:
					cmds.append(f"!{cmd}: No description for this command yet")
			await ctx.send("```" + "\n\n".join(cmds) + "```")


@bot.command(name="convert")
async def convertDeckcode(ctx, arg=None):
	if commandAvailableInServer(ctx):
		if not arg or arg == "\n":
			# await ctx.message.add_reaction('❌')
			return
		# await ctx.message.add_reaction('✅')
		await ctx.reply(convertDeckCode(arg, server_id_to_name[ctx.message.guild.id])[1])


@bot.command(name="unit")
async def getUnit(ctx, *argv):
	if commandAvailableInServer(ctx):
		kwargs = {"mod": "vanilla"}
		main_search = ""
		add_to_search_string = True
		for idx, arg in enumerate(argv):
			if arg.startswith("-"):
				if add_to_search_string:
					add_to_search_string = False
				if arg[1:] in mod_tables:
					kwargs.update({"mod": arg[1:]})
				elif arg[1:] in kwargs and len(argv) > idx + 1:
					kwargs.update({arg[1:]: argv[idx + 1]})
			elif add_to_search_string:
				main_search += " " + arg
		main_search = main_search.strip(" ")
		kwargs.update({"mod": mod_tables[kwargs["mod"]]})
		res, img = unitcard.getUnitcard(main_search, **kwargs)
		if res and img:
			fn = f'unit.png'
			img.save(fn, "PNG")
			img = discord.File(fn)
			# await ctx.message.add_reaction('✅')
			await ctx.reply(file=img, content=("   " + "\n".join(res)))
			os.remove(fn)
		else:
			await ctx.message.add_reaction('❌')


bot.run(DISCORD_TOKEN)
