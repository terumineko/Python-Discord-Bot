#Credits to Sophie shoutout to my lovely wife for helping me with the code
#more features will be added soon

import discord
import asyncio
from discord.ext import commands, tasks
from discord.utils import get
import youtube_dl
from random import choice
intents = discord.Intents.default()
intents.members = True
youtube_dl.utils.bug_reports_message = lambda: ''

client = commands.Bot(command_prefix='*', intents=intents)
status = ["ur mum", "Despacito", "with cute anime girls!"]
music_queue = []

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@client.event
async def on_ready():
    change_status.start()
    print("online")

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}! Use `*help` command for details!')

@client.command(name='ping', help='This command returns the latency')
async def ping(ctx):
    await ctx.send(f'Latency: {round(client.latency * 1000)}ms')

@client.command(name='join', help='Watame will join the voice channel you are connected to')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        if not is_connected(ctx):
            channel = ctx.message.author.voice.channel
            await channel.connect()
            await ctx.send(f"Connected to **{ctx.message.author.voice.channel.name}**")
        else:
            await ctx.send(f"I'm already connected to **{ctx.message.guild.voice_client.channel.name}**")

@client.command(name='leave', help='Watame leaves the voice channel')
async def leave(ctx):
    if ctx.message.author.voice:
        if is_connected(ctx):
            playing.stop()
            voice_channel = ctx.message.guild.voice_client
            if voice_channel.is_playing():
                voice_channel.stop()
            music_queue.clear()
            await voice_channel.disconnect()
            await ctx.send('**Goodbye** :wave:')
        else:
            await ctx.send('I am not connected to a voice channel')

    else:
        await ctx.send('You are not connected to a voice channel')

@tasks.loop(seconds=20)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))

@client.command(name='pause', help='Pauses the current song')
async def pause(ctx):
    if not ctx.message.author.voice:
        await ctx.send('You are not connected to a voice channel')
    else:
        if is_connected(ctx):
            voice_channel = ctx.message.guild.voice_client
            if ctx.message.author.voice.channel == ctx.message.guild.voice_client.channel:
                if voice_channel.is_playing():
                    voice_channel.pause()
                    await ctx.send('**Paused** :play_pause:')
                elif voice_channel.is_paused:
                    await ctx.send('Already paused')
                else:
                    await ctx.send('Nothing is currently playing')
            else:
                await ctx.send("I'm not connected to your voice channel")
        else:
            await ctx.send("I'm not connected to a voice channel")

@client.command(name='resume', help='Resumes the current song')
async def resume(ctx):
    if not ctx.message.author.voice:
        await ctx.send('You are not connected to a voice channel')
    else:
        if is_connected(ctx):
            voice_channel = ctx.message.guild.voice_client
            if ctx.message.author.voice.channel == ctx.message.guild.voice_client.channel:
                if voice_channel.is_paused():
                    voice_channel.resume()
                    await ctx.send('**Resumed** :arrow_forward:')
                elif voice_channel.is_playing():
                    await ctx.send('Already playing')
                else:
                    await ctx.send('Nothing is currently playing')
            else:
                await ctx.send("I'm not connected to your voice channel")
        else:
            await ctx.send("I'm not connected to a voice channel")

@client.command(name='stop', help='Stops the current song')
async def stop(ctx):
    if not ctx.message.author.voice:
        await ctx.send('You are not connected to a voice channel')
    else:
        if is_connected(ctx):
            voice_channel = ctx.message.guild.voice_client
            if ctx.message.author.voice.channel == ctx.message.guild.voice_client.channel:
                if voice_channel.is_playing():
                    voice_channel.stop()
                    await ctx.send('**Stopped** :stop_button:')
                else:
                    await ctx.send('Nothing is currently playing')
            else:
                await ctx.send("I'm not connected to your voice channel")
        else:
            await ctx.send("I'm not connected to a voice channel")

def is_connected(ctx):
    voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()

@client.command(name="hello", help="Watame will greet you")
async def greeting(ctx):
    responses = ["Hey!", "***grumble*** Why did you wake me up?", "How can I help?", "I'm busy getting this bread", "Go away greasy gamer"]
    await ctx.send(choice(responses))

@client.command(name='hode', help='Hode')
async def hode(ctx):
    hod = ['hode?', 'hode...', 'HODEEE!' ]
    await ctx.send(choice(hod))

@client.command(name="play", help="Play url song")
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
    else:
        if len(music_queue) < 20:
            channel = ctx.message.author.voice.channel

            if not is_connected(ctx):
                await channel.connect()
                await ctx.send(f"Connected to **{ctx.message.author.voice.channel.name}**")

            server = ctx.message.guild
            voice_channel = server.voice_client
            if channel == voice_channel.channel:
                async with ctx.typing():
                    try:
                        if len(music_queue) == 0:
                            player = await YTDLSource.from_url(url, loop=client.loop)
                            music_queue.append(player)
                            voice_channel.play(music_queue[0])
                            playing.start(ctx)
                            await ctx.send(f"**Now playing:** {player.title} :notes:")

                        elif len(music_queue) >= 20:
                            await ctx.send("The queue is full")

                        else:
                            player = await YTDLSource.from_url(url, loop=client.loop)
                            music_queue.append(player)
                            await ctx.send(f"**{player.title}** has been added to the queue")

                    except:
                        await ctx.send("Invalid URL")
            else:
                await ctx.send("I'm not connected to your voice channel")

@client.command(name="skip", help="Skip the current song")
async def skip(ctx):
    if not ctx.message.author.voice:
        await ctx.send('You are not connected to a voice channel')
    else:
        if is_connected(ctx):
            voice_channel = ctx.message.guild.voice_client.channel
            if ctx.message.author.voice.channel == ctx.message.guild.voice_client.channel:
                voice_channel.stop()
                await next(ctx)
            else:
                await ctx.send("I'm not connected to your voice channel")
        else:
            await ctx.send("I'm not connected to a voice channel")

@client.command(name="clear", help="Clear the queue")
async def clear(ctx):
    if not ctx.message.author.voice:
        await ctx.send('You are not connected to a voice channel')
    else:
        if is_connected(ctx):
            if ctx.message.author.voice.channel == ctx.message.guild.voice_client.channel:
                if len(music_queue) > 0 and len(music_queue) <= 20:
                    music_queue.clear()
                    await ctx.send ('**Cleared** :wastebasket:')
                else:
                    await ctx.send ('The queue is already empty')
            else:
                await ctx.send("I'm not connected to your voice channel")
        else:
            await ctx.send("I'm not connected to a voice channel")

@client.command(name='queue', help='Show the queue')
async def queue(ctx):
    length = len(music_queue)
    i = 0
    if len(music_queue) > 0 and len(music_queue) <= 20:
        while i < length:
            await ctx.send(f"{i + 1}: {music_queue[i].title}")
            i = i + 1
    else:
        await ctx.send('The queue is empty')


@client.command(name='np', help='Shows the current song')
async def np(ctx):
    voice_channel = ctx.message.guild.voice_client
    if voice_channel.is_playing():
        await ctx.send(f'**Currently playing:** {music_queue[0].title} :notes:')
    else:
        await ctx.send('Nothing is curretly being played')

async def next(ctx):
    if len(music_queue) > 1:
        music_queue.pop(0)
        server = ctx.message.guild
        voice_channel = server.voice_client
        voice_channel.play(music_queue[0])
        await ctx.send(f"**Now playing:** {music_queue[0].title} :notes:")
    elif len(music_queue) == 0:
        if ctx.message.guild.voice_client.is_playing():
            await ctx.send("Queue empty")
    else:
        music_queue.pop(0)
        playing.stop()

@tasks.loop(seconds=2)
async def playing(ctx):
    try:
        if not ctx.message.guild.voice_client.is_playing() and not ctx.message.guild.voice_client.is_paused():
            await next(ctx)
    except:
        print('Unexpected stop')

client.run("bot key")