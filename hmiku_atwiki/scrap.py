import requests
from multiprocessing import Pool, JoinableQueue, Process
import glob

def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()

def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

def dump_page_with_proxy(page_id, proxy):
    for _ in range(5):
        try:
            resp = requests.get(f'https://w.atwiki.jp/hmiku/pedit/{page_id}.html', proxies={"https": f"https://{proxy}"}, timeout=5)
            text = resp.text
            if resp.status_code == 404:
                with open(f"not_founds/{page_id}.html", "w") as f:
                    f.write(text)
                print(f"{page_id}: Not found.")
                break
            if resp.status_code != 200:
                print(f"{page_id}: {proxy}. {resp.status_code}")
                continue
            if "はこのWikiにログインしているメンバーか管理者に編集を許可しています。" in text or "編集モード廃止に伴い" in text or "は管理者からの編集のみ許可しています" in text or "サポートしておりません。" in text:
                print(f"{page_id}: no permission")
                with open(f"no_permissions/{page_id}.html", "w") as f:
                    f.write(text)
                break
            if "でスパムと判断される内容が存在しています" in text:
                print(f"{page_id}: {proxy}. Spam detected")
                break
            if "<textarea" not in text:
                print(f"{page_id}: {proxy}. 200 but no source")
                with open(f"no_source_pages/{page_id}_{proxy.replace(':', '_')}.html", "w") as f:
                    f.write(text)
                break
            with open(f"pages/{page_id}.html", "w") as f:
                f.write(text)
            return True
        except Exception as e:
            print(f"{page_id}: {proxy}. {e}")
            continue
    delete_proxy(proxy)
    return False


def generate_queue():
    q = JoinableQueue()
    pendings = set(range(3, 45386 + 1))
    pgs = set(int(i[6:-5]) for i in glob.glob("pages/*.html"))
    nfs = set(int(i[11:-5]) for i in glob.glob("not_founds/*.html"))
    nps = set(int(i[15:-5]) for i in glob.glob("no_permissions/*.html"))
    print("Total:", len(pendings))
    print("pages:", len(pgs))
    print("not founds:", len(nfs))
    print("no permissions", len(nps))
    pendings = pendings - pgs - nfs - nps
    print("Pendings:", len(pendings))
    for i in pendings:
        q.put(i)
    return q


def dump_page(worker, q: JoinableQueue):
    while True:
        try:
            page_id: int = q.get(10)
        except JoinableQueue.Empty:
            return
        print(f"{page_id}: collected by worker #{worker}")
        success = False
        for _ in range(10):
            proxy = None
            while proxy is None:
                proxy = get_proxy().get("proxy")
            print(f"{page_id}: {proxy}...")
            if dump_page_with_proxy(page_id, proxy):
                q.task_done()
                success = True
                break
        if not success:
            print(f"{page_id}: failed with 10 proxies")
            q.put(page_id)
            q.task_done()


if __name__ == '__main__':
    q = generate_queue()
    # dump_page(i, q)
    jobs = []

    for i in range(10): # 3 multiprocess
        p = Process(target=dump_page, args=(i, q))
        jobs.append(p)
        p.start()

    for p in jobs: #<--- join on all processes ...
        p.join()
    print("Done.")
    exit()