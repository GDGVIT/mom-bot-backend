import sys
import time
from os import system

import config
import discord
import utils
from discord.commands import ApplicationContext
from summary import summarize
from voice_data import VoiceData

bot = discord.Bot(debug_guilds=config.guild_ids)
bot.connections = {}
voice_data = VoiceData()


@bot.command()
async def start(ctx: ApplicationContext) -> None:
    """
    Record your voice!
    """
    global voice_data
    await ctx.defer()
    voice_data = VoiceData()
    sink = discord.sinks.WaveSink()

    voice = ctx.author.voice

    if not voice:
        await ctx.respond("You're not in a Voice Channel right now")
        return None

    vc = await voice.channel.connect()
    bot.connections.update({ctx.guild.id: vc})

    for member in voice.channel.members:
        if not member.voice.self_mute and member != bot.user:
            voice_data.add_speaker(member=member)

    vc.start_recording(
        sink,
        finished_callback,
        ctx.channel,
    )

    await ctx.respond("The recording has started!")


async def finished_callback(
    sink: discord.sinks.WaveSink, channel: discord.TextChannel, *args
) -> None:
    """
    Callback for finished audio recordings.
    """
    await sink.vc.disconnect()
    voice_data.meeting_end_time = time.time()
    # create an empty wav file to store our meeting transcript
    system("sox --ignore-length -n -r 16000 -c 1 -b 16 full_record.wav trim 0.0 0.1")
    utils.save_all_audio(sink)
    transcription = ""
    full_summary = ""

    message = await channel.send("Transcribing audio :)")
    for timestamp in voice_data.timestamps:
        """
        Processing the audio and transcribing it.
        """
        user = await bot.get_or_fetch_user(timestamp["id"])
        async with channel.typing():
            transcript = utils.get_transcription(
                f"{user.id}_processed.wav",
                timestamp["start_actual"],
                timestamp["duration"],
            )
            transcription += f"{user.name}: {transcript}\n"

    # Upload file to cloud
    file_link = utils.upload_recording_to_cloud()
    if file_link:
        embed = discord.Embed(
            title="Meeting Recording Complete",
            description=f"Find your meeting recording [here]({file_link.media_link})",
            color=discord.Color.blurple(),
        )
        await message.edit(content="", embed=embed)

    else:
        await channel.send(f"Error recording audio!")

    with open("transcript.txt", "w") as file:
        file.write(transcription)

    async with channel.typing():
        summary = summarize(transcription)

    summary_string = "\n".join(x for x in summary)
    with open("summary.txt", "w") as file:
        file.write(summary_string)

    transcript_file = open("transcript.txt", "r")
    summary_file = open("summary.txt", "r")

    await channel.send("Transcript:", file=discord.File(transcript_file))
    await channel.send("Summary:", file=discord.File(summary_file))

    transcript_file.close()
    summary_file.close()
    utils.cleanup_tmp()


@bot.command()
async def stop(ctx: ApplicationContext) -> None:
    """
    Stop recording.
    """
    await ctx.defer()
    if ctx.guild.id in bot.connections:
        vc = bot.connections[ctx.guild.id]
        for member in vc.channel.members:
            voice_data.remove_speaker(member)
        vc.stop_recording()
        del bot.connections[ctx.guild.id]
        await ctx.respond("Processing...")
    else:
        await ctx.respond("Not recording in this guild.")


@bot.event
async def on_ready() -> None:
    """
    Called when the bot is logged in and is ready to process commands.
    """
    print(f"Logged in as {bot.user.name}#{bot.user.discriminator}")


@bot.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
) -> None:
    """
    Called when a user's voice state is updated.
    """
    if not voice_data.is_recording:
        return None
    if after.channel == before.channel:
        if before.self_mute or before.mute:
            # speaker has started speaking
            voice_data.add_speaker(member)

        if after.self_mute or after.mute:
            voice_data.remove_speaker(member)


bot.run(config.bot_token)
