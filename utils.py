from datetime import datetime
import os
import json
from errors import TileExistsError

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

def get_completed_lines(matrix):
    fully_completed_rows = [row for row in matrix if all(cell == 'X' for cell in row)]
    fully_completed_columns = [list(column) for column in zip(*matrix) if all(cell == 'X' for cell in column)]
    fully_completed_diagonals = []

    main_diagonal = [matrix[i][i] for i in range(min(len(matrix), len(matrix[0]))) if matrix[i][i] == 'X']
    if len(main_diagonal) == min(len(matrix), len(matrix[0])):
        fully_completed_diagonals.append(main_diagonal)

    anti_diagonal = [matrix[i][len(matrix[0]) - 1 - i] for i in range(min(len(matrix), len(matrix[0]))) if matrix[i][len(matrix[0]) - 1 - i] == 'X']
    if len(anti_diagonal) == min(len(matrix), len(matrix[0])):
        fully_completed_diagonals.append(anti_diagonal)

    return f'Rows completed: {len(fully_completed_rows)}', f'Columns completed: {len(fully_completed_columns)}', f'Diagonals completed: {len(fully_completed_diagonals)}'