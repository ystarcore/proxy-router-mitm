from mitmproxy import http
from mitmproxy import ctx
import urllib3
import httpx
import json


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxy_path = r"proxy.json"

try:
    with open(proxy_path, "r") as file:
        proxy_data = json.load(file)
except Exception as e:
    proxy_data = {}
    ctx.log.error(f"Could not load proxy data: {e}")


class KeywordProxy:
    def __init__(self):
        self.proxies = [
            {
                "uri": proxy_data.get("proxy1", {}).get("uri"),
                "keywords": proxy_data.get("proxy1", {}).get("keywords", []),
            },
            {
                "uri": proxy_data.get("proxy2", {}).get("uri"),
                "keywords": proxy_data.get("proxy2", {}).get("keywords", []),
            },
        ]

        # self.cookie_jar = httpx.Cookies()

    async def request(self, flow: http.HTTPFlow) -> None:
        url = flow.request.pretty_url
        method = flow.request.method

        selected_proxy = None

        for proxy in self.proxies:
            if any(keyword in url for keyword in proxy["keywords"]):
                selected_proxy = proxy["uri"]
                break

        cookies = dict(flow.request.cookies.items())
        headers = dict(flow.request.headers)

        headers.pop("te", None)
        headers.pop("connection", None)
        headers.pop("proxy-connection", None)

        if selected_proxy:
            # Forward the request to the upstream proxy
            try:
                async with httpx.AsyncClient(
                    verify=False,
                    timeout=30.0,
                    # cookies=self.cookie_jar,
                    proxies={"http://": selected_proxy, "https://": selected_proxy},
                ) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=flow.request.content,
                        params=flow.request.query,
                        cookies=cookies,
                    )

                    # self.cookie_jar.update(dict(response.cookies.items()))

                    if "set-cookie" in dict(flow.request.headers):
                        flow.response.headers["set-cookie"] = response.headers[
                            "set-cookie"
                        ]

                    if response.status_code == 303:
                        location = response.headers.get("Location")
                        if location:
                            ctx.log.info(
                                f" ------------- Redirecting to ----------: {location}"
                            )
                            return

                    res_headers = http.Headers()

                    for k, v in response.headers.items():
                        if k.lower() == "set-cookie":
                            for c in response.headers.get_list(k):
                                res_headers.add(k, c)
                        else:
                            res_headers.add(k, v)

                    flow.response = http.Response.make(
                        status_code=response.status_code,
                        content=response.content,
                        headers=res_headers,
                    )

                ctx.log.info(f"Forwarding request to upstream proxy: {url}")
            except (
                httpx.HTTPStatusError,
                httpx.RequestError,
                httpx.ConnectError,
                httpx.LocalProtocolError,
            ) as e:
                ctx.log.error(f"Proxy connection failed: {e}")
                flow.response = http.Response.make(
                    403,
                    b"Unable to connect to the proxy",
                    {"Content-Type": "text/plain"},
                )
            except Exception as e:
                ctx.log.error(f"Unexpected error: {e}")
                flow.response = http.Response.make(500, b"Internal server error.")
        else:
            # Directly serve the request
            ctx.log.info(f"Serving request directly: {url}")
            pass

    def response(self, flow: http.HTTPFlow) -> None:
        # Ensure response cookies are properly passed to the browser
        if "set-cookie" in flow.response.headers:
            ctx.log.info(
                f"Set-Cookie header found: {flow.response.headers['set-cookie']}"
            )


addons = [KeywordProxy()]
