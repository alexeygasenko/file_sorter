import logging
import os
from collections import namedtuple

import click
import eyed3
import re

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

Tags = namedtuple('Tags', ['title', 'artist', 'album'])

def replace_symbols(tags):
    """
    Replaces special symbols using regex.

    :param tags: - file tags
    :return: - changed tags
    """
    if tags.tag.title is not None:
        tags.tag.title = re.sub(r'[<>/\\:*?"|]', '', tags.tag.title).strip()

    if tags.tag.artist is not None:
        tags.tag.artist = re.sub(r'[<>/\\:*?"|]', '', tags.tag.artist).strip()

    if tags.tag.album is not None:
        tags.tag.album = re.sub(r'[<>/\\:*?"|]', '', tags.tag.album).strip()

    return tags

def filter_files(directory_contents):
    """
    Checks if directory content is a file (not a folder)
    and file extension is .mp3.

    :param directory_contents: - iterator of os.DirEntry objects
    :return: - generator
    """
    for entry in directory_contents:
        file_extension = os.path.splitext(entry.name)[1]

        if entry.is_file() and file_extension == '.mp3':
            yield entry

def read_tags(path):
    """
    Reads tags of the file and puts them into namedtuple.

    :param path: - path to the file
    :return: - namedtuple of tags
    """
    file_tags = eyed3.load(path)
    if file_tags.tag is not None:
        file_tags = replace_symbols(file_tags)
        tags = Tags(file_tags.tag.title, file_tags.tag.artist, file_tags.tag.album)
    else:
        return None
    return tags

def move_file(entry, tags, src_dir, dst_dir):
    """
    Moves file to destination directory

    :param entry: - DirEntry object the contains file information.
    :param tags: - file tags
    :param src_dir: - source directory path
    :param dst_dir: - destination directory path
    """
    if tags is None:
        return

    if not tags.artist or not tags.album:
        return

    dir_path = os.path.join(dst_dir, tags.artist, tags.album)

    src_file_path = os.path.join(src_dir, entry.name)

    if not tags.title:
        dst_file_path = os.path.join(dir_path, entry.name)
    else:
        file_extension = os.path.splitext(entry.name)[1]
        new_file_name = f'{tags.title} - {tags.artist} - {tags.album}{file_extension}'
        dst_file_path = os.path.join(dir_path, new_file_name)

    try:
        try:
            os.renames(src_file_path, dst_file_path)
            click.echo(f'{src_file_path} -> {dst_file_path}')
        except FileExistsError:
            os.replace(src_file_path, dst_file_path)
            click.echo(f'{src_file_path} -> {dst_file_path}')
    except OSError as err:
        print(f'Something went wrong, cannot move file {src_file_path}!\nError: {err}')

@click.command()
@click.option('-s', '--src-dir', default='.', help='Source directory.')
@click.option('-d', '--dst-dir', default='.', help='Destination directory.')
def sort_files(src_dir, dst_dir):
    """
    Sorts music files by moving them into corresponding folders using
    their tags (artist, album, title).

    :param src_dir: - source directory path
    :param dst_dir: - destination directory path
    """
    if not os.path.isdir(src_dir):
        click.echo('Source directory does not exist!')
        return

    directory_contents = os.scandir(src_dir)

    for entry in filter_files(directory_contents):
        tags = read_tags(entry.path)
        move_file(entry, tags, src_dir, dst_dir)

    click.echo('Done.')

if __name__ == '__main__':
    sort_files()