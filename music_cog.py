from ast import alias
import discord
from discord.ext import commands
from youtube_dl import YoutubeDL


class music_cog(commands.Cog):
    """Will be used to create the commands for the bot

    Args:
        commands (module): class with commands for the bot
    """
    def __init__(self, bot):
        self.bot = bot
    
        self.playing = False
        self.paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {
        'format': 'bestaudio/best',
        'noplaylist': 'True'
        }
    
        self.FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
        }

        self.vc = None


    #Searches through youtube for the song
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    #Used to play the next song in queue
    def play_next(self):
        if len(self.music_queue) > 0:
            self.playing = True

            
            m_url = self.music_queue[0][0]['source']

            #pops current song from queue while it plays
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.playing = False
            
    #Plays song
    async def play_music(self, ctx):
        if len(self.music_queue) > 0: #checks that there is a song in queue
            self.playing = True
            m_url = self.music_queue[0][0]['source']
            
            #Connects to voice channel
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                #Error message
                if self.vc == None:
                    await ctx.send("Could'nt connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            #pops current song from queue while it plays
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.playing = False


    #command to play music
    @commands.command(name='p', help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args) #Grabs the user's query
        
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Connect to a voice channel")
        elif self.paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.channel.send(f"{ctx.author.display_name.upper()} has added '{query}' to the queue")
                self.music_queue.append([song, voice_channel])
                
                if self.playing == False:
                    await self.play_music(ctx)

    #Command to pause
    @commands.command(name="pa", help="Pauses the current song")
    async def pause(self, ctx, *args):
        if self.playing:
            self.playing = False
            self.paused = True
            self.vc.pause()
        elif self.paused:
            self.paused = False
            self.playing = True
            self.vc.resume()

    #Command to resume
    @commands.command(name = "re", help="Resumes playing song")
    async def resume(self, ctx, *args):
        if self.paused:
            self.paused = False
            self.playing = True
            self.vc.resume()

    #Command to skip 
    @commands.command(name="s", help="Skips the current song")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            #try to play next in the queue if it exists
            await self.play_music(ctx)


    #Command to see queued songs
    @commands.command(name="q", help="Displays the current songs in queue")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += self.music_queue[i][0]['title'] + '\n'
            
            
        if retval != "":
            await ctx.send(f"Songs queued: \n {retval}")
        else:
            await ctx.send("No music in queue")

    #command to clear songs in queue
    @commands.command(name="c", help="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")

    #command to disconnect bot from vc
    @commands.command(name="d", help="Disconnects bot from VC")
    async def dc(self, ctx):
        self.playing = False
        self.paused = False
        await self.vc.disconnect()