# coub_dl
Download coubs by id or batch download by file
- moviepy very efficiently uses cpu (~100%) while converting
- downloads full audio tracks and loops video over it
- failed downloads will be listed at the end (in case of txt-file mode)
- **File-Mode** creates subdir in working dir with txt-filename
- **ID-Mode** just downloads to working dir
## Dependencies
### common
- argparse
- re
- requests
- unicodedata
- json
- os
- textwrap
### others
- BeautifulSoup4 (bs4)
- moviepy
### install others and dependencies from shell/cmd
```bash
pip install beautifulsoup4 moviepy
```
## Usage
```bash
python3 coub_downloader --id 2ck4sw                 # ID-Mode
python3 coub_downloader --file nicecoubs.txt        # File-Mode
```
## txt-file format for File-Mode
- one url per line
```
https://coub.com/view/2sq91g
https://coub.com/view/2t2fgu
https://coub.com/view/2r0typ
...
```