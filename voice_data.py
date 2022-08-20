import time
import discord


class VoiceData:
    def __init__(self):
        self.is_recording = True
        self.meeting_start_time = time.time()
        self.current_speakers = {}
        self.speaker_info = {}
        self.timestamps = []
        self.meeting_end_time = None

    def add_speaker(self, member: discord.Member) -> None:
        if not member.id in self.current_speakers.keys():
            self.current_speakers[member.id] = time.time()
        if not member.id in self.speaker_info.keys():
            # maintains a record of speakers' individual times in their own tracks
            self.speaker_info[member.id] = {"start_time": time.time(), "duration": 0}

    def remove_speaker(self, member: discord.Member) -> None:
        if member.id in self.current_speakers.keys():
            # calculating the start and end times in the entire meeting.
            start_time = self.current_speakers.pop(member.id) - self.meeting_start_time
            end_time = time.time() - self.meeting_start_time

            # calculate the start and end times in the individual audio record.
            start_time_local = self.speaker_info[member.id]["duration"]
            end_time_local = self.speaker_info[member.id]["duration"] + (
                end_time - start_time
            )
            self.speaker_info[member.id]["duration"] = end_time_local

            self.timestamps.append(
                dict(
                    id=member.id,
                    start=start_time,
                    end=end_time,
                    start_actual=start_time_local,
                    end_actual=end_time_local,
                    duration=end_time - start_time,
                )
            )
