#Bot.py
# ======================================================================================
#                                           DEPS
# ======================================================================================

from discord.utils import DISCORD_EPOCH
import youtube_dl
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
from dotenv import load_dotenv
import asyncio
import nacl
import time
import os
import random

load_dotenv()
bot = commands.Bot(command_prefix=".")

async def on_ready():
    print ("Ready")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# ======================================================================================
#                                       YOUTUBE-DL
# ======================================================================================


youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
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
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

# ======================================================================================
#                                          AUDIO LOOP
# ======================================================================================

vc = None
loopActive = False
urlQueue = []
repeatSong = False
stopFlag = False

def audioLoop(voice_channel):
    global loopActive
    global urlQueue
    global repeatSong
    global stopFlag

    if stopFlag or len(urlQueue) == 0:
        loopActive = False
        return
    
    if not repeatSong:
        urlQueue.pop(0)
        if len(urlQueue) == 0:
            loopActive = False
            return

    loopActive = True
    voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=urlQueue[0]),
                            after = lambda e: audioLoop(voice_channel))
    

# ======================================================================================
#                                           COMMANDS
# ======================================================================================

# if bot is not connected use this function to connect it to voice chat
async def autoJoin(ctx):
    global vc
    if vc == None:
        voice_channel = ctx.author.voice.channel
        channel = None
        if voice_channel != None:
            channel = voice_channel.name
            vc = await voice_channel.connect()

@bot.command(name='join', pass_context=True, help='Invite DJ to the Party')
async def join(ctx):
    await autoJoin(ctx)


@bot.command(name='play', help='Add song from url to queue or add all matching already downloaded tracks by given name', aliases=['p'])
async def play(ctx,url): 
    await autoJoin(ctx)

    try :
        global loopActive
        global urlQueue
        global repeatSong
        global stopFlag

        voice_channel = ctx.message.guild.voice_client
        filename = []
        # if URL to song, download it
        if len(url) > 5 and url[0:5] == "https":
            filename = [await YTDLSource.from_url(url, loop=bot.loop)]
        # if name, find all mathing files
        else: 
            url = url.lower()
            files = os.listdir()
            for f in files:
                if isFileNameValid(f) and url in f.lower():
                    filename.append(f)
        
        # empty song skipped automatically on play
        if not loopActive:
            urlQueue.append("Dummy")

        urlQueue.extend(filename)

        # if not playing begin the audio loop
        if not loopActive:
            audioLoop(voice_channel)
    except:
        await ctx.send("Error")

def isFileNameValid(n):
    #exclude .py files, .part and .env files
    #rest of files are assumed to be valid music files
    return  n[-1] != "y" and n[-1] != "t" and n != ".env"

# toggle repeat
@bot.command(name='repeat', help='Toggle the repeat of the song')
async def repeat(ctx):
    global repeatSong
    repeatSong = not repeatSong
    await ctx.send("Repeat set to: "+str(repeatSong))

# simple skip
@bot.command(name='skip', help='Skip song', aliases=['fs', 'forceskip'])
async def skip(ctx):
    global urlQueue

    if repeatSong:
        urlQueue.pop(0)

    await ctx.message.guild.voice_client.stop()

@bot.command(name='lss', help='Lists downloaded songs')
async def lss(ctx):
    files = os.listdir()
    composed = ""
    for f in files:
        if isFileNameValid(f):
            composed = composed + f + "\n"
    await ctx.send(composed)

@bot.command(name='prd', help='Play all downloaded songs in random order')
async def prd(ctx):
    await autoJoin(ctx)

    files = os.listdir()
    composed = []
    for f in files:
        if isFileNameValid(f): 
            composed.append(f)
    global loopActive
    global urlQueue
    if not loopActive:
        urlQueue.append("Dummy")
        urlQueue.extend(random.sample(composed, len(composed)))
        audioLoop(ctx.message.guild.voice_client)
    else:
        urlQueue.extend(random.sample(composed, len(composed)))


@bot.command(name='leave', help='Leaves the VC')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        global stopFlag
        stopFlag = True
        await voice_client.stop()
        stopFlag = False
    global vc
    vc = None
    await voice_client.disconnect()

# if bot gets DM-ed it tries to download a song from url
@bot.event
async def on_message(message: discord.Message):
    if message.guild is None and not message.author.bot:
        filename = await YTDLSource.from_url(message.content, loop=bot.loop)
        await message.channel.send('Downloaded')
        #print(message.content)
    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
