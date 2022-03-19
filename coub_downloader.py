import argparse
import re
import textwrap

import requests
import unicodedata
from bs4 import BeautifulSoup
import json
import moviepy.editor as mpe
import moviepy.video.fx.all as mpv
import os


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def main_id(coub_id=None, subdir=None, no_loop=False):
    if coub_id is None:
        raise ValueError('main_id did not get a coub id')
    print(f"Coub ID: {coub_id}")
    url = "https://coub.com/view/" + coub_id
    print(f"querying {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise ConnectionError(f"Failed download of {url} - {response.status_code}")
    html_file = BeautifulSoup(response.content, 'html.parser')
    data = html_file.find('script', {'id': 'coubPageCoubJson'})
    data_sanitized = data.contents[0].strip()
    data_json = json.loads(data_sanitized)
    title = slugify(data_json['title'])  # remove invalid chars
    # if title has no valid characters
    if len(title) < 1:
        title = coub_id
    else:
        title = coub_id + ' - ' + title

    # get video file
    video_url_dict = data_json['file_versions']['html5']['video']  # higher, high, med
    video_url = get_highest_from_dict(video_url_dict)
    video_stream = requests.get(video_url, stream=True)
    video_name = title + '.mp4'
    temp_video_name = 'tmp_' + video_name
    with open(temp_video_name, 'wb') as f:
        for chunk in video_stream.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    # get audio file
    temp_audio_name = None
    try:
        audio_url_dict = data_json['file_versions']['html5']['audio']  # high, med
        audio_url = get_highest_from_dict(audio_url_dict)
        try:
            audio_duration = float(data_json['file_versions']['html5']['audio']['sample_duration'])
        except KeyError:
            audio_duration = None
        audio_stream = requests.get(audio_url, stream=True)
        temp_audio_name = 'tmp_' + title + '.mp3'
        with open(temp_audio_name, 'wb') as f:
            for chunk in audio_stream.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    except KeyError:
        audio_duration = None

    # merge audio and video
    video_clip = merge_audio_video(temp_video_name, temp_audio_name, audio_duration, no_loop)
    if subdir is not None:
        video_clip.write_videofile(subdir + os.sep + video_name)
    else:
        video_clip.write_videofile(video_name)
    video_clip.close()
    # delete temp files
    print("Cleanup... ", end="")
    if temp_audio_name is not None:
        os.remove(temp_audio_name)
    os.remove(temp_video_name)
    print("Done.")

def simple_id(coub_id):
    # uses download button
    # TODO: simple
    #  https://coub-anubis-a.akamaized.net/coub_storage/coub/simple/cw_video_for_sharing/3224468e86a/c0d7b2ba8f5956db9bb25/1647569180_looped_1647569179.mp4?dl=1
    # <a class="sb -st -rn coub__download" href="https://coub-anubis-a.akamaized.net/coub_storage/coub/simple/cw_video_for_sharing/3224468e86a/c0d7b2ba8f5956db9bb25/1647569180_looped_1647569179.mp4?dl=1" download="" data-permalink="318vkk">  <i><svg width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M7 19a1 1 0 100 2h10a1 1 0 100-2H7zm-.707-8.207a1 1 0 011.414 0L11 14.086V4a1 1 0 112 0v10.086l3.293-3.293a1 1 0 111.414 1.414l-5 5a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414z" fill="#999"></path></svg></i> <span>Download</span> </a>
    pass

def main_txt(filepath=None, no_loop=False):
    if filepath is None:
        raise ValueError("main_txt did not get a filepath :(")
    # create subdir
    filename = os.path.splitext(os.path.basename(filepath))[0]
    if not os.path.exists(filename):
        os.makedirs(filename)

    success_counter = 0
    failed_coubs = []
    with open(filepath, "r") as file:
        lines = file.readlines()
    for line in lines:
        print(f"Starting {line}")
        coub_id = extract_id(line)
        try:
            main_id(coub_id, filename, no_loop)
            success_counter += 1
        except (ConnectionError, KeyError) as e:
            print(e)
            failed_coubs.append((coub_id, e))
    print(f"Successful downloads: {success_counter}")
    print(f"Failed downloads: {len(failed_coubs)}")
    print("failed coubs:")
    for failed_coub in failed_coubs:
        print(failed_coub)


def extract_id(line):
    # can be:
    # https://coub.com/view/2ck4sw
    # 2ck4sw
    http_pattern = r'http[s]*://coub.com/view/([a-zA-Z0-9]+)'
    match = re.match(http_pattern, line)
    if match is not None:
        coub_id = match.group(1)
    else:
        coub_id = line
    return coub_id


def get_highest_from_dict(url_dict):
    qualities = ['higher', 'high', 'med']
    for ele in qualities:
        if ele in url_dict.keys():
            return url_dict[ele]['url']
    raise ValueError("Found no quality")


def merge_audio_video(videofile, audiofile, audio_duration=None, no_loop=False):
    """needs videofile(path) and audiofile(path), returns mpe.VideoFileClip"""
    video = mpe.VideoFileClip(videofile)
    if audiofile is not None:
        audio = mpe.AudioFileClip(audiofile)
        video = video.set_audio(audio)
        if audio_duration is None and not no_loop:
            print(f"Looping... audio_duration = {audio.duration}")
            # https://zulko.github.io/moviepy/getting_started/effects.html?highlight=loop
            video = video.fx(mpv.loop, duration=audio.duration)
            audio_duration = audio.duration
        video = video.subclip(0, audio_duration)
    return video


if __name__ == '__main__':
    # TODO: identify mode by parameter, remove --id, --file
    parser = argparse.ArgumentParser(description='Coub downloader. RIP 2022-04-01',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent("""examples:
     coub_downloader --id 2ck4sw
     coub_downloader --file nicecoubs.txt"""))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--id', help='Coub id')
    mode.add_argument('--file', help='TXT-File with coub links or IDs')
    parser.add_argument('--no-loop', required=False, action='store_true')

    args = vars(parser.parse_args())

    if args['id'] is not None:
        main_id(args['id'])
    elif args['file'] is not None:
        main_txt(args['file'], args['no-loop'])
    else:
        raise ValueError("Please report to dev")

    # main('2wrd7u')
    # main('1203yq')
    # main('1k9fll')
    # music.duration > video.duration --> 1k9fll
