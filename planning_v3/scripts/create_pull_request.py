from pathlib import Path
import subprocess,json,urllib.parse
P=Path(__file__).resolve().parents[1];repo=P.parent;branch='planning-v3-cartography-20261028';name='yijunw811-sketch/shanghai-city-model';title='GIS V3：真实卫星、66.0948公顷设计边界与多尺度制图升级'
current=subprocess.check_output(['git','branch','--show-current'],cwd=repo,text=True).strip()
if current!=branch:raise SystemExit('Dedicated V3 branch required; main must not change')
r=subprocess.run(['gh','pr','create','--repo',name,'--base','main','--head',branch,'--draft','--title',title,'--body-file',str(P/'reports/PR_BODY.md')],cwd=repo,text=True,capture_output=True)
body='GIS V3：39张图、66.0948ha真实设计线、10m卫星、多尺度统计。正文见planning_v3/reports/PR_BODY.md；下载见planning_v3/downloads/RESULTS_INDEX.md。'
entry='https://github.com/'+name+'/compare/main...'+branch+'?'+urllib.parse.urlencode({'expand':'1','title':title,'body':body})
result={'branch':branch,'base':'main','main_not_merged':True,'returncode':r.returncode,'status':'created' if r.returncode==0 else 'blocked_API_access','output':r.stdout.strip() if r.returncode==0 else (r.stderr or r.stdout).strip()[:2000],'create_PR_entry_not_existing_PR':entry,'full_PR_body':'planning_v3/reports/PR_BODY.md'}
(P/'downloads/github_delivery_status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(r.returncode)
