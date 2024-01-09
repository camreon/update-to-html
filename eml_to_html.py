from email import message_from_file
from email.message import Message
from email.policy import default
import mimetypes
import os
from pathlib import Path
import sys
from typing import Any, List, Union
from PIL import Image
from pillow_heif import register_heif_opener
import urllib.parse

register_heif_opener()


def message_to_str(message: Message) -> str:
    payload: Any = message.get_payload()

    if isinstance(payload, str):
        payload_decoded: bytes = message.get_payload(decode=True)
        payload_decoded_str: str = payload_decoded.decode("utf-8")
        return payload_decoded_str
    elif isinstance(payload, List):
        return "\n".join(
            [
                message_to_str(message)
                for message in payload
                if message.get_content_type() == "text/html"
            ]
        )
    else:
        raise ValueError(f"`payload` type is {type(payload)}")


def eml_to_html(eml_path_str: Union[str, Path], output_path: str, save_attachments = True) -> Path:
    eml_path: Path = Path(eml_path_str)
    if not eml_path.is_file():
        print(f"🟡 Skipping `{eml_path}`; is not a file")

    if eml_path.suffix != ".eml":
        print(f"🟡 Skipping `{eml_path}`; not an .eml file")

    with eml_path.open(mode="r") as eml_file:
        message: Message = message_from_file(eml_file, policy=default)
        date = message["Date"][:-6]  # remove timezone

        directory = os.path.join(output_path, date)
        try:
            os.makedirs(directory)
        except FileExistsError:
            pass

        raw_html = None
        content_ids = []
        for part in message.walk():
            # multipart/* are just containers
            if part.get_content_maintype() == "multipart":
                continue

            filename = part.get_filename()
            ext = mimetypes.guess_extension(part.get_content_type())

            if ext == ".html" and not raw_html:
                raw_html = part.get_payload(decode=True).decode()
            else:
                if not filename:
                    # print(f"🟡 Skipping part; no filename; {part['Content-Type']}")
                    continue

                # encode filename for jekyll & webservers
                filename = make_safe(filename)
                filename = filename.lstrip("_")

                output_path = os.path.join(directory, filename)
                output_path = (
                    output_path[:255] if len(output_path) > 255 else output_path
                )
                if save_attachments:
                    with open(output_path, "wb") as fp:
                        fp.write(part.get_payload(decode=True))

                if ext == ".heic" or ext == ".tiff":
                    filename = str(Path(filename).with_suffix(".png"))
                    if save_attachments:
                        try:
                            Image.open(output_path).save(Path(output_path).with_suffix(".png"))
                        except OSError:
                            # handle grayscale tiff conversion error https://stackoverflow.com/a/43980135
                            image = Image.open(output_path)
                            image.mode = "I"
                            image.point(lambda i: i * (1.0 / 256)).convert("L").save(Path(output_path).with_suffix(".png"))
                        os.remove(output_path)

                # add to list of cids and img names
                id = (
                    part["Content-Id"].lstrip("<").rstrip(">")
                    if part["Content-Id"]
                    else filename
                )
                content_ids.append((id, filename))

        if raw_html:
            # add css
            raw_html = raw_html.replace(
                '<html><head>', 
                "<html><head><link rel='stylesheet' type='text/css' href='../../index.css'>"
            )
            
            # replace cids in html with img path
            raw_html = f"{raw_html}".lstrip("b'").rstrip("'")
            for cid, filename in content_ids:
                if not filename:
                    print(f"🟡 Skipping cid; no filename; {cid}")
                if f"cid:{cid}" not in raw_html:
                    raw_html += create_html_element(filename)
                else:
                    raw_html = raw_html.replace(f"cid:{cid}", make_safe(filename))
        else:
            # create html from img paths
            raw_html = "<html><head><link rel='stylesheet' type='text/css' href='../../index.css'></head><body>"
            for cid, filename in content_ids:
                raw_html += create_html_element(filename)
            raw_html += "\n</body></html>"

        # write updated html file
        html_path: Path = Path(os.path.join(directory, "index.html"))
        with html_path.open(mode="w", encoding="utf-8") as html_file:
            html_file.write(raw_html)
            print(f"🟢 Written `{html_path}`")

    return html_path


def make_safe(filename: str) -> str:
    safe_chars = "/,@+©"
    return urllib.parse.quote_plus(filename, safe=safe_chars)


def create_html_element(filename: str) -> str:
    # the filename needs to be url encoded again for the html
    safe_filename = make_safe(filename)

    if filename.endswith((".mov", ".mp4")):
        return f'\n<video controls="controls" name="{safe_filename}"><source src="{filename}"></video><br/><br/>'
    else:
        return f'\n<img src="{safe_filename}" alt="{filename}" /><br/><br/>'


def create_index(output_path: str, page_paths: List[Path]) -> None:
    # create index page with links to each sub page
    output_path = str(Path(output_path).parent)
    page_paths.reverse()

    index_html = "<html><head></head><body>"
    for page_path in page_paths:
        relative_path = os.path.relpath(page_path, output_path)
        relative_path_dir = os.path.dirname(relative_path)[len("updates/") :]
        index_html += f'\n<a href="{relative_path}">{relative_path_dir}</a><br/>'
    index_html += "\n</body></html>"

    html_path: Path = Path(os.path.join(output_path, "index.html"))
    with html_path.open(mode="w", encoding="utf-8") as html_file:
        html_file.write(index_html)
        print(f"🟢 Written index page `{html_path}`")

def append_index(output_path: str, page_paths: List[Path]) -> None:
    # add new sub page links to existing index page
    output_path = str(Path(output_path).parent)
    page_paths.reverse()

    index_html = ''
    for page_path in page_paths:
        relative_path = os.path.relpath(page_path, output_path)
        relative_path_dir = os.path.dirname(relative_path)[len("updates/") :]
        index_html += f'\n<a href="{relative_path}">{relative_path_dir}</a><br/>'

    print(f"\n🟢 Add the following links to you main index.html: \n{index_html}")


def main():
    # for debugging in vscode
    # output_path: str = "updates"
    # file_paths: List[str] = ["../../../Downloads/Update/22/022322-1.eml"]

    output_path: str = sys.argv[1]
    file_paths: List[str] = sys.argv[2:]
    save_attachments = True

    page_paths = []
    for file_path in file_paths:
        html_path = eml_to_html(file_path, output_path, save_attachments)
        page_paths.append(html_path)

    # don't create index again until new pages are added
    # create_index(output_path, page_paths)
    append_index(output_path, page_paths)


if __name__ == "__main__":
    main()
