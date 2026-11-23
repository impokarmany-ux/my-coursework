import re
def ed(p,pairs):
    s=open(p,encoding="utf-8").read()
    for o,n in pairs:
        assert o in s,(p,o); s=s.replace(o,n,1)
    open(p,"w",encoding="utf-8").write(s)
# 16_run_full: мир из параметра, альянс по тегу в выбранном мире, файл-стоп панели
s=open("16_run_full.py",encoding="utf-8").read()
s=s.replace('if int(bd.get("kingdom") or 0) != 837: raise SystemExit("СТОП: bundle не 837")','if int(bd.get("kingdom") or 0) != a.world: raise SystemExit(f"СТОП: bundle не {a.world}")',1)
assert "!= a.world: raise SystemExit(f\"СТОП: bundle" in s
o='if int(hit[0].get("world_id") or 0) != a.world or int(hit[0]["alliance_id"]) != ALLY_EXPECT:'
n='if int(hit[0].get("world_id") or 0) != a.world or (want == "3cy" and int(hit[0]["alliance_id"]) != ALLY_EXPECT) or hit[0].get("alliance_id") is None:'
assert o in s; s=s.replace(o,n,1)
o='ALLY = ALLY_EXPECT; extra'; assert o in s; s=s.replace(o,'ALLY = int(hit[0]["alliance_id"]); extra',1)
o='    for s in steps:\n'; assert o in s
s=s.replace(o,o+'        # панель: файл-стоп - аккуратно выходим перед следующей командой\n        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "panel_stop.flag")): raise SystemExit(f"СТОП: остановлено панелью - продолжать --from {s[\'idx\']}")\n',1)
open("16_run_full.py","w",encoding="utf-8").write(s)
# 16_state_new: необязательный мир вторым аргументом
ed("16_state_new.py",[('print("RESULT_837", w == ["837"])','WANT = sys.argv[2] if len(sys.argv) > 2 else "837"\nprint("RESULT_837", w == ["837"])\nprint("RESULT_OK", w == [str(WANT)])')])
# _once_castle_gw: королевство из --kingdom
ed("_once_castle_gw.py",[('KINGDOM = 837','KINGDOM = int(sys.argv[sys.argv.index("--kingdom") + 1]) if "--kingdom" in sys.argv else 837')])
print("ok")
