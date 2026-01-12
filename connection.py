import socket
from ssl import create_default_context
from sys import argv

"""
    SUMMARY: Here we went from an empty file to a rudimentary web browser that can
    1. parse a URL into a scheme, host, port, and path
    2. connect to that host using the socket and ssl libraries
    3. send an HTTP request to that host, including a Host header
    4. split the HTTP response into a status line, headers, and a body
    5. print the text (and not the tags) in the body
"""

class URL:
    def __init__(self, url) -> None:
        """Construct the elements (scheme, host, path) from the given url"""
        try:
            self.scheme, url = url.split("://", 1)
            assert self.scheme in {"http", "https", "file"}, "glimpse only supports http(s) & file protocol"

            if self.scheme == "http": self.port = 80
            elif self.scheme == "https": self.port = 443 # for https
            elif self.scheme == "file": self.port = 445

            if '/' not in url: url += '/'

            self.host, url = url.split('/', 1)
            self.path = '/' + url

            # supporting custom port
            if ':' in self.host:
                self.host, port = self.host.split(':', 1)
                self.port = int(port)

            # setting headers
            self.http_version = 1.1
            self.user_agent = "Mozilla/5.0"
            # `close` indicates that either the client or the server would like to close the connection
            self.connection = "close"
            self.content_language = "en-US"
        except:
            print("Malformed URL found")
            print("Formation of a standard url is 'https://www.google.com:8000/index.html'")

    def __repr__(self):
        """Representation of a URL object"""
        return f"URL(scheme={self.scheme}, host={self.host}, port={self.port}, path={self.path!r})"

    def request(self):
        """
            Download the web page at the given url
            1. connect to the host (server) using sockets
            2. request for data and get the response
            3. extract informations from the response
            4. finally return the body from the response
        """

        # creating a socket named `sock`
        # family: tells us how to find the other computer
        # type: describes the sort of conversation that's going to happen
        # protocol: describes the steps by which the two computer will establish a connection
        sock = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )

        # use the socket `sock` to connect to the other computer
        # (this won't work if we're offline or we're behind a proxy)
        # for IP sockets, the address is a pair (host, port).
        # port depends on the protocol we are using, for http protocol, the port is 80
        sock.connect((self.host, self.port))

        # Making the connection encrypted with ssl if the scheme is `https`

        # The https scheme, or more formally HTTP over TLS (Transport Layer Security),
        # is identical to the normal http scheme
        # except that all communication between the browser and the host is encrypted.
        # Luckily, the Python ssl library implements all of these for us
        # so making an encrypted connection is almost as easy as making a regular connection.

        # Suppose we’ve already created a socket, `sock`, and connected it to example.org.
        # To encrypt the connection, we use ssl.create_default_context to create a context `context`
        # and use that context to wrap the socket `sock`
        if self.scheme == "https":
            context = create_default_context()
            sock = context.wrap_socket(sock, server_hostname=self.host)

        # now we have a (encrypted) connection
        # we now make a request to the other server
        request = f"GET {self.path} HTTP/{self.http_version}\r\nHost: {self.host}\r\n"
        request += f"User-Agent: {self.user_agent}\r\n"
        request += f"Connection: {self.connection}\r\n"
        request += f"Content-Language: {self.content_language}\r\n"
        request += "\r\n" # sending that blank line at the end of the request
        # we need to send raw bits and bytes (not string)
        # so we are encoding the string into bytes using utf-8 encoding
        sock.send(request.encode("utf-8"))

        # reading the server's response
        # makefile returns a file-like object containing every byte we
        # receive from the server
        response = sock.makefile('r', encoding="utf-8", newline="\r\n")

        # extracting information from the response
        statusline = response.readline() # the first line is the status line
        version, status, explanation = statusline.split(' ', 2)

        # after the status line, we get the headers
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(':', 1)
            response_headers[header.casefold()] = value.strip()

        # a couple of headers are especially important because
        # they tell us that the data we're trying to access is
        # being sent in an unsual way
        # so, make sure that we don't have these headers from the response
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        # the usual way to get the data is everything after the headers
        # this is the body, that we're going to display
        content = response.read()
        sock.close() # close the connection

        return content # return the body

def show(body):
    """Take the page HTML and print all the text, but not the tags, in it"""
    # this loop goes through the request body character by character
    # states: inside_tag, when it is currently between a pair of angle brackets, and not inside_tag.
    # When the current character is an angle bracket, it changes between those states
    # normal characters, not inside a tag, are printed.
    inside_tag = False
    for char in body:
        if char == "<": inside_tag = True
        elif char == ">": inside_tag = False
        elif not inside_tag: print(char, end='')

def load(url):
    """Load a web page just by stringing together request and show"""
    body = url.request() # url is an object from the URL class
    show(body)


if __name__ == "__main__":
    url = URL(argv[1])
    load(url)
