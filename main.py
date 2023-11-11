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

@client.event
async def on_ready():
    print('Bot ready')


@client.command(pass_context = True)
async def bhelp(ctx):

    embed = discord.Embed(
        colour = discord.Colour.orange()
    )

    embed.set_author(name='Help')
    embed.add_field(name='!register', value='Register a bingo player (Example. !register Elf)', inline=False)
    embed.add_field(name='!submit', value='Submit an entry for a tile (Example. !submit 13 Elf)', inline=False)
    embed.add_field(name='!get_all_entries', value='Get all entries for user (Example. !get_all_entries Elf)', inline=False)
    embed.add_field(name='!get_entry', value='Register a bingo player (Example. !get_entry 13 Elf)', inline=False)

    await ctx.send(embed=embed)

@client.command(pass_context=True)
@commands.has_role('Bingo Master')
async def register(ctx, *args):

    # Get the name from the args (can contain spaces)
    name = " ".join(args)

    # Form folder path with the name to track with the given username
    path = os.path.dirname(__file__) + '/' + name 
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
@commands.has_role('Bingo Master')
async def submit(ctx, tile, *args):
    # Get the name from the args (can contain spaces) and form a path
    name = " ".join(args)
    overwrite = False

    if "--ow" in name:
        split_name = name.split("--ow")
        name = split_name[0].strip()
        overwrite = True

    path = os.path.dirname(__file__) + '/' + name
    file_exists = os.path.isdir(path)
    
    if not file_exists:
        await ctx.send('Account does not exist, please use !register {name} to begin tracking.')
        return
        
    # If the account exists, create a text entry of the submission
    print(overwrite)
    try:
        create_submit_entry(path, tile, overwrite)
    except TileExistsError as e:
        await ctx.send(e)
        return

    # If the account exists, create an image entry of the submission
    img_data = requests.get(ctx.message.attachments[0].url).content
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
@commands.has_role('Bingo Master')
async def get_all_entries(ctx, *args):
    # Get the name from the args (can contain spaces) and form a path
    name = " ".join(args)
    path = os.path.dirname(__file__) + '/' + name
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
            entries.append(entry['tile'])

        entries = ', '.join(entries)
        await ctx.send('Entries exist for tiles: ' + entries)


@client.command(pass_context=True)
@commands.has_role('Bingo Master')
async def get_entry(ctx, tile, *args):
    name = " ".join(args)
    path = os.path.dirname(__file__) + '/' + name
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

        submission_time = next((entry for entry in data['entries'] if entry['tile'] == '2'), None)['submitted']

        with open(path + '/' + tile + '.jpg', 'rb') as f:
            picture = discord.File(f)
            await ctx.channel.send(content='Name: %s\nTile: %s\nSubmitted: %s' % (name, tile, submission_time), file=picture)


client.run(DISCORD_API_KEY)