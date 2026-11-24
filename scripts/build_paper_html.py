"""Build both PDFs and alternate manuscript formats from the same LaTeX."""
import os
import shutil
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
import sys
import pypandoc
from pypdf import PdfWriter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.publication_tables import ROOT,tables,latex
from scripts.validate_manuscript_consistency import source_digest

def build():
    paper = ROOT/'paper'
    for name,spec in tables().items():
        for directory in [paper/'tables',ROOT/'results/tables']:
            (directory/(name+'.tex')).write_text(latex(spec),encoding='utf8')
    for fig in (ROOT/'results/figures').iterdir():
        if fig.suffix in ('.pdf','.png'):
            shutil.copyfile(fig,paper/'figures'/fig.name)
    digest = source_digest(ROOT)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        for name in ['cover_letter','manuscript','supplementary']:
            subprocess.run([os.environ.get('TECTONIC','tectonic'),'--keep-logs','--outdir',td,name+'.tex'],cwd=paper,check=True)
            log = (out/(name+'.log')).read_text(errors='replace')
            for phrase in ['undefined references','Citation ','multiply defined','Overfull \\hbox']:
                if phrase in log:
                    raise ValueError(f'Inspect {name} compilation: {phrase} '+str([l for l in log.splitlines() if phrase in l][:3]))
        for name,parts in [('manuscript',['manuscript']),('supplementary',['supplementary']),('submission_package',['cover_letter','manuscript'])]:
            writer = PdfWriter()
            for part in parts:
                writer.append(out/(part+'.pdf'))
            writer.add_metadata({'/SourceDigest':digest})
            writer.write(paper/(name+'.pdf'))
    pandoc = pypandoc.get_pandoc_path()
    for document in ['manuscript','supplementary']:
        for fmt,ext in [('gfm','md'),('html5','html')]:
            args = [pandoc,document+'.tex','--from=latex','--citeproc','--bibliography=references.bib','--to='+fmt,'--wrap=none']
            if ext=='html':args += ['--standalone','--mathml']
            text = subprocess.check_output(args,cwd=paper,text=True,encoding='utf8').replace('.pdf"', '.png"').replace('.pdf)', '.png)')
            if ext == 'md':
                import re
                source = (paper/(document+'.tex')).read_text(encoding='utf8')
                abstract = source.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0].strip()
                title=re.search(r'\\title\{([^}]+)\}',source)[1]
                text = '# '+title+'\n\n## Abstract\n\n'+abstract+'\n\n'+text
            (paper/(document+'.'+ext)).write_text(text,encoding='utf8')
    subprocess.run([pandoc,'cover_letter.tex','-t','gfm','-o','cover_letter.md'],cwd=paper,check=True)
    with ZipFile(paper/'submission_package.zip','w',compression=ZIP_DEFLATED) as archive:
        for name in ['manuscript.tex','related_work.tex','supplementary.tex','supplementary.pdf','references.bib','manuscript.pdf','cover_letter.tex','submission_package.pdf']:
            archive.write(paper/name,name)
        for directory in ['figures','tables']:
            for path in sorted((paper/directory).glob('*')):
                archive.write(path,path.relative_to(paper))
        archive.write(ROOT/'README.md','supplement/REPRODUCE.md')
        for name in ['PREDICTION_TIME_VALIDITY_AUDIT','EXTERNAL_VALIDATION_PROTOCOL','EXTERNAL_DATA_PROVENANCE',
                     'DATA_AND_SOFTWARE_LICENSING','RELIABILITY_USEFULNESS_ANALYSIS','STATISTICAL_INFERENCE_AUDIT','SESSION_SEGMENTATION_AUDIT',
                     'CONFORMAL_MATHEMATICS_AUDIT','MISSINGNESS_CALIBRATION_AUDIT','EXTERNAL_SIRHAN_COMPARISON',
                     'CLOCK_TRIGGERED_PRIMARY_MODEL_AUDIT','STATISTICAL_DESIGN_IMPROVEMENT','CROSS_NETWORK_GENERALIZATION',
                     'RESEARCH_BASELINE_AUDIT','NOVELTY_COMPARISON_MATRIX','PROPOSED_METHOD_FORMULATION',
                     'EXPERIMENTAL_DESIGN','STATISTICAL_ANALYSIS_PLAN','REPRODUCIBILITY_AUDIT',
                     'MATCHED_COST_ANALYSIS','PROSPECTIVE_VALIDATION_PROTOCOL',
                     'MARUR_IMPLEMENTATION_SPECIFICATION','NOVELTY_AND_CONTRIBUTION_AUDIT','PROSPECTIVE_VALIDATION_READINESS_AUDIT',
                     'MARUR_INFORMATION_EXPERIMENT_PROTOCOL','MARUR_INFORMATION_EXPERIMENT_RESULTS',
                     'REVIEWER_BASELINE_PROTOCOL','REVIEWER_BASELINE_RESULTS','REVIEWER_REVISION_COMPLETION','PROSPECTIVE_VIDEO_VALIDATION_PLAN',
                     'REJECTION_RISK_REVISIONS','POSITIVE_OFFER_SELECTION','PLAYBACK_REPLAY_PROTOCOL','TRIP_AND_APPLICATION_RESULTS','DRIVE3_PROTOCOL','DRIVE3_REPLICATION','NR_STRESS_AUDIT','STATISTICAL_VALIDITY_AUDIT','EXTERNAL_VALIDATION_PLAN',
                     'ADVERSARIAL_ROBUSTNESS_AUDIT','PRIMARY_CONTRIBUTION_DECISION','RESEARCH_GAP_AND_NOVELTY_REVIEW']:
            archive.write(ROOT/'docs'/(name+'.md'),'supplement/'+name+'.md')

if __name__=='__main__':
    build()
