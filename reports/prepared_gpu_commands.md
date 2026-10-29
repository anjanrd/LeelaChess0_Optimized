# Prepared GPU commands — NOT RUN

Prepared 2026-10-28T10:57:04+05:30; run from `C:\Users\HP\Desktop\LC0-B\leela-int8`. Existing study remains untouched.

Run only after the existing study/score has finished and nvidia-smi confirms GPU idle. Use one script at a time. Each launcher runs hidden in the background, writes stdout/stderr logs, and stops on its first nonzero model exit. Rerunning the same command resumes completed JSONL keys.

Hard low-budget study: existing --ids option, 43 positions, six models, five budgets; output is results/hard_lowbudget/<model>/study_b.jsonl. Study A is not requested. Threads=1 and MinibatchSize=256 preserve current config uniformly; nodes can overshoot the requested low budgets by up to a minibatch (README trap 6), so compare recorded actual nodes. This does not promise exact 10/25/50/100/200-node searches.

studyc uses current config: fp16 and s4; 200,800 ms; limit=0 (all test positions); default engine Threads; MoveOverheadMs=20. hw uses all configured parts: bench,sweep,trt,roofline. Its bench models are hardcoded in ladder.py as fp16,best,native = fp16,s4,native. s4aa cannot be added through config; no code/config changed.

## hard_lowbudget

```powershell
& 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 'fp16' '--weights' 'models/fp16.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=6' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'
& 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's1' '--weights' 'models/s1.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'
& 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's2' '--weights' 'models/s2.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'
& 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's3' '--weights' 'models/s3.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'
& 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's4' '--weights' 'models/s4.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'
& 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's4aa' '--weights' 'models/s4aa.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'
```

Prepared background launcher (not executed):

```powershell
Start-Process -FilePath powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "C:\Users\HP\Desktop\LC0-B\leela-int8\reports\prepared_hard_lowbudget.ps1"'
```

## studyc

```powershell
& 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'ladder.py' 'studyc'
```

Prepared background launcher (not executed):

```powershell
Start-Process -FilePath powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "C:\Users\HP\Desktop\LC0-B\leela-int8\reports\prepared_studyc.ps1"'
```

## hw

```powershell
& 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'ladder.py' 'hw'
```

Prepared background launcher (not executed):

```powershell
Start-Process -FilePath powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "C:\Users\HP\Desktop\LC0-B\leela-int8\reports\prepared_hw.ps1"'
```

