import discord
from discord.ext import commands, tasks
import youtube_dl

TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
YOUTUBE_PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PL0L_zzLQSZ2WaWjtrObXM9jPep3d45d8H'

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)

ytdl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch',
    'quiet': True,
}
ytdl = youtube_dl.YoutubeDL(ytdl_options)

# Extracts playlist from the provided URL
def extract_playlist(url):
    with youtube_dl.YoutubeDL({'quiet': True}) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        return [entry['url'] for entry in info_dict['entries']]

playlist = extract_playlist(YOUTUBE_PLAYLIST_URL)
current_song_index = 0

async def play_song(ctx, url):
    voice_client = ctx.guild.voice_client
    if not voice_client:
        await ctx.invoke(join)
    info = ytdl.extract_info(url, download=False)
    voice_client.play(discord.FFmpegPCMAudio(info['url']), after=lambda e: bot.loop.create_task(play_next(ctx)))

async def play_next(ctx):
    global current_song_index
    current_song_index = (current_song_index + 1) % len(playlist)
    await play_song(ctx, playlist[current_song_index])

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()

@bot.command()
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        await voice_client.disconnect()

@bot.command()
async def play(ctx, url: str = None):
    if url:
        await play_song(ctx, url)
    else:
        await play_song(ctx, playlist[current_song_index])

@bot.command()
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()

@bot.command()
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()

@bot.command()
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()

@tasks.loop(seconds=5)
async def check_voice_activity():
    for guild in bot.guilds:
        voice_client = guild.voice_client
        if voice_client:
            if len(voice_client.channel.members) == 1:  # Only the bot is left in the channel
                if voice_client.is_playing():
                    voice_client.pause()
            elif voice_client.is_paused() and len(voice_client.channel.members) > 1:
                voice_client.resume()

@bot.event
async def on_voice_state_update(member, before, after):
    voice_client = member.guild.voice_client
    if voice_client:
        if before.channel == voice_client.channel and len(voice_client.channel.members) == 1:
            if voice_client.is_playing():
                voice_client.pause()
        elif after.channel == voice_client.channel and voice_client.is_paused():
            if len(voice_client.channel.members) > 1:
                voice_client.resume()

@bot.event
async def on_ready():
    check_voice_activity.start()

bot.run(TOKEN)
