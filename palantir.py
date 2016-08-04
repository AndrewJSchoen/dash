#!/usr/bin/env python

import sys
import os
import json
import shutil
import string
import copy
import re
import datetime
from docopt.docopt import docopt

Version = "0.1.3"
doc = """
Palantir.

Usage:
  palantir create <dir> (-n <text> | --name <text>)
  palantir update <dir> [--addrow <row>...] [--rmrow <row>...] [--addcol <col>...] [--rmcol <col>...]
  palantir cell <dir> (-r <row> | --row <row>) (-c <col> | --col <col>) [options]

Commands:
  create       Create an empty dashboard in the directory specified.
  update       Update a dashboard in the directory specified. See options for specifics.
  cell         Update specific cells by row/column id.

Options:
  -h --help                     Show this screen.
  -v --version                  Show the current version.
  -n <text> --name <text>       Specify the name of the dashboard. (create)
  --addrow <row>...             Add a row. (update)
  --addcol <col>...             Add a column. (update)
  --rmrow <row>...              Remove a row. (update)
  --rmcol <col>...              Remove a column. (update)
  -r <row> --row <row>          Specify the row of the cell. (cell)
  -c <col> --col <col>          Specify the column of the cell. (cell)
  --settext <text>              Specify the new text. (cell)
  --setbgcolor <hex>            Specify the new background color. (cell)
  --settxtcolor <hex>           Specify the new text color. (cell)
  --setanimate <animation>      Specify the animation.
                                Choose from 'wave', 'toggle', 'bars', or 'none'. (cell)
  --setbool <bool>              Specify the value of the cell boolean.
                                Choose from 'True', 'False' or 'None'. (cell)
  --addimage <path>             Add an image to the cell. (cell)
  --rmimage <index>             Remove an image from the cell. (cell)
  --addnote <text>              Add a note to the cell. (cell)
"""

def write_json(path, data):
    with open(path, 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4, ensure_ascii=False)

def update_json(path, callback=None, **kwargs):
    with open(cleaned_path(path), "r+") as jsonFile:
        jsondata = json.load(jsonFile)
        newdata = callback(byteify(jsondata), **kwargs)
        if newdata != None and newdata != jsondata:
            jsonFile.seek(0)
            jsonFile.truncate()
            json.dump(newdata, jsonFile, sort_keys=True, indent=4, ensure_ascii=False)
            return newdata
        else:
            raise IOError("Update not completed. Check that your input parameters were correct.")
            return None

def read_json(path):
    try:
        with open(cleaned_path(path), "r") as jsonFile:
          jsondata = json.load(jsonFile)
          jsonFile.seek(0)
        return byteify(jsondata)
    except:
        raise IOError("Error! json file '{0}' does not exist!".format(cleaned_path(path)))
        return None

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [ byteify(element) for element in input ]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def is_hex_color(string):
    match = re.search(r'^#(?:[0-9a-fA-F]{1,2}){3}$', string)
    return match

def idify(name):
    valid_chars = "-_.{0}{1}".format(string.ascii_letters, string.digits)
    returnid = ''.join(c for c in name if c in valid_chars)
    return returnid

def get_dash_src():
    return os.path.abspath(os.path.join(os.path.dirname( __file__ )))

def cleaned_path(path):
  if path.endswith("/"):
    path = path[:-1]
  if path.startswith("="):
    path = path[1:]
  realpath = os.path.realpath(os.path.expanduser(path))
  return realpath

def structure_updater(structure, root, add_columns=None, remove_columns=None, add_rows=None, remove_rows=None):
    working = copy.deepcopy(structure)
    removed_columns = []
    removed_rows = []
    added_columns = []
    added_rows = []
    if add_columns != None and add_columns != []:
        for column in add_columns:
            candidate_column_id = idify(column)
            if candidate_column_id not in [existingcolumn["id"] for existingcolumn in structure["cols"]]:
                working["cols"].append({"id":candidate_column_id,"text":str(column)})
                added_columns.append({"id":candidate_column_id,"text":str(column)})
    if add_rows != None and add_rows != []:
        for row in add_rows:
            candidate_row_id = idify(row)
            if candidate_row_id not in [existingrow["id"] for existingrow in structure["rows"]]:
                working["rows"].append({"id":candidate_row_id,"text":str(row)})
                added_rows.append({"id":candidate_row_id,"text":str(row)})
    if remove_columns != None and remove_columns != []:
        for column in remove_columns:
            if idify(column) in [existingcolumn["id"] for existingcolumn in working["cols"]]:
                for candidate_remove_column in working["cols"]:
                    if idify(column) == candidate_remove_column["id"]:
                        working["cols"].remove(candidate_remove_column)
                        removed_columns.append(idify(column))
    if remove_rows != None and remove_rows != []:
        for row in remove_rows:
            if idify(row) in [existingrow["id"] for existingrow in working["rows"]]:
                for candidate_remove_row in working["rows"]:
                    if idify(row) == candidate_remove_row["id"]:
                        working["rows"].remove(candidate_remove_row)
                        removed_rows.append(idify(row))
    if len(working["rows"]) >= 1 and len(working["cols"]) >= 1:
        for column in removed_columns:
            for cell in ["{0}-{1}".format(row["id"], column) for row in structure["rows"]]:
                try:
                    os.unlink(root+"/data/"+cell+".json")
                except:
                    pass
        for row in removed_rows:
            for cell in ["{0}-{1}".format(row, column["id"]) for column in structure["cols"]]:
                try:
                    os.unlink(root+"/data/"+cell+".json")
                except:
                    pass
        structure_row_set = set([row["id"] for row in structure["rows"]])
        structure_col_set = set([col["id"] for col in structure["cols"]])
        removed_row_set = set(removed_rows)
        removed_col_set = set(removed_columns)
        added_row_set = set([row["id"] for row in added_rows])
        added_col_set = set([col["id"] for col in added_columns])
        structure_row_set.difference_update(removed_row_set)
        structure_row_set.update(added_row_set)
        structure_col_set.difference_update(removed_col_set)
        structure_col_set.update(added_col_set)
        final_rows = list(structure_row_set)
        final_columns = list(structure_col_set)

        added_cells = set()
        for column in final_columns:
            for row in list(added_row_set):
                added_cells.add("{0}-{1}".format(row, column))
        for row in final_rows:
            for column in list(added_col_set):
                added_cells.add("{0}-{1}".format(row, column))
        for cell in list(added_cells):
            try:
                defaultcell = {
                  "id": cell,
                  "text": "",
                  "bgcolor": "#F0F0F0",
                  "color": "#969696",
                  "animation": "none",
                  "images": [],
                  "notes": [],
                  "boolean": "none"
                }
                write_json(root+"/data/"+cell+".json", defaultcell)
            except:
                pass
        return working
    else:
        raise IOError("Errors were found with your update. No changes were made.")
        return structure

def cell_updater(cell, root, row_id=None, column_id=None, text=None, background_color=None, text_color=None, boolean=None, animation=None, add_image=None, remove_image=None, add_note=None):
    working = copy.deepcopy(cell)
    if text != None and type(text) == str:
        working["text"] = str(text)
    if background_color != None and is_hex_color(background_color):
        working["bgcolor"] = background_color
    if text_color != None and is_hex_color(text_color):
        working["color"] = text_color
    if boolean != None and boolean in [True, "True","true"]:
        working["boolean"] = True
    elif boolean != None and boolean in [False, "False","false"]:
        working["boolean"] = False
    elif boolean != None and boolean in ["None", "none"]:
        working["boolean"] = None
    if animation != None and animation in ["none", "wave", "toggle", "bars"]:
        working["animation"] = animation
    if add_note != None and type(add_note) == str:
        working["notes"] = [{"timestamp":datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), "text":add_note}]+working["notes"]
    if remove_image != None and type(int(remove_image)) == int:
        try:
            index = int(remove_image)
            imagepath = root+"/"+working["images"][index]
            os.unlink(imagepath)
            working["images"].remove(working["images"][index])
        except:
            pass
    if add_image != None and type(add_image) == str:
        try:
            filepath, filename = os.path.split(cleaned_path(add_image))
            destination = root+"/images/"+filename
            shutil.copyfile(cleaned_path(add_image), destination)
            relpath = "images/"+filename
            working["images"].append(relpath)
        except:
            pass
    return working

def create(dirpath, name):
    """
    create : create the dashboard
    ----------------

    #usage:
    `create(dirpath, name)`
    Specify the path to the directory you want to use as a dashboard, and the name of the dashboard.
    """
    src = get_dash_src()
    root = cleaned_path(dirpath)
    os.makedirs(root)
    os.mkdir(root+"/data")
    os.mkdir(root+"/images")
    shutil.copytree(src+"/resources/assets", root+"/assets")
    shutil.copytree(src+"/resources/templates", root+"/templates")
    shutil.copyfile(src+"/resources/index.html", root+"/index.html")
    startingdata = {"name": name, "rows": [], "cols": []}
    write_json(root+"/data/structure.json", startingdata)

def update(dirpath, add_columns=None, remove_columns=None, add_rows=None, remove_rows=None):
    """
    update : update a dashboard's structure
    ----------------

    #usage:
    `update(dirpath, add_columns=None, remove_columns=None, add_rows=None, remove_rows=None)`
    dirpath: Specify the path to the dashboard directory.
    All other arguments are optional, and take lists of strings
    For adding row/columns, strings are the row/column names
    For removing rows/columns, strings are the row/column ids
    """
    root = cleaned_path(dirpath)
    update_json(root+"/data/structure.json", callback=structure_updater, root=root, add_columns=add_columns, remove_columns=remove_columns, add_rows=add_rows, remove_rows=remove_rows)

def cell(dirpath, row_id, column_id, text=None, background_color=None, text_color=None, boolean=None, animation=None, add_image=None, remove_image=None, add_note=None):
    """
    cell : update a cell's characteristics
    ----------------

    #usage:
    `cell(dirpath, row_id, column_id, text=None, background_color=None, text_color=None, boolean=None, animation=None, add_image=None, remove_image=None, add_note=None)`
    dirpath: Specify the path to the dashboard directory.
    row_id: Specify the row of the cell.
    column_id: Specify the column of the cell.
    All other arguments are optional:
        text: string
        background_color: string (hex code, e.g. #f5f5f5)
        text_color: string (hex code, e.g. #f5f5f5)
        boolean: boolean value (or string 'none' to set to none.)
        animation: string, choose from ['wave', 'bars', 'toggle', 'none']
        add_image: string, path.
        remove_image: int (index of image to remove)
        add_note: string
    """
    root = cleaned_path(dirpath)
    update_json(root+"/data/{0}-{1}.json".format(row_id, column_id), callback=cell_updater, root=root, row_id=row_id, column_id=column_id, text=text, background_color=background_color, text_color=text_color, boolean=boolean, animation=animation, add_image=add_image, remove_image=remove_image, add_note=add_note)

def query(dirpath, row_id=None, column_id=None, field=None):
    print()

#============================================================================
#       Main
#============================================================================

if __name__ == '__main__':
    arguments = docopt(doc, version='Dash v{0}'.format(Version))
    if arguments["create"] == True:
        create(arguments["<dir>"], arguments["--name"])
    elif arguments["update"] == True:
        update(arguments["<dir>"], add_columns=arguments["--addcol"],
                                   remove_columns=arguments["--rmcol"],
                                   add_rows=arguments["--addrow"],
                                   remove_rows=arguments["--rmrow"])
    elif arguments["cell"] == True:
        cell(arguments["<dir>"], row_id=arguments["--row"],
                                 column_id=arguments["--col"],
                                 text=arguments["--settext"],
                                 background_color=arguments["--setbgcolor"],
                                 text_color=arguments["--settxtcolor"],
                                 boolean=arguments["--setbool"],
                                 animation=arguments["--setanimate"],
                                 add_image=arguments["--addimage"],
                                 remove_image=arguments["--rmimage"],
                                 add_note=arguments["--addnote"])
