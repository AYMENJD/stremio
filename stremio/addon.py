import asyncio
import os.path
from http import HTTPStatus as status
from urllib.parse import parse_qs

import uvicorn
from blacksheep import Application, Request, json, Response, HTMLContent, Content
from blacksheep.client import ClientSession
from blacksheep.settings.json import json_settings

from . import json_dumps, json_loads, lint_manifest

json_settings.use(
    loads=json_loads,
    dumps=json_dumps,
)

DEFAULT_CENTRAL_API_URL = "https://api.strem.io"


def json_response(
    data,
    status_code: int = status.OK,
    headers: dict = None,
):
    res = json(
        data,
        status=status_code,
    )

    if headers:
        for k, v in headers.items():
            res.headers.add(k.encode("utf-8"), v.encode("utf-8"))

    return res


class Addon:
    def __init__(
        self,
        manifest: dict,
        static_dir: list = None,
        cache_max_age: int = 0,
        host: str = "0.0.0.0",
        port: int = 7000,
        public_host: str = "",
        log_level: str = "info",
    ):
        """
        Create a new Stremio addon

        Parameters:
            manifest (``dict``):
                The manifest dictionary containing addon metadata. See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/manifest.md

            static_dir (``str`` || ``list``, *optional*):
                A list of directories to serve static files from. Default is ``None``

            cache_max_age (``int``, *optional*):
                The cache max age for responses. Default is ``0``

            host (``str``, *optional*):
                The host address to bind the server to. Default is "0.0.0.0"

            port (``int``, *optional*):
                The port number to bind the server to. Default is ``7000``

            public_host (``str``, *optional*):
                The public host address for the addon. Default is an empty string

            log_level (``str``, *optional*):
                The log level for the server. Default is "info"
        """

        assert isinstance(static_dir, (list, str, type(None))), (
            "static_dir must be list or str"
        )
        assert isinstance(cache_max_age, int), "cache_max_age must be integer"

        assert isinstance(host, str), "host must be string"
        assert isinstance(port, int), "port must be integer"
        assert isinstance(public_host, str), "public_host must be string"
        assert isinstance(log_level, str), "log_level must be string"

        lint_manifest(manifest)

        self.manifest = manifest
        self.cache_max_age = cache_max_age
        self.log_level = log_level
        self.cache_headers = {
            "cacheMaxAge": "max-age",
            "staleRevalidate": "stale-while-revalidate",
            "staleError": "stale-if-error",
        }

        if len(json_dumps(manifest)) > 8192:
            raise manifest(
                "manifest size exceeds 8kb, which is incompatible with addonCollection API"
            )

        self.__app = Application()
        self.__host = host
        self.__port = port
        self.__public_host = public_host
        self.__handlers = {}
        self.__landing_page_callback = None

        async def landingPage(req: Request):
            if self.__landing_page_callback:
                return Response(
                    200, content=HTMLContent(await self.__landing_page_callback(req))
                )
            else:
                return json_response(
                    None,
                    status.TEMPORARY_REDIRECT,
                    {"Location": "https://github.com/AYMENJD/stremio"},
                )

        async def manifestHandler():
            return json_response(self.manifest)

        async def resolveResource(req: Request, resource, type_, id_):
            return await self.__handle_request(req, resource, type_, id_)

        async def resolveResourceExtraArgs(
            req: Request, resource, type_, id_, extra_arg
        ):
            return await self.__handle_request(req, resource, type_, id_, extra_arg)

        @self.__app.after_start()
        async def after_start():
            print(f"Server running on http://{self.__host}:{self.__port}")
            if public_host:
                print(f"Addon installation link: stremio://{public_host}/manifest.json")

        self.__app.use_cors(
            allow_methods="*",
            allow_origins="*",
            allow_headers="*",
        )

        static_dir = [static_dir] if isinstance(static_dir, str) else static_dir

        if static_dir:
            for dir_ in static_dir:
                path = os.path.abspath(dir_)
                print(f"Serving static files in {path}")
                self.__app.serve_files(
                    path,
                    cache_time=cache_max_age,
                    root_path=os.path.basename(path),
                )

        self.__app.router.add_get("/", landingPage)
        self.__app.router.add_get("/manifest.json", manifestHandler)
        self.__app.router.add_get("/{resource}/{type_}/{id_}.json", resolveResource)
        self.__app.router.add_get(
            "/{resource}/{type_}/{id_}/{extra_arg}.json", resolveResourceExtraArgs
        )

    async def publishToCentral(self, manifest_url: str, api_url: str = None):
        """Publishes the addon to addon catalogs

        Example:
            .. code-block:: python

                >>> await publishToCentral("https://example.com/manifest.json")
                >>> await publishToCentral("https://example.com/manifest.json", "https://api.example.com")

        Parameters:
            manifest_url (``str``):
                URL of the addon manifest to publish

            api_url (``str``, *optional*):
                Central registry API URL, Default is ``https://api.strem.io``
        """
        assert isinstance(manifest_url, str)

        api_url = api_url if isinstance(api_url, str) else DEFAULT_CENTRAL_API_URL

        async with ClientSession(base_url=api_url) as req:
            res = await req.post(
                "/api/addonPublish",
                content=Content(
                    b"application/json",
                    data=json_dumps(
                        {"transportUrl": manifest_url, "transportName": "http"}
                    ).encode("utf-8"),
                ),
            )
            return res.json(json_loads)

    def add_handler(self, resource, handler):
        """
        Add a handler for a specific resource

        Example:
            .. code-block:: python
            >>> addon = Addon()
            >>> async def my_handler(data):  # data is a dictionary containing the request data
            ...     pass
            >>> addon.add_handler('resource_name', my_handler)

        Parameters:
            resource (``str``):
                The name of the resource for which the handler is being added. Eg: "meta", "stream", "catalog", "subtitles"

            handler (``function``):
                The async function that will handle the resource

        """

        if resource in self.__handlers:
            raise ValueError(f"Handler for {resource} already exists")
        else:
            if not asyncio.iscoroutinefunction(handler):
                raise ValueError(f"{resource} handler must be async function")

            self.__handlers[resource] = handler

    def landing_page(self):
        """Decorator to add a landing page handler. the function must return a string containing the HTML content"""

        if self.__landing_page_callback:
            raise ValueError("Landing page handler already exists")

        def decorator(func):
            self.__landing_page_callback = func
            return func

        return decorator

    def stream(self):
        """
        Decorator to add a stream handler. It's expected to return a dictionary containing the streams data
        See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/stream.md
        """

        def decorator(func):
            self.add_handler("stream", func)
            return func

        return decorator

    def meta(self):
        """
        Decorator to add a meta handler. It's expected to return a dictionary containing the meta data.
        See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/meta.md
        """

        def decorator(func):
            self.add_handler("meta", func)
            return func

        return decorator

    def catalog(
        self,
    ):
        """
        Decorator to add a catalog handler. It's expected to return a list containing meta data.
        See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/requests/defineCatalogHandler.md#returns
        """

        def decorator(func):
            self.add_handler("catalog", func)
            return func

        return decorator

    def subtitles(
        self,
    ):
        """
        Decorator to add a subtitles handler. It's expected to return a dictionary containing the subtitles data.
        See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/subtitles.md
        """

        def decorator(func):
            self.add_handler("subtitles", func)
            return func

        return decorator

    async def __handle_request(self, req: Request, resource, type_, id_, extra=None):
        if resource not in self.__handlers:
            return json_response({"error": "Bad request"}, status.BAD_REQUEST)

        extra_args = (
            None
            if not isinstance(extra, str)
            else {k: v[0] if len(v) == 1 else v for k, v in parse_qs(extra).items()}
        )

        fres = await self.__handlers[resource](
            {
                "id": id_,
                "type": type_,
                "extraArgs": extra_args,
            }
        )

        if not isinstance(fres, dict):
            raise ValueError(f"{resource} handler must return a dictionary")

        cache_headers = [
            f"{v}={fres[k]}" for k, v in self.cache_headers.items() if k in fres
        ]

        headers = (
            {"Cache-Control": f"{', '.join(cache_headers)}, public"}
            if cache_headers
            else None
        )

        return json_response(data=fres, headers=headers)

    def run(self):
        """Run the addon server; Blocking call"""
        for t in self.manifest["resources"]:
            if t not in self.__handlers:
                raise ValueError(f"Handler for type {t} is missing")

        uvicorn.run(
            self.__app,
            host=self.__host,
            port=self.__port,
            headers=(
                ("Cache-Control", f"max-age={self.cache_max_age}, public"),
                ("X-Powered-By", "aymenjd/stremio"),
            ),
            log_level=self.log_level,
        )
