# What these two folders are

`vault/` is the one running server: it gives Claude its tools for this vault (search, session brief, skill lookup).
`kb/` is the meaning-search engine that `vault/` loads, so vague questions still find the right notes.
You never run either by hand; `install.py` wires them up and the Claude apps start them.
