from pathlib import Path
import importlib.util, json, math, subprocess, sys, types, os, zipfile
from unittest.mock import patch
import pandas as pd

root=Path(__file__).resolve().parents[1]
downloads=root/"public/downloads"
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
lesson=load("lesson",downloads/"lesson_01.py")
data=pd.read_csv(downloads/"demo_prices.csv")
refs=json.loads((root/"tests/fixtures/reference-signals.json").read_text())
for ref in refs:
    actual=lesson.build_signals(data,ref["short"],ref["long"])
    for i,row in enumerate(ref["rows"]):
        for python_name,js_name in [("sma_short","short"),("sma_long","long")]:
            value=actual.iloc[i][python_name]
            if row[js_name] is None: assert pd.isna(value)
            else: assert math.isclose(value,row[js_name],rel_tol=1e-12,abs_tol=1e-10)
        assert int(actual.iloc[i]["target"])==row["target"]
        assert int(actual.iloc[i]["next_open_target"])==row["nextOpenTarget"]
        assert bool(actual.iloc[i]["changed"])==row["changed"]
print("PASS: all 120 rows match JS and pandas for 3 parameter pairs.")

api=load("bars",downloads/"webull_bars.py")
calls={}
class FakeApiClient:
    def __init__(self,key,secret,region): calls["region"]=region
    def add_endpoint(self,region,host): calls["host"]=host
    def set_stream_logger(self,**kwargs): pass
class FakeDataClient:
    def __init__(self,client): self.market_data=self
    def get_batch_history_bar(self,**kwargs):
        calls["params"]=kwargs
        return types.SimpleNamespace(status_code=200,json=lambda:{"result":[]})
modules={"webull":types.ModuleType("webull"),"webull.core":types.ModuleType("webull.core"),"webull.core.client":types.ModuleType("webull.core.client"),"webull.data":types.ModuleType("webull.data"),"webull.data.data_client":types.ModuleType("webull.data.data_client")}
modules["webull.core.client"].ApiClient=FakeApiClient
modules["webull.data.data_client"].DataClient=FakeDataClient
with patch.dict(sys.modules,modules),patch.dict(os.environ,{"WEBULL_APP_KEY":"TEST_ONLY","WEBULL_APP_SECRET":"TEST_ONLY"}):
    assert api.fetch_bars()=={"result":[]}
assert calls["region"]=="th"
assert calls["host"]=="th-api.uat.webullbroker.com"
assert calls["params"]==dict(symbols=["AAPL"],category="US_STOCK",timespan="D",count=120,real_time_required=True,trading_sessions="RTH")
print("PASS: read-only SDK adapter mocked with UAT and exact documented params.")
r=subprocess.run([sys.executable,str(downloads/"webull_bars.py")],capture_output=True,text=True,check=True)
assert "No network request" in r.stdout
print("PASS: default script path does not import/connect the SDK.")
nb=json.loads((downloads/"robo-trade-01.ipynb").read_text())
assert len([c for c in nb["cells"] if c["cell_type"]=="code"])==9
assert not any(o.get("output_type")=="error" for c in nb["cells"] for o in c.get("outputs",[]))
with zipfile.ZipFile(downloads/"robo-trade-01-materials.zip") as z:
    assert z.testzip() is None and len(z.namelist())==6
    assert not any(n.endswith(".pdf") for n in z.namelist())
print("PASS: executed notebook and 6-file teaching ZIP are valid; no source PDF included.")
print("Environment: Python",sys.version.split()[0],"pandas",pd.__version__)
