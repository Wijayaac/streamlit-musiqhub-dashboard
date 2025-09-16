# --- AUTO-GENERATED ROOM RATES (from room_rate.md, deduplicated, with tutor-specific rates) ---
import re

def normalize_name(name: str) -> str:
    if not name or name is None:
        return ""
    s = str(name).strip().lower()
    s = re.sub(r"[’'`\(\)\[\]\{\},.]", "", s)
    s = re.sub(r"[^0-9a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalize_tutor_name(name: str) -> str:
    if not name or name is None:
        return ""
    s = str(name).strip().lower()
    s = s.replace(" ", "")
    return s

# Data from room_rate.md
room_rate_raw = '''franchisee name, school name,room rate per week
barboravarnaite,bobby's private studio hurford road,$225.00
barboravarnaite,bobby's private studio new plymouth (saxton road),$187.50
barboravarnaite,egmont village school,$0.00
barboravarnaite,inglewood (mamaku centre),$15.00
barboravarnaite,lepperton school,$0.00
barboravarnaite,puketapu school,$0.00
barboravarnaite,urenui community hall,$0.00
barboravarnaite,welbourn school,$0.00
barboravarnaite,oakura school,$0.00
barrylee,macleans primary school,$12.50
barrylee,mellons bay school,$0.00
barrylee,ormiston primary school,$0.00
barrylee,stanhope road school,$0.00
barrylee,sunnyhills school,$40.00
barrylee,the gardens school,$0.00
barrylee,cockle bay school,$0.00
benlee,macleans primary school,$12.50
benlee,point view school,$34.50
benlee,st john's school,$20.70
benlee,mellons bay school,$0.00
benlee,ormiston primary school,$0.00
benlee,cockle bay school,$0.00
davegatman,belmont primary school,$20.00
davegatman,campbells bay school,$30.00
davegatman,devonport school,$17.25
davegatman,milford school (auckland),$23.00
davegatman,stanley bay school,$25.87
davegatman,sunnynook school,$28.75
davegatman,willow park,$37.50
davegatman,bayswater school,$0.00
davegatman,chelsea primary school,$0.00
davegatman,forrest hill school,$0.00
davegatman,takapuna school,$0.00
davegatman,westminster christian school,$0.00
joeldalloway,andersons bay school,$10.00
joeldalloway,columba college,$22.01
joeldalloway,east taieri school,$0.00
joeldalloway,elmgrove school,$0.00
joeldalloway,fairfield school (dunedin),$0.00
joeldalloway,george street normal school,$0.00
joeldalloway,grants braes school,$0.00
joeldalloway,joel's online lessons,$0.00
joeldalloway,kaikorai school,$10.00
joeldalloway,macandrew bay school,$0.00
joeldalloway,maori hill school,$15.00
joeldalloway,silverstream (south) primary school,$0.00
joeldalloway,st brigids school (tainui),$0.00
joeldalloway,st hildas collegiate school,$0.00
joeldalloway,st mary's school (mosgiel),$0.00
joeldalloway,taieri college,$0.00
johncasson,bayview school,$0.00
johncasson,hauraki school,$0.00
johncasson,hobsonville point primary school,$0.00
johncasson,northcote school (auckland),$0.00
johncasson,northcote war memorial hall,$0.00
johncasson,st mary's school (northcote),$11.40
johncasson,windy ridge school,$0.00
jordanmorrison,bucklands beach school,$60.00
jordanmorrison,farm cove intermediate,$20.00
jordanmorrison,golden grove school,$0.00
jordanmorrison,howick primary school,$0.00
jordanmorrison,oranga school,$0.00
jordanmorrison,pakuranga heights school,$0.00
jordanmorrison,st mark's catholic school,$20.00
jordanmorrison,sunnyhills school,$40.00
jordanmorrison,wakaaranga school,$0.00
paulbarry,edendale school (auckland),$70.00
paulbarry,victoria avenue,$92.00
paulbarry,greenhithe school,$60.00
paulbarry,waimauku school,$48.00
paulbarry,maraetai beach school,$60.00
paulbarry,huapai district school,$15.00
paulbarry,matua ngaru school,$45.00
paulbarry,three kings,$22.00
paulbarry,freemans bay school,$0.00
paulbarry,halsey drive school,$0.00
paulbarry,northcote intermediate,$0.00
paulbarry,paul's home studio,$0.00
paulbarry,st mary's school (papakura),$0.00
paulbarry,takapuna normal intermediate school,$0.00
paulbarry,taupaki school,$0.00
paulbarry,upper harbour primary school,$0.00
paulbarry,waterlea public school,$0.00
paulbarry,whenuapai school,$0.00
philmoore,glamorgan school,$30.00
philmoore,murrays bay school,$10.00
philmoore,oteha valley school,$15.00
philmoore,ahutoetoe school,$0.00
philmoore,nukumea primary school,$0.00
philmoore,torbay school,$0.00
shauno'kane,farmcove intermediate,$30.00
shauno'kane,sunnyhills school,$20.00
shauno'kane,st heliers school,$0.00
shauno'kane,halsey drive school,$0.00
shauno'kane,macleans primary school,$0.00
shauno'kane,waikowhai intermediate,$0.00
benholmes,gladstone school (auckland),$0.00
benholmes,mt eden normal school,$0.00
jakubroznawski,blockhouse bay primary,$0.00
jakubroznawski,fruitvale road school,$0.00
jakubroznawski,glen eden intermediate,$0.00
jakubroznawski,marina view school,$0.00
jakubroznawski,titirangi school,$0.00
jakubroznawski,waikowhai intermediate,$0.00
jakubroznawski,waterview school,$0.00
musiqhubbopltd,matua school,$0.00
musiqhubbopltd,pillans point school,$0.00
musiqhubbopltd,suzanne aubert catholic school,$0.00
lihfoo,blockhouse bay intermediate,$0.00
lihfoo,churchil park school,$0.00
lihfoo,conifer grove school,$0.00
lihfoo,kohia terrace school,$0.00
lihfoo,new windsor school,$0.00
lihfoo,reremoana primary school,$0.00
lihfoo,st heliers school,$0.00
lihfoo,st mary's school (papakura),$0.00
lihfoo,stanhope road school,$0.00
lihfoo,the gardens school,$0.00
lihfoo,lih guitar studio,$0.00
germon(ruth&michael),aberdeen school,$0.00
germon(ruth&michael),david street school,$0.00
germon(ruth&michael),endeavour school,$0.00
germon(ruth&michael),hamilton east school,$0.00
germon(ruth&michael),horsham downs school,$0.00
germon(ruth&michael),hukanui school,$0.00
germon(ruth&michael),marian catholic school (hamilton),$0.00
germon(ruth&michael),morrinsville intermediate,$0.00
germon(ruth&michael),motumaoho school,$0.00
germon(ruth&michael),newstead model school,$0.00
germon(ruth&michael),orini combined school,$0.00
germon(ruth&michael),rototuna primary school,$0.00
germon(ruth&michael),rototuna junior high school,$0.00
germon(ruth&michael),rototuna senior high school,$0.00
germon(ruth&michael),sacred heart girls college,$0.00
germon(ruth&michael),st columba's catholic school (frankton),$0.00
germon(ruth&michael),st joseph's catholic school (fairfield),$0.00
germon(ruth&michael),st joseph's catholic school (morrinsville),$0.00
germon(ruth&michael),st pius x catholic school (melville),$0.00
germon(ruth&michael),tauhei combined school,$0.00
germon(ruth&michael),tauwhare school,$0.00
germon(ruth&michael),te mata school (raglan),$0.00
germon(ruth&michael),te rapa primary school,$0.00
germon(ruth&michael),te totara primary school,$0.00
germon(ruth&michael),waikato waldorf school (rudolf steiner),$0.00
germon(ruth&michael),whitikahu school,$0.00
germon(ruth&michael),waitetuna school,$0.00
scottwotherspoon,huapai district school,$0.00
scottwotherspoon,scott's home studio,$0.00
scottwotherspoon,st heliers school,$0.00
scottwotherspoon,new windsor school,$0.00
scottwotherspoon,golden grove school,$0.00
waynemortensen,tahatai coast school,$0.00'''.strip().splitlines()

import csv
from collections import defaultdict

ROOM_RATES_BY_TUTOR = {}
ROOM_RATES = {}
lowest_rate_per_school = {}
zero_rate_schools = set()

reader = csv.reader(room_rate_raw)
header = next(reader)
for row in reader:
    tutor, school, rate = row
    tutor_norm = normalize_tutor_name(tutor)
    school_norm = normalize_name(school)
    # Remove $ and convert to float
    rate_val = float(rate.replace("$", "").replace(",", ""))
    # Tutor-specific
    ROOM_RATES_BY_TUTOR[(school_norm, tutor_norm)] = rate_val
    # Track if any tutor for this school has a $0 rate
    if rate_val == 0:
        zero_rate_schools.add(school_norm)
    # For ROOM_RATES, keep the lowest nonzero rate for each school
    if school_norm not in lowest_rate_per_school:
        lowest_rate_per_school[school_norm] = rate_val
    else:
        if rate_val != 0 and (lowest_rate_per_school[school_norm] == 0 or rate_val < lowest_rate_per_school[school_norm]):
            lowest_rate_per_school[school_norm] = rate_val
# If any tutor for a school has a $0 rate, set ROOM_RATES[school] = 0
for school_norm in lowest_rate_per_school:
    if school_norm in zero_rate_schools:
        ROOM_RATES[school_norm] = 0.0
    else:
        ROOM_RATES[school_norm] = lowest_rate_per_school[school_norm]

def get_room_rate(school, tutor=None):
    """
    Returns the room rate for a given school and (optionally) tutor.
    If not found, returns 0.
    """
    school_norm = normalize_name(school)
    if tutor is not None:
        tutor_norm = normalize_tutor_name(tutor)
        rate = ROOM_RATES_BY_TUTOR.get((school_norm, tutor_norm))
        if rate is not None:
            return rate
    # Fallback to default rate for the school
    return ROOM_RATES.get(school_norm, 0)

# Aliases (unchanged)
ALIASES = {
	# Map normalized abbreviations to normalized canonical names
	"hurford rd": "bobbys private studio hurford road",
	"new plymouth studio": "bobbys private studio new plymouth saxton road",
	"saxton road studio": "bobbys private studio new plymouth saxton road",
	"mps": "macleans primary school",
	"ops": "ormiston primary school",
	"stanhope": "stanhope road school",
	"sunnyhills": "sunnyhills school",
	"tgs": "the gardens school",
	"cockle bay": "cockle bay school",
	"macleans mon": "macleans primary school",
	"point view fri": "point view school",
	"st johns church tue": "st johns school",
	"mellons bay mon": "mellons bay school",
	"ormiston wed": "ormiston primary school",
	"cockle bay wed": "cockle bay school",
	"belmont school": "belmont primary school",
	"milford school": "milford school auckland",
	"chelsea school": "chelsea primary school",
	"andersons bay": "andersons bay school",
	"columba college": "columba college",
	"kaikorai primary": "kaikorai school",
	"maori hill": "maori hill school",
	"bayview": "bayview school",
	"hauraki": "hauraki school",
	"hpps": "hobsonville point primary school",
	"northcote primary": "northcote school auckland",
	"st mary's": "st marys school northcote",
	"windy ridge": "windy ridge school",
	"bbps": "bucklands beach school",
	"farm cove": "farm cove intermediate",
	"farmcove int": "farmcove intermediate",
	"golden grove": "golden grove school",
	"hps": "howick primary school",
	"oranga": "oranga school",
	"phs": "pakuranga heights school",
	"st marks": "st marks catholic school",
	"wakaaranga": "wakaaranga school",
	"edendale": "edendale school auckland",
	"victoria ave": "victoria avenue",
	"greenhithe": "greenhithe school",
	"waimauku": "waimauku school",
	"mbs": "maraetai beach school",
	"huapai": "huapai district school",
	"matua ngaru": "matua ngaru school",
	"three kings": "three kings",
	"freemans bay": "freemans bay school",
	"halsey drive": "halsey drive school",
	"nis": "northcote intermediate",
	"tnis": "takapuna normal intermediate school",
	"taupaki": "taupaki school",
	"waterlea": "waterlea public school",
	"whenuapai": "whenuapai school",
	"glamorgan school": "glamorgan school",
	"murrays bay school": "murrays bay school",
	"oteha valley school": "oteha valley school",
	"ahutoetoe school": "ahutoetoe school",
	"nukumea primary school": "nukumea primary school",
	"torbay school": "torbay school",
	"farmcove": "farmcove intermediate",
	"sunnyhills": "sunnyhills school",
	"st heliers": "st heliers school",
	"macleans prim": "macleans primary school",
	"waikowhai": "waikowhai intermediate",
	"menps": "mt eden normal school",
	"matua": "matua school",
	"pillans point": "pillans point school",
	"suzanne aubert": "suzanne aubert catholic school",
}
# --- END AUTO-GENERATED ---
