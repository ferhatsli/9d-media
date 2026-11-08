import json,subprocess,re,glob,os,statistics as st
sel={r["id"]:r for r in json.load(open("deep/selection.json"))}
res={}
for f in sorted(glob.glob("deep/vid/*.mp4")):
    vid=os.path.basename(f)[:-4]
    pr=json.loads(subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_streams","-show_format",f],capture_output=True,text=True).stdout)
    dur=float(pr["format"]["duration"]);v=[s for s in pr["streams"] if s["codec_type"]=="video"][0]
    hasaudio=any(s["codec_type"]=="audio" for s in pr["streams"])
    sd=subprocess.run(["ffmpeg","-hide_banner","-i",f,"-vf","scale=320:-2,select='gt(scene,0.30)',showinfo","-an","-f","null","-"],capture_output=True,text=True).stderr
    cuts=[float(x) for x in re.findall(r"pts_time:([\d.]+)",sd)]
    cuts=[c for i,c in enumerate(cuts) if i==0 or c-cuts[i-1]>0.25]
    b=[0]+cuts+[dur];shots=[b[i+1]-b[i] for i in range(len(b)-1)]
    vol=""
    if hasaudio:
        a=subprocess.run(["ffmpeg","-hide_banner","-i",f,"-af","volumedetect","-vn","-f","null","-"],capture_output=True,text=True).stderr
        m=re.search(r"mean_volume: ([-\d.]+)",a);vol=m.group(1) if m else ""
    res[vid]=dict(dur=round(dur,1),w=v["width"],h=v["height"],cuts=len(cuts),asl=round(st.mean(shots),2),med_shot=round(st.median(shots),2),
        first_cut=round(cuts[0],2) if cuts else None,cuts_first5=sum(1 for c in cuts if c<5),cuts_per_10s=round(10*len(cuts)/dur,1),audio_mean_db=vol)
    # hook frames 0.2,1,2,3 + sheet of 12 frames over the video
    for t in (0.2,1.0,2.0,3.0):
        subprocess.run(["ffmpeg","-y","-v","quiet","-ss",str(t),"-i",f,"-frames:v","1","-vf","scale=-2:480",f"deep/frames/{vid}_t{t}.jpg"])
    subprocess.run(["ffmpeg","-y","-v","quiet","-ss","0.2","-i",f,"-t","3.2","-vf","fps=2.5,scale=-2:360,tile=8x1","-frames:v","1",f"deep/frames/{vid}_hook.jpg"])
    subprocess.run(["ffmpeg","-y","-v","quiet","-i",f,"-vf",f"fps={12/dur},scale=-2:300,tile=12x1","-frames:v","1",f"deep/frames/{vid}_sheet.jpg"])
    print(vid,res[vid])
json.dump(res,open("deep/tempo.json","w"),indent=1)
