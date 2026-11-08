import json,re
rows=json.load(open("raw/rows.json"))
LIST=re.compile(r"satılık|satilik|for sale|devren|kiralık|for lease|for rent|m2|m²|metrekare|sq\.? ?ft|sqft|square f|acre|dönüm|tour|turu|gezisi|tanıtım|📍|ilan no|fiyat|price|\$\d|₺|tl\b|zoned|cephe",re.I)
OFF=re.compile(r"arrested|fire|ruh halim|tebrik|kiracının kontratı|warehouse sale on|aritzia|adidas|garanti|forma|pasta|gurme|ürünler|polietilen|defolu|nostalgia|template|capcut|people behind|who you work|follow @|evaluate|ortaklık|dikkat etmeniz",re.I)
PROP=re.compile(r"depo|warehouse|imalathane|fabrika|factory|ofis|office|işyeri|isyeri|dükkan|shop|commercial|ticari|bina|building|plaza|godown|industrial|atölye|flex",re.I)
for r in rows:
    t=r["text"];r["listing"]=bool(LIST.search(t) and PROP.search(t) and not OFF.search(t))
json.dump(rows,open("raw/rows.json","w"),ensure_ascii=False)
L=[r for r in rows if r["listing"]]
print("listing",len(L),"of",len(rows))
for r in sorted(L,key=lambda r:-r["views"])[:45]:
    print(f'{r["p"]:4} {r["views"]:>8} {r["dur"]:>4}s {r["lang"]} @{(r["author"] or "")[:16]:16} | {r["text"][:110]}')
