import asyncio
import discord
import typing
import wavelink

from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.position = 0
        self.repeat = False
        self.repeatMode = "NONE"
        self.playingTextChannel = 0
        bot.loop.create_task(self.create_nodes())
    
    async def create_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot, host="127.0.0.1", port="2333", password="youshallnotpass", region="asia")
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Music Cog is now ready!")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node <{node.identifier}> is now Ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: wavelink.Player, track: wavelink.Track):
        try:
            self.queue.pop(0)
        except:
            pass

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if str(reason) == "FINISHED":
            if not len(self.queue) == 0:
                next_track: wavelink.Track = self.queue[0]
                channel = self.bot.get_channel(self.playingTextChannel)

                try:
                    await player.play(next_track)
                except:
                    return await channel.send(embed=discord.Embed(title=f"Something went wrong while playing **{next_track.title}**", color=discord.Color.from_rgb(255, 255, 255)))
                
                await channel.send(embed=discord.Embed(title=f"Now playing: {next_track.title}", color=discord.Color.from_rgb(255, 255, 255)))
            else:
                pass
        else:
            print(reason)
    
    @commands.command(name="join", aliases=["connect", "summon"])
    async def join_command(self, ctx: commands.Context, channel: typing.Optional[discord.VoiceChannel]):
        if channel is None:
            channel = ctx.author.voice.channel
        
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if player is not None:
            if player.is_connected():
                return await ctx.send("bot is already connected to a voice channel")
        
        await channel.connect(cls=wavelink.Player)
        mbed=discord.Embed(title=f"Connected to {channel.name}", color=discord.Color.from_rgb(255, 255, 255))
        await ctx.send(embed=mbed)

    @commands.command(name="leave", alises=["disconnect"])
    async def leave_command(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if player is None:
            return await ctx.send("bot is not connected to any voice channel")
        
        await player.disconnect()
        mbed = discord.Embed(title="Disconnected", color=discord.Color.from_rgb(255, 255, 255))
        await ctx.send(embed=mbed)
    
    @commands.command(name="play")
    async def play_command(self, ctx: commands.Context, *, search: str):
        try:
            search = await wavelink.YouTubeTrack.search(query=search, return_first=True)
        except:
            return await ctx.reply(embed=discord.Embed(title="Something went wrong while searching for this track", color=discord.Color.from_rgb(255, 255, 255)))

        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client
        
        if not vc.is_playing():
            try:
                await vc.play(search)
            except:
                return await ctx.reply(embed=discord.Embed(title="Something went wrong while playing this track", color=discord.Color.from_rgb(255, 255, 255)))
        else:
            self.queue.append(search)

        mbed = discord.Embed(title=f"Added {search} To the queue", color=discord.Color.from_rgb(255, 255, 255))
        await ctx.send(embed=mbed)
    
    @commands.command(name="stop")
    async def stop_command(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if player is None:
            return await ctx.send("Bot is not connected to any voice channel")

        self.queue.clear()
        
        if player.is_playing():
            await player.stop()
            mbed = discord.Embed(title="Playback Stoped", color=discord.Color.from_rgb(255, 255, 255))
            return await ctx.send(embed=mbed)
        else:
            return await ctx.send("Nothing Is playing right now")
    
    @commands.command(name="pause")
    async def pause_command(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if player is None:
            return await ctx.send("Bot is not connected to any voice channel")
        
        if not player.is_paused():
            if player.is_playing():
                await player.pause()
                mbed = discord.Embed(title="Playback Paused", color=discord.Color.from_rgb(255, 255, 255))
                return await ctx.send(embed=mbed)
            else:
                return await ctx.send("Nothing is playing right now")
        else:
            return await ctx.send("Playback is Already paused")
    
    @commands.command(name="resume")
    async def resume_command(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if player is None:
            return await ctx.send("bot is not connnected to any voice channel")
        
        if player.is_paused():
            await player.resume()
            mbed = discord.Embed(title="Playback resumed", color=discord.Color.from_rgb(255, 255, 255))
            return await ctx.send(embed=mbed)
        else:
            if not len(self.queue) == 0:
                track: wavelink.Track = self.queue[0]
                player.play(track)
                return await ctx.reply(embed=discord.Embed(title=f"Now playing: {track.title}"))
            else:
                return await ctx.send("playback is not paused")

    @commands.command(name="volume")
    async def volume_command(self, ctx: commands.Context, to: int):
        if to > 100:
            return await ctx.send("Volume should be between 0 and 100")
        elif to < 1:
            return await ctx.send("Volume should be between 0 and 100")

        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        await player.set_volume(to)
        mbed = discord.Embed(title=f"Changed Volume to {to}", color=discord.Color.from_rgb(255, 255, 255))
        await ctx.send(embed=mbed)

    #adding more commands
    @commands.command(name="playnow", aliases=["pn"])
    async def play_now_command(self, ctx: commands.Context, *, search: str):
        try:
            search = await wavelink.YouTubeTrack.search(query=search, return_first=True)
        except:
            return await ctx.reply(embed=discord.Embed(title="Something went wrong while searching for this track", color=discord.Color.from_rgb(255, 255, 255)))
        
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel(cls=wavelink.Player)
            await player.connect(ctx.author.voice.channel)
        else:
            vc: wavelink.Player = ctx.voice_client

        try:
            await vc.play(search)
        except:
            return await ctx.reply(embed=discord.Embed(title="Something went wrong while playing this track", color=discord.Color.from_rgb(255, 255, 255)))
        await ctx.reply(embed=discord.Embed(title=f"Playing: **{search.title}** Now", color=discord.Color.from_rgb(255, 255, 255)))

    @commands.command(name="nowplaying", aliases=["now_playing", "np"])
    async def now_playing_command(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if player is None:
            return await ctx.reply("Bot is not connected to any voice channel")

        if player.is_playing():
            mbed = discord.Embed(
                title=f"Now Playing: {player.track}",
                #you can add url as one the arugument over here, if you want the user to be able to open the video in youtube
                #url = f"{player.track.info['uri']}"
                color=discord.Color.from_rgb(255, 255, 255)
            )

            t_sec = int(player.track.length)
            hour = int(t_sec/3600)
            min = int((t_sec%3600)/60)
            sec = int((t_sec%3600)%60)
            length = f"{hour}hr {min}min {sec}sec" if not hour == 0 else f"{min}min {sec}sec"

            mbed.add_field(name="Artist", value=player.track.info['author'], inline=False)
            mbed.add_field(name="Length", value=f"{length}", inline=False)

            return await ctx.reply(embed=mbed)
        else:
            await ctx.reply("Nothing is playing right now")

    @commands.command(name="search")
    async def search_command(self, ctx: commands.Context, *, search: str):
        try:
            tracks = await wavelink.YouTubeTrack.search(query=search)
        except:
            return await ctx.reply(embed=discord.Embed(title="Something went wrong while searching for this track", color=discord.Color.from_rgb(255, 255, 255)))

        if tracks is None:
            return await ctx.reply("No tracks found")

        mbed = discord.Embed(
            title="Select the track: ",
            description=("\n".join(f"**{i+1}. {t.title}**" for i, t in enumerate(tracks[:5]))),
            color = discord.Color.from_rgb(255, 255, 255)
        )
        msg = await ctx.reply(embed=mbed)

        emojis_list = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '❌']
        emojis_dict = {
            '1️⃣': 0,
            "2️⃣": 1,
            "3️⃣": 2,
            "4️⃣": 3,
            "5️⃣": 4,
            "❌": -1
        }

        for emoji in list(emojis_list[:min(len(tracks), len(emojis_list))]):
            await msg.add_reaction(emoji)

        def check(res, user):
            return(res.emoji in emojis_list and user == ctx.author and res.message.id == msg.id)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await msg.delete()
            return
        else:
            await msg.delete()

        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        try:
            if emojis_dict[reaction.emoji] == -1: return
            choosed_track = tracks[emojis_dict[reaction.emoji]]
        except:
            return

        vc: wavelink.Player = ctx.voice_client or await ctx.author.voice.channel.connect(cls=wavelink.Player)

        if not player.is_playing() and not player.is_paused():
            try:
                await vc.play(choosed_track)
            except:
                return await ctx.reply(embed=discord.Embed(title="Something went wrong while playing this track", color=discord.Color.from_rgb(255, 255, 255)))
        else:
            self.queue.append(choosed_track)
        
        await ctx.reply(embed=discord.Embed(title=f"Added {choosed_track.title} to the queue", color=discord.Color.from_rgb(255, 255, 255)))

    @commands.command(name="skip")
    async def skip_command(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)

        if not len(self.queue) == 0:
            next_track: wavelink.Track = self.queue[0]
            try:
                await player.play(next_track)
            except:
                return await ctx.reply(embed=discord.Embed(title="Something went wrong while playing this track", color=discord.Color.from_rgb(255, 255, 255)))

            await ctx.reply(embed=discord.Embed(title=f"Now playing {next_track.title}", color=discord.Color.from_rgb(255, 255, 255)))
        else:
            await ctx.reply("The queue is empty")

    #this command would queue a song if some args(search) is provided else it would just show the queue
    @commands.command(name="queue")
    async def queue_command(self, ctx: commands.Context, *, search=None):
        node = wavelink.NodePool.get_node()
        player = node.get_player(ctx.guild)
        
        if search is None:
            if not len(self.queue) == 0:
                mbed = discord.Embed(
                    title=f"Now playing: {player.track}" if player.is_playing else "Queue: ",
                    description = "\n".join(f"**{i+1}. {track}**" for i, track in enumerate(self.queue[:10])) if not player.is_playing else "**Queue: **\n"+"\n".join(f"**{i+1}. {track}**" for i, track in enumerate(self.queue[:10])),
                    color=discord.Color.from_rgb(255, 255, 255)
                )

                return await ctx.reply(embed=mbed)
            else:
                return await ctx.reply(embed=discord.Embed(title="The queue is empty", color=discord.Color.from_rgb(255, 255, 255)))
        else:
            try:
                track = await wavelink.YoutubeTrack.search(query=search, return_first=True)
            except:
                return await ctx.reply(embed=discord.Embed(title="Something went wrong while searching for this track", color=discord.Color.from_rgb(255, 255, 255)))
            
            if not ctx.voice_client:
                vc: wavelink.Player = await ctx.author.voice.channel(cls=wavelink.Player)
                await player.connect(ctx.author.voice.channel)
            else:
                vc: wavelink.Player = ctx.voice_client
            
            if not vc.isp_playing():
                try:
                    await vc.play(track)
                except:
                    return await ctx.reply(embed=discord.Embed(title="Something went wrong while playing this track", color=discord.Color.from_rgb(255, 255, 255)))
            else:
                self.queue.append(track)
            
            await ctx.reply(embed=discord.Embed(title=f"Added {track.title} to the queue", color=discord.Color.from_rgb(255, 255, 255)))
            

def setup(client):
    client.add_cog(Music(client))
