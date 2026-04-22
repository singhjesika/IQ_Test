from dotenv import load_dotenv
load_dotenv()
import json,os,sys,time,threading
from groq import Groq

class C:
    RESET="\033[0m";BOLD="\033[1m";DIM="\033[2m";RED="\033[91m";GREEN="\033[92m";YELLOW="\033[93m";CYAN="\033[96m";BLUE="\033[94m";MAGENTA="\033[95m"
def clr(t,*c):return"".join(c)+str(t)+C.RESET
def clear():os.system("cls" if os.name=="nt" else"clear")

class CountdownTimer:
    def __init__(self,s):
        self.total=s;self.left=s
        self._stop=threading.Event()
        self._thread=threading.Thread(target=self._run,daemon=True)
    def _run(self):
        while self.left>0 and not self._stop.is_set():
            r=self.left/self.total;f=int(r*20)
            b="█"*f+"░"*(20-f)
            c=C.GREEN if r>.5 else(C.YELLOW if r>.25 else C.RED)
            sys.stdout.write(f"\r  {clr(b,c)}  {clr(f'{self.left:2d}s',c,C.BOLD)}  ")
            sys.stdout.flush()
            time.sleep(1);self.left-=1
        if not self._stop.is_set():
            sys.stdout.write(f"\r  {clr('Time is up!',C.RED,C.BOLD)}{' '*30}\n")
            sys.stdout.flush()
    def start(self):self._thread.start()
    def stop(self):
        self._stop.set();self._thread.join()
        sys.stdout.write("\r"+" "*55+"\r");sys.stdout.flush()
    def expired(self):return self.left<=0

CATEGORIES={"1":"Math & Numbers","2":"Pattern Recognition","3":"Verbal Reasoning","4":"Logical Deduction"}
DIFFICULTY_TIME={"Easy":20,"Medium":30,"Hard":45}
DIFFICULTY_BONUS={"Easy":0,"Medium":5,"Hard":12}

def generate_questions(client,categories,difficulty,count):
    cat_str=", ".join(categories)
    prompt=f"""Generate exactly {count} IQ test questions as a JSON array.

STRICT RULES:
- Output MUST be valid JSON
- No extra text
- No markdown
- No line breaks inside strings

Categories: {cat_str}
Difficulty: {difficulty}

Format:
[{{"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"answer":"A","category":"...","explanation":"..."}}]
"""
    for _ in range(3):
        print(clr("\n  Groq is generating your questions",C.CYAN,C.BOLD),end="")
        for i in range(3):
            time.sleep(0.3)
            print(clr(".",C.CYAN),end="",flush=True)

        response=client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.8,
            max_tokens=2500,
        )

        raw=response.choices[0].message.content.strip()
        raw=raw.replace("```json","").replace("```","").strip()

        s=raw.find("[");e=raw.rfind("]")+1
        if s==-1 or e==0:continue

        clean=raw[s:e]

        try:
            q=json.loads(clean)

            valid=True
            for item in q:
                if "options" not in item or len(item["options"])!=4:
                    valid=False
                    break

            if not valid:
                continue

            print(clr(f"  {len(q)} questions ready!\n",C.GREEN,C.BOLD))
            return q
        except:
            try:
                clean=clean.replace("\n"," ").replace("\r"," ").replace("'","\"")
                q=json.loads(clean)

                valid=True
                for item in q:
                    if "options" not in item or len(item["options"])!=4:
                        valid=False
                        break

                if not valid:
                    continue

                print(clr(f"  {len(q)} questions ready!\n",C.GREEN,C.BOLD))
                return q
            except:
                continue

    raise ValueError("Failed to generate valid questions")

def estimate_iq(r,d):
    if not r:return 85
    c=sum(1 for x in r if x["correct"]);t=len(r)
    a=c/t;avg=sum(x["time_taken"] for x in r)/t
    tl=DIFFICULTY_TIME[d]
    sb=max(0,(tl-avg)/tl)*15;db=DIFFICULTY_BONUS[d]
    iq=70+(a*65)+sb+db
    return max(70,min(145,round(iq)))

def iq_label(i):
    if i>=140:return clr("Genius",C.MAGENTA,C.BOLD)
    if i>=130:return clr("Gifted",C.CYAN,C.BOLD)
    if i>=120:return clr("Superior",C.BLUE,C.BOLD)
    if i>=110:return clr("Above Average",C.GREEN,C.BOLD)
    if i>=90:return clr("Average",C.YELLOW,C.BOLD)
    if i>=80:return clr("Below Average",C.RED)
    return clr("Developing",C.RED)

def generate_insights(r):
    s={}
    for x in r:
        c=x["category"]
        s.setdefault(c,{"correct":0,"total":0,"time":0})
        s[c]["total"]+=1
        s[c]["time"]+=x["time_taken"]
        if x["correct"]:s[c]["correct"]+=1
    strong=[];weak=[];slow=[]
    for c,v in s.items():
        acc=v["correct"]/v["total"]
        avg=v["time"]/v["total"]
        if acc>=0.7:strong.append(c)
        if acc<0.4:weak.append(c)
        if avg>DIFFICULTY_TIME["Medium"]:slow.append(c)
    return strong,weak,slow

def banner():
    clear()
    print(clr("AI IQ TEST - powered by Groq",C.CYAN,C.BOLD))

def divider():print(clr("  "+"─"*44,C.DIM))

def print_dashboard(r,d):
    c=sum(1 for x in r if x["correct"]);t=len(r)
    iq=estimate_iq(r,d)
    avg=sum(x["time_taken"] for x in r)/t
    acc=c/t*100
    banner()
    print(clr("\n  RESULTS DASHBOARD\n",C.BOLD));divider()
    print(f"\n  {'Estimated IQ':<22} {clr(iq,C.CYAN,C.BOLD)}  {iq_label(iq)}")
    print(f"  {'Score':<22} {clr(f'{c} / {t}',C.BOLD)}")
    print(f"  {'Accuracy':<22} {clr(f'{acc:.0f}%',C.BOLD)}")
    print(f"  {'Avg Response Time':<22} {clr(f'{avg:.1f}s',C.BOLD)}")
    print(f"  {'Difficulty':<22} {clr(d,C.BOLD)}\n")
    divider()
    strong,weak,slow=generate_insights(r)
    print(clr("\n  AI Insights\n",C.BOLD))
    if strong:
        print(clr("  Strong Areas:",C.GREEN,C.BOLD))
        for s in strong:print(f"   - {s}")
    if weak:
        print(clr("\n  Weak Areas:",C.RED,C.BOLD))
        for w in weak:print(f"   - {w}")
    if slow:
        print(clr("\n  Needs Speed Improvement:",C.YELLOW,C.BOLD))
        for s in slow:print(f"   - {s}")

class IQTestApp:
    def __init__(self):
        k=os.environ.get("GROQ_API_KEY","")
        if not k:
            print("Set GROQ_API_KEY");sys.exit(1)
        self.client=Groq(api_key=k)
        self.score=0;self.last_results=[]
        self.difficulty="Medium";self.categories=list(CATEGORIES.values());self.q_count=5

    def display_menu(self):
        banner()
        print("1 Take Test\n2 Show Score\n3 Exit")
        ch=input("Choice: ").strip()
        {"1":self.take_test,"2":self.show_score,"3":self.exit_app}.get(ch,lambda:None)()

    def take_test(self):
        try:q=generate_questions(self.client,self.categories,self.difficulty,self.q_count)
        except Exception as e:
            print(e);return
        r=[]
        for x in q:
            print(x["question"])
            for k,v in x["options"].items():
                print(f"{k}. {v}")
            ans=input("A/B/C/D: ").strip().upper()
            r.append({"category":x["category"],"correct":ans==x["answer"],"time_taken":1})
        self.last_results=r
        print_dashboard(r,self.difficulty)

    def show_score(self):
        if self.last_results:
            print_dashboard(self.last_results,self.difficulty)

    def exit_app(self):
        sys.exit()

if __name__=="__main__":
    app=IQTestApp()
    while True:app.display_menu()