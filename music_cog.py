from ast import alias
import discord
from discord.ext import commands
from youtube_dl import YoutubeDL


class music_cog(commands.Cog):
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



    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.playing = True

            #get the first url
            m_url = self.music_queue[0][0]['source']

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.playing = False

    # infinite loop checking 
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.playing = True

            m_url = self.music_queue[0][0]['source']
            
            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                #in case we fail to connect
                if self.vc == None:
                    await ctx.send("Could'nt connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.playing = False

    @commands.command(name='p', help="Plays the selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            #you need to be connected so that the bot knows where to go
            await ctx.send("Connects to a voice channel")
        elif self.paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. May be incorrect format. Try another Keyword (Cannot download playlists or live streams)")
            else:
                await ctx.channel.send(f"{ctx.author.display_name.upper()} has added '{query}' to the queue")
                #await ctx.send(f"'{query}' has been added to the queue")
                self.music_queue.append([song, voice_channel])
                
                if self.playing == False:
                    await self.play_music(ctx)

    @commands.command(name="pa", help="Pauses current song")
    async def pause(self, ctx, *args):
        if self.playing:
            self.playing = False
            self.paused = True
            self.vc.pause()
        elif self.paused:
            self.paused = False
            self.playing = True
            self.vc.resume()

    @commands.command(name = "re", help="Resumes song")
    async def resume(self, ctx, *args):
        if self.paused:
            self.paused = False
            self.playing = True
            self.vc.resume()

    @commands.command(name="s", help="Skips the current song")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            #try to play next in the queue if it exists
            await self.play_music(ctx)


    @commands.command(name="q", help="Displays the current songs in queue")
    async def queue(self, ctx):
        retval = ""
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="c", help="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue has been cleared")

    @commands.command(name="d", help="disconnects bot from VC")
    async def dc(self, ctx):
        self.playing = False
        self.paused = False
        await self.vc.disconnect()
            