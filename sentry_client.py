# Author: Ing. Luciano Bono - choncba@gmail.com
# Date: 2022/05
# licence: GNU GPL v3.0
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# Free to use and modify, but please keep the above information.

import requests
import json
from requests.auth import HTTPBasicAuth
import logging

class _NullHandler(logging.Handler):
    def emit(self, record):
        pass

logger = logging.getLogger(__name__)
logger.addHandler(_NullHandler())

class SentryAPIException(Exception):
    """ 
        Exception raised when the Sentry API returns an error.
        code list:
         -32700 - invalid JSON. An error occurred on the server while parsing the JSON text (typo, wrong quotes, etc.)
         -32600 - received JSON is not a valid JSON-RPC Request 
         -32601 - requested remote-procedure does not exist
         -32602 - invalid method parameters
         -32603 - Internal JSON-RPC error
         -32400 - System error
         -32300 - Transport error
         -32500 - Application error
    """
    def __init__(self, *args, **kwargs):
        super(SentryAPIException, self).__init__(*args)

        self.error = kwargs.get("error", None)

class SentryAPI(object):
    def __init__(   self, 
                    ip=None,
                    session = None,
                    user = None,
                    password = None):
        
        self.session = requests.Session()

        # Default headers for all requests
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

        self.id = 0
        self.url = "http://" + ip + "/vnm-api/index.php"
        self.user = user
        self.password = password
        logger.info("JSON-RPC Server Endpoint: %s", self.url)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if isinstance(exception_value, (SentryAPIException, type(None))):
            if self.is_authenticated and not self.use_api_token:
                """ Logout the user if they are authenticated using username + password."""
                self.user.logout()
            return True

    def do_request(self, method, params=None):
        cmd = {"outputType":"json"}
        if params:
            cmd.update(params)
        request_json = {
            'jsonrpc': '2.0',
            'method': method,
            'params': cmd,
            'id': self.id
        }

        params = {"rpc":json.dumps(request_json)}

        logger.info("Sending: %s", json.dumps(request_json,
                                               indent=4,
                                               separators=(',', ': ')))
        response = self.session.post(
            self.url,
            auth=HTTPBasicAuth(self.user, self.password),
            params=params
        )
        logger.info("Response Code: %s", str(response.status_code))

        # NOTE: Getting a 412 response code means the headers are not in the
        # list of allowed headers.
        response.raise_for_status()

        if not len(response.text):
            raise SentryAPIException("Received empty response")

        try:
            response_json = json.loads(response.text)
        except ValueError:
            raise SentryAPIException(
                "Unable to parse json: %s" % response.text
            )
        logger.info("Response Body: %s", json.dumps(response_json,
                                                     indent=4,
                                                     separators=(',', ': ')))

        self.id += 1

        if 'error' in response_json:  # some exception
            if 'data' not in response_json['error']:  # some errors don't contain 'data': workaround for ZBX-9340
                response_json['error']['data'] = "No data"
            msg = u"Error {code}: {message}, {data}".format(
                code=response_json['error']['code'],
                message=response_json['error']['message'],
                data=response_json['error']['data']
            )
            raise SentryAPIException(msg, response_json['error']['code'], error=response_json['error'])

        return response_json

    def __getattr__(self, attr):
        """Dynamically create an object class (ie: host)"""
        return SentryAPIObjectClass(attr, self)

class SentryAPIObjectClass(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

        if self.name.startswith("Alert"):
            self.name = self.name.replace("Alert", "Alert/", 1)
            #print(self.name)
            

    def __getattr__(self, attr):
        """Dynamically create a method (ie: get)"""

        def fn(*args, **kwargs):
            if args and kwargs:
                raise TypeError("Found both args and kwargs")

            return self.parent.do_request(
                '{0}.{1}'.format(self.name, attr),
                args or kwargs
            )['result']

        return fn

