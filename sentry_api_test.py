# Author: Ing. Luciano Bono - choncba@gmail.com
# Date: 2022/05
# licence: GNU GPL v3.0
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# Free to use and modify, but please keep the above information.

import json
from sentry_client import SentryAPI
import sys, logging

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)
log = logging.getLogger('sentry_client')
log.addHandler(stream)
log.setLevel(logging.DEBUG)

sentry_ip = "SENTRY_IP"
user = "API_USER"
password = "API_USER_PASSWORD"

sentry = SentryAPI(ip=sentry_ip, user=user, password=password)

# Example #1: Get all programs from specified port
programs = sentry.Program.GetAllPrograms(portNumber=2)
for program in programs:
    print(json.dumps(program, indent=4))

# Example #2: Get all programs Discontinuity Alerts
print(sentry.AlertProgramAlert.GetAllDiscontinuityAlerts())

# Example #3: Get all Open Alerts
openedAlerts = sentry.Report.GetOpenAlerts()
print(f"Alerts number: {len(openedAlerts)}")
for alert in openedAlerts:
    if alert["program_name"] is not "":
        print(json.dumps(alert, indent=4))

# Example #4: Get System Status
print(sentry.Status.GetSentrySystemStatus())
