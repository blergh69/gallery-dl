# -*- coding: utf-8 -*-

# Copyright 2021 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://kemono.party/"""

from .common import Extractor, Message
from .. import text, util


class KemonopartyExtractor(Extractor):
    """Base class for kemonoparty extractors"""
    category = "kemonoparty"
    root = "https://kemono.party"
    directory_fmt = ("{category}", "{user_id}")
    filename_fmt = "{post_id}_{title}_{filename}.{extension}"
    archive_fmt = "{user_id}_{post_id}_{filename}.{extension}"

    def items(self):
        for post in self.posts():

            post["post_id"] = post["id"]
            post["user_id"] = post["user"]
            post["date"] = text.parse_datetime(
                post["published"], "%a, %d %b %Y %H:%M:%S %Z")

            files = []
            if post["file"]:
                files.append(post["file"])
            if post["attachments"]:
                files.extend(post["attachments"])

            util.delete_items(post, ("id", "user", "file", "attachments"))
            yield Message.Directory, post

            names = set()
            post["num"] = 0
            for file in files:
                name = file["name"]
                if name not in names:
                    names.add(name)
                    post["num"] += 1
                    text.nameext_from_url(name, post)
                    yield Message.Url, self.root + file["path"], post


class KemonopartyUserExtractor(KemonopartyExtractor):
    """Extractor for all posts from a kemono.party user listing"""
    subcategory = "user"
    pattern = r"(?:https?://)?kemono\.party/([^/?#]+)/user/(\d+)/?(?:$|[?#])"
    test = ("https://kemono.party/fanbox/user/6993449", {
        "range": "1-25",
        "count": 25,
    })

    def __init__(self, match):
        KemonopartyExtractor.__init__(self, match)
        service, user_id = match.groups()
        self.api_url = "{}/api/{}/user/{}".format(self.root, service, user_id)

    def posts(self):
        url = self.api_url
        params = {"o": 0}

        while True:
            posts = self.request(url, params=params).json()
            yield from posts

            if len(posts) < 25:
                return
            params["o"] += 25


class KemonopartyPostExtractor(KemonopartyExtractor):
    """Extractor for a single kemono.party post"""
    subcategory = "post"
    pattern = r"(?:https?://)?kemono\.party/([^/?#]+)/user/(\d+)/post/(\d+)"
    test = ("https://kemono.party/fanbox/user/6993449/post/506575", {
        "pattern": r"https://kemono\.party/files/fanbox"
                   r"/6993449/506575/P058kDFYus7DbqAkGlfWTlOr\.jpeg",
        "keyword": {
            "added": "Wed, 06 May 2020 20:28:02 GMT",
            "content": str,
            "date": "dt:2019-08-11 02:09:04",
            "edited": None,
            "embed": dict,
            "extension": "jpeg",
            "filename": "P058kDFYus7DbqAkGlfWTlOr",
            "num": 1,
            "post_id": "506575",
            "published": "Sun, 11 Aug 2019 02:09:04 GMT",
            "service": "fanbox",
            "shared_file": False,
            "subcategory": "post",
            "title": "c96取り置き",
            "user_id": "6993449",
        },
    })

    def __init__(self, match):
        KemonopartyExtractor.__init__(self, match)
        service, user_id, post_id = match.groups()
        self.api_url = "{}/api/{}/user/{}/post/{}".format(
            self.root, service, user_id, post_id)

    def posts(self):
        posts = self.request(self.api_url).json()
        return (posts[0],) if len(posts) > 1 else posts
