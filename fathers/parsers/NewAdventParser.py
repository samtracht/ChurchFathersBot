import requests
from bs4 import BeautifulSoup
import json
from typing import Optional
import hashlib

from common.MistralAIEngine import MistralAIEngine


class NewAdventParser:

    def __init__(
        self,
    ):
        self.url = "https://www.newadvent.org/fathers/"
        self.mistral_engine = MistralAIEngine()

    def apply_function_to_strings(self, d, func):
        """
        Recursively applies a function to all string values in a nested dictionary.

        :param d: Dictionary to traverse.
        :param func: Function to apply to each string value.
        :return: None (modifies the dictionary in place).
        """
        if isinstance(d, dict):
            for key, value in d.items():
                if isinstance(value, dict):
                    self.apply_function_to_strings(value, func)
                elif isinstance(value, list):
                    for i in range(len(value)):
                        if isinstance(value[i], dict) or isinstance(value[i], list):
                            self.apply_function_to_strings(value[i], func)
                        elif isinstance(value[i], str):
                            value[i] = func(value[i])
                elif isinstance(value, str):
                    d[key] = func(value)
        return d

    def get_writing_links(
        self,
    ) -> dict:

        full_dict = {}
        response = requests.get(self.url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            p_list = soup.find_all("p")

            for i in p_list:
                name = i.find("strong")
                if name is None:
                    continue

                links = i.find_all("a")
                urls = {
                    link.text: link.get("href").replace("../", "")
                    for link in links
                    if link.get("href")
                    and "fathers" in link.get("href")
                    and "index" not in link.get("href")
                }
                if urls == {}:
                    continue
                for writing in urls:
                    try:
                        sub_response = requests.get(
                            f"https://www.newadvent.org/{urls[writing]}"
                        )
                        sub_soup = BeautifulSoup(sub_response.content, "html.parser")
                        a_list = sub_soup.find_all("a")
                        sub_urls = {
                            link.text: link.get("href").replace("../", "")
                            for link in a_list
                            if link.get("href")
                            and "fathers" in link.get("href")
                            and "index" not in link.get("href")
                        }
                        if name.text not in full_dict:
                            full_dict[name.text] = {}

                        if sub_urls == {}:
                            full_dict[name.text][writing] = urls[writing]
                        else:
                            full_dict[name.text][writing] = sub_urls
                    except Exception as e:
                        print(f"Couldnt search through {writing} from {name.text}")

        return full_dict

    def get_writing_json(self, link):
        for i in range(5):
            try:
                response = requests.get(f"https://www.newadvent.org/{link}")
                doc_info = {}
                if response.status_code == 200:
                    soup_obj = BeautifulSoup(response.content, "html.parser")
                    h2_count = len(
                        [
                            i
                            for i in soup_obj.find_all(["h2"])
                            if i.text != "About this page"
                        ]
                    )

                    if h2_count == 0:
                        rtn_lst = []
                        for element in soup_obj.find_all(["h2", "p"]):
                            if "Please help support" in element.text:
                                continue
                            elif element.name == "h2":
                                break
                            rtn_lst.append(element.text)
                        return rtn_lst
                    else:
                        curr_h2 = "Intro"
                        doc_info[curr_h2] = []

                    for element in soup_obj.find_all(["h2", "p"]):
                        if "Please help support" in element.text:
                            continue

                        if element.name == "p":
                            doc_info[curr_h2].append(element.text)
                        elif element.name == "h2":
                            if element.text == "About this page":
                                break
                            curr_h2 = element.text
                            doc_info[curr_h2] = []
                    return doc_info
            except Exception as e:
                print(f"Attempt {i + 1} failed: {e}")

    def save_writings(self, data, path: str):
        with open(path, "w") as f:
            json.dump(data, f)

    def retrieve(self, path: Optional[str] = None):
        hyperlink_dict = self.get_writing_links()
        full_writings = self.apply_function_to_strings(
            hyperlink_dict, self.get_writing_json
        )
        if path:
            self.save_writings(full_writings, "data/full_writings.json")
        return full_writings

    def traverse_and_apply(self, d, callback, path=None):
        if path is None:
            path = []

        if isinstance(d, dict):
            for k, v in d.items():
                yield from self.traverse_and_apply(v, callback, path + [k])
        elif isinstance(d, list):
            for idx, item in enumerate(d):
                yield from self.traverse_and_apply(
                    item, callback, path + [str(idx + 1)]
                )
        else:
            if d is not None and d != "":
                yield callback(path, d)

    def get_id(self, val) -> str:
        return hashlib.md5(val.encode()).hexdigest()[:16]

    def format_pinecone_data(self, path: list[str], value: str):
        data = {
            "metadata": {
                "citation": (path_str := " -- ".join(path)),
                "text": value,
                "author": path[0],
            },
            "values": self.mistral_engine.embed(value)[0],
            "id": self.get_id(f"{path_str} {value}"),
        }
        return data

    def get_pinecone_data(
        self, data: dict, father_name: Optional[str] = None
    ) -> list[dict]:
        if father_name is not None and father_name not in data:
            print("This father is not in the database")
            return

        elif father_name is None:
            return [i for i in self.traverse_and_apply(data, self.format_pinecone_data)]

        elif father_name in data:
            return [
                i
                for i in self.traverse_and_apply(
                    data[father_name], self.format_pinecone_data, [father_name]
                )
            ]
