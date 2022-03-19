# coub_dl
Download coubs by id or by urls from file
- moviepy very efficiently uses cpu (~100%) while converting
- downloads full audio tracks and loops video over it
- failed downloads will be listed at the end (in case of txt-file mode)
- file-mode creates subdir in working dir with txt-filename
- id-mode just downloads to working dir
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
python3 coub_downloader --id 2ck4sw
python3 coub_downloader --file nicecoubs.txt
```
## txt-file format
- just the complete urls
```
https://coub.com/view/2sq91g
https://coub.com/view/2t2fgu
https://coub.com/view/2r0typ
```