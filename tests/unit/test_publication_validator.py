from copy import deepcopy
import pytest
from scripts.publication_tables import ROOT,tables,latex
from scripts.validate_manuscript_consistency import check_rows,tex_rows,pdf_tables,source_digest

def test_published_benchmark_table():
    spec = tables()['table2_main_benchmark']
    check_rows(tex_rows((ROOT/'paper/tables/table2_main_benchmark.tex').read_text()),[spec[1],*spec[2]],'benchmark')

@pytest.mark.parametrize('fault',['wrong value','swapped row','swapped column','missing method','missing regime','rounding'])
def test_table_corruption(fault):
    spec = tables()['table2_main_benchmark']
    header,rows = deepcopy(spec[1:])
    if fault=='wrong value':
        rows[0][2]='0.9999'
    elif fault=='swapped row':
        rows[0],rows[-1]=rows[-1],rows[0]
    elif fault=='swapped column':
        rows[0][2],rows[0][3]=rows[0][3],rows[0][2]
    elif fault=='missing method':
        for row in [header,*rows]:
            del row[-2:]
    elif fault=='missing regime':
        rows=[r for r in rows if not r[0].startswith('E3')]
    else:
        rows[0][2]=f'{float(rows[0][2])+0.0001:.4f}'
    broken = latex((spec[0],header,rows))
    with pytest.raises(ValueError):
        check_rows(tex_rows(broken),[spec[1],*spec[2]],'benchmark')

def test_reject_stale_real_pdf():
    with pytest.raises(ValueError,match='Stale PDF'):
        pdf_tables(ROOT/'paper/manuscript.pdf',tables(),source_digest(ROOT)+'changed')

