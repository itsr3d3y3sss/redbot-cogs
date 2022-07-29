from redbot.core import Config, commands, checks
from redbot.cogs.admin import admin
import asyncio
import aiohttp
import discord
from discord import Webhook, AsyncWebhookAdapter
from urllib.parse import quote
import json
import typing

class Hellohook(commands.Cog):
    """Custom welcome message bots"""

    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=806715409318936616)
        self.bot = bot
        default_guild = {
            "hellohookEnabled": False,
            "greetWebhook": "",
            "greetMessage": {},
            # "greetUserMention": False,
            # "embedAuthor": {
            #     "authorField": None,
            #     "authorIconUrl": None,
            #     "authorLink": None
            # },
            # "embedDescription": None,
        }
        self.config.register_guild(**default_guild)

    # This cog does not store any End User Data
    async def red_get_data_for_user(self, *, user_id: int):
        return {}
    async def red_delete_data_for_user(self, *, requester, user_id: int) -> None:
        pass


    # Utility Commands

    async def hellohookSender(self, webhook, userObj: discord.Member):
        greetMessage = await self.config.guild(userObj.guild).greetMessage()
        # Replace with content
        greetMessageStr = str(json.dumps(greetMessage))
        if "https://&&USERAVATAR&&" in greetMessageStr:
            greetMessageStr = greetMessageStr.replace("https://&&USERAVATAR&&", str(userObj.avatar_url))
        if "https://&&USERMENTION&&" in greetMessageStr:
            greetMessageStr = greetMessageStr.replace("https://&&USERMENTION&&", str(userObj.mention))
        if "https://&&USERNAME&&" in greetMessageStr:
            greetMessageStr = greetMessageStr.replace("https://&&USERNAME&&", str(userObj.name))
        if "https://&&USERNAME1234&&" in greetMessageStr:
            greetMessageStr = greetMessageStr.replace("https://&&USERNAME1234&&", str(userObj.name)+"#"+str(userObj.discriminator))
        if "https://&&SERVERCOUNT&&" in greetMessageStr:
            greetMessageStr = greetMessageStr.replace("https://&&SERVERCOUNT&&", str(userObj.guild.member_count))
        if "https://&&SERVERCOUNTORD&&" in greetMessageStr:
            greetMessageStr = greetMessageStr.replace("https://&&SERVERCOUNTORD&&", str(self.ordinalize_num(userObj.guild.member_count)))
        greetMessageJson = json.loads(str(greetMessageStr))
        # Patch fix: send() got an unexpected keyword argument 'attachments'
        if "attachments" in greetMessageJson:
            greetMessageJson.pop("attachments")
        # Create embed
        if greetMessageJson["embeds"]:
            e = discord.Embed.from_dict(greetMessageJson["embeds"][0])
            greetMessageJson["embeds"] = [e]
        # Send webhook
        try:
            return await webhook.send(**greetMessageJson,
                username=userObj.display_name,
                avatar_url=userObj.avatar_url)
        except Exception as e:
            return print(e)

    def ordinalize_num(self, n):
        # https://stackoverflow.com/a/50992575/15923512 CC BY-SA 4.0
        n = int(n)
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return str(n) + suffix

    def validChecker(self, item):
        if item:
            return item
        else:
            return None


    # Bot Commands

    @commands.guild_only()
    @commands.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def hellohook(self, ctx: commands.Context):
        """Hellohook settings
        
        Set a welcome message using **`[p]hellohook set`**.
        
        Due to Discord limitations, you will have to create a webhook yourself in the channel you want the welcome message in. See **`[p]hellohook setwebhook`** for more details. 
        
        [See Documentation >](https://github.com/coffeebank/coffee-cogs/wiki/Hellohook)
        """
        if not ctx.invoked_subcommand:
            guildData = await self.config.guild(ctx.guild).all()
            e = discord.Embed(color=(await ctx.embed_colour()), title="Hellohook Settings")
            e.add_field(name="Greet Enabled", value=guildData.get("hellohookEnabled", None), inline=False)
            e.add_field(name="Greet Webhook", value=self.validChecker(guildData.get("greetWebhook", None)), inline=False)
            e.add_field(name="Greet Message", value='```json\n'+str(json.dumps(guildData.get("greetMessage", {})))+'```', inline=False)
            await ctx.send(embed=e)
            # pass
    
    @hellohook.command(name="setwebhook", aliases=["setchannel"])
    async def hellohooksetchannel(self, ctx, webhookUrl):
        """Set the webhook URL to send the welcome message to
        
        Must be webhook URL. Due to Discord limitations, you will have to make the webhook yourself. You can create a webhook in your desired channel by:
        
        #channel ⚙ settings > Integrations > Webhooks > New Webhook

        [How to create a webhook (image) >](https://support.discord.com/hc/article_attachments/1500000463501/Screen_Shot_2020-12-15_at_4.41.53_PM.png)

        After you create the webhook, you can customize the profile picture and name of the "bot", which will be used when Hellohook sends a welcome message.
        """
        await self.config.guild(ctx.guild).greetWebhook.set(webhookUrl)
        await ctx.message.add_reaction("✅")
        
    @hellohook.command(name="toggle")
    async def hellohooktoggle(self, ctx, TrueOrFalse: bool):
        """Enable/Disable Hellohook welcomes"""
        await self.config.guild(ctx.guild).hellohookEnabled.set(TrueOrFalse)
        await ctx.send("Hellohook is now set to "+str(TrueOrFalse))
    
    @hellohook.command(name="test")
    async def hellohooktest(self, ctx):
        """Send a test welcome message to the hellohook"""
        try:
            hellohookEnabled = await self.config.guild(ctx.guild).hellohookEnabled()
            greetWebhook = await self.config.guild(ctx.guild).greetWebhook()
            # Send Webhook
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(greetWebhook, adapter=AsyncWebhookAdapter(session))
                await self.hellohookSender(webhook, ctx.message.author)
            # Confirm
            await ctx.send("hellohookEnabled: "+str(hellohookEnabled))
        except Exception as e:
            await ctx.send("Error: "+str(e))

    @hellohook.command(name="set", aliases=["setwelcome"])
    async def hellohooksetwelcome(self, ctx, *, DiscohookJSON: str):
        """Set the hellohook welcome

        Welcome message must be a `{ "content": …, "embeds": [{}] }` object.
        
        You can use variables to put the info of new users into the welcome message automatically.
        
        [Create a webhook message here >\nSee Hellohook help documentation >](https://github.com/coffeebank/coffee-cogs/wiki/Hellohook)

        When you are done on Discohook:
        - Scroll to the bottom
        - Click "JSON Data Editor"
        - Click "Copy to Clipboard"
        - Paste it into this bot command
        """
        welcomeMsg = json.loads(DiscohookJSON)
        await self.config.guild(ctx.guild).greetMessage.set(welcomeMsg)
        await ctx.message.add_reaction("✅")
    
    @hellohook.command(name="reset")
    async def hellohooksetclear(self, ctx, TypeTrueToConfirm: bool):
        """⚠️ Reset all settings"""
        await self.config.guild(ctx.guild).clear_raw()
        await ctx.message.add_reaction("✅")

    
    # Listeners

    @commands.Cog.listener()
    async def on_member_join(self, userObj: discord.Member) -> None:
        # Ignore if it's a bot
        if userObj.bot:
            return

        # Ignore if hellohook is disabled in the user's guild
        userGuild = userObj.guild
        hellohookEnabled = await self.config.guild(userGuild).hellohookEnabled()
        if hellohookEnabled == False:
            return

        greetMessage = await self.config.guild(userGuild).greetMessage()
        if not greetMessage:
            updatev1data = await self.updatev1data(userObj.guild)
            if updatev1data == False:
                return
        greetWebhook = await self.config.guild(userGuild).greetWebhook()
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(greetWebhook, adapter=AsyncWebhookAdapter(session))
            await self.hellohookSender(webhook, userObj)
        return
        

    # Legacy

    async def updatev1data(self, guildObj):
        def toContent(a):
            if a == True:
                return "https://&&USERMENTION&&"
            else:
                return None
        greetMessage = await self.config.guild(guildObj).greetMessage()
        if not greetMessage:
            guildData = await self.config.guild(guildObj).all()
            v1migrate = {
                "content": toContent(guildData.get("greetUserMention", None)),
                "embeds": [{
                    "author": {
                        "name": guildData["embedAuthor"].get("authorField", None),
                        "url": guildData["embedAuthor"].get("authorLink", None),
                        "icon_url": guildData["embedAuthor"].get("authorIconUrl", None)
                    },
                    "color": 2474073,
                    "description": guildData.get("embedDescription", None)
                }]
            }
            await self.config.guild(guildObj).greetMessage.set(v1migrate)
            return v1migrate
        else:
            return False
