"""
localguard.py  --  no passwords, and still not open to the internet.

Maha Transcribe holds no server-side state at all -- every key, every
transcript, every setting lives in the browser's own localStorage, and the
Flask process here does one job: hand over one static HTML file. That is a
much smaller attack surface than GDRIVE_DOWNLOADER's job queue, but it is
not zero:

    any site you visit can make your browser send requests to
    http://127.0.0.1:8420 in the background. Binding to 127.0.0.1 alone
    stops the network from reaching in, it does NOT stop DNS REBINDING: a
    site can point a hostname at 127.0.0.1 after the fact, so the
    connection really is local but the browser still sends a Host header
    naming their domain, not this one.

One check closes that, and it costs nothing to use:

    HOST    the Host header must be a loopback name. Reading it is what
            catches a rebound request; binding to 127.0.0.1 by itself does
            not.

There is no Origin/guard-header check here the way GDRIVE_DOWNLOADER has
one, because that guards POST endpoints that change something on disk --
credentials, running jobs, deleted files. This app has no such endpoint.
If one is ever added, port the rest of the original guard over rather than
inventing a second one; see modules/keyring.md's own rule about reusing a
solved problem instead of rewriting it.

Ported from markoboskoauroville/GDRIVE_DOWNLOADER_FLASK_MACOS/localguard.py.
"""

from flask import jsonify, request

# Loopback by every name it answers to. A Host that is not one of these did
# not come from a browser pointed at this app.
# NOT 0.0.0.0. bandit flagged it in the original and it was right to: 0.0.0.0
# means "every interface", so accepting it as a loopback name would let a
# request that arrived from the network past the check.
LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]", "::1"}


def _host_ok(host_header):
    if not host_header:
        return False
    host = host_header.rsplit(":", 1)[0] if host_header.count(":") == 1 else host_header
    if host.startswith("[") and "]" in host:
        host = host[:host.index("]") + 1]
    return host in LOCAL_HOSTS


def check(port):
    """Returns None to allow, or a (body, status) to refuse.

    Called from a before_request hook. Deliberately small: a guard nobody
    can read is a guard nobody can check.
    """
    if not _host_ok(request.headers.get("Host", "")):
        return (jsonify({
            "error": "This app only answers to 127.0.0.1. The address used "
                     "to reach it was different, which is what a "
                     "DNS-rebinding attack looks like. Open "
                     "http://127.0.0.1:%d instead." % port
        }), 403)

    return None
