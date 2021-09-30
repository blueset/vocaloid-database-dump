import glob
import tqdm
from bs4 import BeautifulSoup
from multiprocessing import Pool
import frontmatter


def extract_files(path: str):
    with open(path, "r") as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    page_id = soup.select("span[data-pageid]")[0].attrs["data-pageid"]
    title = "/".join(i.text for i in soup.select("#wikibody > h2 > a"))
    content = soup.select("textarea")[0].text
    p = frontmatter.Post(content, title=title, page_id=int(page_id))
    with open(f"data/{page_id}.txt", "wb") as f:
        frontmatter.dump(p, f)


if __name__ == "__main__":
    files = glob.glob("pages/*.html")
    with Pool(8) as p:
        list(tqdm.tqdm(p.imap(extract_files, files), total=len(files)))
    print("Done!")
