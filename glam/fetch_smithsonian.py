#!/usr/bin/env python3
"""
Example Command from root of repository:
    pipenv run glam/fetch_smithsonian.py
"""

# Standard library
import sys
import traceback
from pprint import pprint

# Third-party
import query_secrets
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

TIMEOUT = 10


def fetch_data(session):
    params = {"api_key": query_secrets.S_I_O_A_API_Key}
    with session.get(
        "https://api.si.edu/openaccess/api/v1.0/stats",
        params=params,
        timeout=TIMEOUT,
    ) as response:
        response.raise_for_status()
        data = response.json()
    return data


def main():
    # print("API_KEY:", query_secrets.S_I_O_A_API_Key)  # DEBUG

    # Requests configurations
    max_retries = Retry(
        # try again after 5, 10, 20, 40, 80 seconds
        # for specified HTTP status codes
        total=5,
        backoff_factor=10,
        status_forcelist=[403, 408, 429, 500, 502, 503, 504],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=max_retries))

    # Fetch and format domain data
    data = fetch_data(session)

    # Print data
    pprint(data)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        sys.exit(e.code)
    except KeyboardInterrupt:
        print("INFO (130) Halted via KeyboardInterrupt.", file=sys.stderr)
        sys.exit(130)
    except Exception:
        print("ERROR (1) Unhandled exception:", file=sys.stderr)
        print(traceback.print_exc(), file=sys.stderr)
        sys.exit(1)

# the difference between a record and an object.
