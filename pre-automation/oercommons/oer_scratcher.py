#!/usr/bin/env python
"""
This file is dedicated to obtain a .csv record report for Open Education
Resources Commons data.
"""

# Standard library
import csv
import os
import re
import sys
import traceback
import xml.etree.ElementTree as ET

# Third-party
import query_secrets
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# import lxml.etree as ET


TIMEOUT = 20
ENDPOINT = "https://www.oercommons.org/api/search"
BASE_URL = f"{ENDPOINT}?token={query_secrets.ACCESS_TOKEN}"
CWD = os.path.dirname(os.path.abspath(__file__))


def get_license_list():
    """Returns list of licenses to query."""
    return [
        "cc-by",
        "cc-by-sa",
        "cc-by-nd",
        "cc-by-nc",
        "cc-by-nc-sa",
        "cc-by-nc-nd",
    ]


def fetch_data(session, params):
    """Fetch data."""
    params["token"] = query_secrets.ACCESS_TOKEN
    with session.get(
        ENDPOINT,
        params=params,
        timeout=TIMEOUT,
    ) as response:
        try:
            response.raise_for_status()
            data = ET.fromstring(re.sub(r"&\w*;", "", response.text))
            return data
        except Exception:
            print("Error with params: " + str(params))
            return None


def get_license_total_count(session, lcs):
    """Returns total items for a license."""
    params = {"f.license": lcs, "batch_size": 0}
    root = fetch_data(session, params)
    print(lcs, "Done")
    return root.attrib["total-items"]


def get_all_license_count(session, api_usage):
    """Saves total license count to disk."""
    license_count = []
    if api_usage:
        license_lst = get_license_list()
        print("license list done")
        for lcs in license_lst:
            print("starting" + lcs)
            license_count.append(get_license_total_count(session, lcs))
        with open(
            os.path.join(CWD, "license_counts.csv"),
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(license_lst)
            writer.writerow(license_count)
    else:
        with open(
            os.path.join(CWD, "license_counts.csv"), "r", encoding="utf-8"
        ) as file:
            next(file)
            license_count = list(
                map(int, next(file).replace("\n", "").split(","))
            )
    return license_count


def batch_retrieve(session, lcs, batch_start, writer):
    """Returns ET object with the next 50 results."""
    params = {"f.license": lcs, "batch_size": 50, "batch_start": batch_start}
    root = fetch_data(session, params)
    if root is None:
        return
    for result in root:
        id = result.attrib["id"]
        date = None
        temp = {}
        for attribute in result:
            # Modification Date
            if attribute.tag == "modification_date":
                date = attribute.text
            # OER Summary Data
            elif attribute.tag == "oersummary":
                temp = {
                    "Education Level": "",
                    "Subject Area": "",
                    "Material Type": "",
                    "Media Format": "",
                    "Languages": "",
                    "Primary User": "",
                    "Educational Use": "",
                }
            for item in attribute:
                if (
                    ("title" in item.attrib)
                    and ("value" in item.attrib)
                    and item.attrib["title"] in temp
                ):
                    temp[item.attrib["title"]] = item.attrib["value"]
        writer.writerow([str(id)] + [lcs] + [date] + list(temp.values()))


def record_license_data(session, lcs, total, writer):
    """Retrieve all data for a license."""
    current_index = 0
    # replace total with 100 for testing purposes
    while current_index < total:
        batch_retrieve(session, lcs, current_index, writer)
        print(lcs + " batch starting at " + str(current_index) + " complete.")
        current_index += 50


def record_all_licenses(session):
    """Records the data of all license types."""
    license_list = get_license_list()
    # pass in True if you want to re-fetch all license counts
    license_count = get_all_license_count(session, False)
    with open(
        os.path.join(CWD, "oer.csv"), "w", newline="", encoding="utf8"
    ) as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(
            [
                "id",
                "license",
                "modification_date",
                "Education Level",
                "Subject Area",
                "Material Type",
                "Media Format",
                "Languages",
                "Primary User",
                "Educational Use",
            ]
        )
        # uncomment line below for testing
        # record_license_data(
        #     session, license_list[0], license_count[0], writer
        #     )
        # don't run below in testing
        for x in range(0, len(license_list)):
            record_license_data(
                session, license_list[x], license_count[x], writer
            )


def test_access():
    """Tests endpoint by filtering under cc-by license."""
    response = requests.get(f"{BASE_URL}&f.license=cc-by&batch_size=50")
    print(response.status_code)
    with open(os.path.join(CWD, "data.xml"), "w") as f:
        print(type(response.text))
        f.write(re.sub(r"&\w*;", "", response.text))


def test_xml_parse():
    """Tests getting elements from XML."""
    tree = ET.parse(os.path.join(CWD, "data.xml"))
    root = tree.getroot()

    row_data = ["cc-by"]
    for result in root:
        result_id = [result.attrib]
        for attribute in result:
            # Modification Date
            if attribute.tag == "modification_date":
                date = [attribute.text]
            # OER Summary
            if attribute.tag == "oersummary":
                temp = {
                    "Education Level": "",
                    "Subject Area": "",
                    "Material Type": "",
                    "Media Format": "",
                    "Languages": "",
                    "Primary User": "",
                    "Educational Use": "",
                }

                for item in attribute:
                    if temp.get(item.attrib["title"]) is not None:
                        temp[item.attrib["title"]] = item.attrib[
                            "value"
                        ].replace('"', "")

                print(result_id + row_data + date + list(temp.values()))


def main():

    # fetch data simple

    # Requests configurations
    max_retries = Retry(
        total=5,
        backoff_factor=10,
        # retry even when encounters this error
        # status_forcelist=[403, 408, 429, 500, 502, 503, 504],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=max_retries))

    # get_all_license_count(session, True)
    record_all_licenses(session)


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
