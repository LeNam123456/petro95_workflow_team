# -*- coding: utf-8 -*-
import os

def fix_file(p):
    if not os.path.exists(p):
        return
    with open(p, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if line ends with unclosed quote
        if line.strip() == 'print("' and i + 1 < len(lines):
            next_line = lines[i + 1]
            fixed_lines.append('    print("\\n' + next_line.lstrip())
            i += 2
            continue
        elif 'print("\\n' in line and not line.strip().endswith('")'):
            # It's split across lines
            combined = line.rstrip() + ' ' + lines[i+1].lstrip()
            fixed_lines.append(combined)
            i += 2
            continue
        else:
            fixed_lines.append(line)
            i += 1
            
    with open(p, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    print(f"Cleaned {p}")

for base in [r"D:\Petro_95\SPAFS_DELIVERABLES_PACKAGE", r"C:\Users\LeeNam\Downloads\SPAFS_DELIVERABLES_PACKAGE"]:
    fix_file(os.path.join(base, "01_run_m3_asymmetric_adl_and_wald_test.py"))
    fix_file(os.path.join(base, "02_train_predict_evaluate_m4_m5.py"))
