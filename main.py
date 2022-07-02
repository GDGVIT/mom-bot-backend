import utils

import discord
import config
from discord.commands import ApplicationContext

bot = discord.Bot(debug_guilds=config.guild_ids)
bot.connections = {}
discord.opus.load_opus(name=config.opus_path)


@bot.command()
async def start(ctx: ApplicationContext):
    """
    Record your voice!
    """
    await ctx.defer()
    sink = discord.sinks.WaveSink()

    voice = ctx.author.voice

    if not voice:
        return await ctx.respond("You're not in a vc right now")

    vc = await voice.channel.connect()
    bot.connections.update({ctx.guild.id: vc})

    vc.start_recording(
        sink,
        finished_callback,
        ctx.channel,
    )

    await ctx.respond("The recording has started!")


async def finished_callback(sink: discord.sinks.WaveSink, channel: discord.TextChannel, *args):
    recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
    await sink.vc.disconnect()
    file_link = None
    for audio in sink.audio_data.items():
        file_link = utils.upload_to_cloud(audio[1].file)
    
    if file_link:
        await channel.send(f"Recording finished! Link: {file_link}")
    else:
        await channel.send("Error occured during recording.")



@bot.command()
async def stop(ctx):
    """
    Stop recording.
    """
    await ctx.defer()
    if ctx.guild.id in bot.connections:
        vc = bot.connections[ctx.guild.id]
        vc.stop_recording()
        del bot.connections[ctx.guild.id]
        await ctx.delete()
    else:
        await ctx.respond("Not recording in this guild.")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}#{bot.user.discriminator}")


bot.run(config.bot_token)