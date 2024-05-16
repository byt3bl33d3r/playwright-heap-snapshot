# Playwright Heap Snapshot

Capture heap snapshots and query the snapshot for objects matching a set of properties. 

> [!NOTE]
> This is a port of [puppeteer-heap-snapshot](https://github.com/adriancooney/puppeteer-heap-snapshot) to Python & Playwright.
> Read more about it in the [original authors blog post](https://www.adriancooney.ie/blog/web-scraping-via-javascript-heap-snapshots).

## Install

```
pipx install git+ssh:://github.com/byt3bl33d3r/playwright-heap-snapshot.git
```

## CLI

This package comes with a small CLI that allows you to fetch heap snapshots for URLs and run queries on them. It's meant to be mostly the same as the original project 

```
$ playwright-heap-snapshot --help
                                                                                                                                                                                                                       
 Usage: playwright-heap-snapshot [OPTIONS] COMMAND [ARGS]...                                                                                                                                                           
                                                                                                                                                                                                                       
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                                                                                                             │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                                                                                                      │
│ --help                        Show this message and exit.                                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ fetch   fetch a heap snapshot for a URL and/or write to a file then output the matching objects in JSON                                                                                                             │
│ query   read a heap snapshot and output the matching objects in JSON                                                                                                                                                │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```


For example, fetch from a URL and output matching objects:

```
$ playwright-heap-snapshot query -f tests/test.heapsnapshot -p channelId,viewCount,keywords
finding objects properties=['channelId', 'viewCount', 'keywords'] ignore_properties=[]
finding property edges for string channelId
7 nodes found with property channelId
7 common nodes
finding property edges for string channelId
7 nodes found with property channelId
7 common nodes
finding property edges for string viewCount
8 nodes found with property viewCount
3 common nodes
finding property edges for string keywords
4 nodes found with property keywords
3 node(s) found, compiling object(s) [804767, 1439519, 1684179]
building node object for node 804767
compiling graph node object 804767
building node object for node 1439519
compiling graph node object 1439519
building node object for node 1684179
compiling graph node object 1684179
[
    {'lengthSeconds': '1155', 'isOwnerViewing': False, 'isCrawlable': True, 'allowRatings': True, 'isPrivate': False, 'isUnpluggedCorpus': False, 'isLiveContent': False},
    {
        'videoId': 'ux',
        'title': 'jb',
        'lengthSeconds': '90',
        'keywords': ['th', 'ts', 'yg', 'gy', 'ih', 'iq', 'zj'],
        'channelId': 'pg',
        'isOwnerViewing': 6.0,
        'shortDescription': 'ts',
        'isCrawlable': 62.0,
        'thumbnail': {
            'thumbnails': [
                {'url': 'vx', 'width': 8.0, 'height': 58.0},
                {'url': 'bp', 'width': 44.0, 'height': 79.0},
                {'url': 'oh', 'width': 47.0, 'height': 66.0},
                {'url': 'hm', 'width': 34.0, 'height': 55.0},
                {'url': 'vr', 'width': 0.0, 'height': 20.0}
            ]
        },
        'allowRatings': 24.0,
        'viewCount': '49',
        'author': 'xr',
        'isPrivate': 70.0,
        'isUnpluggedCorpus': 66.0,
        'isLiveContent': 99.0
    },
    {
        'videoId': 'L_o_O7v1ews',
        'title': 'Zoolander - The Files are IN the Computer!',
        'lengthSeconds': '21',
        'keywords': ['Zoolander', 'Movie Quotes', '2000s', 'Humor', 'Files', 'IN the Computer', 'Hansel'],
        'channelId': 'UCGQ6kU3NRI3WDxvTGIsaVjA',
        'isOwnerViewing': False,
        'shortDescription': '',
        'isCrawlable': True,
        'thumbnail': {
            'thumbnails': [
                {'url': 'https://i.ytimg.com/vi/L_o_O7v1ews/hqdefault.jpg?sqp=-oaymwEbCKgBEF5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLCRXqKq4f3pDXFysaLwvaK7zokbcA', 'width': 168.0, 'height': 94.0},
                {'url': 'https://i.ytimg.com/vi/L_o_O7v1ews/hqdefault.jpg?sqp=-oaymwEbCMQBEG5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLAUYKiFQE7AsuwoLrJZldUQRzjZig', 'width': 196.0, 'height': 110.0},
                {'url': 'https://i.ytimg.com/vi/L_o_O7v1ews/hqdefault.jpg?sqp=-oaymwEcCPYBEIoBSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLB_nQ2Un8uDxAAYOYB_E4fMaxCt2g', 'width': 246.0, 'height': 138.0},
                {'url': 'https://i.ytimg.com/vi/L_o_O7v1ews/hqdefault.jpg?sqp=-oaymwEcCNACELwBSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLB7uDAGHDaTSAe3xy5q3H2JqekbAw', 'width': 336.0, 'height': 188.0}
            ]
        },
        'allowRatings': True,
        'viewCount': '209419',
        'author': 'James Anderson',
        'isPrivate': False,
        'isUnpluggedCorpus': False,
        'isLiveContent': False
    }
]
```

## To Do

- Speed things up. It's pretty slow.
- Actually use the Pydantic models in the graph construction functions
