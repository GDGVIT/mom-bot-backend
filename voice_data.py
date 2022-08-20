import time
import discord


class VoiceData:
    def __init__(self):
        self.is_recording = True
        self.meeting_start_time = time.time()
        self.current_speakers = {}
        self.timestamps = []
        self.meeting_end_time = None

    def add_speaker(self, member: discord.Member) -> None:
        self.current_speakers[str(member.id)] = time.time()

    def remove_speaker(self, member: discord.Member) -> None:
        if str(member.id) in self.current_speakers.keys():
            start_time = (
                self.current_speakers.pop(str(member.id)) - self.meeting_start_time
            )
            end_time = time.time() - self.meeting_start_time
            self.timestamps.append(
                dict(
                    id=member.id,
                    start=start_time,
                    end=end_time,
                    duration=end_time - start_time,
                )
            )
