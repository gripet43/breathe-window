#!/usr/bin/env python3
"""Build the correction spec for EXISTING-but-wrong card images.

The review pass (9 reviewers, 61 openable cities) confirmed 14 images that
misattribute geography/culture or break the square/no-text house style. These
are currently shown to users, so they should be regenerated and overwritten.
This file supplies targeted replacement prompts (same house-style suffix and
palette logic as the missing-image spec); actual generation happens in the
user's image tooling, then the file overwrites /assets/images/<filename>.

Frame colors are pulled from locations.json (authoritative).
"""
import json, os
from collections import Counter

ROOT = "/Users/gripet/.gemini/antigravity/scratch/breathe-window"
PUB = os.path.join(ROOT, "public")
OUT = os.path.join(ROOT, "scripts", "window_correction_spec.json")

ZH_SUF = "，柔和水彩水粉手绘，细微纸纹，温润低饱和，方形构图，画面无任何文字"
EN_SUF = (", soft watercolor and gouache illustration, subtle paper grain, "
          "warm muted natural palette, painterly, square 1:1, no text, no words, "
          "no letters, no signage")

AMERICAS = {"us","ca","mx","br","ar","cl","pe","co","cu","cr","pa","jm","bo","ec","ve","uy","py","gt","do","hn","ni","tt","ht","sv","bz","sr","gy"}
EUROPE = {"gb","fr","de","it","es","pt","nl","be","ch","at","ie","se","no","fi","dk","is","gr","pl","cz","hu","ro","hr","ru","ua","tr","mt","lu","ee","lv","lt","rs","ba","bg","sk","si","by","al","mk","me","xk","md","cy","ge","am","az"}
AFRICA = {"eg","ma","za","ke","tz","et","ng","gh","sn","dz","tn","mu","sc","na","zw","ug","rw","mg","sd","ss","cd","cg","cm","ci","ml","bf","ne","td","so","mz","zm","bw","ao","ga","gq","lr","sl","gn","gw","gm","tg","bj","bi","ly","er","dj","st","cv","km"}
OCEANIA = {"au","nz","fj","pg","ws","sb","vu","to","ki","fm","pw","mh","tv","nr"}
def continent(cc):
    cc = (cc or "").lower()
    if cc in AMERICAS: return "美洲"
    if cc in EUROPE: return "欧洲"
    if cc in AFRICA: return "非洲"
    if cc in OCEANIA: return "大洋洲"
    return "亚洲"

# (city, bucket, filename, issue, zh_body, en_body)
CORR = [
 ("冰岛 · 雷克雅未克","思想火花","loc_reykjavik_spark.webp",
  "船身文字为瑞典/挪威语拼法且画面含文字，违反无文字规范",
  "雷克雅未克旧港一隅，一艘刷着蓝白漆的渔船静静泊在灰蓝水面，船身洁净无任何文字，远处哈尔格林姆大教堂的玄武岩塔轮廓隐约，极昼将尽的午夜蓝调，海面泛着碎银光，一个远去的背影，冷灰蓝主调，静谧出神",
  "A corner of Reykjavik's old harbour, a blue-and-white painted fishing boat resting on grey-blue water, its hull clean with no lettering at all, the basalt tower of Hallgrimskirkja faint in the distance, the midnight-blue tone of a near-endless summer day, silver glints on the sea, one receding figure, cool grey-blue palette, quiet stillness"),
 ("希腊 · 圣托里尼","思想火花","loc_santorini_spark.webp",
  "画成温带湖畔小屋且冷调单色，应为火山口悬崖+基克拉泽斯白蓝平顶",
  "圣托里尼伊亚小镇的悬崖边缘，一面刷白的小屋与一座蓝顶圆穹，俯瞰火山口深陷的深蓝爱琴海，落日把白墙染成暖粉与蜜金，崖边一盏小灯初亮，留白辽阔的海与天，静谧出神，暖低饱和的蓝白主调",
  "The cliff edge of Oia in Santorini, a whitewashed cottage and a blue-domed chapel looking down into the deep blue Aegean of the sunken caldera, the setting sun warming the white walls to pink and honey-gold, one small lamp just lit on the ledge, vast open sea and sky, quiet stillness, warm muted blue-and-white palette"),
 ("英国 · 伦敦","思想火花","loc_london_spark.webp",
  "背景画成中式曲檐亭阁与垂柳园林，张冠李戴",
  "伦敦摄政公园一处清晨角落，雾中一张铸铁长椅，椅旁是英式草坪与悬铃木，远处淡雾里隐约圣保罗大教堂的穹顶剪影，一盏维多利亚式路灯尚亮着暖光，冷灰雾气中一点暖意，静谧出神，灰绿与暖灯主调",
  "A quiet morning corner of Regent's Park in London, a cast-iron bench in the mist beside an English lawn and plane trees, the faint silhouette of St Paul's dome in the haze beyond, one Victorian lamp post still glowing warm, a spot of warmth in cool grey fog, quiet stillness, grey-green and warm-lamp palette"),
 ("中国 · 北京故宫","思想火花","loc_beijing_spark.webp",
  "竖长幅构图非方形，方形容器裁切会丢内容",
  "方形满幅的紫禁城黄昏一角，朱红宫墙与金黄琉璃瓦在暮色里延展，一只北京雨燕掠过翘起的檐角，一盏宫灯初上，天空大面积留白染着暖橙，庄严而静谧，红金主调",
  "A full-square dusk corner of the Forbidden City, vermilion walls and golden glazed tiles stretching in the fading light, a Beijing swift skimming past an upturned eave, one palace lantern just lit, a large open sky washed in warm orange, solemn and still, vermilion-and-gold palette"),
 ("中国 · 西安古城","旧物新看","loc_xian_old.webp",
  "画成西式石砌茅草屋cottage，与关中/西安无关",
  "西安碑林一方老旧石碑的特写，碑面楷书刻字已风化漫漶，石面有岁月裂纹与苔痕，斜光打出碑刻的凹凸质感，旁置一张半揭的拓片与拓包，厚重沉静的土黄砖灰主调",
  "Close-up of an aged stone stele in Xi'an's Beilin, its carved characters weathered and softened, the stone surface cracked and touched with moss, raking light revealing the relief of the carving, beside it a half-lifted ink rubbing and a rubbing pad, weighty and calm, earthy yellow and brick-grey palette"),
 ("中国 · 敦煌莫高窟","科学自然","loc_dunhuang_nature.webp",
  "绿洲画成椰枣/棕榈的中东景观，敦煌不生长棕榈",
  "敦煌月牙泉边的真实绿洲：沙丘环抱一弯清泉，泉畔是胡杨、沙枣树、杨柳与成片芦苇，戈壁砾石滩延展向鸣沙山，无棕榈无椰枣，干旱区绿洲生态，赭黄沙色与一点湿润绿的主调",
  "The real oasis at Crescent Lake in Dunhuang: a clear spring cradled by sand dunes, its banks lined with poplars, sand-date trees, willows and thick reeds, a gobi gravel plain stretching toward the Mingsha dunes, no palms or date-palms, an arid-zone oasis ecology, ochre-sand tones with a touch of moist green"),
 ("中国 · 桂林山水","思想火花","loc_guilin_spark.webp",
  "画成温带秋色落叶林，无桂林喀斯特峰林",
  "桂林漓江的一隅黄昏，几座喀斯特孤峰倒映在镜面般的江面，一叶竹筏静泊筏上无人，岸边凤尾竹与一点渔火，雾气轻笼峰丛，亚热带岩溶地貌，宁静出神，青绿主调",
  "A dusk corner of the Li River in Guilin, a few solitary karst peaks mirrored on the glassy river, a still bamboo raft with no one aboard, phoenix-tail bamboo on the bank and a single fishing lantern, light mist veiling the peak clusters, subtropical karst landform, quiet stillness, blue-green palette"),
 ("中国 · 丽江古城","思想火花","loc_lijiang_spark.webp",
  "画成英式科茨沃尔德半木乡村，与纳西古城无关",
  "丽江古城四方街附近的小桥流水一隅，纳西木楼与青瓦屋顶沿河错落，一座小石拱桥，远处玉龙雪山雪顶隐约，几盏红灯笼在暮色里亮起暖光，水面映灯，静谧出神，赭红木色与灯笼暖橙主调",
  "A waterside corner near Sifang Street in Lijiang's old town, Naxi timber houses with grey-tiled roofs stepping along the canal, a small stone arch bridge, the snow peak of Jade Dragon Mountain faint beyond, a few red lanterns glowing warm in the dusk, their light mirrored on the water, quiet stillness, ochre-timber and warm-lantern palette"),
 ("中国 · 丽江古城","旧物新看","loc_lijiang_old.webp",
  "识字卡画成蒙古/满文竖写体与西双版纳大象，非纳西东巴文且动物错",
  "一张纳西东巴纸的特写，纸上以褐黑颜料手绘着图画式的东巴象形符号（日、山、人等抽象图形纹样，非可识读竖排文字），纸边粗粝泛黄，旁置一支竹笔与一小碟矿物颜料，温润斑驳，暖木色与赭褐主调",
  "Close-up of a sheet of Naxi dongba paper, hand-drawn pictographic dongba symbols in brown-black pigment (abstract motif-like glyphs of sun, mountain, figure, not readable vertical script), the deckled yellowed edge of the paper, beside it a bamboo pen and a small dish of mineral pigment, warm and weathered, warm-wood and ochre-brown palette"),
 ("中国 · 哈尔滨冰雪","思想火花","loc_harbin_spark.webp",
  "冰雕在融化且配春花，季节与冰雪主题相悖",
  "哈尔滨松花江畔严冬深夜，一座棱角完好的冰雕在夜色里透出冷蓝与暖金的灯光，江面封冻覆着白雪，远处斯大林公园与防洪纪念塔的剪影，空中飘着细雪，绝无春花与融化，纯净寒冬，冰蓝与暖灯主调",
  "A deep midwinter night on the Songhua River in Harbin, a crisp intact ice sculpture glowing from within with cold blue and warm gold light, the river frozen over and dusted with snow, the silhouettes of Stalin Park and the Flood Control Monument beyond, fine snow drifting in the air, no blossoms and no melting, pure deep winter, ice-blue and warm-lamp palette"),
 ("中国 · 重庆山城","思想火花","loc_chongqing_spark.webp",
  "画成地中海橙瓦白墙山城，与重庆不符",
  "重庆渝中半岛的夜景一隅，吊脚楼与摩天楼沿江层叠而上，长江与嘉陵江在远处交汇，洪崖洞式的暖黄灯火挂满崖壁，一条跨江索道与轻轨的灯带隐约穿过雾气，湿热山城，暖橙红与夜蓝主调",
  "A night corner of Chongqing's Yuzhong peninsula, stilted houses and skyscrapers stacking up the bank in layers, the Yangtze and Jialing rivers meeting in the distance, Hongya-dong-style warm yellow lights climbing the cliff face, the faint light-trails of a river cableway and monorail threading the humid haze, a hot humid mountain city, warm orange-red and night-blue palette"),
 ("中国 · 大理洱海","科学自然","loc_dali_nature.webp",
  "题为洱海却通篇无湖，画成干旱峡谷",
  "洱海湖滨的湿地一隅，苍山十九峰的雪顶与云带倒映在湛蓝湖面，近处是水草与浅滩，一艘白族木船静泊，白云舒展，湿润明亮的高原湖泊生态，蓝绿主调",
  "A wetland corner of Erhai Lake, the snowy peaks and cloud bands of the nineteen Cangshan mountains mirrored on the blue lake, marsh grass and shallows in front, a single Bai wooden boat resting at anchor, open white clouds, a bright moist highland-lake ecology, blue-green palette"),
 ("中国 · 香港旺角","旧物新看","loc_hongkong_old.webp",
  "画了只行驶港岛的叮叮车，九龙旺角从无电车线",
  "旺角街头一隅的旧式唐楼骑楼特写，斑驳的霓虹招牌与晾衫竹伸出窗外，楼下一处旧报摊与 KMB 九龙巴士站牌，明确是九龙街景，绝无电车叮叮车，市井烟火气，霓虹暖色与水泥灰主调",
  "Close-up of old tong-lau arcades on a Mong Kok street corner, weathered neon signboards and bamboo clothes-poles reaching from the windows, an old news-stand and a KMB Kowloon bus stop sign below, unmistakably a Kowloon street with no tram at all, everyday street life, warm neon and cement-grey palette"),
 ("马来西亚 · 吉隆坡","思想火花","loc_kualalumpur_spark.webp",
  "画成群山环抱坡屋顶的温带山城夜景，应为热带平地高楼天际线",
  "吉隆坡热带夜景一隅，国油双子塔与吉隆坡塔的天际线在暖夜里发光，前景是热带雨林浓密的树冠与几株棕榈，平地高楼绝无山坡与坡屋顶，赤道暖湿的空气里一点薄雾，静谧出神，暖金与夜蓝主调",
  "A tropical night corner of Kuala Lumpur, the Petronas Twin Towers and KL Tower skyline glowing in the warm night, foreground filled with dense tropical rainforest canopy and a few palms, flat-land towers with no hills or pitched roofs, a touch of haze in the equatorial warm-humid air, quiet stillness, warm-gold and night-blue palette"),
]

def main():
    locs = json.load(open(os.path.join(PUB, "assets", "data", "locations.json"), encoding="utf-8"))
    byname = {l["name"]: l for l in locs}
    spec, errors = {}, []
    for city, bucket, fn, issue, zh, en in CORR:
        l = byname.get(city, {})
        if not l:
            errors.append(f"{city}: not in locations.json")
        cc = l.get("countryCode") or ""
        node = spec.setdefault(city, {
            "countryCode": cc, "continent": continent(cc),
            "emblem": l.get("emblem"), "wood": l.get("wood"),
            "stampColor": l.get("stampColor"), "corrections": [],
        })
        node["corrections"].append({
            "bucket": bucket, "filename": fn, "path": "/assets/images/" + fn,
            "issue": issue, "zh": zh + ZH_SUF, "en": en + EN_SUF,
        })
        # sanity: path exists on disk?
        dp = os.path.join(PUB, "assets", "images", fn)
        if not os.path.isfile(dp):
            errors.append(f"{city}/{fn}: target file not on disk")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=2)
    n = sum(len(v["corrections"]) for v in spec.values())
    print(f"cities: {len(spec)}  corrections: {n}")
    bc = Counter(c[1] for c in CORR)
    print("by bucket:", dict(bc))
    print(f"errors: {len(errors)}")
    for e in errors: print("   ", e)
    print(f"written -> {OUT}")

if __name__ == "__main__":
    main()
