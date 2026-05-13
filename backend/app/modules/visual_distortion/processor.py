import zipfile
import xml.etree.ElementTree as ET
import csv
import os
from datetime import datetime

class VDDataProcessor:
    """
    Official Data Cleaning Layer for Aseer Visual Distortion Dashboard.
    Handles extraction, filtering, deduplication, and refinement.
    """
    
    # Columns to KEEP (from original 28 columns)
    KEEP_INDICES = {
        2: "البلدية",
        5: "رقم البلاغ المجمع",
        6: "رقم الزيارة لدى ممتثل",
        7: "رقم البلاغ لدى Crm",
        10: "حالة البلاغ",
        11: "حالة الزيارة",
        13: "تاريخ الاسناد",
        14: "تاريخ الاغلاق",
        15: "احداثي X",
        16: "احداثي Y",
        17: "اسم التصنيف",
        20: "اسم النطاق",
        22: "الحالة حسب الاغلاق"
    }

    DEDUPE_COL_INDEX = 5 # رقم البلاغ المجمع
    
    # Geographic Bounds
    MIN_LON, MAX_LON = 40.0, 46.0
    MIN_LAT, MAX_LAT = 16.0, 21.0

    @staticmethod
    def parse_date(date_str):
        if not date_str or date_str.strip() == "": return None
        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%y %I:%M:%S %p'):
            try: return datetime.strptime(date_str, fmt)
            except: continue
        return None

    # Strategic Management Categorization Mapping
    MANAGEMENT_MAPPING = {
        # Group 1: Regulatory & Policy (Enforcement based)
        "تسوير المباني تحت الإنشاء": ("Regulatory & Policy", "Regulatory (Construction)"),
        "مخلفات البناء": ("Regulatory & Policy", "Regulatory (Construction)"),
        "مجاري وتمديدات التكييف": ("Regulatory & Policy", "Regulatory (Construction)"),
        "الهناجر المخالفة فوق السطوح": ("Regulatory & Policy", "Regulatory (Construction)"),
        "التشوين": ("Regulatory & Policy", "Regulatory (Construction)"),
        "نقل مواد البناء": ("Regulatory & Policy", "Regulatory (Construction)"),
        "الحواجز الخرسانية": ("Regulatory & Policy", "Regulatory (Construction)"),
        "أطباق الأقمار الصناعية": ("Regulatory & Policy", "Regulatory (Construction)"),
        "تغطية الشرفات": ("Regulatory & Policy", "Regulatory (Construction)"),
        "وقوف السيارات الغير المصرح بها": ("Regulatory & Policy", "Regulatory (Construction)"),
        "واجهات المباني المتهالكة": ("Regulatory & Policy", "Regulatory (Construction)"),
        "تغطية المباني تحت الإنشاء": ("Regulatory & Policy", "Regulatory (Construction)"),
        "مداخن التهوية في المطاعم": ("Regulatory & Policy", "Regulatory (Construction)"),
        "السيارات التالفة": ("Regulatory & Policy", "Regulatory (Construction)"),
        "المباني المهجورة": ("Regulatory & Policy", "Regulatory (Construction)"),
        "اللوحات التجارية": ("Regulatory & Policy", "Service (Signage)"),
        "اللوحات التحذيرية": ("Regulatory & Policy", "Service (Signage)"),
        "اللوحات الإرشادية": ("Regulatory & Policy", "Service (Signage)"),
        "اللوحات الإعلانية": ("Regulatory & Policy", "Service (Signage)"),
        "أعمدة الاتصالات": ("Regulatory & Policy", "Service (Signage)"),

        # Group 2: Resource & Funding (O&M / Budget based)
        "الكتابة المشوهة للجدران والدهان": ("Resource & Funding", "Regulatory (Behavioral)"),
        "المظلات والخيام": ("Resource & Funding", "Regulatory (Behavioral)"),
        "الباعة المتجولون": ("Resource & Funding", "Regulatory (Behavioral)"),
        "عدم دهان الشوارع": ("Resource & Funding", "Service (Infrastructure)"),
        "حفر الشوارع": ("Resource & Funding", "Service (Infrastructure)"),
        "الأرصفة المتهالكة": ("Resource & Funding", "Service (Infrastructure)"),
        "الحاويات وتكدس النفايات": ("Resource & Funding", "Service (Infrastructure)"),
        "دهان البردورات": ("Resource & Funding", "Service (Infrastructure)"),
        "تكسيات المباني المتهالكة": ("Resource & Funding", "Service (Infrastructure)"),
        "أعمدة الإنارة": ("Resource & Funding", "Service (Infrastructure)"),
        "نظافة الأماكن العامة": ("Resource & Funding", "Service (Infrastructure)"),
        "أثاث الشوارع": ("Resource & Funding", "Service (Infrastructure)"),
        "محولات الكهرباء في الشوارع": ("Resource & Funding", "Service (Infrastructure)"),
        "تشجير الأرصفة وممرات المشاة": ("Resource & Funding", "Service (Infrastructure)"),
        "مشاريع الخدمات والحفريات": ("Resource & Funding", "Service (Infrastructure)"),
        "دورات المياه العامة": ("Resource & Funding", "Service (Infrastructure)")
    }

    def process_file(self, xlsx_path, output_csv):
        print(f"--- Starting Unified Cleaning Layer (Strategic Edition) ---")
        seen_ids = set()
        stats = {"total": 0, "unique": 0, "date_fixes": 0, "coord_fixes": 0, "unmapped": 0}
        
        with zipfile.ZipFile(xlsx_path, 'r') as z:
            strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                with z.open('xl/sharedStrings.xml') as f:
                    context = ET.iterparse(f, events=('end',))
                    for _, elem in context:
                        if elem.tag.endswith('t'): strings.append(elem.text or "")
                        elif elem.tag.endswith('si'): elem.clear()

            with z.open('xl/worksheets/sheet1.xml') as f:
                with open(output_csv, 'w', encoding='utf-8', newline='') as out_f:
                    # Added two new columns for management analysis
                    output_headers = [self.KEEP_INDICES[i] for i in sorted(self.KEEP_INDICES.keys())]
                    output_headers += ["مجموعة الإدارة", "التصنيف النوعي"]
                    
                    writer = csv.writer(out_f)
                    writer.writerow(output_headers)
                    
                    context = ET.iterparse(f, events=('start', 'end'))
                    row_data = {}
                    row_idx = 0
                    
                    for event, elem in context:
                        if event == 'start' and elem.tag.endswith('row'):
                            row_data = {}
                        elif event == 'end' and elem.tag.endswith('c'):
                            ref = elem.get('r')
                            col_ref = ''.join([char for char in ref if char.isalpha()])
                            c_idx = 0
                            for char in col_ref: c_idx = c_idx * 26 + (ord(char.upper()) - ord('A') + 1)
                            c_idx -= 1
                            
                            if c_idx in self.KEEP_INDICES:
                                t = elem.get('t')
                                v_elem = elem.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                                val = v_elem.text if v_elem is not None else ""
                                if t == 's' and val: val = strings[int(val)]
                                row_data[c_idx] = val
                        
                        elif event == 'end' and elem.tag.endswith('row'):
                            if row_idx > 0:
                                rid = row_data.get(self.DEDUPE_COL_INDEX)
                                if rid and rid not in seen_ids:
                                    seen_ids.add(rid)
                                    
                                    # Strategic Mapping Logic
                                    cls_name = row_data.get(17, "").strip()
                                    mapping = self.MANAGEMENT_MAPPING.get(cls_name, ("Other", "Other"))
                                    if mapping[0] == "Other": stats["unmapped"] += 1
                                    
                                    # Date Logic
                                    d_assign = self.parse_date(row_data.get(13))
                                    d_close = self.parse_date(row_data.get(14))
                                    if d_assign and d_close and d_close < d_assign:
                                        row_data[14] = row_data[13]
                                        stats["date_fixes"] += 1
                                    
                                    # Geo Logic
                                    try:
                                        lon = float(row_data.get(15, 0))
                                        lat = float(row_data.get(16, 0))
                                        if not (self.MIN_LON <= lon <= self.MAX_LON and self.MIN_LAT <= lat <= self.MAX_LAT):
                                            row_data[15] = row_data[16] = ""
                                            stats["coord_fixes"] += 1
                                    except:
                                        row_data[15] = row_data[16] = ""
                                        stats["coord_fixes"] += 1
                                        
                                    output_row = [row_data.get(i, "") for i in sorted(self.KEEP_INDICES.keys())]
                                    output_row += [mapping[0], mapping[1]]
                                    writer.writerow(output_row)
                                    stats["unique"] += 1
                            
                            stats["total"] += 1
                            row_idx += 1
                            if row_idx % 50000 == 0: print(f"Processed {row_idx} rows...")
                            elem.clear()
        
        print(f"--- Processing Summary ---")
        print(f"Total: {stats['total']} | Unique: {stats['unique']} | Unmapped Classifications: {stats['unmapped']}")
        return stats

if __name__ == "__main__":
    p = VDDataProcessor()
    p.process_file("مختصر بوابة البلاغات_Tab 1_التفاصيل_20260509_1535.xlsx", "scratch/vd_master_clean.csv")
