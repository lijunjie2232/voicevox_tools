import sqlite3
import re
from pathlib import Path

if __name__ == "__main__":
    ROOT = Path(__file__).parent.resolve()
    db_path = ROOT / f"{Path(__file__).stem}.db"
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    res = cur.execute("SELECT tags,sfld from notes")
    data = res.fetchall()
    
    target_tags = ["N5", "N4", "N3", "N2", "N1", "オノマトペ", "外", "N4N5真题词汇补充"]
    words = [[] for _ in  range(len(target_tags))]

    for tag, sfld in data:
        tags = [t.split("::")[1] for t in tag.strip().split(" ")]
        if sfld.startswith("〜"):
            sfld = sfld[1:]
        if sfld.endswith("〜"):
            sfld = sfld[:-1]
        sfld = re.sub(r"\[.*?\]", "", sfld)
        sfld = re.sub(r"\(.*?\)", "", sfld)
        sfld = sfld.replace("　", "").replace(" ", "")
        for idx, target_tag in enumerate(target_tags):
            if target_tag in tags:
                words[idx].append(sfld)
        pass

    for i in range(len(target_tags)):
        print(target_tags[i], len(words[i]))
        with open(f"txt/{target_tags[i]}.txt", "w") as f:
            f.write("\n".join(words[i]))
    pass
