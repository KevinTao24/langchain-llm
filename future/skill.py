import os
from datetime import datetime, timedelta

import discord
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytrends.request import TrendReq
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled

# Make sure to replace this with your actual bot token
TOKEN = ""

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)


async def fetch_messages_from_server(server):
    await client.wait_until_ready()
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name.lower() == server:
                try:
                    messages = await channel.history(limit=10).flatten()
                    print(f"--- Messages from {channel.name} in {guild.name} ---")
                    for message in messages:
                        print(f"{message.author.name}: {message.content}")
                    return
                except discord.errors.Forbidden:
                    print(
                        f"Cannot access messages in {channel.name} of {guild.name}. Missing permissions."
                    )
    print("Channel 'Roblox' not found in any server the bot is in.")


@client.event
async def on_ready(query):
    print(f"Logged in as {client.user.name}")
    await fetch_messages_from_server(query)
    await client.close()


client.run(TOKEN)

# Load the API key from the .env file
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    print("Failed to load YOUTUBE_API_KEY from .env file.")
    exit(1)

# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=API_KEY)


def search_videos(hours, query, max_res):
    # Calculate the date 10 hours ago in the required format
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    time_threshold = time_threshold.isoformat("T") + "Z"

    try:
        # Search for videos
        search_response = (
            youtube.search()
            .list(
                q=query,
                part="id,snippet",
                maxResults=50,
                publishedAfter=time_threshold,
                order="viewCount",
                type="video",
            )
            .execute()
        )

        # Filter top 3 videos
        videos = []
        for item in search_response.get("items", []):
            if len(videos) < max_res:
                videos.append(item)
            else:
                break

        return videos
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []


def get_transcripts(videos):
    transcripts = []
    for video in videos:
        video_id = video["id"]["videoId"]
        video_title = video["snippet"]["title"]
        try:
            # Fetch the transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([t["text"] for t in transcript])
            transcripts.append((video_title, transcript_text))
        except TranscriptsDisabled:
            print(f"Transcript is disabled for video: {video_title}")
        except Exception as e:
            print(f"An error occurred: {e}")

    return transcripts


def main():
    videos = search_videos()
    if videos:
        transcripts = get_transcripts(videos)
        for title, transcript in transcripts:
            print(f"Title: {title}\nTranscript: {transcript}\n")
    else:
        print("No videos found or an error occurred.")


def fetch_and_plot_google_trends(search_query, time_span, x, y):
    # Initialize pytrends
    pytrends = TrendReq(hl="en-US", tz=360)

    # Prepare the payload
    pytrends.build_payload([search_query], cat=0, timeframe=time_span, geo="", gprop="")

    # Fetch the interest over time
    interest_over_time_df = pytrends.interest_over_time()

    # Check if the dataframe is empty
    if interest_over_time_df.empty:
        print(f"No data found for the keyword '{search_query}'.")
        return
    else:
        # Plotting
        plt.figure(figsize=(x, y))
        plt.plot(
            interest_over_time_df.index,
            interest_over_time_df[search_query],
            label="Interest over time",
        )
        plt.title(f'Google Trends over time for the keyword "{search_query}"')
        plt.xlabel("Date")
        plt.ylabel("Trend")
        plt.legend()
        plt.grid(True)

        # Save the plot
        filename = f'{search_query.replace(" ", "_")}.png'
        plt.savefig(filename)
        print(f"The chart has been saved as '{filename}'.")


"""python script that fetches X number of most viewed videos, 
their titles and total number of views of all times froma 
youtube channel with ID Y

YOUTUBE_API_KEY should be saved as an environment
variable"""


# Load the API key from the .env file
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    raise ValueError("Missing YOUTUBE_API_KEY in the environment variables.")

# Set up the YouTube API service
try:
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
except HttpError as e:
    print(f"An error occurred: {e}")
    exit(1)


def get_most_viewed_videos(channel_id, topic, max_results=10):
    try:
        # Use the search endpoint to find videos about AI within the channel
        search_response = (
            youtube.search()
            .list(
                q=topic,
                channelId=channel_id,
                part="id",
                type="video",
                maxResults=50,
                order="viewCount",
            )
            .execute()
        )

        video_ids = [item["id"]["videoId"] for item in search_response["items"]]

        # Fetch video details
        videos_response = (
            youtube.videos()
            .list(id=",".join(video_ids), part="snippet,statistics")
            .execute()
        )
        videos_info = []
        for video in videos_response["items"]:
            videos_info.append(
                {
                    "title": video["snippet"]["title"],
                    "views": int(video["statistics"]["viewCount"]),
                    "videoId": video["id"],
                }
            )

        # Sort videos by view count just in case
        videos_info.sort(key=lambda x: x["views"], reverse=True)

        # Return the top N videos
        return videos_info[:max_results]
    except HttpError as e:
        print(f"An error occurred: {e}")
        return []


# Channel ID for the specified YouTube channel
channel_id = "UCbY9xX3_jW5c2fjlZVBI4cg"
topic = "AI"

# Fetch and display the most viewed videos about AI
most_viewed_videos = get_most_viewed_videos(channel_id, topic)
for video in most_viewed_videos:
    print(
        f"Title: {video['title']}, Views: {video['views']}, Link: https://www.youtube.com/watch?v={video['videoId']}"
    )
