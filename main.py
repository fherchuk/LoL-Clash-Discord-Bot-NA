import discord
from dotenv import load_dotenv
import os
from discord.ext import commands
import embed_generator
from game_info import ClashTournament
import riot_api
from datetime import datetime


def main():
    load_dotenv()
    intents = discord.Intents.all()
    intents.members = True
    intents.presences = True
    intents.guilds = True
    intents.messages = True

    bot = commands.Bot(command_prefix='!', intents=intents)
    riot_client = riot_api.RiotAPI(os.getenv('RIOT_TOKEN'))

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        await bot.change_presence(status=discord.Status.online, activity=discord.Game("League of Legends"))

    @bot.command()
    async def level(ctx, *, arg):
        arg = meCheck(ctx, arg)
        summoner = await riot_client.get_summoner_by_name(arg)
        if(summoner["status_code"] == 200):
            await ctx.send(f'{summoner["name"]} is level {summoner["summonerLevel"]}')
        else:
            await ctx.send(f'Summoner {arg} doesn\'t exsit!')

    @bot.command(aliases=['last', 'm', 'l'])
    async def match(ctx, *, arg):
        arg = meCheck(ctx, arg)
        id = arg.split(" ")[-1]
        isNumber = True
        for c in id:
            if(c < "0" or c > "9"):
                isNumber = False
        if(not isNumber):
            id = 1
        summoner_name = ""
        for i in arg.split(" ")[:-1]:
            summoner_name += i
        if(not isNumber):
            summoner_name = arg
        summoner = await riot_client.get_summoner_by_name(summoner_name)
        if(summoner["status_code"] != 200):
            await ctx.send(f"Summoner {arg} doesn't exist!")
            return
        if(int(id) > 100 or int(id) < 1):
            await ctx.send(f"You can only see your last 100 matches!")
            return
        match_info = await riot_client.get_recent_match_info(summoner["name"], int(id)-1)
        if(match_info == None):
            await ctx.send(f"Match not found!")
            return
        embed = await embed_generator.generate_match_embed(match_info, summoner["name"])
        await ctx.send(embed=embed)

    @bot.command(aliases=['player', 'rank', 'user', 'p', 'r', 'u'])
    async def profile(ctx, *, arg):
        arg = meCheck(ctx, arg)
        data = await riot_client.get_profile_info(arg)
        if(data["status_code"] != 200):
            await ctx.send(f"Summoner {arg} doesn't exist!")
            return
        user = data["user"]
        embed = await embed_generator.generate_user_embed(user)
        await ctx.send(embed=embed)
    


    @bot.command(aliases=['matches', 'h'])
    async def history(ctx, *, arg):
        arg = meCheck(ctx, arg)
        count = arg.split(" ")[-1]
        isNumber = True
        for c in count:
            if(c < "0" or c > "9"):
                isNumber = False
        if(not isNumber or int(count) <= 0 or int(count) > 20):
            count = 5
            summoner_name = arg
        else:
            summoner_name = ""
            for i in arg.split(" ")[:-1]:
                summoner_name += i
        data = await riot_client.get_recent_matches_infos(summoner_name, int(count))
        if (len(data[0]) <= 0):
            await ctx.send(f"Summoner {arg} doesn't exist, you can only see your last 20 games")
            return
        embed = await embed_generator.generate_history_embed(data)
        await ctx.send(embed=embed)

    @bot.command(aliases=['clash', 'c'])
    async def clash_lookup(ctx, *, arg):
        users = []
        arg = meCheck(ctx, arg)
        teamId = await riot_client.get_team_id(arg)
        if teamId == False:
            await ctx.send(f"Clash Team for {arg} not Found!")
        else:
            teamData = await riot_client.get_clash_team(teamId)
            for i in range(len(teamData['players'])):
                teamData['players'][i]['summonerId'] = await riot_client.get_name_from_id(teamData['players'][i]['summonerId'])
                data = await riot_client.get_profile_info(teamData['players'][i]['summonerId'])
                users.append(data['user'])
            embed = await embed_generator.generate_clash_embed(teamData, users)
            await ctx.send(embed=embed)
            for i in range(len(users)):
                embed = await embed_generator.generate_user_embed(users[i])
                await ctx.send(embed=embed)

    
    @bot.command(aliases=['schedule', 'register'])
    async def clash_schedule(ctx, arg: int=None):
        est = 0
        schedule = await riot_client.get_clash_schedule()
        print(f"current time: {datetime.now()}")
        for i in schedule:
            phase = i['schedule']
            print(phase[0]['registrationTime'] - est)
            regTime = datetime.fromtimestamp((phase[0]['registrationTime'] - est)/1000)
            start = datetime.fromtimestamp((phase[0]['startTime'] - est)/1000)
            tournament = ClashTournament(i['id'], i['themeId'], i['nameKey'], i['nameKeySecondary'],phase[0]['id'], regTime, start, phase[0]['cancelled'] )
            print(f"Upcomming Tournament: {tournament.clashId}")
            print(f"Starts on: {tournament.registrationTime} EST")
    bot.run(os.environ.get('DISCORD_TOKEN'))



def meCheck(ctx, arg):
    if (arg == "me"):
        return ctx.author.display_name
    return arg

def unpack(args, **kwargs):
    for key, value in kwargs.items():
        if key == 'schedule':
            print(value["cancelled"])
        else:
            args.append(value)
    return args

def convert(lst):
    res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
    return res_dct


if __name__ == "__main__":
    main()

