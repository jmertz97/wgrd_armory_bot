import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

import unitcard
from convertDeckCode import convertDeckCode

server_id_to_name = {  # map Server Names to server IDs
	304436901165662209: "Bootcamp",
	330318123964039190: "WG1991",
	811338519141810257: "Unofficial Patch",
	903614488928997438: "Annihilation",
	951544203530350622: "Blitzwar Community",
	1056769011779641355: "Asia In Conflict",
	1090841670574166276: "Testing server",
	1123483010671591558: "Redder Dragoner",
}  # TODO: store server permissions data in separate file, or dynamically populate upon running

available_commands_by_server = {
	"Testing server": ["listservers", "bat" "unit"],
	"WG1991": [],
	"Blitzwar Community": ["convert"],
}  # add to this as the bot is added to more servers

command_descriptions = {
	"listservers": "Returns a list of IDs of servers/guilds the bot is present within.",
	"convert": "Converts a REDFOR deck code for a both-factions nation to a BLUFOR deck code, and vice versa, for compatible nations in the server's affiliated WG:RD mod.",
	"unit": "Returns the statcard for a unit in image form."
}

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# sets intents for the bot
intents = discord.Intents.all()

# creates the client
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command("help")

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
			print(f"User '{ctx.message.author.name}' attempted to invoke !{ctx.command} command in server '{server}'")
	else:
		print(f"Server '{ctx}' not recognized")
	return False


@bot.event
async def on_ready():
	print("-------------------------------------------------------------------------\nbatbot is online")


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
async def showHelp(self, ctx):
	if ctx.message.guild.id in available_commands_by_server:
		for cmd in available_commands_by_server[ctx.message.guild.id]:
			print(f"!{cmd}: {command_descriptions[cmd]}")


@bot.command(name="convert")
async def convertDeckcode(ctx, arg=None):
	if commandAvailableInServer(ctx):
		if not arg or arg == "\n":
			# await ctx.message.add_reaction('❌')
			return
		# await ctx.message.add_reaction('✅')
		convertDeckCode(arg, server_id_to_name[ctx.message.guild.id])
		await ctx.reply()


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
