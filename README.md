```
███████╗██╗                   ██████╗ ████████╗
██╔════╝██║                   ██╔══██╗╚══██╔══╝
█████╗  ██║         █████╗    ██████╔╝   ██║   
██╔══╝  ██║         ╚════╝    ██╔══██╗   ██║   
██║     ███████╗              ██████╔╝   ██║   
╚═╝     ╚══════╝              ╚═════╝    ╚═╝   
```

This project is a wrapper for separating tracks of songs from YouTube URLs using Spleeter. This works in a API, then you can call the `/yt-path/{url:path}` to receive the result as a `.zip` file.

Still so experimental, doesn't checks nothing related to data transmission or even multiple requests at same time. This is not good for low-end machines, specially low-end VSPs. Medium and higher computers can run this  softly.

> Note: this project uses Python 3.10 due to the compatibility with current Spleeter development state.