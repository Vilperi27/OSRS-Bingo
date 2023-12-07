import os
import discord
from discord.ext import commands

from datetime import datetime
import json
import requests
from local_secrets import DISCORD_API_KEY
from errors import TileExistsError

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)
role = 'Lieutenant'
authorized_ids = [201768152982487041]
base_user_folder = os.path.dirname(__file__) + '/Users/'

@client.event
async def on_ready():
    print('Bot ready')


@client.command(pass_context = True)
@commands.has_role(role)
async def bhelp(ctx):

    embed = discord.Embed(
        colour = discord.Colour.orange()
    )

    embed.set_author(name='Help')
    embed.add_field(name='!register', value='(Elf only) Register a bingo player (Example. !register Elf)', inline=False)
    embed.add_field(name='!submit', value='(Elf only) Submit an entry for a tile. (Example. !submit 13 Elf)\nYou can also overwrite entries with --ow tag (Example. !submit 13 Elf --ow)\nIt is also possible to submit with a link to a picture. (Example. !submit 13 Elf --url=www.google.com/this.png)', inline=False)
    embed.add_field(name='!submit', value='(Elf only) Get a list of all registered users', inline=False)
    embed.add_field(name='!get_all', value='Get all entries for user (Example. !get_all Elf)', inline=False)
    embed.add_field(name='!get', value='Register a bingo player (Example. !get 13 Elf)', inline=False)
    await ctx.send(embed=embed)

@client.command(pass_context=True)
@commands.has_role(role)
async def register(ctx, *args):
    if ctx.author.id not in authorized_ids:
        await ctx.send("Unauthorized user")
        return

    # Get the name from the args (can contain spaces)
    name = " ".join(args)

    # Form folder path with the name to track with the given username
    path = base_user_folder + name 
    file_exists = os.path.isdir(path)
    
    if file_exists:
        await ctx.send('Account already registered.')
        return

    # If the account entry does not exist, create entry and create
    # preliminary data
    if not file_exists:
        os.mkdir(path)

        # Specify the path to point to a json-file
        path = path + '/user_details.json'

        with open(path, "a+") as f:
            data = {
                'user_details': [
                    {
                        'name': name,
                        'created': datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                    }
                ]
            }

            json_string = json.dumps(data)
            f.write(json_string)
    await ctx.send(name + ' registered!')


@client.command(pass_context=True)
@commands.has_role(role)
async def submit(ctx, tile, *args):
    if ctx.author.id not in authorized_ids:
        await ctx.send("Unauthorized user")
        return
    
    custom_image_url = ""

    # Get the name from the args (can contain spaces) and form a path
    args_data = " ".join(args)
    name = args_data
    overwrite = False

    if "--ow" in args_data:
        args_data = args_data.replace(" --ow", "")
        overwrite = True

    if "--url" in args_data:
        split_data = args_data.split(" --url=")
        name = split_data[0]
        custom_image_url = split_data[1]

    path = base_user_folder + name
    file_exists = os.path.isdir(path)
    
    if not file_exists:
        await ctx.send('Account does not exist, please use !register {name} to begin tracking.')
        return
    
    try:
        if custom_image_url:
            img_data = requests.get(custom_image_url).content
        else:
            img_data = requests.get(ctx.message.attachments[0].url).content
    except Exception:
        await ctx.send("No image provided, entry must have an image attached")
        return
        
    # If the account exists, create a text entry of the submission
    try:
        create_submit_entry(path, tile, overwrite)
    except TileExistsError as e:
        await ctx.send(e)
        return

    # If the account exists, create an image entry of the submission
    with open(path + '/' + tile + '.jpg', 'wb') as handler:
        handler.write(img_data)
        handler.truncate()

    await ctx.send('Submission saved for account %s, Tile: %s.' % (name, tile))


def create_submit_entry(path, tile, overwrite=False):
    path = path + '/entries.json'
    file_exists = os.path.isfile(path)

    # If file exists, append the new entry to the json file,
    # If no entries exist, create the json-file.
    if file_exists:
        with open(path, 'r') as json_file:
            data = json.load(json_file)

        tile_exists = False
        found_tile_index = -1

        for index, entry in enumerate(data['entries']):
            if entry['tile'] == tile:
                tile_exists = True
                found_tile_index = index
                break

        if not overwrite and tile_exists:
            raise TileExistsError("Tile already exists for that id. If you want to overwrite the data, use --ow (i.e. !submit 2 Elf --ow)")
        
        if not tile_exists:
            data['entries'].append({
                'tile': tile,
                'submitted': datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            })
        else:
            data['entries'][found_tile_index]['tile'] = tile
            data['entries'][found_tile_index]['submitted'] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

        with open(path, 'w') as json_file:
            json_string = json.dumps(data)
            json_file.write(json_string)
    else:
        with open(path, "a+") as f:
            data = {
                'entries': [
                    {
                        'tile': tile,
                        'submitted': datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                    }
                ]
            }

            json_string = json.dumps(data)
            f.write(json_string)


@client.command(pass_context=True)
@commands.has_role(role)
async def get_all(ctx, *args):
    # Get the name from the args (can contain spaces) and form a path
    args_data = " ".join(args)
    name = args_data
    filter_data = None

    if "--filter" in args_data:
        split_data = args_data.split(" --filter=")
        name = split_data[0]
        filter_data = split_data[1]

    path = base_user_folder + name
    file_exists = os.path.isdir(path)
    
    # If account exists, get all the entries from the json-file.
    if not file_exists:
        await ctx.send('Account does not exist, please use !register {name} to begin tracking.')
        return
    else:
        with open(path + '/entries.json', 'r') as json_file:
            data = json.load(json_file)

        entries = []
        for entry in data['entries']:
            if filter_data and filter_data not in entry['tile']:
                continue
            entries.append(entry['tile'])

        if entries:
            entries = sorted(entries, key=int)
            entries = ', '.join(entries)
            await ctx.send('Entries for ' + name + ' exist for tiles: ' + entries)
        else:
            await ctx.send('No entries found')


@client.command(pass_context=True)
@commands.has_role(role)
async def get(ctx, tile, *args):
    name = " ".join(args)
    path = base_user_folder + name
    file_exists = os.path.isdir(path)
    
    # If the account and entry exists, get the given entry and return the submission image
    # With the name of the account, tile number and time of submission.
    if not file_exists:
        await ctx.send('Account does not exist, please use !register {name} to begin tracking.')
        return
    else:
        submission_time = "N/A"

        with open(path + '/entries.json', 'r') as json_file:
            data = json.load(json_file)

        submission_time = next((entry for entry in data['entries'] if entry['tile'] == tile), None)['submitted']

        with open(path + '/' + tile + '.jpg', 'rb') as f:
            picture = discord.File(f)
            await ctx.channel.send(content='Name: %s\nTile: %s\nSubmitted: %s' % (name, tile, submission_time), file=picture)


@client.command(pass_context=True)
@commands.has_role(role)
async def remove(ctx, tile, *args):
    if ctx.author.id not in authorized_ids:
        await ctx.send("Unauthorized user")
        return
        
    name = " ".join(args)
    path = base_user_folder + name
    file_exists = os.path.isdir(path)

    if not file_exists:
        await ctx.send('Account does not exist, please use !register {name} to begin tracking.')
        return
    
    with open(path + '/entries.json', 'r') as json_file:
        data = json.load(json_file)

    for index, entry in enumerate(data['entries']):
        if entry['tile'] == tile:
            del data['entries'][index]
            
            with open(path + '/entries.json', 'w') as json_file:
                json_string = json.dumps(data)
                json_file.write(json_string)
            break
    await ctx.send('Tile ' + tile + ' removed for user ' + name)


@client.command(pass_context=True)
@commands.has_role(role)
async def get_all_users(ctx, *args):
    if ctx.author.id not in authorized_ids:
        await ctx.send("Unauthorized user")
        return
        
    folders = next(os.walk('.'))[1]
    folders.remove('.git')
    folders.remove('__pycache__')
    await ctx.send('\n'.join(folders))


# TODO async def export_as_csv()


client.run(DISCORD_API_KEY)