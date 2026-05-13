import pandas as pd
import json

df = pd.read_csv('مختصر بوابة البلاغات .csv', encoding='utf-8-sig')

# Indices
mun_idx = 0
id_idx = 1
cls_idx = 11
status_idx = 4
x_idx = 9
y_idx = 10

df['lat'] = pd.to_numeric(df.iloc[:, y_idx], errors='coerce')
df['lon'] = pd.to_numeric(df.iloc[:, x_idx], errors='coerce')
df = df.dropna(subset=['lat', 'lon'])
df['lat_grp'] = df['lat'].round(5)
df['lon_grp'] = df['lon'].round(5)

# Group by location and classification
groups = df.groupby(['lat_grp', 'lon_grp', df.columns[cls_idx]])

results = {}
total_recurrences_global = 0

for name, group in groups:
    mun = str(group.iloc[0, mun_idx]).strip()
    cls = str(name[2]).strip()
    
    # Logic: Only count as chronic if there was a closure
    has_been_closed = group[df.columns[status_idx]].astype(str).str.contains('مغلق').any()
    
    total_reports = len(group)
    if has_been_closed and total_reports > 1:
        # TRUE RECURRENCES = Total - 1 (The first one is the original)
        recurrence_count = total_reports - 1
        total_recurrences_global += recurrence_count
        
        mun_clean = mun.replace('بلدية ', '').strip()
        key = (mun_clean, cls)
        if key not in results: results[key] = []
        
        rep_ids = group[df.columns[id_idx]].astype(str).unique().tolist()
        results[key].append({
            'id': f"نقطة مزمنة ({total_reports} بلاغات)",
            'count': total_reports,
            'details': rep_ids
        })

final_data = {}
for (mun, cls), data in results.items():
    if mun not in final_data: final_data[mun] = {}
    final_data[mun][cls] = sorted(data, key=lambda x: x['count'], reverse=True)

with open('all_recurrences.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False)

print(f"Total True Recurrences: {total_recurrences_global}")
