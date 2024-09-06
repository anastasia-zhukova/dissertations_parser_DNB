from typing import List
from loguru import logger
import tika
tika.initVM()
from tika import parser
import requests
import re
import pyhocon
import pandas as pd
import os
import gdown
import gzip
from bs4 import BeautifulSoup
import shutil

parse_config = None
MAX_LEN_DOC_LINES = 100000


def collect_related_items(parse_config) -> str:
    """
    Given a file name of the DNB's dissertation collection in XML format, collect the bibliograph items that are
    related to the domain by filtering using the specified codes.
    :param input_file_path: a location of the input file
    :return: a path to a file where the selected bibliography objects are saved
    """
    input_file_path = os.path.join(os.getcwd(), "tmp", "dnb-all_online_hochschulschriften_frei_dnbmarc_20231101mrc.xml")
    zip_path = os.path.join(os.getcwd(), "tmp", "dnb-all_online_hochschulschriften_frei_dnbmarc_20231101mrc.xml.gz")
    if not os.path.exists(input_file_path):
        if not os.path.exists(zip_path):
            gdown.download("https://data.dnb.de/FreieOnlineHochschulschriften/dnb-all_online_hochschulschriften_frei_dnbmarc_20240327mrc.xml.gz",
                       zip_path, quiet=False)
        with gzip.open(zip_path, "rb") as file_input:
            with open(input_file_path, "wb") as file_output:
                shutil.copyfileobj(file_input, file_output)

    with open(input_file_path, "r", encoding="utf-8") as file:
        collected_df = pd.DataFrame()
        new_record = None
        record_id = 0
        file_id = 0
        save_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

        for line in file:
            if '<record type="Bibliographic">' in line:
                if new_record is not None:
                    if record_id % 100 == 0:
                        logger.info(f'Checking {record_id} document...')

                    record_id += 1
                    soup = BeautifulSoup(new_record, "lxml")

                    # language
                    try:
                        langs = soup.find(tag="041").find_all(code="a")
                    except AttributeError:
                        try:
                            langs = soup.find(tag="040").find_all(code="b")
                        except AttributeError:
                            langs = None
                    langs = [v.text for v in langs] if langs is not None else []

                    # domain code
                    try:
                        domain_codes_extracted = soup.find(tag="082").find_all(code="a")
                    except AttributeError:
                        domain_codes_extracted = []

                    domain_codes_filtered = []
                    for domain_code_extracted in domain_codes_extracted:
                        for domain_code in parse_config["domain_codes"]:
                            if not domain_code_extracted.text.startswith(domain_code):
                                continue

                            if domain_code_extracted.text in parse_config["exception_list"]:
                                continue

                            domain_codes_filtered.append(domain_code_extracted.text)

                    # author
                    try:
                        author_name = soup.find(tag="100").find(code="a").text
                    except AttributeError:
                        author_name = ""

                    # title
                    try:
                        title = "\n".join([v.text for v in soup.find(tag="245").find_all(code="a")])
                    except AttributeError:
                        title = ""

                    # ID
                    try:
                        diss_id = soup.find(tag="001").text
                    except AttributeError:
                        diss_id = ""

                    pdf_url = f"https://d-nb.info/{diss_id}/34"
                    try:
                        page = requests.get(pdf_url)
                        content = page.content
                    except:
                        page = None

                    if len(domain_codes_filtered) and parse_config["language"] in langs and len(author_name) and page is not None and len(diss_id):

                        paragraphs = parse_pdf(pdf_url)

                        if len(paragraphs):
                            record_df = pd.DataFrame({
                                "category": ", ".join(domain_codes_filtered),
                                "author": author_name,
                                "title": title,
                                "url": pdf_url,
                                "text": paragraphs
                            }, index=[f'{record_id}_{p}' for p in range(len(paragraphs))])

                            collected_df = pd.concat([collected_df, record_df])

                            if len(collected_df) > parse_config["paragraphs_per_file"]:
                                save_path_csv = os.path.join(save_folder,
                                                             f"{parse_config['domain_name']}_dnb_dissertations_{parse_config['language']}-part_{file_id}.csv")
                                collected_df.to_csv(save_path_csv, sep="\t")
                                logger.info(f'Saved part {file_id} of the parsed dissertations!')
                                file_id += 1
                                collected_df = pd.DataFrame()

                    elif page is None:
                        logger.warning(f"No pdf under the pdf-link {pdf_url}")

                new_record = line
            elif new_record is not None:
                new_record += line

    return save_path_csv


def parse_pdf(url: str) -> List[str]:
    """
    Parses a PDF into a list pf paragraphs given a link, which can point either to a saved file path or a url
    :param url: file path or url
    :return:
    """
    try:
        parsed = parser.from_file(url, requestOptions={'timeout': 60})
    except Exception as e:
        logger.warning(f'Error occurred when parsing {url}: {e}. Aborted')
        return []

    if parsed["content"] is None:
        logger.warning(f'No text found/parsed from {url}. Aborted')
        return []

    lines = parsed["content"].split("\n")
    # check how many lines are extracted from the file. If too many, ignore the file cause it might contain code of the full project
    if len(lines) > MAX_LEN_DOC_LINES:
        logger.warning(f'Too long document {url}. Aborted')
        return []

    paragraphs = []
    paragraph = ""
    for line_id, line in enumerate(lines):
        # create paragraphs my merging the lines that do not end with full-stops
        if line.strip().endswith("."):
            paragraph += line
            paragraph = re.sub("\s+", " ", paragraph.strip())
            global parse_config
            if len(paragraph) > parse_config["min_chars_paragraph"]:
                paragraphs.append(paragraph.strip())

            paragraph = ""
        else:
            paragraph += line if line else " "
    return paragraphs


if __name__ == "__main__":
    parse_config = pyhocon.ConfigFactory.parse_file("parse_config.json")
    collect_related_items(parse_config)