# Standard library
import datetime as dt
import os
import sys
import traceback

# Third-party
import pandas as pd

# Third-Party Libary
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

today = dt.datetime.today()
CWD = os.path.dirname(os.path.abspath(__file__))
DATA_WRITE_FILE = (
    f"{CWD}" f"/data_wikicommons_{today.year}_{today.month}_{today.day}.csv"
)


def get_imageinfo(image_name):
    url = (
        r"https://commons.wikimedia.org/w/api.php?"
        r"action=query&titles="
        f"{image_name}&prop=imageinfo&format=json"
    )

    return url


def get_categorymembers(license_type, session):
    url = (
        # r"https://commons.wikimedia.org/w/api.php?"
        # r"action=query&prop=categoryinfo&titles="
        # f"Category:{license}&format=json"
        r"https://commons.wikimedia.org/w/api.php?"
        r"action=query&list=categorymembers"
        r"&cmlimit=500&cmtype=file&cmtitle="
        f"Category:{license_type}&format=json"
    )

    with session.get(url) as response:
        response.raise_for_status()
        search_result = response.json()

    category_members = []
    for member in search_result["query"]["categorymembers"]:
        category_members.append((member["pageid"], member["title"]))

    return category_members


def get_image_timestamp_list(image_list, session):
    year_dict = {
        2004: 0,
        2005: 0,
        2006: 0,
        2007: 0,
        2008: 0,
        2009: 0,
        2010: 0,
        2011: 0,
        2012: 0,
        2013: 0,
        2014: 0,
        2015: 0,
        2016: 0,
        2017: 0,
        2018: 0,
        2019: 0,
        2020: 0,
        2021: 0,
        2022: 0,
        2023: 0,
    }

    for member in image_list:
        try:
            image_url = get_imageinfo(member[1])
            with session.get(image_url) as response:
                response.raise_for_status()
                image_result = response.json()

            year = str(
                image_result["query"]["pages"][str(member[0])]["imageinfo"][0][
                    "timestamp"
                ]
            )[0:4]

            year_dict[int(year)] += 1

        except Exception:
            print(
                f"Search data for image with {member[1]} of license"
                f" {member[0]} could not be found"
            ),
            continue

    return year_dict


def convert_csv(license_type, year_dict):

    if "," in license_type:
        license_type = license_type.replace(",", "|")

    line = license_type + ","

    for x in year_dict:
        line += str(year_dict[x]) + ","

    return line


def set_up_data_file():
    """Writes the header row to file to contain WikiCommons Query data."""

    header_title = (
        "License Type,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,"
        "2015,2016,2017,2018,2019,2020,2021,2022,2023\n"
    )

    with open(DATA_WRITE_FILE, "w") as f:
        f.write(header_title)


def write_file(line):
    with_newline = line[:-1] + "\n"
    print(with_newline)
    with open(DATA_WRITE_FILE, "w") as f:
        f.write(with_newline)


def main():
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

    license_list = pd.read_csv("license_list.csv").head(2)
    print(license_list["LICENSE TYPE"])

    set_up_data_file()

    for license in license_list["LICENSE TYPE"]:
        images = get_categorymembers(license, session)
        year_info = get_image_timestamp_list(images, session)
        converted = convert_csv(license, year_info)
        print(converted)
        # write_file(converted)

    print("Complete")


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

#     # Requests configurations
#     max_retries = Retry(
#         # try again after 5, 10, 20, 40, 80 seconds
#         # for specified HTTP status codes
#         total=5,
#         backoff_factor=10,
#         status_forcelist=[403, 408, 429, 500, 502, 503, 504],
#     )
#     session = requests.Session()
#     session.mount("https://", HTTPAdapter(max_retries=max_retries))
