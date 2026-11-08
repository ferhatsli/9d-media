import json,csv,sys
ig=json.load(open("raw/ig.json"));tt=json.load(open("raw/tt.json"));yt=json.load(open("raw/yt.json"))
def secs(d):
    s=0
    for a in (d or "0").split(":"): s=s*60+int(a)
    return s
rows=[]
for x in ig:
    tag=x.get("inputUrl","").rstrip("/").split("/")[-1]
    w,h=x.get("dimensionsWidth") or 0,x.get("dimensionsHeight") or 0
    rows.append(dict(p="IG",src="#"+tag,lang="TR" if any(c in tag for c in "ıışçğüö") or tag.startswith(("satılık","ticari")) else "EN",
      views=x.get("videoPlayCount") or x.get("igPlayCount") or 0,likes=x.get("likesCount") or 0,comments=x.get("commentsCount") or 0,
      dur=round(x.get("videoDuration") or 0),ar="9:16" if h>w*1.5 else ("1:1" if abs(h-w)<20 else ("16:9" if w>h else "4:5")),
      author=x.get("ownerUsername"),date=(x.get("timestamp") or "")[:10],music=(x.get("musicInfo") or {}).get("song_name") or "",
      original_audio=(x.get("musicInfo") or {}).get("uses_original_audio"),url=x.get("url"),text=(x.get("caption") or "").replace("\n"," ⏎ ")))
for x in tt:
    vm=x.get("videoMeta") or {};w,h=vm.get("width") or 0,vm.get("height") or 0;q=x.get("searchQuery")
    rows.append(dict(p="TT",src=q,lang="TR" if "satılık" in q else "EN",views=x.get("playCount") or 0,likes=x.get("diggCount") or 0,comments=x.get("commentCount") or 0,
      dur=vm.get("duration") or 0,ar="9:16" if h>w*1.5 else ("16:9" if w>h else "other"),author=(x.get("authorMeta") or {}).get("name"),
      date=(x.get("createTimeISO") or "")[:10],music=(x.get("musicMeta") or {}).get("musicName") or "",original_audio=(x.get("musicMeta") or {}).get("musicOriginal"),
      url=x.get("webVideoUrl"),text=(x.get("text") or "").replace("\n"," ⏎ ")))
for x in yt:
    q=x.get("input") or "";rows.append(dict(p="YT-"+("S" if x.get("type")=="shorts" else "V"),src=q,lang="TR" if "satılık" in q else "EN",
      views=x.get("viewCount") or 0,likes=x.get("likes") or 0,comments=x.get("commentsCount") or 0,dur=secs(x.get("duration")),
      ar="9:16" if x.get("type")=="shorts" else "16:9",author=x.get("channelName"),date=(x.get("date") or "")[:10],music="",original_audio=None,
      url=x.get("url"),text=((x.get("title") or "")+" || "+(x.get("text") or "")).replace("\n"," ⏎ ")))
for r in rows: r["er%"]=round(100*(r["likes"]+r["comments"])/r["views"],2) if r["views"] else ""
w=csv.DictWriter(open("references.csv","w",newline=""),fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(sorted(rows,key=lambda r:-r["views"]))
json.dump(rows,open("raw/rows.json","w"),ensure_ascii=False)
